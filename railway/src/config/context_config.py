# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/src/config/context_config.py
# PURPOSE: Configuration for smart context loading
#
# WHAT IT DOES:
#   - Defines token budgets per query type
#   - Configures cache settings (TTL, enabled flag)
#   - Sets KB search parameters
#   - Manages fallback behavior
#
# DEPENDENCIES:
#   - os (for environment variables)
#
# USAGE:
#   from config.context_config import get_context_config
#
#   config = get_context_config()
#   print(config.SYSTEM_QUERY_TOKENS)  # 2000
# ═══════════════════════════════════════════════════════════════════════════

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ContextConfig:
    """Configuration for context loading and caching."""

    # ─────────────────────────────────────────────────────────────────────────
    # Token Budgets (per query type)
    # ─────────────────────────────────────────────────────────────────────────

    # SYSTEM queries: Current status, real-time data
    # Needs: System specs + minimal KB (if any)
    SYSTEM_QUERY_TOKENS: int = 2000

    # RESEARCH queries: Best practices, documentation
    # Needs: System specs + full KB search + potential web search
    RESEARCH_QUERY_TOKENS: int = 4000

    # PLANNING queries: Scheduling, optimization
    # Needs: System specs + historical data + relevant KB
    PLANNING_QUERY_TOKENS: int = 3500

    # GENERAL queries: Greetings, simple questions
    # Needs: Minimal context
    GENERAL_QUERY_TOKENS: int = 1000

    # ─────────────────────────────────────────────────────────────────────────
    # Cache Settings
    # ─────────────────────────────────────────────────────────────────────────

    # Enable/disable caching
    CACHE_ENABLED: bool = True

    # Cache TTL (time-to-live) in seconds
    CACHE_TTL_SECONDS: int = 300  # 5 minutes

    # Redis connection settings
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_MAX_RETRIES: int = 3
    REDIS_TIMEOUT: int = 5  # seconds
    REDIS_SSL: bool = False

    # ─────────────────────────────────────────────────────────────────────────
    # KB Search Settings
    # ─────────────────────────────────────────────────────────────────────────

    # Minimum similarity score for KB results (0-1)
    KB_MIN_SIMILARITY: float = 0.3

    # Maximum KB documents per query type
    KB_MAX_DOCS_SYSTEM: int = 1      # System queries rarely need KB
    KB_MAX_DOCS_RESEARCH: int = 5    # Research needs comprehensive KB
    KB_MAX_DOCS_PLANNING: int = 3    # Planning needs moderate KB
    KB_MAX_DOCS_GENERAL: int = 0     # General queries don't need KB

    # Maximum tokens allocated to KB context (per query type)
    KB_MAX_TOKENS_SYSTEM: int = 500
    KB_MAX_TOKENS_RESEARCH: int = 2000
    KB_MAX_TOKENS_PLANNING: int = 1000
    KB_MAX_TOKENS_GENERAL: int = 0

    # ─────────────────────────────────────────────────────────────────────────
    # Conversation History Settings
    # ─────────────────────────────────────────────────────────────────────────

    # Maximum number of conversation messages to include
    MAX_CONVERSATION_MESSAGES: int = 5

    # Maximum tokens for conversation history
    MAX_CONVERSATION_TOKENS: int = 1000

    # ─────────────────────────────────────────────────────────────────────────
    # Fallback Behavior
    # ─────────────────────────────────────────────────────────────────────────

    # If cache miss, load context directly
    FALLBACK_ON_CACHE_MISS: bool = True

    # If Redis unavailable, continue without caching
    FALLBACK_ON_ERROR: bool = True

    # If token budget exceeded, truncate intelligently
    TRUNCATE_ON_BUDGET_EXCEEDED: bool = True

    # ─────────────────────────────────────────────────────────────────────────
    # Token Estimation (approximate characters per token)
    # ─────────────────────────────────────────────────────────────────────────

    # Approximate: 1 token ≈ 4 characters (for English text)
    CHARS_PER_TOKEN: float = 4.0

    # ─────────────────────────────────────────────────────────────────────────
    # System Context (always included)
    # ─────────────────────────────────────────────────────────────────────────

    # Always include system specs context
    ALWAYS_INCLUDE_SYSTEM_CONTEXT: bool = True

    # Reserved tokens for system context (never truncated)
    SYSTEM_CONTEXT_RESERVED_TOKENS: int = 1000


