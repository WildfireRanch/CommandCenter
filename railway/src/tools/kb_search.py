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
from ..kb.sync import search_kb


# ─────────────────────────────────────────────────────────────────────────────
# High-Level Interface (This is what agents use)
# ─────────────────────────────────────────────────────────────────────────────

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


def get_context_files() -> str:
    """
    Retrieve all context files that should be loaded into agent system prompts.

    WHAT: Fetches documents marked as is_context_file=TRUE
    WHY: Critical information that agents should always have available
    HOW: Queries kb_documents table, returns formatted content

    Returns:
        str: Formatted context file content, or empty string if none found

    Example:
        >>> context = get_context_files()
        >>> print(context)

        ## KNOWLEDGE BASE CONTEXT

        ### solar-shack-context.docx

        [Full document content here...]
    """
    try:
        from ..utils.db import get_connection, query_all

        with get_connection() as conn:
            context_docs = query_all(
                conn,
                """
                SELECT title, full_content
                FROM kb_documents
                WHERE is_context_file = TRUE
                ORDER BY title
                """,
                as_dict=True
            )

        if not context_docs:
            return ""

        # Format as markdown sections
        context = "\n\n## KNOWLEDGE BASE CONTEXT\n\n"
        context += "The following information is critical system knowledge:\n\n"

        for doc in context_docs:
            context += f"### {doc['title']}\n\n"
            context += f"{doc['full_content']}\n\n"
            context += "---\n\n"

        return context

    except Exception as e:
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

    result = search_knowledge_base(test_query, limit=3)
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
