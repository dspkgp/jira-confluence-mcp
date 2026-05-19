#!/bin/bash

# Atlassian AI Chatbot - Unix/Linux/Mac Startup Script
# This script starts all required servers in background

echo ""
echo "========================================"
echo "Atlassian AI Chatbot - Starting Servers"
echo "========================================"
echo ""

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure it first."
    echo ""
    exit 1
fi

# Check if virtual environment exists
if [ ! -f "venv/bin/activate" ]; then
    echo "WARNING: Virtual environment not found!"
    echo "Run: python3 -m venv venv"
    echo "Then: source venv/bin/activate"
    echo "Then: pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Source virtual environment
source venv/bin/activate

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "========================================"
    echo "Shutting down servers..."
    echo "========================================"
    kill $JIRA_PID $CONFLUENCE_PID $STREAMLIT_PID 2>/dev/null
    wait 2>/dev/null
    echo "All servers stopped."
}

trap cleanup EXIT

echo "Starting JIRA MCP Server on port 8001..."
python jira_server.py &
JIRA_PID=$!

sleep 2

echo "Starting Confluence MCP Server on port 8002..."
python confluence_server.py &
CONFLUENCE_PID=$!

sleep 2

echo "Starting Streamlit UI on port 8501..."
streamlit run app_streamlit.py &
STREAMLIT_PID=$!

echo ""
echo "========================================"
echo "All servers are running!"
echo "========================================"
echo ""
echo "Web UI: http://localhost:8501"
echo "JIRA MCP: http://localhost:8001"
echo "Confluence MCP: http://localhost:8002"
echo ""
echo "Press Ctrl+C to stop all servers."
echo ""

# Wait for all processes
wait
