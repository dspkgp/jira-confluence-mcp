# 🔧 Advanced Configuration & Customization

Advanced setup options for power users and production deployments.

## Table of Contents

1. [Custom Tools](#custom-tools)
2. [Database Integration](#database-integration)
3. [Docker Setup](#docker-setup)
4. [Production Deployment](#production-deployment)
5. [Performance Optimization](#performance-optimization)
6. [Security Hardening](#security-hardening)

## Custom Tools

### Adding New JIRA Tools

Edit `jira_server.py` and add new tools:

```python
@mcp.tool()
def bulk_update_issues(jql: str, field: str, value: str) -> dict[str, Any]:
    """
    Bulk update multiple JIRA issues.
    Example: Update all open bugs to High priority
    """
    try:
        issues = jira_client.search_issues(jql, maxResults=None)
        updated_count = 0
        
        for issue in issues:
            fields = {field: value}
            issue.update(**fields)
            updated_count += 1
        
        return {
            "success": True,
            "updated_count": updated_count,
            "message": f"Updated {updated_count} issues"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Adding New Confluence Tools

Edit `confluence_server.py`:

```python
@mcp.tool()
def batch_search_pages(queries: list[str]) -> dict[str, Any]:
    """
    Search multiple queries in Confluence.
    Returns consolidated results.
    """
    all_results = {}
    
    for query in queries:
        results = confluence_client.get_search(
            query=query,
            limit=5,
            type="page"
        )
        all_results[query] = [
            r.get("title") for r in results.get("results", [])
        ]
    
    return {"results": all_results}
```

### Tool Best Practices

1. **Error Handling** - Always wrap in try/except
2. **Documentation** - Use detailed docstrings
3. **Type Hints** - Specify input/output types
4. **Limits** - Respect API rate limits
5. **Logging** - Log important operations

## Database Integration

### Store Conversation History

```python
# install: pip install sqlalchemy
from sqlalchemy import create_engine, Column, String, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    message = Column(String)
    response = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create engine
engine = create_engine("sqlite:///chatbot.db")
Base.metadata.create_all(engine)

# Usage
Session = sessionmaker(bind=engine)
session = Session()

# Save conversation
conv = Conversation(
    user_id="user123",
    message="Search for open issues",
    response="Found 5 open issues..."
)
session.add(conv)
session.commit()
```

### Analytics Dashboard

```python
# Create analytics with Streamlit
import streamlit as st
from sqlalchemy import func

st.title("Chatbot Analytics")

# Query statistics
with Session() as session:
    total_messages = session.query(func.count(Conversation.id)).scalar()
    unique_users = session.query(func.count(func.distinct(Conversation.user_id))).scalar()
    
    st.metric("Total Messages", total_messages)
    st.metric("Unique Users", unique_users)
```

## Docker Setup

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose ports
EXPOSE 8001 8002 8501 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501')" || exit 1

CMD ["streamlit", "run", "app_streamlit.py", "--server.port=8501"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  jira-mcp:
    build: .
    environment:
      - JIRA_SERVER=${JIRA_SERVER}
      - JIRA_EMAIL=${JIRA_EMAIL}
      - JIRA_API_TOKEN=${JIRA_API_TOKEN}
    ports:
      - "8001:8001"
    command: python jira_server.py
    restart: unless-stopped

  confluence-mcp:
    build: .
    environment:
      - CONFLUENCE_URL=${CONFLUENCE_URL}
      - CONFLUENCE_EMAIL=${CONFLUENCE_EMAIL}
      - CONFLUENCE_API_TOKEN=${CONFLUENCE_API_TOKEN}
    ports:
      - "8002:8002"
    command: python confluence_server.py
    restart: unless-stopped

  streamlit:
    build: .
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - JIRA_SERVER_URL=http://jira-mcp:8001/mcp
      - CONFLUENCE_SERVER_URL=http://confluence-mcp:8002/mcp
    ports:
      - "8501:8501"
    depends_on:
      - jira-mcp
      - confluence-mcp
    restart: unless-stopped

volumes:
  chatbot_data:
```

**Run with Docker Compose:**
```bash
docker-compose up -d
```

## Production Deployment

### AWS Deployment

**1. Create ECS Task Definition:**

```json
{
  "family": "atlassian-chatbot",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "streamlit",
      "image": "your-registry/chatbot:latest",
      "portMappings": [{"containerPort": 8501}],
      "environment": [
        {"name": "OPENAI_API_KEY", "value": "xxx"}
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/atlassian-chatbot",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

**2. Deploy to ECS:**
```bash
aws ecs create-service \
  --cluster default \
  --service-name atlassian-chatbot \
  --task-definition atlassian-chatbot:1 \
  --desired-count 1
```

### Heroku Deployment

**1. Create Procfile:**
```
web: streamlit run app_streamlit.py --server.port=$PORT
jira: python jira_server.py
confluence: python confluence_server.py
```

**2. Deploy:**
```bash
git push heroku main
```

## Performance Optimization

### Caching

```python
# Add caching to reduce API calls
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def cached_get_issue(issue_key: str):
    """Cache issue lookups for 5 minutes"""
    return get_issue(issue_key)

# Clear cache periodically
def clear_cache_periodically():
    while True:
        time.sleep(300)  # 5 minutes
        cached_get_issue.cache_clear()
```

### Async Operations

```python
# Use async for better concurrency
import asyncio

async def search_multiple(queries: list[str]):
    """Search JIRA and Confluence in parallel"""
    tasks = [
        asyncio.create_task(search_jira_async(q))
        for q in queries
    ]
    results = await asyncio.gather(*tasks)
    return results
```

### Connection Pooling

```python
# Reuse connections
from jira import JIRA

class JiraPool:
    _instance = None
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = JIRA(
                server=JIRA_SERVER,
                basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN),
                options={'agile_rest_path': 'agile/1.0'}
            )
        return cls._instance
```

## Security Hardening

### Environment Variable Management

```python
# Use secrets manager instead of .env in production
import boto3

def get_secret(secret_name):
    """Retrieve secrets from AWS Secrets Manager"""
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return response['SecretString']

OPENAI_API_KEY = get_secret('openai-key')
JIRA_API_TOKEN = get_secret('jira-token')
```

### Rate Limiting

```python
# Protect against abuse
from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import FastAPI

limiter = Limiter(key_func=get_remote_address)
app = FastAPI()
app.state.limiter = limiter

@app.post("/chat")
@limiter.limit("100/minute")
async def chat(request):
    # Your endpoint
    pass
```

### Input Validation

```python
from pydantic import BaseModel, validator

class ChatMessage(BaseModel):
    message: str
    
    @validator('message')
    def message_not_empty(cls, v):
        if not v or len(v.strip()) < 1:
            raise ValueError('Message cannot be empty')
        if len(v) > 5000:
            raise ValueError('Message too long (max 5000 chars)')
        return v
```

### Logging & Monitoring

```python
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Log operations
@mcp.tool()
def get_issue(issue_key: str):
    try:
        logger.info(f"Fetching issue: {issue_key}")
        issue = jira_client.issue(issue_key)
        logger.info(f"Successfully fetched {issue_key}")
        return issue
    except Exception as e:
        logger.error(f"Error fetching {issue_key}: {e}", exc_info=True)
        raise
```

## Monitoring & Alerting

### Prometheus Metrics

```python
from prometheus_client import Counter, Gauge, Histogram

# Metrics
chat_requests = Counter('chat_requests_total', 'Total chat requests')
active_chats = Gauge('active_chats', 'Active chat sessions')
response_time = Histogram('response_time_seconds', 'Response time')

@app.post("/chat")
async def chat(message: str):
    chat_requests.inc()
    active_chats.inc()
    
    start = time.time()
    result = await chatbot.chat(message)
    duration = time.time() - start
    
    response_time.observe(duration)
    active_chats.dec()
    
    return result
```

---

For questions or issues, refer to the main [README.md](README.md).