# ─────────────────────────────────────────────────────────────────────────────
# Configuration Factory
# ─────────────────────────────────────────────────────────────────────────────

_config_instance: Optional[ContextConfig] = None


def get_context_config() -> ContextConfig:
    """
    Get the global context configuration instance.

    WHAT: Returns configured ContextConfig with environment overrides
    WHY: Centralized configuration management
    HOW: Creates singleton instance, reads from environment variables

    Returns:
        ContextConfig: Configured instance

    Example:
        >>> config = get_context_config()
        >>> print(config.CACHE_ENABLED)
        True
    """
    global _config_instance

    if _config_instance is not None:
        return _config_instance

    # Load configuration from environment with defaults
    config = ContextConfig(
        # Token budgets
        SYSTEM_QUERY_TOKENS=int(os.getenv("CONTEXT_SYSTEM_TOKENS", "2000")),
        RESEARCH_QUERY_TOKENS=int(os.getenv("CONTEXT_RESEARCH_TOKENS", "4000")),
        PLANNING_QUERY_TOKENS=int(os.getenv("CONTEXT_PLANNING_TOKENS", "3500")),
        GENERAL_QUERY_TOKENS=int(os.getenv("CONTEXT_GENERAL_TOKENS", "1000")),

        # Cache settings
        CACHE_ENABLED=os.getenv("CONTEXT_CACHE_ENABLED", "true").lower() in ("true", "1", "yes"),
        CACHE_TTL_SECONDS=int(os.getenv("CONTEXT_CACHE_TTL", "300")),

        # Redis settings
        REDIS_URL=os.getenv("REDIS_URL", "redis://localhost:6379"),
        REDIS_MAX_RETRIES=int(os.getenv("REDIS_MAX_RETRIES", "3")),
        REDIS_TIMEOUT=int(os.getenv("REDIS_TIMEOUT", "5")),
        REDIS_SSL=os.getenv("REDIS_SSL", "false").lower() in ("true", "1", "yes"),

        # KB search settings
        KB_MIN_SIMILARITY=float(os.getenv("KB_MIN_SIMILARITY", "0.3")),
        KB_MAX_DOCS_SYSTEM=int(os.getenv("KB_MAX_DOCS_SYSTEM", "1")),
        KB_MAX_DOCS_RESEARCH=int(os.getenv("KB_MAX_DOCS_RESEARCH", "5")),
        KB_MAX_DOCS_PLANNING=int(os.getenv("KB_MAX_DOCS_PLANNING", "3")),
        KB_MAX_DOCS_GENERAL=int(os.getenv("KB_MAX_DOCS_GENERAL", "0")),

        # KB token limits
        KB_MAX_TOKENS_SYSTEM=int(os.getenv("KB_MAX_TOKENS_SYSTEM", "500")),
        KB_MAX_TOKENS_RESEARCH=int(os.getenv("KB_MAX_TOKENS_RESEARCH", "2000")),
        KB_MAX_TOKENS_PLANNING=int(os.getenv("KB_MAX_TOKENS_PLANNING", "1000")),
        KB_MAX_TOKENS_GENERAL=int(os.getenv("KB_MAX_TOKENS_GENERAL", "0")),

        # Conversation history
        MAX_CONVERSATION_MESSAGES=int(os.getenv("MAX_CONVERSATION_MESSAGES", "5")),
        MAX_CONVERSATION_TOKENS=int(os.getenv("MAX_CONVERSATION_TOKENS", "1000")),

        # Fallback behavior
        FALLBACK_ON_CACHE_MISS=os.getenv("FALLBACK_ON_CACHE_MISS", "true").lower() in ("true", "1", "yes"),
        FALLBACK_ON_ERROR=os.getenv("FALLBACK_ON_ERROR", "true").lower() in ("true", "1", "yes"),
        TRUNCATE_ON_BUDGET_EXCEEDED=os.getenv("TRUNCATE_ON_BUDGET_EXCEEDED", "true").lower() in ("true", "1", "yes"),

        # Token estimation
        CHARS_PER_TOKEN=float(os.getenv("CHARS_PER_TOKEN", "4.0")),

        # System context
        ALWAYS_INCLUDE_SYSTEM_CONTEXT=os.getenv("ALWAYS_INCLUDE_SYSTEM_CONTEXT", "true").lower() in ("true", "1", "yes"),
        SYSTEM_CONTEXT_RESERVED_TOKENS=int(os.getenv("SYSTEM_CONTEXT_RESERVED_TOKENS", "1000")),
    )

    _config_instance = config
    return config


