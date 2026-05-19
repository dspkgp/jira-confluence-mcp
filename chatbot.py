import os
import json
from typing import Annotated, TypedDict, Any

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, ToolMessage, AIMessage, SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")

if not OPENAI_API_KEY or not OPENAI_MODEL:
    raise ValueError("Missing OPENAI_API_KEY or OPENAI_MODEL")


class AgentState(TypedDict):
    """State for the agent graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict[str, Any]


class AtlassianChatbot:
    def __init__(self):
        self.tools = []
        self.llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY)
        self.graph = None
        self.mcp_client = None
        self.system_prompt = """You are an AI assistant that helps users interact with Atlassian tools (JIRA and Confluence).

You can help users:
- Search, view, create, and update JIRA issues
- Search and view Confluence pages
- Add comments to JIRA issues
- Transition issues between statuses
- Get project information

When users ask about issues or pages, use the appropriate tools to fetch real data.
Always provide helpful, concise responses based on the actual data returned from the tools.
If a tool returns an error, explain it clearly to the user.
Do not provide any other information than the response from the tools."""

    async def initialize(self):
        """Initialize chatbot with MCP servers and available tools"""
        print("Initializing Atlassian Chatbot...")
        
        # Initialize MCP client with both servers
        self.mcp_client = MultiServerMCPClient(
            {
                "jira-mcp-server": {
                    "command": "python",
                    "args": ["jira_server.py"],
                    "transport": "stdio",
                },
                "confluence-mcp-server": {
                    "command": "python",
                    "args": ["confluence_server.py"],
                    "transport": "stdio",
                },
            }
        )
        
        # Get tools from MCP servers (new API - no context manager needed)
        self.tools = await self.mcp_client.get_tools()
        
        # Create the agent graph
        self._create_agent_graph()
        print(f"\n✓ Chatbot initialized successfully! ({len(self.tools)} tools available)")
        print("\nAvailable tools:")
        for t in self.tools:
            print(f"  - {t.name}: {t.description}")

    def _create_agent_graph(self):
        """Create the ReAct agent graph"""
        
        llm_with_tools = self.llm.bind_tools(self.tools)
        
        async def call_model(state: AgentState):
            """Node that calls the LLM"""
            messages = state["messages"]
            
            # Add system message if not present
            if not messages or not isinstance(messages[0], SystemMessage):
                messages = [SystemMessage(content=self.system_prompt)] + list(messages)
            
            response = await llm_with_tools.ainvoke(messages)
            return {"messages": [response]}
        
        async def tool_node(state: AgentState):
            """Node that executes tools via MCP servers"""
            messages = []
            last_message = state["messages"][-1]
            
            if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
                return {"messages": messages}
            
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call.get("args", {})
                
                # Find and call the tool
                tool_obj = None
                for t in self.tools:
                    if t.name == tool_name:
                        tool_obj = t
                        break
                
                if tool_obj:
                    try:
                        result = await tool_obj.ainvoke(tool_args)
                    except Exception as e:
                        result = json.dumps({"error": str(e)})
                else:
                    result = json.dumps({"error": f"Tool {tool_name} not found"})
                
                messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    )
                )
            
            return {"messages": messages}
        
        def should_continue(state: AgentState):
            """Determine if we should continue to tools or end"""
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return END
        
        # Build graph
        workflow = StateGraph(AgentState)
        
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)
        
        workflow.set_entry_point("agent")
        
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                END: END,
            },
        )
        
        workflow.add_edge("tools", "agent")
        
        self.graph = workflow.compile()

    async def chat(self, user_message: str, conversation_history: list = None) -> str:
        """
        Process a user message and return the chatbot response.
        
        Args:
            user_message: The user's input message
            conversation_history: Optional list of previous messages
        
        Returns:
            The chatbot's response
        """
        if conversation_history is None:
            conversation_history = []
        
        # Build messages list
        messages = []
        for item in conversation_history:
            if isinstance(item, dict):
                if item.get("role") == "user":
                    messages.append(HumanMessage(content=item["content"]))
                else:
                    messages.append(AIMessage(content=item["content"]))
            else:
                messages.append(item)
        
        messages.append(HumanMessage(content=user_message))
        
        # Run the agent
        state = {
            "messages": messages,
            "context": {}
        }
        
        result = await self.graph.ainvoke(state)
        
        # Extract the final response
        final_messages = result["messages"]
        
        # Find the last AI message
        for msg in reversed(final_messages):
            if isinstance(msg, AIMessage):
                return msg.content
            elif hasattr(msg, "content") and not isinstance(msg, ToolMessage):
                return msg.content
        
        # Fallback
        return str(final_messages[-1]) if final_messages else "No response"


async def create_chatbot() -> AtlassianChatbot:
    """Create and initialize a chatbot instance"""
    chatbot = AtlassianChatbot()
    await chatbot.initialize()
    return chatbot
