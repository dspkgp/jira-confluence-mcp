#!/usr/bin/env python
"""
Quick setup script to configure and start the Atlassian chatbot.
This script helps with environment setup and server startup.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.9+"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required, but you have {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")


def check_env_file():
    """Check if .env file exists and is configured"""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found!")
        print("   → Copy .env.example to .env and fill in your credentials")
        print("   → cp .env.example .env")
        return False
    
    with open(env_path) as f:
        content = f.read()
    
    required_keys = [
        "OPENAI_API_KEY",
        "JIRA_SERVER",
        "JIRA_EMAIL",
        "JIRA_API_TOKEN",
        "CONFLUENCE_URL",
        "CONFLUENCE_EMAIL",
        "CONFLUENCE_API_TOKEN"
    ]
    
    missing = [key for key in required_keys if f"{key}=your_" in content or f"{key}=" not in content]
    
    if missing:
        print(f"❌ Missing/unconfigured keys in .env: {', '.join(missing)}")
        return False
    
    print("✓ .env file configured")
    return True


def check_dependencies():
    """Check if all required packages are installed"""
    try:
        import langchain
        import streamlit
        import mcp
        import openai
        print("✓ All dependencies installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("   → Run: pip install -r requirements.txt")
        return False


def start_servers():
    """Start MCP servers and Streamlit"""
    print("\n" + "="*60)
    print("Starting Atlassian Chatbot Servers")
    print("="*60 + "\n")
    
    servers = [
        {
            "name": "JIRA MCP Server",
            "cmd": ["python", "jira_server.py"],
            "port": 8001,
            "env": {"JIRA_PORT": "8001"}
        },
        {
            "name": "Confluence MCP Server",
            "cmd": ["python", "confluence_server.py"],
            "port": 8002,
            "env": {"CONFLUENCE_PORT": "8002"}
        },
        {
            "name": "Streamlit Chatbot UI",
            "cmd": ["streamlit", "run", "app_streamlit.py"],
            "port": 8501,
            "env": {}
        }
    ]
    
    print("To run all servers, open 3 separate terminal windows and run:\n")
    
    for i, server in enumerate(servers, 1):
        print(f"Terminal {i}: {server['name']}")
        print(f"  → {' '.join(server['cmd'])}")
        if server["port"]:
            print(f"     (runs on port {server['port']})")
        print()
    
    print("="*60)
    print("Web UI will be available at: http://localhost:8501")
    print("="*60 + "\n")


def main():
    """Main setup flow"""
    print("\n🤖 Atlassian AI Chatbot - Setup\n")
    
    # Check Python version
    check_python_version()
    
    # Check .env configuration
    if not check_env_file():
        print("\n❌ Please configure .env file first")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Please install dependencies first")
        print("   → pip install -r requirements.txt")
        sys.exit(1)
    
    print("\n✓ All checks passed!\n")
    
    # Ask what to do
    while True:
        print("\nWhat would you like to do?")
        print("  1. Show how to start servers")
        print("  2. Verify API credentials")
        print("  3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            start_servers()
        elif choice == "2":
            verify_credentials()
        elif choice == "3":
            print("Goodbye! 👋")
            break
        else:
            print("Invalid choice, try again")


def verify_credentials():
    """Verify API credentials are working"""
    print("\n" + "="*60)
    print("Verifying Credentials")
    print("="*60 + "\n")
    
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Check OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        client.models.list()
        print("✓ OpenAI API key is valid")
    except Exception as e:
        print(f"❌ OpenAI API key error: {e}")
    
    # Check JIRA
    try:
        from jira import JIRA
        jira = JIRA(
            server=os.getenv("JIRA_SERVER"),
            basic_auth=(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))
        )
        jira.projects()
        print("✓ JIRA credentials are valid")
    except Exception as e:
        print(f"❌ JIRA credentials error: {e}")
    
    # Check Confluence
    try:
        from atlassian import Confluence
        confluence = Confluence(
            url=os.getenv("CONFLUENCE_URL"),
            username=os.getenv("CONFLUENCE_EMAIL"),
            password=os.getenv("CONFLUENCE_API_TOKEN")
        )
        confluence.get_page_by_id("0")  # Small request
        print("✓ Confluence credentials are valid")
    except Exception as e:
        if "Could not find page" in str(e):
            print("✓ Confluence credentials are valid (dummy page check)")
        else:
            print(f"❌ Confluence credentials error: {e}")


if __name__ == "__main__":
    main()
