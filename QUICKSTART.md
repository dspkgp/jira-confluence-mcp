# ⚡ Quick Start Guide

Get the Atlassian AI Chatbot running in 5 minutes.

## Step 1: Prerequisites ✅

Make sure you have:
- Python 3.9 or higher
- OpenAI API key (from https://platform.openai.com/api-keys)
- Atlassian Cloud account
- JIRA API token
- Confluence API token

## Step 2: Environment Setup 🔧

### Get API Tokens

**JIRA & Confluence API Token:**
1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name like "Chatbot"
4. Copy the token

### Configure .env File

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your credentials
# On Windows: notepad .env
# On Mac/Linux: nano .env
```

Fill in these values:
```env
OPENAI_API_KEY=sk-xxxxx...  # From OpenAI Platform
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=ATATT...
CONFLUENCE_URL=https://your-domain.atlassian.net/wiki
CONFLUENCE_EMAIL=your-email@example.com
CONFLUENCE_API_TOKEN=ATATT...
```

## Step 3: Install Dependencies 📦

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Mac/Linux:
source venv/bin/activate

# Install packages
pip install -r requirements.txt
```

## Step 4: Start the Servers 🚀

### Option A: Windows Users

```bash
# Double-click start_all.bat
# OR run from terminal:
start_all.bat
```

This opens 3 new windows for:
- JIRA MCP Server
- Confluence MCP Server  
- Streamlit UI

### Option B: Mac/Linux Users

```bash
chmod +x start_all.sh
./start_all.sh
```

### Option C: Manual Start (All Users)

Open 3 separate terminal windows:

**Window 1:**
```bash
python jira_server.py
```

**Window 2:**
```bash
python confluence_server.py
```

**Window 3:**
```bash
streamlit run app_streamlit.py
```

## Step 5: Use the Chatbot 💬

Open your browser to: **http://localhost:8501**

Click "🚀 Initialize Chatbot" and start asking questions:

```
"Search for open bugs in project PROJ"
"Create a new task for the homepage redesign"
"Show me Confluence pages about API documentation"
"Update issue PROJ-123 to In Progress"
```

## Troubleshooting 🔧

### Port Already in Use
If you get "Address already in use", change the port:

Edit `.env`:
```env
JIRA_PORT=9001
CONFLUENCE_PORT=9002
STREAMLIT_PORT=9501
```

Then update `chatbot.py` URLs accordingly.

### "Connection refused" Error
Make sure all 3 servers are running. Check:
- http://localhost:8001 (JIRA)
- http://localhost:8002 (Confluence)
- http://localhost:8501 (Streamlit)

### API Token Invalid
- Verify token in `.env` matches exactly
- Check token hasn't expired (recreate if needed)
- Ensure account has access to JIRA/Confluence

### Module Not Found
```bash
# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

## Next Steps 🎯

1. **Explore Features**: Try different queries to understand capabilities
2. **Read README**: See [README.md](README.md) for detailed documentation
3. **Customize**: Check [ADVANCED.md](ADVANCED.md) for customization options
4. **API Integration**: Use FastAPI endpoints if building integrations

## Example Queries

### JIRA Queries
```
"Show me all tasks assigned to me"
"Create a bug: Login button not working"
"What's the status of PROJ-456?"
"Add a comment to PROJ-789: Looks good!"
"Move PROJ-123 to Done status"
```

### Confluence Queries
```
"Find documentation about authentication"
"What's in the API guide page?"
"Search for deployment procedures"
"Create a new page about CI/CD"
```

### Combined Queries
```
"Create a JIRA bug and link it to the security docs"
"Search for related issues and documentation"
```

## Getting Help

If you encounter issues:

1. **Check Logs**: Look at terminal output for error messages
2. **Verify Config**: Ensure all credentials are correct in `.env`
3. **Read README**: See [README.md](README.md) troubleshooting section
4. **Test Credentials**: Run `python setup.py` to verify API access

## Performance Tips

- **Keep queries specific** - "JIRA issues" is better than "issues"
- **Use issue keys** - Reference PROJ-123 directly when possible
- **Batch requests** - Ask multiple things in one message
- **Monitor API usage** - OpenAI charges per request

## Next Advanced Topics

- [Custom Tools](ADVANCED.md#custom-tools) - Add new capabilities
- [Database Integration](ADVANCED.md#database) - Store conversation history
- [Docker Setup](ADVANCED.md#docker) - Run in containers
- [Production Deployment](ADVANCED.md#deployment) - Deploy to cloud

---

**Questions?** Check README.md or open an issue!

Happy chatting! 🎉
