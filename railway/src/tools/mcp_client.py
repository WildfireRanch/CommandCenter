# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/tools/mcp_client.py
# PURPOSE: MCP client wrapper for Tavily web search integration
#
# WHAT IT DOES:
#   - Provides CrewAI tools for web search via Tavily MCP
#   - Wraps tavily-search and tavily-extract MCP tools
#   - Handles HTTP communication with remote Tavily MCP server
#
# DEPENDENCIES:
#   - mcp (MCP SDK for Python)
#   - httpx (HTTP client for remote MCP)
#   - TAVILY_API_KEY environment variable
#
# USAGE:
#   from tools.mcp_client import tavily_search, tavily_extract
#
#   result = tavily_search("solar panel best practices 2025")
#   print(result)
# ═══════════════════════════════════════════════════════════════════════════

import os
import json
import logging
from typing import Optional, Dict, Any
from crewai.tools import tool
import httpx

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Tavily MCP Client Configuration
# ─────────────────────────────────────────────────────────────────────────────

def get_tavily_api_key() -> Optional[str]:
    """
    Get Tavily API key from environment.

    Returns:
        str: API key if found, None otherwise
    """
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        logger.error("TAVILY_API_KEY not found in environment variables")
    return api_key


def get_tavily_mcp_url() -> str:
    """
    Get Tavily MCP server URL.

    Returns:
        str: MCP server URL with API key
    """
    base_url = os.getenv("TAVILY_MCP_URL", "https://mcp.tavily.com/mcp")
    api_key = get_tavily_api_key()

    if not api_key:
        return base_url

    # Add API key as query parameter
    return f"{base_url}?tavilyApiKey={api_key}"


