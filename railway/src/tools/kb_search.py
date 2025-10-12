# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/tools/kb_search.py
# PURPOSE: Knowledge Base search tool for CrewAI agents
#
# WHAT IT DOES:
#   - Searches the knowledge base using semantic similarity
#   - Returns relevant document chunks with source citations
#   - Formats results for agent consumption
#
# DEPENDENCIES:
#   - kb.sync (for search_kb function)
#
# USAGE:
#   from tools.kb_search import search_knowledge_base
#
#   result = search_knowledge_base("What is the minimum battery SOC?")
#   print(result)
# ═══════════════════════════════════════════════════════════════════════════

from typing import Dict
from crewai.tools import tool
from ..kb.sync import search_kb


# ─────────────────────────────────────────────────────────────────────────────
# High-Level Interface (This is what agents use)
# ─────────────────────────────────────────────────────────────────────────────

@tool("Search Knowledge Base")
def search_knowledge_base(query: str, limit: int = 5) -> str:
    """
    Search the knowledge base for relevant information.

    WHAT: Searches KB using semantic similarity
    WHY: Agents need access to system documentation and procedures
    HOW: Generates query embedding, searches pgvector, returns formatted results

    Use this tool when you need detailed information about:
    - Solar system specifications
    - Battery thresholds and operating limits
    - Operating procedures and best practices
    - Ranch infrastructure details
    - Business plans and guidelines

    Args:
        query: Natural language search query
        limit: Number of results to return (default 5, max 20)

    Returns:
        str: Formatted search results with source citations

    Example:
        >>> result = search_knowledge_base("What is the minimum battery SOC?")
        >>> print(result)
        Here's what I found:

        1. Minimum SOC: 30% (never go below)...
           Source: solar-shack-context.docx (similarity: 0.92)

        Sources consulted: solar-shack-context.docx, battery-guide.docx
    """
    # Validate inputs
    if not query or len(query.strip()) < 3:
        return "Error: Query must be at least 3 characters long."

    limit = min(max(1, limit), 20)  # Clamp between 1 and 20

    try:
        # Call the search function
        result = search_kb(query, limit=limit)

        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return f"Search failed: {error}"

        # Format results for agent
        chunks = result.get("results", [])
        citations = result.get("citations", [])

        if not chunks:
            return (
                f"No relevant information found in knowledge base for query: '{query}'\n\n"
                "Try rephrasing your query or searching for more general terms."
            )

        # Build formatted response
        response = "Here's what I found:\n\n"

        for i, chunk in enumerate(chunks, 1):
            content = chunk['content']
            source = chunk['source']
            similarity = chunk['similarity']

            # Truncate very long chunks for readability
            if len(content) > 500:
                content = content[:500] + "..."

            response += f"{i}. {content}\n"
            response += f"   Source: {source} (similarity: {similarity:.2f})\n\n"

        # Add citation summary
        if citations:
            response += f"Sources consulted: {', '.join(citations)}"

        return response

    except Exception as e:
        return f"Error searching knowledge base: {str(e)}"


def get_context_files(essential_only: bool = False, max_chars: int = None) -> str:
    """
    Retrieve context files that should be loaded into agent system prompts.

    WHAT: Fetches documents marked as is_context_file=TRUE with optional filtering
    WHY: Critical information that agents should always have available
    HOW: Queries kb_documents table with selective loading, returns formatted content

    Args:
        essential_only: If True, only load essential context (excludes large/optional files)
        max_chars: Optional maximum character limit (truncates if exceeded)

    Returns:
        str: Formatted context file content, or empty string if none found

    Example:
        >>> # Load all context files
        >>> context = get_context_files()

        >>> # Load only essential context (for SYSTEM queries)
        >>> context = get_context_files(essential_only=True)

        >>> # Load with character limit
        >>> context = get_context_files(max_chars=5000)
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info(f"=== get_context_files(essential_only={essential_only}, max_chars={max_chars}) START ===")
        from ..utils.db import get_connection, query_all
        logger.info("Imports successful, attempting database connection...")

        with get_connection() as conn:
            logger.info("Database connection established, querying for context files...")
            context_docs = query_all(
                conn,
                """
                SELECT title, full_content, LENGTH(full_content) as content_length
                FROM kb_documents
                WHERE is_context_file = TRUE
                ORDER BY title
                """,
                as_dict=True
            )
            logger.info(f"Query complete: Found {len(context_docs) if context_docs else 0} context files")

        if not context_docs:
            logger.warning("⚠️  No context files returned from query!")
            return ""

        # Filter out large non-essential files if essential_only=True
        # Files larger than 5000 chars are considered non-essential for SYSTEM queries
        if essential_only:
            essential_docs = []
            for doc in context_docs:
                content_len = doc.get('content_length', 0)
                # Keep files smaller than 5000 chars (essential info)
                if content_len < 5000:
                    essential_docs.append(doc)
                    logger.info(f"Including essential file: {doc.get('title')} ({content_len} chars)")
                else:
                    logger.info(f"Skipping non-essential file: {doc.get('title')} ({content_len} chars) - too large")
            context_docs = essential_docs

        # Format as markdown sections
        context = "\n\n## KNOWLEDGE BASE CONTEXT\n\n"
        context += "The following information is critical system knowledge:\n\n"

        total_chars = 0
        for doc in context_docs:
            doc_title = doc.get('title', 'Untitled')
            doc_content = doc.get('full_content', '')
            content_length = len(doc_content)

            # Check if adding this doc would exceed max_chars limit
            if max_chars and (total_chars + content_length > max_chars):
                remaining = max_chars - total_chars
                if remaining > 500:  # Only include if we can fit at least 500 chars
                    doc_content = doc_content[:remaining] + "\n[...truncated for token budget...]"
                    content_length = len(doc_content)
                    logger.info(f"Truncating {doc_title} to fit within {max_chars} char budget")
                else:
                    logger.info(f"Skipping {doc_title} - would exceed char budget")
                    break

            logger.info(f"Processing context file: {doc_title} ({content_length} chars)")

            context += f"### {doc_title}\n\n"
            context += f"{doc_content}\n\n"
            context += "---\n\n"

            total_chars += content_length

            if max_chars and total_chars >= max_chars:
                logger.info(f"Reached character budget limit ({max_chars}), stopping")
                break

        total_length = len(context)
        logger.info(f"✅ Context compiled successfully: {total_length} total characters")
        logger.info("=== get_context_files() END ===")
        return context

    except Exception as e:
        logger.error(f"❌ ERROR in get_context_files(): {e}", exc_info=True)
        print(f"⚠️  Warning: Could not load context files: {e}")
        return ""


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Test the KB search tool from command line.

    Usage:
        python -m src.tools.kb_search

    Requires database to be populated with KB documents.
    """
    import sys

    print("🔍 Testing KB Search Tool...\n")

    # Test search
    test_query = "solar battery threshold"
    print(f"Query: '{test_query}'")
    print("\nResults:")
    print("-" * 80)

    result = search_knowledge_base.func(test_query, limit=3)
    print(result)
    print("-" * 80)

    # Test context files
    print("\n\n📚 Loading context files...")
    print("-" * 80)
    context = get_context_files()

    if context:
        print(f"Loaded {context.count('###')} context file(s)")
        print(context[:500] + "..." if len(context) > 500 else context)
    else:
        print("No context files found")

    print("-" * 80)
    print("\n✅ Test complete!")
