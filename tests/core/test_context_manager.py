"""Tests for consolidated context manager."""

import threading
import time
from unittest.mock import Mock, patch
import pytest

from any_agent.core.context_manager import (
    ContextManager,
    ContextState,
    BaseContextWrapper,
    SessionManagedWrapper,
    GenericContextWrapper,
    create_context_wrapper
)


class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name: str = "test_agent", model: str = "test_model"):
        self.name = name
        self.model = model
        self.call_count = 0

    def __call__(self, message: str, **kwargs) -> str:
        self.call_count += 1
        return f"Response from {self.name}: {message}"


class TestContextManager:
    """Test ContextManager functionality."""

    def test_get_or_create_context_new(self):
        """Test creating new context."""
        manager = ContextManager()
        agent_factory = lambda: MockAgent("test")

        context_id, agent = manager.get_or_create_context("ctx1", agent_factory)

        assert context_id == "ctx1"
        assert isinstance(agent, MockAgent)
        assert agent.name == "test"
        assert "ctx1" in manager.contexts

    def test_get_or_create_context_existing(self):
        """Test retrieving existing context."""
        manager = ContextManager()
        agent_factory = lambda: MockAgent("test")

        # Create first time
        context_id1, agent1 = manager.get_or_create_context("ctx1", agent_factory)

        # Get same context
        context_id2, agent2 = manager.get_or_create_context("ctx1", agent_factory)

        assert context_id1 == context_id2 == "ctx1"
        assert agent1 is agent2  # Same instance
        assert manager.contexts["ctx1"].message_count == 2

    def test_get_or_create_context_default(self):
        """Test using default context ID."""
        manager = ContextManager()
        agent_factory = lambda: MockAgent("test")

        context_id, agent = manager.get_or_create_context(None, agent_factory)

        assert context_id == "default"
        assert "default" in manager.contexts

    def test_cleanup_context(self):
        """Test context cleanup."""
        manager = ContextManager()
        agent_factory = lambda: MockAgent("test")

        # Create context
        manager.get_or_create_context("ctx1", agent_factory)
        assert "ctx1" in manager.contexts

        # Clean up
        result = manager.cleanup_context("ctx1")
        assert result is True
        assert "ctx1" not in manager.contexts

        # Try to clean up non-existent context
        result = manager.cleanup_context("nonexistent")
        assert result is False

    def test_list_contexts(self):
        """Test listing contexts."""
        manager = ContextManager()
        agent_factory = lambda: MockAgent("test")

        manager.get_or_create_context("ctx1", agent_factory)
        manager.get_or_create_context("ctx2", agent_factory)

        contexts = manager.list_contexts()
        assert set(contexts) == {"ctx1", "ctx2"}

    def test_get_context_stats(self):
        """Test context statistics."""
        manager = ContextManager()
        agent_factory = lambda: MockAgent("test")

        manager.get_or_create_context("ctx1", agent_factory)
        time.sleep(0.01)  # Small delay to ensure different timestamps
        manager.get_or_create_context("ctx1", agent_factory)  # Access again

        stats = manager.get_context_stats()
        assert "ctx1" in stats
        assert stats["ctx1"]["message_count"] == 2
        assert "created_at" in stats["ctx1"]
        assert "last_accessed" in stats["ctx1"]

    def test_thread_safety(self):
        """Test thread safety of context manager."""
        manager = ContextManager()
        agent_factory = lambda: MockAgent("test")
        results = {}

        def worker(thread_id: int):
            context_id, agent = manager.get_or_create_context(f"ctx{thread_id}", agent_factory)
            results[thread_id] = (context_id, agent.name)

        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All threads should have completed successfully
        assert len(results) == 5
        for i in range(5):
            assert results[i][0] == f"ctx{i}"
            assert results[i][1] == "test"


class TestSessionManagedWrapper:
    """Test SessionManagedWrapper functionality."""

    def test_session_managed_wrapper_with_session_manager(self):
        """Test wrapper with session manager."""
        agent = MockAgent()
        agent.session_manager = Mock()
        agent.session_manager.session_id = "original"

        wrapper = SessionManagedWrapper(agent, "Test wrapper")
        result = wrapper("hello", context_id="new_session")

        assert "hello" in result
        # Session should be restored
        assert agent.session_manager.session_id == "original"

    def test_session_managed_wrapper_without_session_manager(self):
        """Test wrapper without session manager."""
        agent = MockAgent()
        wrapper = SessionManagedWrapper(agent, "Test wrapper")

        result = wrapper("hello", context_id="ctx1")
        assert "hello" in result
        assert agent.call_count == 1


class TestGenericContextWrapper:
    """Test GenericContextWrapper functionality."""

    def test_generic_wrapper_context_isolation(self):
        """Test that different contexts get different agent instances."""
        agent = MockAgent("original")
        wrapper = GenericContextWrapper(agent, "Test wrapper")

        # Call with different contexts
        result1 = wrapper("msg1", context_id="ctx1")
        result2 = wrapper("msg2", context_id="ctx2")

        # Should have created separate instances
        stats = wrapper.get_context_stats()
        assert len(stats) == 2
        assert "ctx1" in stats
        assert "ctx2" in stats

    def test_generic_wrapper_same_context(self):
        """Test that same context reuses agent instance."""
        agent = MockAgent("original")
        wrapper = GenericContextWrapper(agent, "Test wrapper")

        # Call same context twice
        result1 = wrapper("msg1", context_id="ctx1")
        result2 = wrapper("msg2", context_id="ctx1")

        # Should reuse instance
        stats = wrapper.get_context_stats()
        assert len(stats) == 1
        assert stats["ctx1"]["message_count"] == 2

    def test_generic_wrapper_attribute_delegation(self):
        """Test that attributes are delegated to original agent."""
        agent = MockAgent("original")
        agent.custom_attr = "test_value"
        wrapper = GenericContextWrapper(agent, "Test wrapper")

        assert wrapper.custom_attr == "test_value"
        assert wrapper.name == "original"


class TestFactoryFunction:
    """Test create_context_wrapper factory function."""

    def test_create_strands_wrapper(self):
        """Test creating Strands wrapper."""
        agent = MockAgent()
        wrapper = create_context_wrapper(agent, "strands")

        assert isinstance(wrapper, SessionManagedWrapper)

    def test_create_generic_wrapper(self):
        """Test creating generic wrapper."""
        agent = MockAgent()
        wrapper = create_context_wrapper(agent, "langchain")

        assert isinstance(wrapper, GenericContextWrapper)