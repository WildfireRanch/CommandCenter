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
import time
from typing import Optional, Dict, Any
from crewai.tools import tool
import httpx

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Rate Limiting and Retry Configuration
# ─────────────────────────────────────────────────────────────────────────────

# Simple rate limiting state (in-memory)
_last_request_time = 0
_min_request_interval = 1.0  # Minimum seconds between requests


def rate_limit_wait():
    """
    Simple rate limiting: wait if needed between requests.

    WHAT: Prevents hitting Tavily API rate limits
    WHY: Production stability and API quota management
    HOW: Tracks last request time, sleeps if needed
    """
    global _last_request_time

    current_time = time.time()
    time_since_last = current_time - _last_request_time

    if time_since_last < _min_request_interval:
        sleep_time = _min_request_interval - time_since_last
        logger.debug(f"Rate limiting: sleeping {sleep_time:.2f}s")
        time.sleep(sleep_time)

    _last_request_time = time.time()


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


def call_tavily_api(tool_name: str, arguments: Dict[str, Any], max_retries: int = 3) -> Dict[str, Any]:
    """
    Call Tavily API directly via REST endpoint with retry logic.

    NOTE: Using direct Tavily REST API instead of MCP for CrewAI compatibility.
    CrewAI tools must be synchronous, and the Tavily API is simpler than MCP.

    Args:
        tool_name: Name of the tool ("search" or "extract")
        arguments: Tool arguments as dictionary
        max_retries: Maximum number of retry attempts (default 3)

    Returns:
        dict: API response

    Raises:
        Exception: If API call fails after all retries
    """
    api_key = get_tavily_api_key()
    if not api_key:
        raise ValueError("TAVILY_API_KEY environment variable not set")

    # Tavily REST API endpoints
    base_url = "https://api.tavily.com"

    # Map tool names to endpoints
    endpoint_map = {
        "tavily-search": f"{base_url}/search",
        "search": f"{base_url}/search",
        "tavily-extract": f"{base_url}/extract",
        "extract": f"{base_url}/extract"
    }

    endpoint = endpoint_map.get(tool_name)
    if not endpoint:
        raise ValueError(f"Unknown Tavily tool: {tool_name}")

    # Add API key to arguments
    payload = {**arguments, "api_key": api_key}

    # Retry loop with exponential backoff
    last_error = None
    for attempt in range(max_retries):
        try:
            # Rate limiting
            rate_limit_wait()

            # Use synchronous httpx client for CrewAI compatibility
            with httpx.Client(timeout=30.0) as client:
                response = client.post(endpoint, json=payload)
                response.raise_for_status()
                result = response.json()

                # Check for API errors
                if "error" in result:
                    error_msg = result.get("error", "Unknown error")
                    raise Exception(f"Tavily API error: {error_msg}")

                logger.info(f"Tavily API call successful on attempt {attempt + 1}")
                return result

        except httpx.TimeoutException as e:
            last_error = f"Tavily API request timed out (30s)"
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff: 1s, 2s, 4s

        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_json = e.response.json()
                error_detail = error_json.get("error", error_json.get("message", ""))
            except:
                error_detail = e.response.text[:200]

            last_error = f"Tavily API HTTP {e.response.status_code}: {error_detail}"

            # Don't retry on client errors (400-499), except rate limits
            if 400 <= e.response.status_code < 500 and e.response.status_code != 429:
                logger.error(f"Client error, not retrying: {last_error}")
                raise Exception(last_error)

            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except httpx.HTTPError as e:
            last_error = f"Tavily API HTTP error: {str(e)}"
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

        except Exception as e:
            last_error = f"Tavily API call failed: {str(e)}"
            logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {last_error}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)

    # All retries exhausted
    error_msg = f"Tavily API failed after {max_retries} attempts. Last error: {last_error}"
    logger.error(error_msg)
    raise Exception(error_msg)


# ─────────────────────────────────────────────────────────────────────────────
# CrewAI Tools for Web Search
# ─────────────────────────────────────────────────────────────────────────────

@tool("Web Search via Tavily")
def tavily_search(query: str, max_results: int = 5) -> str:
    """
    Search the web using Tavily AI search engine.

    WHAT: Performs web search with AI-powered result summarization
    WHY: Agents need access to current information not in local KB
    HOW: Calls Tavily REST API, returns formatted results with citations

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
    # Validate inputs
    if not query or len(query.strip()) < 3:
        return "Error: Query must be at least 3 characters long."

    max_results = min(max(1, max_results), 10)  # Clamp between 1 and 10

    try:
        logger.info(f"Tavily search: {query} (max_results={max_results})")

        # Call Tavily API synchronously (CrewAI compatible)
        arguments = {
            "query": query,
            "max_results": max_results,
            "include_answer": True,
            "include_raw_content": False,
            "search_depth": "advanced"  # Get comprehensive results
        }

        result = call_tavily_api("search", arguments)

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
            if score:
                response += f"   Relevance: {score:.2f}\n"
            response += "\n"

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
    HOW: Calls Tavily REST API extract endpoint, returns formatted content

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
    # Validate input
    if not url or not url.startswith(("http://", "https://")):
        return "Error: Invalid URL. Must start with http:// or https://"

    try:
        logger.info(f"Tavily extract: {url}")

        # Call Tavily API synchronously (CrewAI compatible)
        arguments = {"urls": [url]}  # Tavily extract API expects array
        result = call_tavily_api("extract", arguments)

        # Extract content (result is a list of extracted pages)
        results = result.get("results", [])
        if not results:
            return f"No content could be extracted from: {url}"

        # Get first result
        page = results[0]
        title = page.get("title", "Untitled")
        content = page.get("raw_content", "") or page.get("content", "")

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
    Test the Tavily API tools from command line.

    Usage:
        python -m src.tools.mcp_client

    Requires TAVILY_API_KEY environment variable to be set.
    """
    import sys

    print("🌐 Testing Tavily API Tools...\n")

    # Check API key
    api_key = get_tavily_api_key()
    if not api_key:
        print("❌ Error: TAVILY_API_KEY not set in environment")
        sys.exit(1)

    print(f"✅ API key found: {api_key[:10]}...")
    print(f"📡 API URL: https://api.tavily.com\n")

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
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Test extract (skip in basic test)
    print("\n💡 To test extract, run:")
    print('   python -c "from src.tools.mcp_client import tavily_extract; print(tavily_extract.func(\\"https://example.com/article\\"))"')
    print("\n✅ All tests complete!")
