@echo off
REM Atlassian AI Chatbot - Windows Startup Script
REM This script starts all required servers in separate windows

echo.
echo ========================================
echo Atlassian AI Chatbot - Starting Servers
echo ========================================
echo.

REM Check if .env file exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo Please copy .env.example to .env and configure it first.
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "venv\Scripts\activate" (
    echo WARNING: Virtual environment not found!
    echo Run: python -m venv venv
    echo Then: venv\Scripts\activate
    echo Then: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo Starting JIRA MCP Server...
start "JIRA MCP Server (Port 8001)" cmd /k "venv\Scripts\activate & python jira_server.py"

REM Wait a moment before starting next server
timeout /t 2 /nobreak

echo Starting Confluence MCP Server...
start "Confluence MCP Server (Port 8002)" cmd /k "venv\Scripts\activate & python confluence_server.py"

REM Wait a moment before starting UI
timeout /t 2 /nobreak

echo Starting Streamlit UI...
start "Streamlit UI (Port 8501)" cmd /k "venv\Scripts\activate & streamlit run app_streamlit.py"

echo.
echo ========================================
echo All servers are starting...
echo ========================================
echo.
echo Web UI: http://localhost:8501
echo JIRA MCP: http://localhost:8001
echo Confluence MCP: http://localhost:8002
echo.
echo Note: It may take a few seconds for servers to fully start.
echo.
pause
