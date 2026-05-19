import os
from typing import Any
from dotenv import load_dotenv
from atlassian import Confluence

from mcp.server.fastmcp import FastMCP

load_dotenv()

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")
CONFLUENCE_EMAIL = os.getenv("CONFLUENCE_EMAIL")
CONFLUENCE_API_TOKEN = os.getenv("CONFLUENCE_API_TOKEN")

if not all([CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN]):
    raise ValueError("Missing Confluence environment variables")

confluence_client = Confluence(
    url=CONFLUENCE_URL,
    username=CONFLUENCE_EMAIL,
    password=CONFLUENCE_API_TOKEN
)

mcp = FastMCP("confluence-mcp-server")


@mcp.tool()
def get_all_spaces(limit: int = 50) -> dict[str, Any]:
    """
    Get all Confluence spaces accessible to the user.
    Returns space keys, names, and types.
    """
    try:
        spaces = confluence_client.get_all_spaces(limit=limit)
        
        result = []
        for space in spaces.get("results", []):
            result.append({
                "key": space.get("key"),
                "name": space.get("name"),
                "type": space.get("type"),
            })
        
        return {
            "total_spaces": len(result),
            "spaces": result
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def search_pages(query: str, limit: int = 10) -> dict[str, Any]:
    """
    Search Confluence pages by query.
    Returns page titles, URLs, and summaries.
    """
    try:
        results = confluence_client.get_search(
            query=query,
            limit=limit,
            type="page"
        )
        
        pages = []
        for result in results.get("results", []):
            pages.append({
                "id": result.get("id"),
                "title": result.get("title"),
                "space": result.get("space", {}).get("name"),
                "url": result.get("url"),
                "excerpt": result.get("excerpt", "")[:200],  # First 200 chars
            })
        
        return {
            "query": query,
            "total_results": len(pages),
            "pages": pages
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_page_content(page_id: str) -> dict[str, Any]:
    """
    Get full content of a Confluence page by ID.
    Returns title, space, and HTML content.
    """
    try:
        page = confluence_client.get_page_by_id(
            page_id,
            expand="body.storage"
        )
        
        return {
            "id": page.get("id"),
            "title": page.get("title"),
            "space": page.get("space", {}).get("name"),
            "url": page.get("_links", {}).get("webui"),
            "content": page.get("body", {}).get("storage", {}).get("value", ""),
            "version": page.get("version", {}).get("number"),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_page_by_title(space_key: str, title: str) -> dict[str, Any]:
    """
    Get Confluence page by space key and title.
    """
    try:
        page = confluence_client.get_page_by_title(
            space=space_key,
            title=title,
            expand="body.storage"
        )
        
        return {
            "id": page.get("id"),
            "title": page.get("title"),
            "space": page.get("space", {}).get("name"),
            "url": page.get("_links", {}).get("webui"),
            "content": page.get("body", {}).get("storage", {}).get("value", ""),
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def get_space_pages(space_key: str, limit: int = 25) -> dict[str, Any]:
    """
    Get all pages in a specific Confluence space.
    Provide the space key (e.g., 'dspkgp', 'TEAM').
    """
    try:
        pages = confluence_client.get_all_pages_from_space(
            space=space_key,
            limit=limit,
            expand="version"
        )
        
        result = []
        for page in pages:
            result.append({
                "id": page.get("id"),
                "title": page.get("title"),
                "version": page.get("version", {}).get("number"),
                "url": page.get("_links", {}).get("webui"),
            })
        
        return {
            "space_key": space_key,
            "total_pages": len(result),
            "pages": result
        }
    except Exception as e:
        return {"error": str(e)}


@mcp.tool()
def create_page(
    space_name: str,
    title: str,
    body: str,
    parent_page_id: str | None = None
) -> dict[str, Any]:
    """
    Create a new Confluence page.
    Provide the space name (e.g., 'My Project', 'Team Documentation').
    Body should be in HTML or wiki format.
    """
    try:
        # Look up space key from space name
        spaces = confluence_client.get_all_spaces(limit=100)
        space_key = None
        
        for space in spaces.get("results", []):
            if space.get("name", "").lower() == space_name.lower():
                space_key = space.get("key")
                break
        
        if not space_key:
            return {
                "error": f"Space '{space_name}' not found. Use get_all_spaces to see available spaces.",
                "success": False
            }
        
        result = confluence_client.create_page(
            space=space_key,
            title=title,
            body=body,
            parent_id=parent_page_id
        )
        
        return {
            "success": True,
            "page_id": result.get("id"),
            "title": result.get("title"),
            "space_name": space_name,
            "space_key": space_key,
            "url": result.get("_links", {}).get("webui"),
        }
    except Exception as e:
        return {"error": str(e), "success": False}


@mcp.tool()
def update_page(
    page_id: str,
    title: str,
    body: str,
    version_number: int
) -> dict[str, Any]:
    """
    Update an existing Confluence page.
    Must provide the current version number.
    """
    try:
        result = confluence_client.update_page(
            page_id=page_id,
            title=title,
            body=body,
            version_number=version_number
        )
        
        return {
            "success": True,
            "page_id": result.get("id"),
            "title": result.get("title"),
            "new_version": result.get("version", {}).get("number"),
        }
    except Exception as e:
        return {"error": str(e), "success": False}


if __name__ == "__main__":
    print("Starting Confluence MCP Server...")
    print("Available tools:")
    print("  - get_all_spaces: Get all Confluence spaces accessible to user")
    print("  - search_pages: Search Confluence pages by query")
    print("  - get_page_content: Get full content of a Confluence page by ID")
    print("  - get_page_by_title: Get Confluence page by space key and title")
    print("  - get_space_pages: Get all pages in a specific space")
    print("  - create_page: Create a new Confluence page (uses space name)")
    print("  - update_page: Update an existing Confluence page")
    print("\nServer running on port 8002...")
    mcp.run()

