"""
Tools for CrewAI agents.

Available tools:
- solark: Fetch real-time SolArk solar system data
- kb_search: Search the knowledge base
"""

from .solark import get_solark_status, format_status_summary
from .kb_search import search_knowledge_base, get_context_files

__all__ = [
    "get_solark_status",
    "format_status_summary",
    "search_knowledge_base",
    "get_context_files",
]
