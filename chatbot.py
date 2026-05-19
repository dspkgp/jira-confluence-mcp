import os
import json
from typing import Annotated, TypedDict, Any

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, BaseMessage, ToolMessage, AIMessage, SystemMessage
from langchain_core.tools import tool
from dotenv import load_dotenv
from jira import JIRA
from atlassian import Confluence

load_dotenv()

# Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL")
JIRA_SERVER = os.getenv("JIRA_SERVER")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

if not OPENAI_API_KEY or not OPENAI_MODEL:
    raise ValueError("Missing OPENAI_API_KEY or OPENAI_MODEL")

# Initialize Atlassian clients
jira_client = None
confluence_client = None

def init_jira_client():
    global jira_client
    if jira_client is None and all([JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN]):
        jira_client = JIRA(
            server=JIRA_SERVER,
            basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
        )
    return jira_client

def init_confluence_client():
    global confluence_client
    if confluence_client is None and all([CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN]):
        confluence_client = Confluence(
            url=CONFLUENCE_URL,
            username=CONFLUENCE_EMAIL,
            password=CONFLUENCE_API_TOKEN
        )
    return confluence_client


class AgentState(TypedDict):
    """State for the agent graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    context: dict[str, Any]


class AtlassianChatbot:
    def __init__(self):
        self.tools = []
        self.llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY)
        self.graph = None
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
        """Initialize chatbot with available tools"""
        print("Initializing Atlassian Chatbot...")
        
        # Initialize API clients
        init_jira_client()
        init_confluence_client()
        
        # Create tool wrappers for JIRA
        self._create_jira_tools()
        
        # Create tool wrappers for Confluence
        self._create_confluence_tools()
        
        # Create the agent graph
        self._create_agent_graph()
        print(f"\n✓ Chatbot initialized successfully! ({len(self.tools)} tools available)")
        print("\nAvailable tools:")
        for t in self.tools:
            print(f"  - {t.name}: {t.description}")

    def _create_jira_tools(self):
        """Create JIRA tool wrappers with real API calls"""
        
        @tool("get_jira_projects")
        def get_projects_tool() -> str:
            """Get all JIRA projects accessible to the user"""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                projects = client.projects()
                result = []
                for proj in projects:
                    result.append({
                        "key": proj.key,
                        "name": proj.name,
                        "id": proj.id
                    })
                return json.dumps({"projects": result, "total": len(result)})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("get_jira_issue")
        def get_issue_tool(issue_key: str) -> str:
            """Get JIRA issue details by issue key (e.g., KAN-1, PROJ-123)"""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                issue = client.issue(issue_key)
                return json.dumps({
                    "key": issue.key,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name,
                    "issue_type": issue.fields.issuetype.name,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                    "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
                    "priority": issue.fields.priority.name if issue.fields.priority else "None",
                    "description": str(issue.fields.description) if issue.fields.description else "",
                    "created": str(issue.fields.created),
                    "updated": str(issue.fields.updated),
                })
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("search_jira_issues")
        def search_issues_tool(jql: str, limit: int = 10) -> str:
            """Search JIRA issues using JQL query language. Examples:
            - 'project = KAN' - all issues in KAN project
            - 'status = "In Progress"' - issues in progress
            - 'assignee = currentUser()' - your assigned issues
            - 'project = KAN AND status = Done' - done issues in KAN"""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                issues = client.search_issues(jql, maxResults=limit)
                results = []
                for issue in issues:
                    results.append({
                        "key": issue.key,
                        "summary": issue.fields.summary,
                        "status": issue.fields.status.name,
                        "issue_type": issue.fields.issuetype.name,
                        "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                        "priority": issue.fields.priority.name if issue.fields.priority else "None",
                    })
                return json.dumps({"issues": results, "total": len(results), "jql": jql})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("create_jira_issue")
        def create_issue_tool(project_key: str, summary: str, description: str = "", issue_type: str = "Task") -> str:
            """Create a new JIRA issue in the specified project"""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                issue = client.create_issue(
                    project=project_key,
                    summary=summary,
                    description=description,
                    issuetype={"name": issue_type}
                )
                return json.dumps({
                    "success": True,
                    "issue_key": issue.key,
                    "summary": summary,
                    "message": f"Issue {issue.key} created successfully"
                })
            except Exception as e:
                return json.dumps({"error": str(e), "success": False})
        
        @tool("update_jira_issue")
        def update_issue_tool(issue_key: str, summary: str = "", description: str = "") -> str:
            """Update fields in a JIRA issue. Provide only the fields you want to change."""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                issue = client.issue(issue_key)
                fields = {}
                if summary:
                    fields["summary"] = summary
                if description:
                    fields["description"] = description
                
                if fields:
                    issue.update(fields=fields)
                    return json.dumps({
                        "success": True,
                        "issue_key": issue_key,
                        "message": f"Issue {issue_key} updated successfully",
                        "updated_fields": list(fields.keys())
                    })
                else:
                    return json.dumps({"error": "No fields provided to update"})
            except Exception as e:
                return json.dumps({"error": str(e), "success": False})
        
        @tool("add_jira_comment")
        def add_comment_tool(issue_key: str, comment: str) -> str:
            """Add a comment to a JIRA issue"""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                client.add_comment(issue_key, comment)
                return json.dumps({
                    "success": True,
                    "issue_key": issue_key,
                    "message": f"Comment added to {issue_key} successfully"
                })
            except Exception as e:
                return json.dumps({"error": str(e), "success": False})
        
        @tool("get_issue_transitions")
        def get_transitions_tool(issue_key: str) -> str:
            """Get available status transitions for a JIRA issue"""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                transitions = client.transitions(issue_key)
                result = []
                for t in transitions:
                    result.append({
                        "id": t["id"],
                        "name": t["name"],
                        "to_status": t["to"]["name"]
                    })
                return json.dumps({"issue_key": issue_key, "transitions": result})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("transition_jira_issue")
        def transition_issue_tool(issue_key: str, transition_name: str) -> str:
            """Move a JIRA issue to a new status. Use get_issue_transitions first to see available transitions."""
            try:
                client = init_jira_client()
                if not client:
                    return json.dumps({"error": "JIRA client not configured. Check environment variables."})
                
                transitions = client.transitions(issue_key)
                target_id = None
                for t in transitions:
                    if t["name"].lower() == transition_name.lower():
                        target_id = t["id"]
                        break
                
                if not target_id:
                    available = [t["name"] for t in transitions]
                    return json.dumps({
                        "error": f"Transition '{transition_name}' not found",
                        "available_transitions": available
                    })
                
                client.transition_issue(issue_key, target_id)
                return json.dumps({
                    "success": True,
                    "issue_key": issue_key,
                    "message": f"Issue {issue_key} transitioned to '{transition_name}'"
                })
            except Exception as e:
                return json.dumps({"error": str(e), "success": False})
        
        self.tools.extend([
            get_projects_tool,
            get_issue_tool,
            search_issues_tool,
            create_issue_tool,
            update_issue_tool,
            add_comment_tool,
            get_transitions_tool,
            transition_issue_tool,
        ])

    def _create_confluence_tools(self):
        """Create Confluence tool wrappers with real API calls"""
        
        @tool("search_confluence")
        def search_confluence_tool(query: str, limit: int = 10) -> str:
            """Search for Confluence pages by text query"""
            try:
                client = init_confluence_client()
                if not client:
                    return json.dumps({"error": "Confluence client not configured. Check environment variables."})
                
                results = client.cql(f'type=page AND text~"{query}"', limit=limit)
                pages = []
                for result in results.get("results", []):
                    content = result.get("content", result)
                    pages.append({
                        "id": content.get("id"),
                        "title": content.get("title"),
                        "space": content.get("space", {}).get("key", "Unknown"),
                        "url": content.get("_links", {}).get("webui", ""),
                    })
                return json.dumps({"pages": pages, "total": len(pages), "query": query})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("get_confluence_page")
        def get_confluence_page_tool(page_id: str) -> str:
            """Get the full content of a Confluence page by its ID"""
            try:
                client = init_confluence_client()
                if not client:
                    return json.dumps({"error": "Confluence client not configured. Check environment variables."})
                
                page = client.get_page_by_id(page_id, expand="body.storage,version")
                return json.dumps({
                    "id": page.get("id"),
                    "title": page.get("title"),
                    "space": page.get("space", {}).get("key"),
                    "version": page.get("version", {}).get("number"),
                    "content": page.get("body", {}).get("storage", {}).get("value", "")[:2000],
                    "url": page.get("_links", {}).get("webui", ""),
                })
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("get_confluence_spaces")
        def get_spaces_tool() -> str:
            """Get all Confluence spaces accessible to the user"""
            try:
                client = init_confluence_client()
                if not client:
                    return json.dumps({"error": "Confluence client not configured. Check environment variables."})
                
                spaces = client.get_all_spaces(limit=50)
                result = []
                for space in spaces.get("results", []):
                    result.append({
                        "key": space.get("key"),
                        "name": space.get("name"),
                        "type": space.get("type"),
                    })
                return json.dumps({"spaces": result, "total": len(result)})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("get_space_pages")
        def get_space_pages_tool(space_key: str, limit: int = 10) -> str:
            """Get pages in a Confluence space"""
            try:
                client = init_confluence_client()
                if not client:
                    return json.dumps({"error": "Confluence client not configured. Check environment variables."})
                
                pages = client.get_all_pages_from_space(space_key, limit=limit)
                result = []
                for page in pages:
                    result.append({
                        "id": page.get("id"),
                        "title": page.get("title"),
                        "url": page.get("_links", {}).get("webui", ""),
                    })
                return json.dumps({"space": space_key, "pages": result, "total": len(result)})
            except Exception as e:
                return json.dumps({"error": str(e)})
        
        @tool("create_confluence_page")
        def create_confluence_page_tool(space_key: str, title: str, body: str) -> str:
            """Create a new Confluence page. Body should be in HTML format."""
            try:
                client = init_confluence_client()
                if not client:
                    return json.dumps({"error": "Confluence client not configured. Check environment variables."})
                
                result = client.create_page(
                    space=space_key,
                    title=title,
                    body=body
                )
                return json.dumps({
                    "success": True,
                    "page_id": result.get("id"),
                    "title": result.get("title"),
                    "url": result.get("_links", {}).get("webui", ""),
                    "message": f"Page '{title}' created successfully"
                })
            except Exception as e:
                return json.dumps({"error": str(e), "success": False})
        
        self.tools.extend([
            search_confluence_tool,
            get_confluence_page_tool,
            get_spaces_tool,
            get_space_pages_tool,
            create_confluence_page_tool,
        ])

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
            """Node that executes tools"""
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
                        result = tool_obj.invoke(tool_args)
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
