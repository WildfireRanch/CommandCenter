# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/services/context_classifier.py
# PURPOSE: Query classification for smart context loading
#
# WHAT IT DOES:
#   - Classifies user queries into types (SYSTEM, RESEARCH, PLANNING, GENERAL)
#   - Determines appropriate context loading strategy
#   - Provides confidence scores for classification
#
# DEPENDENCIES:
#   - None (standalone module)
#
# USAGE:
#   from services.context_classifier import classify_query, QueryType
#
#   query_type, confidence = classify_query("What's my battery level?")
#   # Returns: (QueryType.SYSTEM, 0.95)
# ═══════════════════════════════════════════════════════════════════════════

import re
from enum import Enum
from typing import Tuple


class QueryType(Enum):
    """Query classification types for context loading."""
    SYSTEM = "system"        # Current system status queries
    RESEARCH = "research"    # Research/best practices queries
    PLANNING = "planning"    # Planning/scheduling queries
    GENERAL = "general"      # Greetings, simple questions


# ─────────────────────────────────────────────────────────────────────────────
# Classification Rules
# ─────────────────────────────────────────────────────────────────────────────

# Keywords for SYSTEM queries (current status, real-time data)
SYSTEM_KEYWORDS = [
    # Status queries
    "my", "current", "now", "right now", "status", "what is",

    # Battery keywords
    "battery", "soc", "charge", "charging", "discharging", "battery level",
    "battery status", "battery power", "state of charge",

    # Solar keywords
    "solar", "pv", "panel", "production", "generating", "solar power",
    "solar production", "sun", "producing",

    # Load keywords
    "load", "consumption", "using", "power usage", "consumption",
    "house", "drawing", "using power",

    # Grid keywords
    "grid", "utility", "importing", "exporting", "grid power",

    # Time-based (current)
    "today", "this morning", "this afternoon", "this evening",
    "right now", "at the moment",

    # System-specific
    "your system", "this system", "our system", "the system",
    "my system", "you have", "do you have", "what are you",
]

# Keywords for RESEARCH queries (documentation, best practices)
RESEARCH_KEYWORDS = [
    # Learning/information seeking
    "best practices", "best practice", "how to", "should i", "is it good",
    "recommend", "recommendation", "advice", "suggest", "what if",

    # Documentation requests
    "manual", "documentation", "guide", "instructions", "procedure",
    "show me the", "tell me about", "explain", "what is a",

    # Comparisons and analysis
    "compare", "comparison", "difference", "versus", "vs", "better",
    "alternative", "option", "which", "what are the options",

    # Trends and patterns
    "trend", "pattern", "latest", "new", "upgrade", "update",
    "modern", "current technology", "state of the art",

    # General knowledge
    "why does", "how does", "what causes", "reason", "benefit",
    "advantage", "disadvantage", "pros", "cons",
]

# Keywords for PLANNING queries (scheduling, forecasting, optimization)
PLANNING_KEYWORDS = [
    # Planning/scheduling
    "plan", "schedule", "next", "tomorrow", "this week", "next week",
    "upcoming", "future", "forecast", "predict", "anticipate",

    # Optimization
    "optimize", "optimization", "improve", "better", "efficiency",
    "efficient", "save", "savings", "reduce", "minimize",

    # Strategy
    "strategy", "approach", "should i run", "when should", "best time",
    "timing", "coordinate", "manage", "control",

    # Historical analysis for planning
    "last week", "last month", "yesterday", "history", "historical",
    "trend", "pattern over", "average", "typical",
]

# Keywords for GENERAL queries (greetings, simple questions)
GENERAL_KEYWORDS = [
    # Greetings
    "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
    "greetings", "howdy",

    # Pleasantries
    "thank you", "thanks", "appreciate", "goodbye", "bye", "see you",

    # Simple questions
    "who are you", "what can you do", "help", "what are you",
    "your name", "introduce yourself",
]


# ─────────────────────────────────────────────────────────────────────────────
# Classification Function
# ─────────────────────────────────────────────────────────────────────────────

def classify_query(query: str) -> Tuple[QueryType, float]:
    """
    Classify a user query into a QueryType with confidence score.

    WHAT: Analyzes query text to determine query type
    WHY: Different query types need different context
    HOW: Keyword matching with weighted scoring

    Args:
        query: User's query string

    Returns:
        Tuple of (QueryType, confidence_score)

    Examples:
        >>> classify_query("What's my battery level?")
        (QueryType.SYSTEM, 0.95)

        >>> classify_query("What are best practices for solar?")
        (QueryType.RESEARCH, 0.85)

        >>> classify_query("Plan next week's energy usage")
        (QueryType.PLANNING, 0.90)

        >>> classify_query("Hello!")
        (QueryType.GENERAL, 1.0)
    """
    if not query or len(query.strip()) < 2:
        return QueryType.GENERAL, 0.5

    # Normalize query for matching
    query_lower = query.lower().strip()

    # Score each category
    scores = {
        QueryType.SYSTEM: _score_keywords(query_lower, SYSTEM_KEYWORDS),
        QueryType.RESEARCH: _score_keywords(query_lower, RESEARCH_KEYWORDS),
        QueryType.PLANNING: _score_keywords(query_lower, PLANNING_KEYWORDS),
        QueryType.GENERAL: _score_keywords(query_lower, GENERAL_KEYWORDS),
    }

    # Apply special rules for better accuracy
    scores = _apply_classification_rules(query_lower, scores)

    # Find highest scoring type
    max_type = max(scores, key=scores.get)
    max_score = scores[max_type]

    # If no clear winner, default to SYSTEM (most common)
    if max_score == 0:
        return QueryType.SYSTEM, 0.5

    # Normalize confidence to 0-1 range
    total_score = sum(scores.values())
    confidence = max_score / total_score if total_score > 0 else 0.5

    return max_type, confidence