def reload_config() -> None:
    """
    Reload configuration from environment variables.

    Useful for testing or when environment changes.
    """
    global _config_instance
    _config_instance = None


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

def estimate_tokens(text: str) -> int:
    """
    Estimate token count for a given text.

    Uses the CHARS_PER_TOKEN ratio for estimation.

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    config = get_context_config()
    char_count = len(text)
    return int(char_count / config.CHARS_PER_TOKEN)


def format_config_summary() -> str:
    """
    Get human-readable summary of current configuration.

    Returns:
        Formatted configuration summary
    """
    config = get_context_config()

    summary = "═══════════════════════════════════════════\n"
    summary += "SMART CONTEXT LOADING CONFIGURATION\n"
    summary += "═══════════════════════════════════════════\n\n"

    summary += "Token Budgets (per query type):\n"
    summary += f"  SYSTEM:   {config.SYSTEM_QUERY_TOKENS:,} tokens\n"
    summary += f"  RESEARCH: {config.RESEARCH_QUERY_TOKENS:,} tokens\n"
    summary += f"  PLANNING: {config.PLANNING_QUERY_TOKENS:,} tokens\n"
    summary += f"  GENERAL:  {config.GENERAL_QUERY_TOKENS:,} tokens\n\n"

    summary += "Cache Settings:\n"
    summary += f"  Enabled: {config.CACHE_ENABLED}\n"
    summary += f"  TTL: {config.CACHE_TTL_SECONDS}s ({config.CACHE_TTL_SECONDS // 60} minutes)\n"
    summary += f"  Redis URL: {config.REDIS_URL}\n\n"

    summary += "KB Search Limits:\n"
    summary += f"  Min Similarity: {config.KB_MIN_SIMILARITY:.2f}\n"
    summary += f"  SYSTEM: {config.KB_MAX_DOCS_SYSTEM} docs, {config.KB_MAX_TOKENS_SYSTEM} tokens\n"
    summary += f"  RESEARCH: {config.KB_MAX_DOCS_RESEARCH} docs, {config.KB_MAX_TOKENS_RESEARCH} tokens\n"
    summary += f"  PLANNING: {config.KB_MAX_DOCS_PLANNING} docs, {config.KB_MAX_TOKENS_PLANNING} tokens\n\n"

    summary += "Fallback Behavior:\n"
    summary += f"  Cache Miss: {'Continue with direct load' if config.FALLBACK_ON_CACHE_MISS else 'Fail'}\n"
    summary += f"  Redis Error: {'Continue without cache' if config.FALLBACK_ON_ERROR else 'Fail'}\n"
    summary += f"  Budget Exceeded: {'Truncate intelligently' if config.TRUNCATE_ON_BUDGET_EXCEEDED else 'Fail'}\n"

    summary += "\n═══════════════════════════════════════════"

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# CLI Testing Interface
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Test configuration loading."""

    print("⚙️  Context Configuration Test\n")
    print(format_config_summary())

    print("\n\n📊 Token Estimation Examples:\n")
    test_texts = [
        "Hello!",
        "What's my battery level?",
        "This is a longer text with multiple sentences. It should use more tokens than a short greeting.",
    ]

    for text in test_texts:
        tokens = estimate_tokens(text)
        print(f"  '{text[:50]}...' → ~{tokens} tokens")

    print("\n✅ Test complete!")
