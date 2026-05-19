import asyncio
import streamlit as st
from streamlit_chat import message
from chatbot import create_chatbot, AtlassianChatbot

# Page configuration
st.set_page_config(
    page_title="Atlassian AI Chatbot",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stChatMessage {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if "chatbot" not in st.session_state:
    st.session_state.chatbot = None
    st.session_state.initialized = False

if "messages" not in st.session_state:
    st.session_state.messages = []

if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []


async def initialize_chatbot():
    """Initialize the chatbot"""
    try:
        st.session_state.chatbot = await create_chatbot()
        st.session_state.initialized = True
        return True
    except Exception as e:
        st.error(f"Failed to initialize chatbot: {e}")
        return False


# Header
st.title("🤖 Atlassian AI Chatbot")
st.markdown("**Query JIRA issues and Confluence pages with AI assistance**")

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    if not st.session_state.initialized:
        if st.button("🚀 Initialize Chatbot", use_container_width=True):
            with st.spinner("Initializing chatbot..."):
                success = asyncio.run(initialize_chatbot())
                if success:
                    st.success("✓ Chatbot initialized!")
                    st.rerun()
    else:
        st.success("✓ Chatbot initialized")
        
        if st.button("🔄 Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.conversation_history = []
            st.rerun()
    
    st.divider()
    
    st.subheader("📋 Capabilities")
    capabilities = [
        "🔍 Search JIRA issues",
        "📝 Create JIRA issues",
        "✏️ Update issue status",
        "💬 Add comments",
        "📚 Search Confluence",
        "📄 Get page content"
    ]
    for cap in capabilities:
        st.markdown(f"- {cap}")
    
    st.divider()
    
    st.subheader("💡 Example Queries")
    examples = [
        "Search for issues in project PROJ",
        "Create a bug for the login page",
        "Show me Confluence pages about authentication",
        "Update issue PROJ-123 to Done status"
    ]
    for example in examples:
        st.markdown(f"→ {example}")


# Main chat interface
if st.session_state.initialized:
    # Display conversation history
    for i, (sender, text) in enumerate(st.session_state.messages):
        if sender == "user":
            with st.chat_message("user"):
                st.markdown(text)
        else:
            with st.chat_message("assistant"):
                st.markdown(text)
    
    # Input area
    st.divider()
    
    user_input = st.chat_input(
        "Ask me anything about JIRA or Confluence...",
        key="chat_input"
    )

    if user_input:
        st.session_state.messages.append(("user", user_input))
        st.session_state.conversation_history.append({
            "role": "user",
            "content": user_input
        })

        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    response = asyncio.run(
                        st.session_state.chatbot.chat(
                            user_input,
                            st.session_state.conversation_history
                        )
                    )

                    if not response:
                        response = "I couldn't generate a response. Please try again."

                    st.session_state.messages.append(("assistant", response))
                    st.session_state.conversation_history.append({
                        "role": "assistant",
                        "content": response
                    })

                    st.markdown(response)
                except Exception as e:
                    error_text = f"Error: {str(e)}"
                    st.error(error_text)
                    st.session_state.messages.append(("assistant", error_text))
else:
    st.info(
        "👈 Click 'Initialize Chatbot' in the sidebar to get started. "
        "Make sure the JIRA and Confluence servers are running."
    )
