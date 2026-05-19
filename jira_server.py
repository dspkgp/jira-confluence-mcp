import os
from typing import Any
from dotenv import load_dotenv
from jira import JIRA

from mcp.server.fastmcp import FastMCP

load_dotenv()

JIRA_SERVER = os.getenv("JIRA_SERVER")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

if not all([JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN]):
    raise ValueError("Missing Jira environment variables")

jira_client = JIRA(
    server=JIRA_SERVER,
    basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN)
)

# Create FastMCP instance with proper configuration
mcp = FastMCP("jira-mcp-server", debug=True)

# Store tools for HTTP API
available_tools = {}


@mcp.tool()
def get_issue(issue_key: str) -> dict[str, Any]:
    """
    Fetch Jira issue details.
    Example: PROJ-123
    """

    issue = jira_client.issue(issue_key)

    return {
        "key": issue.key,
        "summary": issue.fields.summary,
        "status": issue.fields.status.name,
        "assignee": (
            issue.fields.assignee.displayName
            if issue.fields.assignee
            else None
        ),
        "reporter": issue.fields.reporter.displayName,
        "priority": (
            issue.fields.priority.name
            if issue.fields.priority
            else None
        ),
        "description": str(issue.fields.description),
    }


@mcp.tool()
def search_issues(jql: str, limit: int = 10) -> list[dict[str, Any]]:
    """
    Search Jira issues using JQL.
    """

    issues = jira_client.search_issues(jql, maxResults=limit)

    results = []

    for issue in issues:
        results.append(
            {
                "key": issue.key,
                "summary": issue.fields.summary,
                "status": issue.fields.status.name,
            }
        )

    return results


@mcp.tool()
def create_issue(
    project_key: str,
    summary: str,
    description: str,
    issue_type: str = "Task",
) -> dict[str, str]:
    """
    Create a Jira issue.
    """

    issue = jira_client.create_issue(
        project=project_key,
        summary=summary,
        description=description,
        issuetype={"name": issue_type},
    )

    return {
        "issue_key": issue.key,
        "message": "Issue created successfully",
    }


@mcp.tool()
def add_comment(issue_key: str, comment: str) -> dict[str, str]:
    """
    Add comment to Jira issue.
    """

    jira_client.add_comment(issue_key, comment)

    return {
        "issue_key": issue_key,
        "message": "Comment added successfully",
    }


@mcp.tool()
def update_issue(
    issue_key: str,
    summary: str | None = None,
    description: str | None = None,
    assignee: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """
    Update a Jira issue's fields.
    Only provide fields you want to change.
    """
    try:
        issue = jira_client.issue(issue_key)
        fields = {}
        
        if summary:
            fields["summary"] = summary
        if description:
            fields["description"] = description
        if assignee:
            fields["assignee"] = {"name": assignee}
        
        if fields:
            issue.update(**fields)
        
        # Handle status transition if needed
        if status:
            transitions = jira_client.transitions(issue_key)
            target_transition = None
            for transition in transitions["transitions"]:
                if transition["to"]["name"].lower() == status.lower():
                    target_transition = transition["id"]
                    break
            
            if target_transition:
                jira_client.transition_issue(issue_key, target_transition)
            else:
                return {
                    "success": False,
                    "message": f"Status '{status}' not available for transition"
                }
        
        return {
            "success": True,
            "issue_key": issue_key,
            "message": "Issue updated successfully",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@mcp.tool()
def get_issue_comments(issue_key: str) -> dict[str, Any]:
    """
    Get all comments on a Jira issue.
    """
    try:
        issue = jira_client.issue(issue_key, expand="changelog")
        comments = issue.fields.comment.comments
        
        formatted_comments = []
        for comment in comments:
            formatted_comments.append({
                "author": comment.author.displayName,
                "created": comment.created,
                "body": comment.body,
            })
        
        return {
            "issue_key": issue_key,
            "total_comments": len(formatted_comments),
            "comments": formatted_comments,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_issue_transitions(issue_key: str) -> dict[str, Any]:
    """
    Get available transitions (status changes) for a Jira issue.
    """
    try:
        transitions = jira_client.transitions(issue_key)
        
        available = []
        for transition in transitions["transitions"]:
            available.append({
                "id": transition["id"],
                "name": transition["name"],
                "to_status": transition["to"]["name"],
            })
        
        return {
            "issue_key": issue_key,
            "available_transitions": available,
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def transition_issue(issue_key: str, transition_name: str) -> dict[str, Any]:
    """
    Move a Jira issue to a new status.
    Provide the transition name (e.g., 'To Do', 'In Progress', 'Done').
    """
    try:
        transitions = jira_client.transitions(issue_key)
        target_transition = None
        
        for transition in transitions["transitions"]:
            if transition["name"].lower() == transition_name.lower():
                target_transition = transition["id"]
                break
        
        if not target_transition:
            return {
                "success": False,
                "message": f"Transition '{transition_name}' not found"
            }
        
        jira_client.transition_issue(issue_key, target_transition)
        
        return {
            "success": True,
            "issue_key": issue_key,
            "message": f"Issue transitioned to '{transition_name}'",
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    print("Starting JIRA MCP Server...")
    print("Available tools:")
    print("  - get_issue: Fetch JIRA issue details")
    print("  - search_issues: Search JIRA issues using JQL")
    print("  - create_issue: Create a Jira issue")
    print("  - update_issue: Update a Jira issue's fields")
    print("  - add_comment: Add comment to Jira issue")
    print("  - get_issue_comments: Get all comments on a Jira issue")
    print("  - get_issue_transitions: Get available transitions for a Jira issue")
    print("  - transition_issue: Move a Jira issue to a new status")
    print("\nServer running on port 8001...")
    mcp.run()