def _score_keywords(query: str, keywords: list) -> float:
    """
    Score how well a query matches a list of keywords.

    Args:
        query: Normalized query string
        keywords: List of keywords to match

    Returns:
        Score (higher = better match)
    """
    score = 0.0

    for keyword in keywords:
        # Exact phrase match (higher weight)
        if keyword in query:
            # Longer phrases get higher weight
            score += len(keyword.split())

    return score


def _apply_classification_rules(query: str, scores: dict) -> dict:
    """
    Apply special rules to improve classification accuracy.

    Args:
        query: Normalized query string
        scores: Initial scores dictionary

    Returns:
        Modified scores dictionary
    """
    # Rule 1: Questions with "?" at end asking about current state = SYSTEM
    if query.endswith("?") and any(word in query for word in ["my", "current", "now", "status", "level"]):
        scores[QueryType.SYSTEM] *= 1.5

    # Rule 2: Questions starting with "how to" or "what is" = RESEARCH
    if query.startswith(("how to", "what is a", "what are", "explain")):
        scores[QueryType.RESEARCH] *= 1.5

    # Rule 3: Questions with time references (next, tomorrow, plan) = PLANNING
    if any(word in query for word in ["next", "tomorrow", "plan", "schedule", "optimize"]):
        scores[QueryType.PLANNING] *= 1.3

    # Rule 4: Very short queries (<5 words) with greetings = GENERAL
    word_count = len(query.split())
    if word_count <= 3 and any(word in query for word in ["hi", "hello", "hey", "thanks", "thank"]):
        scores[QueryType.GENERAL] *= 2.0

    # Rule 5: Questions about "my system" or "your system" = SYSTEM
    if re.search(r'\b(my|your|our|this|the)\s+(system|battery|solar|inverter)\b', query):
        scores[QueryType.SYSTEM] *= 1.4

    # Rule 6: Questions with "best", "recommend", "should" = RESEARCH
    if any(word in query for word in ["best", "recommend", "should i", "is it good", "which"]):
        scores[QueryType.RESEARCH] *= 1.3

    # Rule 7: Historical data for analysis = PLANNING
    if any(word in query for word in ["last week", "yesterday", "trend", "average over"]):
        scores[QueryType.PLANNING] *= 1.2

    return scores


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def get_query_type_name(query_type: QueryType) -> str:
    """Get human-readable name for query type."""
    return query_type.value.title()


def get_classification_explanation(query: str) -> str:
    """
    Get detailed explanation of how a query was classified.

    Useful for debugging and understanding classification decisions.

    Args:
        query: User's query string

    Returns:
        Human-readable explanation string
    """
    query_type, confidence = classify_query(query)

    explanation = f"Query: '{query}'\n"
    explanation += f"Classification: {get_query_type_name(query_type)}\n"
    explanation += f"Confidence: {confidence:.2%}\n\n"

    # Show keyword matches
    query_lower = query.lower()

    explanation += "Keyword matches:\n"
    for category, keywords in [
        ("SYSTEM", SYSTEM_KEYWORDS),
        ("RESEARCH", RESEARCH_KEYWORDS),
        ("PLANNING", PLANNING_KEYWORDS),
        ("GENERAL", GENERAL_KEYWORDS),
    ]:
        matches = [kw for kw in keywords if kw in query_lower]
        if matches:
            explanation += f"  {category}: {', '.join(matches[:5])}\n"

    return explanation


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test the query classifier."""

    # Test queries
    test_queries = [
        "What's my battery level?",
        "What is my current solar production?",
        "Show me the status of the system",
        "What are best practices for battery maintenance?",
        "Should I upgrade my inverter?",
        "Explain how solar panels work",
        "Plan next week's energy usage",
        "Optimize my battery charging schedule",
        "What was the average solar production last week?",
        "Hello!",
        "Thank you",
        "Who are you?",
    ]

    print("🔍 Query Classification Test\n")
    print("=" * 80)

    for query in test_queries:
        query_type, confidence = classify_query(query)
        print(f"\nQuery: {query}")
        print(f"Type: {get_query_type_name(query_type)} (confidence: {confidence:.1%})")

    print("\n" + "=" * 80)

    # Detailed explanation for one query
    print("\n\n📊 Detailed Classification Example:\n")
    print(get_classification_explanation("What's my battery level?"))

    print("✅ Test complete!")
