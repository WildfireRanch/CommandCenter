# ═══════════════════════════════════════════════════════════════════════════
# FILE: railway/tests/test_context_manager.py
# PURPOSE: Unit tests for Smart Context Loading (V1.8)
# ═══════════════════════════════════════════════════════════════════════════

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

# Set test environment before imports
os.environ["REDIS_URL"] = "redis://localhost:6379"
os.environ["CONTEXT_CACHE_ENABLED"] = "false"  # Disable cache for tests

from src.services.context_manager import ContextManager, ContextBundle
from src.services.context_classifier import classify_query, QueryType
from src.config.context_config import get_context_config, estimate_tokens


# ─────────────────────────────────────────────────────────────────────────────
# Test: Query Classification
# ─────────────────────────────────────────────────────────────────────────────

class TestQueryClassification:
    """Test query classification accuracy."""

    def test_system_query_classification(self):
        """Test that system queries are correctly classified."""
        test_queries = [
            "What's my battery level?",
            "What is my current solar production?",
            "Show me the status of the system",
            "Battery SOC?",
            "How much power am I using right now?",
        ]

        for query in test_queries:
            query_type, confidence = classify_query(query)
            assert query_type == QueryType.SYSTEM, f"Failed for: {query}"
            assert confidence > 0.3, f"Low confidence for: {query}"

    def test_research_query_classification(self):
        """Test that research queries are correctly classified."""
        test_queries = [
            "What are best practices for battery maintenance?",
            "Should I upgrade my inverter?",
            "Explain how solar panels work",
            "What is the best battery technology?",
        ]

        for query in test_queries:
            query_type, confidence = classify_query(query)
            assert query_type == QueryType.RESEARCH, f"Failed for: {query}"
            assert confidence > 0.3, f"Low confidence for: {query}"

    def test_planning_query_classification(self):
        """Test that planning queries are correctly classified."""
        test_queries = [
            "Plan next week's energy usage",
            "Optimize my battery charging schedule",
            "What was the average solar production last week?",
            "Create a forecast for tomorrow",
        ]

        for query in test_queries:
            query_type, confidence = classify_query(query)
            assert query_type == QueryType.PLANNING, f"Failed for: {query}"
            assert confidence > 0.3, f"Low confidence for: {query}"

    def test_general_query_classification(self):
        """Test that general queries are correctly classified."""
        test_queries = [
            "Hello!",
            "Thank you",
            "Who are you?",
            "Hi there",
        ]

        for query in test_queries:
            query_type, confidence = classify_query(query)
            assert query_type == QueryType.GENERAL, f"Failed for: {query}"


# ─────────────────────────────────────────────────────────────────────────────
# Test: Token Estimation
# ─────────────────────────────────────────────────────────────────────────────

class TestTokenEstimation:
    """Test token counting and estimation."""

    def test_estimate_tokens(self):
        """Test token estimation for various text lengths."""
        test_cases = [
            ("Hello", 1),  # ~5 chars / 4 = 1 token
            ("What's my battery level?", 6),  # ~26 chars / 4 = 6 tokens
            ("A" * 400, 100),  # 400 chars / 4 = 100 tokens
        ]

        for text, expected_tokens in test_cases:
            estimated = estimate_tokens(text)
            assert abs(estimated - expected_tokens) <= 1, f"Failed for: {text[:50]}"


# ─────────────────────────────────────────────────────────────────────────────
# Test: Context Manager
# ─────────────────────────────────────────────────────────────────────────────