async def call_tavily_mcp(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Call a Tavily MCP tool via HTTP.

    Args:
        tool_name: Name of the MCP tool (e.g., "tavily-search")
        arguments: Tool arguments as dictionary

    Returns:
        dict: Tool response

    Raises:
        Exception: If API call fails
    """
    url = get_tavily_mcp_url()

    if not get_tavily_api_key():
        raise ValueError("TAVILY_API_KEY environment variable not set")

    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            result = response.json()

            if "error" in result:
                error_msg = result["error"].get("message", "Unknown error")
                raise Exception(f"MCP error: {error_msg}")

            return result.get("result", {})

    except httpx.TimeoutException:
        raise Exception("Tavily MCP request timed out (30s)")
    except httpx.HTTPError as e:
        raise Exception(f"Tavily MCP HTTP error: {str(e)}")
    except Exception as e:
        raise Exception(f"Tavily MCP call failed: {str(e)}")


# ─────────────────────────────────────────────────────────────────────────────
# CrewAI Tools for Web Search
# ─────────────────────────────────────────────────────────────────────────────

@tool("Web Search via Tavily")
def tavily_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily AI search engine.

    WHAT: Performs web search with AI-powered result summarization
    WHY: Agents need access to current information not in local KB
    HOW: Calls Tavily MCP server, returns formatted results with citations

    Use this tool when you need:
    - Current industry trends and news
    - Technology comparisons and reviews
    - Expert opinions and case studies
    - Information not available in Knowledge Base
    - "What's the latest on..." queries

    Args:
        query: Natural language search query
        max_results: Maximum number of results to return (default 5)

    Returns:
        str: Formatted search results with titles, URLs, and content snippets

    Example:
        >>> result = tavily_search("solar panel efficiency improvements 2025")
        >>> print(result)

        Web Search Results for: "solar panel efficiency improvements 2025"

        1. Title: Latest Solar Panel Technology Advances
           URL: https://example.com/solar-tech-2025
           Summary: New perovskite-silicon tandem cells achieve 32% efficiency...

        2. Title: Industry Trends in Renewable Energy
           URL: https://example.com/renewable-trends
           Summary: Solar efficiency has improved by 15% over past 3 years...
    """
    import asyncio

    # Validate inputs
    if not query or len(query.strip()) < 3:
        return "Error: Query must be at least 3 characters long."

    max_results = min(max(1, max_results), 10)  # Clamp between 1 and 10

    try:
        logger.info(f"Tavily search: {query} (max_results={max_results})")

        # Call Tavily MCP asynchronously
        arguments = {
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False
        }

        result = asyncio.run(call_tavily_mcp("tavily-search", arguments))

        # Extract results
        results = result.get("results", [])
        answer = result.get("answer", "")

        if not results:
            return f"No web results found for query: '{query}'"

        # Format response
        response = f"Web Search Results for: \"{query}\"\n\n"

        # Add AI-generated answer if available
        if answer:
            response += f"Quick Answer: {answer}\n\n"
            response += "Detailed Sources:\n\n"

        for i, item in enumerate(results, 1):
            title = item.get("title", "Untitled")
            url = item.get("url", "")
            content = item.get("content", "")
            score = item.get("score", 0)

            # Truncate content if too long
            if len(content) > 300:
                content = content[:300] + "..."

            response += f"{i}. {title}\n"
            response += f"   URL: {url}\n"
            response += f"   Summary: {content}\n"
            response += f"   Relevance: {score:.2f}\n\n"

        response += f"\nSearched {len(results)} sources from the web."

        logger.info(f"Tavily search successful: {len(results)} results")
        return response

    except Exception as e:
        error_msg = f"Web search failed: {str(e)}"
        logger.error(error_msg)
        return error_msg


@tool("Extract Web Page Content via Tavily")
def tavily_extract(url: str) -> str:
    """
    Extract full content from a specific web page.

    WHAT: Fetches and extracts structured content from a URL
    WHY: Agents need detailed information from specific sources
    HOW: Calls Tavily MCP extract tool, returns formatted article content

    Use this tool when you need:
    - Full content from a specific article or documentation page
    - Deep-dive into a particular source
    - Detailed information from a URL found in search results

    Args:
        url: Web page URL to extract content from

    Returns:
        str: Formatted page content with title and main text

    Example:
        >>> result = tavily_extract("https://example.com/solar-guide")
        >>> print(result)

        Content from: https://example.com/solar-guide

        Title: Complete Solar Installation Guide

        [Full article content here...]
    """
    import asyncio

    # Validate input
    if not url or not url.startswith(("http://", "https://")):
        return "Error: Invalid URL. Must start with http:// or https://"

    try:
        logger.info(f"Tavily extract: {url}")

        # Call Tavily MCP asynchronously
        arguments = {"url": url}
        result = asyncio.run(call_tavily_mcp("tavily-extract", arguments))

        # Extract content
        title = result.get("title", "Untitled")
        content = result.get("content", "")

        if not content:
            return f"No content could be extracted from: {url}"

        # Format response
        response = f"Content from: {url}\n\n"
        response += f"Title: {title}\n\n"
        response += f"{content}\n\n"
        response += f"Source: {url}"

        logger.info(f"Tavily extract successful: {len(content)} chars")
        return response

    except Exception as e:
        error_msg = f"Web page extraction failed: {str(e)}"
        logger.error(error_msg)
        return error_msg


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test the Tavily MCP tools from command line.

    Usage:
        python -m src.tools.mcp_client

    Requires TAVILY_API_KEY environment variable to be set.
    """
    import sys

    print("🌐 Testing Tavily MCP Tools...\n")

    # Check API key
    api_key = get_tavily_api_key()
    if not api_key:
        print("❌ Error: TAVILY_API_KEY not set in environment")
        sys.exit(1)

    print(f"✅ API key found: {api_key[:10]}...")
    print(f"📡 MCP URL: {get_tavily_mcp_url()}\n")

    # Test search
    test_query = "LiFePO4 battery technology 2025"
    print(f"Testing search: '{test_query}'")
    print("-" * 80)

    try:
        result = tavily_search.func(test_query, max_results=3)
        print(result)
        print("-" * 80)
        print("\n✅ Search test complete!")
    except Exception as e:
        print(f"\n❌ Search test failed: {e}")
        sys.exit(1)

    # Test extract (skip in basic test)
    print("\n💡 To test extract, run:")
    print('   tavily_extract.func("https://example.com/article")')
    print("\n✅ All tests complete!")
