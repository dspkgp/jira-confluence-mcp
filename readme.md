# 🤖 Atlassian AI Chatbot

A powerful AI chatbot that integrates with JIRA and Confluence using Atlassian MCP (Model Context Protocol) servers. Query issues, create tasks, search documentation, and manage your Atlassian workspace with natural language.

## Features

✨ **Core Capabilities:**
- 🔍 Search JIRA issues with natural language
- 📝 Create and update JIRA issues
- 🔄 Manage issue workflows (status transitions)
- 💬 Add and retrieve issue comments
- 📚 Search Confluence pages
- 📄 Retrieve and create documentation
- 🧠 Conversational context awareness
- 🛠️ Multi-server MCP integration

## Architecture

```
┌─────────────┐
│  Streamlit  │  User Interface
│     UI      │
└──────┬──────┘
       │
┌──────▼──────────────────┐
│   Chatbot Agent (LLM)   │  GPT-4.1-mini with Tools
│   (LanGraph + OpenAI)   │
└──────┬─────────────────┬┘
       │                 │
   ┌───▼────┐        ┌──▼────┐
   │  JIRA  │        │Conflue │  MCP Servers
   │  MCP   │        │  MCP   │
   └────────┘        └────────┘
       │                 │
   ┌───▼────┐        ┌──▼────┐
   │  JIRA  │        │Conflue │  Atlassian APIs
   │  API   │        │  API   │
   └────────┘        └────────┘
```

## Prerequisites

- Python 3.9+
- OpenAI API key
- Atlassian Cloud account (JIRA and/or Confluence)
- API tokens for JIRA and Confluence

## Installation

### 1. Clone and Setup

```bash
cd jira-mcp
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# OpenAI
OPENAI_API_KEY=sk-...

# JIRA
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=ATATT...

# Confluence
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=ATATT...

# MCP Servers
JIRA_SERVER_URL=http://localhost:8001/mcp
CONFLUENCE_SERVER_URL=http://localhost:8002/mcp
```

### 3. Get API Tokens

#### JIRA API Token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Create an API token
3. Copy and paste into `.env`

#### Confluence API Token:
- Same process as JIRA (uses the same account)

#### OpenAI API Key:
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy and paste into `.env`

## Running the Application

### Option 1: Complete Setup (Recommended)

**Terminal 1 - JIRA Server:**
```bash
python jira_server.py
```

**Terminal 2 - Confluence Server:**
```bash
python confluence_server.py
```

**Terminal 3 - Streamlit UI:**
```bash
streamlit run app_streamlit.py
```

The chatbot will be available at `http://localhost:8501`

### Option 2: FastAPI Backend Only

```bash
python main.py
```

Then visit `http://localhost:8080/docs` for API documentation.

## Usage Examples

### Through Streamlit UI

1. Click "🚀 Initialize Chatbot" in the sidebar
2. Type your queries:

```
"Search for all open bugs in project PROJ"
"Create a new task for the login page feature"
"What Confluence pages cover authentication?"
"Update issue PROJ-123 to Done status"
"Add a comment to PROJ-456: Great progress!"
```

### Through Python

```python
import asyncio
from chatbot import create_chatbot

async def main():
    chatbot = await create_chatbot()
    
    # Single query
    response = await chatbot.chat("Show me open issues in PROJ")
    print(response)
    
    # With conversation history
    history = []
    response1 = await chatbot.chat("Create a bug", history)
    response2 = await chatbot.chat("Assign it to John", history)
    
    await chatbot.close()

asyncio.run(main())
```

## MCP Tools Reference

### JIRA Tools

- **get_issue(issue_key)** - Get issue details
- **search_issues(jql, limit)** - Search using JQL
- **create_issue(project_key, summary, description, issue_type)** - Create new issue
- **update_issue(issue_key, summary, description, assignee, status)** - Update issue
- **add_comment(issue_key, comment)** - Add comment
- **get_issue_comments(issue_key)** - Get all comments
- **get_issue_transitions(issue_key)** - Get available status changes
- **transition_issue(issue_key, transition_name)** - Move issue to new status

### Confluence Tools

- **search_pages(query, limit)** - Search Confluence pages
- **get_page_content(page_id)** - Get full page content
- **get_page_by_title(space_key, title)** - Find page by title
- **create_page(space_key, title, body, parent_page_id)** - Create new page
- **update_page(page_id, title, body, version_number)** - Update page

## Troubleshooting

### "Connection refused" errors

Make sure MCP servers are running on the correct ports:
- JIRA: `http://localhost:8001`
- Confluence: `http://localhost:8002`

### "Invalid API token"

- Verify tokens in `.env` file
- Ensure tokens are not expired
- Check JIRA/Confluence account has proper permissions

### "Tool not found" in responses

- Verify the MCP servers are properly connected
- Check that the tool name matches exactly (case-sensitive)
- See "Available tools" in Streamlit sidebar

## Project Structure

```
jira-mcp/
├── app_streamlit.py          # Streamlit chatbot UI
├── chatbot.py                # Main chatbot agent
├── jira_server.py            # JIRA MCP server
├── confluence_server.py      # Confluence MCP server
├── main.py                   # FastAPI backend
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment config
└── README.md                 # This file
```

## Performance Tips

1. **Batch queries** - Ask multiple things in one message instead of separate queries
2. **Be specific** - More detailed queries = better results
3. **Use context** - The agent remembers your conversation
4. **Rate limiting** - OpenAI API has rate limits; add delays between requests if needed

## Advanced Configuration

### Custom Model

Edit `chatbot.py`:
```python
llm = ChatOpenAI(model="gpt-4-turbo")  # Change model here
```

### Custom Ports

Update `.env`:
```env
JIRA_PORT=9001
CONFLUENCE_PORT=9002
```

Update server connection URLs in `chatbot.py`.

## API Endpoints (FastAPI)

When running `main.py`:

```
POST /api/chat - Send message to chatbot
POST /api/tools/list - List available tools
GET /api/tools/{tool_name} - Get tool details
POST /api/jira/issues/search - Search JIRA issues
POST /api/confluence/search - Search Confluence
```

See `http://localhost:8080/docs` for interactive API documentation.

## Contributing

Feel free to extend the chatbot:

1. Add new MCP servers in `confluence_server.py` or `jira_server.py`
2. Add new tools as `@mcp.tool()` decorated functions
3. Update chatbot initialization in `chatbot.py`

## Limitations

- LLM context window limits for very large conversations
- Some Atlassian fields may not be accessible via API
- Confluence page creation uses HTML format

## License

MIT

## Support

For issues or questions:
- Check the troubleshooting section
- Verify all environment variables are set
- Ensure MCP servers are running
- Check Atlassian API documentation

## Roadmap

- [ ] Confluence page templates
- [ ] Issue workflow automation
- [ ] Multi-user conversation tracking
- [ ] Web UI enhancements
- [ ] Integration with more Atlassian services (Bitbucket, etc.)
- [ ] Rate limiting and caching