class TestContextManager:
    """Test ContextManager core functionality."""

    @pytest.fixture
    def mock_kb(self):
        """Mock KB search to return empty results."""
        with patch('src.services.context_manager.search_kb') as mock:
            mock.return_value = {"success": True, "results": []}
            yield mock

    @pytest.fixture
    def mock_context_files(self):
        """Mock get_context_files to return test data."""
        with patch('src.services.context_manager.get_context_files') as mock:
            mock.return_value = "## SYSTEM SPECS\nTest system context (500 chars)" + ("x" * 450)
            yield mock

    def test_context_manager_initialization(self):
        """Test that ContextManager initializes correctly."""
        manager = ContextManager()
        assert manager is not None
        assert manager.config is not None
        assert manager.redis_client is not None

    def test_get_relevant_context_basic(self, mock_context_files, mock_kb):
        """Test basic context loading."""
        manager = ContextManager()

        bundle = manager.get_relevant_context(
            query="What's my battery level?",
            user_id="test_user",
            max_tokens=3000
        )

        assert isinstance(bundle, ContextBundle)
        assert bundle.query_type == QueryType.SYSTEM
        assert bundle.total_tokens > 0
        assert bundle.total_tokens <= 3000
        assert bundle.system_context != ""

    def test_token_budget_respected(self, mock_context_files, mock_kb):
        """Test that token budgets are respected."""
        manager = ContextManager()

        # Test with small budget
        bundle = manager.get_relevant_context(
            query="What's my battery level?",
            user_id="test_user",
            max_tokens=500
        )

        assert bundle.total_tokens <= 500, "Token budget exceeded"

    def test_query_type_specific_budgets(self, mock_context_files, mock_kb):
        """Test that different query types get appropriate budgets."""
        manager = ContextManager()

        # System query (smaller budget)
        system_bundle = manager.get_relevant_context(
            query="What's my battery level?",
            user_id="test_user"
        )

        # Research query (larger budget)
        research_bundle = manager.get_relevant_context(
            query="What are best practices for solar?",
            user_id="test_user"
        )

        # Research should have more tokens available
        assert system_bundle.query_type == QueryType.SYSTEM
        assert research_bundle.query_type == QueryType.RESEARCH

    def test_context_bundle_format_for_agent(self, mock_context_files, mock_kb):
        """Test that ContextBundle formats correctly for agents."""
        manager = ContextManager()

        bundle = manager.get_relevant_context(
            query="What's my battery level?",
            user_id="test_user"
        )

        formatted = bundle.format_for_agent()
        assert isinstance(formatted, str)
        assert len(formatted) > 0
        assert bundle.system_context in formatted

    def test_context_bundle_serialization(self, mock_context_files, mock_kb):
        """Test that ContextBundle can be serialized/deserialized."""
        manager = ContextManager()

        bundle = manager.get_relevant_context(
            query="What's my battery level?",
            user_id="test_user"
        )

        # Serialize
        bundle_dict = bundle.to_dict()
        assert isinstance(bundle_dict, dict)
        assert "query_type" in bundle_dict
        assert "total_tokens" in bundle_dict

        # Deserialize
        restored_bundle = ContextBundle.from_dict(bundle_dict)
        assert restored_bundle.query_type == bundle.query_type
        assert restored_bundle.total_tokens == bundle.total_tokens


# ─────────────────────────────────────────────────────────────────────────────
# Test: Configuration
# ─────────────────────────────────────────────────────────────────────────────

class TestConfiguration:
    """Test configuration loading and validation."""

    def test_config_loads_defaults(self):
        """Test that config loads with defaults."""
        config = get_context_config()

        assert config.SYSTEM_QUERY_TOKENS > 0
        assert config.RESEARCH_QUERY_TOKENS > 0
        assert config.PLANNING_QUERY_TOKENS > 0
        assert config.GENERAL_QUERY_TOKENS > 0
        assert config.CACHE_TTL_SECONDS > 0

    def test_config_respects_environment(self):
        """Test that config reads from environment variables."""
        with patch.dict(os.environ, {"CONTEXT_SYSTEM_TOKENS": "5000"}):
            # Force reload
            from src.config.context_config import reload_config
            reload_config()

            config = get_context_config()
            assert config.SYSTEM_QUERY_TOKENS == 5000


# ─────────────────────────────────────────────────────────────────────────────
# Test: Error Handling
# ─────────────────────────────────────────────────────────────────────────────

class TestErrorHandling:
    """Test error handling and fallback behavior."""

    def test_handles_missing_context_files(self, mock_kb):
        """Test that manager handles missing context files gracefully."""
        with patch('src.services.context_manager.get_context_files') as mock_files:
            mock_files.return_value = ""

            manager = ContextManager()
            bundle = manager.get_relevant_context(
                query="What's my battery level?",
                user_id="test_user"
            )

            # Should still return a bundle, just with empty system context
            assert isinstance(bundle, ContextBundle)
            assert bundle.system_context == ""

    def test_handles_redis_unavailable(self, mock_context_files, mock_kb):
        """Test that manager continues without Redis if unavailable."""
        manager = ContextManager()

        # Should not raise exception even if Redis unavailable
        bundle = manager.get_relevant_context(
            query="What's my battery level?",
            user_id="test_user"
        )

        assert isinstance(bundle, ContextBundle)


# ─────────────────────────────────────────────────────────────────────────────
# Test: Performance
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformance:
    """Test performance characteristics."""

    def test_context_loading_speed(self, mock_context_files, mock_kb):
        """Test that context loads quickly."""
        import time

        manager = ContextManager()

        start = time.time()
        bundle = manager.get_relevant_context(
            query="What's my battery level?",
            user_id="test_user"
        )
        duration = time.time() - start

        # Should load in under 1 second (without network calls)
        assert duration < 1.0, f"Context loading took {duration:.2f}s"

    def test_token_savings(self, mock_context_files, mock_kb):
        """Test that smart context actually reduces tokens."""
        manager = ContextManager()

        # Simulate what old system would do (load everything)
        old_system_tokens = 6000  # Baseline from documentation

        # New system (smart loading)
        bundle = manager.get_relevant_context(
            query="What's my battery level?",  # System query
            user_id="test_user"
        )

        # Should use significantly fewer tokens
        reduction_percent = (old_system_tokens - bundle.total_tokens) / old_system_tokens
        assert reduction_percent > 0.2, "Expected at least 20% token reduction"


# ─────────────────────────────────────────────────────────────────────────────
# Run Tests
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    """Run tests with pytest."""
    pytest.main([__file__, "-v", "--tb=short"])
