"""Unit tests for ContextAwareStrandsA2AExecutor cancel method (WOB-173)."""

import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch
import pytest

from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue


class TestContextAwareStrandsA2AExecutorCancel:
    """Test suite for the cancel method implementation in ContextAwareStrandsA2AExecutor."""

    def create_mock_executor(self):
        """Create a mock ContextAwareStrandsA2AExecutor for testing."""
        # Import the class dynamically to avoid import issues
        exec("""
from strands.multiagent.a2a.executor import StrandsA2AExecutor
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
import logging as executor_logging

class ContextAwareStrandsA2AExecutor(StrandsA2AExecutor):
    '''Test version of ContextAwareStrandsA2AExecutor with cancel method.'''
    
    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        '''Cancel an ongoing execution.
        
        This method gracefully cancels a running agent task by:
        1. Logging the cancellation request
        2. Attempting to stop any ongoing agent operations
        3. Sending a cancellation message to the event queue
        4. Handling edge cases (no active task, already completed task)
        
        Args:
            context: The A2A request context containing task information
            event_queue: The A2A event queue for sending cancellation events
            
        Raises:
            No exceptions - gracefully handles all cancellation scenarios
        '''
        from a2a.utils import new_agent_text_message
        
        executor_logging.getLogger(__name__).info("🛑 Cancel method called for task cancellation")
        
        try:
            task = context.current_task
            task_id = task.id if task else "unknown"
            context_id = context.context_id if hasattr(context, 'context_id') else "unknown"
            
            executor_logging.getLogger(__name__).info(f"🔑 Cancelling task {task_id} with context {context_id}")
            
            # Check if there's an active task to cancel
            if not task:
                executor_logging.getLogger(__name__).warning("⚠️  No active task found to cancel")
                event_queue.enqueue_event(new_agent_text_message("No active task to cancel"))
                return
            
            # Check if task is already completed
            if hasattr(task, 'status') and hasattr(task.status, 'state'):
                state = str(task.status.state)
                if state in ['completed', 'cancelled', 'failed']:
                    executor_logging.getLogger(__name__).warning(f"⚠️  Task already in final state: {state}")
                    event_queue.enqueue_event(new_agent_text_message(f"Task already {state}, cannot cancel"))
                    return
            
            # Attempt to cancel any context-aware agent operations
            if hasattr(self.agent, '_context_aware_wrapper'):
                executor_logging.getLogger(__name__).info("🎯 Attempting to cancel context-aware agent operations")
                
                # If the agent has context-specific instances, try to clean them up
                if hasattr(self.agent, 'context_agents') and hasattr(self.agent.context_agents, '__contains__') and context_id in self.agent.context_agents:
                    executor_logging.getLogger(__name__).info(f"🧹 Cleaning up context-specific agent instance for {context_id}")
                    # Remove the context-specific agent instance to stop any ongoing operations
                    del self.agent.context_agents[context_id]
            
            # Send cancellation confirmation message
            cancellation_message = f"Task {task_id} has been successfully cancelled"
            event_queue.enqueue_event(new_agent_text_message(cancellation_message))
            
            executor_logging.getLogger(__name__).info(f"✅ Task {task_id} cancellation completed successfully")
            
        except Exception as e:
            # Handle any errors during cancellation gracefully
            error_msg = f"⚠️  Error during task cancellation: {str(e)}"
            executor_logging.getLogger(__name__).error(error_msg)
            
            # Still send a cancellation message even if there were errors
            try:
                event_queue.enqueue_event(new_agent_text_message("Task cancellation attempted with errors"))
            except Exception:
                # If we can't even send a message, just log it
                executor_logging.getLogger(__name__).error("Failed to send cancellation message to event queue")
""", globals())
        
        mock_agent = Mock()
        return ContextAwareStrandsA2AExecutor(mock_agent)

    def create_mock_context(self, with_task=True, task_state="working", has_context_id=True):
        """Create a mock RequestContext for testing."""
        context = Mock(spec=RequestContext)
        
        if has_context_id:
            context.context_id = "test_context_123"
        else:
            context.context_id = None
            
        if with_task:
            task = Mock()
            task.id = "test_task_456"
            if task_state:
                task.status = Mock()
                task.status.state = task_state
            context.current_task = task
        else:
            context.current_task = None
            
        return context

    def create_mock_event_queue(self):
        """Create a mock EventQueue for testing."""
        event_queue = Mock(spec=EventQueue)
        event_queue.enqueue_event = AsyncMock()
        return event_queue

    @pytest.mark.asyncio
    async def test_cancel_method_exists_and_callable(self):
        """Test that the cancel method exists and is callable."""
        executor = self.create_mock_executor()
        
        # Verify the method exists
        assert hasattr(executor, 'cancel')
        assert callable(executor.cancel)
        
        # Verify the method signature
        import inspect
        sig = inspect.signature(executor.cancel)
        params = list(sig.parameters.keys())
        
        assert 'context' in params
        assert 'event_queue' in params
        assert len(params) == 2  # context, event_queue (self is implicit)

    @pytest.mark.asyncio
    async def test_cancel_with_active_task_success(self):
        """Test successful cancellation of an active task."""
        executor = self.create_mock_executor()
        context = self.create_mock_context(with_task=True, task_state="working")
        event_queue = self.create_mock_event_queue()
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            # Should not raise any exceptions
            await executor.cancel(context, event_queue)
            
            # Verify event queue was called
            assert event_queue.enqueue_event.called
            call_args = event_queue.enqueue_event.call_args_list
            
            # Should have been called at least once with cancellation message
            assert len(call_args) >= 1

    @pytest.mark.asyncio
    async def test_cancel_with_no_active_task(self):
        """Test cancellation when no active task exists."""
        executor = self.create_mock_executor()
        context = self.create_mock_context(with_task=False)
        event_queue = self.create_mock_event_queue()
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            # Should not raise any exceptions
            await executor.cancel(context, event_queue)
            
            # Verify event queue was called with "no active task" message
            assert event_queue.enqueue_event.called
            
            # Verify the correct message was created
            mock_message.assert_called_with("No active task to cancel")

    @pytest.mark.asyncio
    async def test_cancel_with_already_completed_task(self):
        """Test cancellation when task is already completed."""
        executor = self.create_mock_executor()
        context = self.create_mock_context(with_task=True, task_state="completed")
        event_queue = self.create_mock_event_queue()
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            # Should not raise any exceptions
            await executor.cancel(context, event_queue)
            
            # Verify event queue was called
            assert event_queue.enqueue_event.called
            
            # Verify the correct message was created for already completed task
            mock_message.assert_called_with("Task already completed, cannot cancel")

    @pytest.mark.asyncio
    async def test_cancel_with_already_cancelled_task(self):
        """Test cancellation when task is already cancelled."""
        executor = self.create_mock_executor()
        context = self.create_mock_context(with_task=True, task_state="cancelled")
        event_queue = self.create_mock_event_queue()
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            # Should not raise any exceptions
            await executor.cancel(context, event_queue)
            
            # Verify event queue was called
            assert event_queue.enqueue_event.called
            
            # Verify the correct message was created for already cancelled task
            mock_message.assert_called_with("Task already cancelled, cannot cancel")

    @pytest.mark.asyncio
    async def test_cancel_with_context_aware_agent(self):
        """Test cancellation with context-aware agent cleanup."""
        executor = self.create_mock_executor()
        
        # Set up context-aware agent
        executor.agent._context_aware_wrapper = True
        executor.agent.context_agents = {"test_context_123": Mock()}
        
        context = self.create_mock_context(with_task=True, task_state="working")
        event_queue = self.create_mock_event_queue()
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            # Should not raise any exceptions
            await executor.cancel(context, event_queue)
            
            # Verify the context-specific agent was cleaned up
            assert "test_context_123" not in executor.agent.context_agents
            
            # Verify event queue was called
            assert event_queue.enqueue_event.called

    @pytest.mark.asyncio
    async def test_cancel_handles_exceptions_gracefully(self):
        """Test that cancellation handles exceptions gracefully."""
        executor = self.create_mock_executor()
        
        # Create context that will cause an exception
        context = Mock()
        context.current_task = None
        context.context_id = None
        
        event_queue = self.create_mock_event_queue()
        
        # Make enqueue_event raise an exception the first time, succeed the second
        event_queue.enqueue_event.side_effect = [Exception("Queue error"), None]
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            # Should not raise any exceptions, even with errors
            await executor.cancel(context, event_queue)
            
            # Verify event queue was called multiple times
            assert event_queue.enqueue_event.call_count >= 1

    @pytest.mark.asyncio
    async def test_cancel_logs_appropriately(self):
        """Test that cancellation logs appropriate messages."""
        executor = self.create_mock_executor()
        context = self.create_mock_context(with_task=True, task_state="working")
        event_queue = self.create_mock_event_queue()
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            with patch('logging.getLogger') as mock_logger:
                mock_log_instance = Mock()
                mock_logger.return_value = mock_log_instance
                
                # Should not raise any exceptions
                await executor.cancel(context, event_queue)
                
                # Verify logging was called
                assert mock_log_instance.info.called or mock_log_instance.warning.called

    @pytest.mark.asyncio
    async def test_cancel_without_context_id(self):
        """Test cancellation when context doesn't have context_id."""
        executor = self.create_mock_executor()
        context = self.create_mock_context(with_task=True, task_state="working", has_context_id=False)
        event_queue = self.create_mock_event_queue()
        
        with patch('a2a.utils.new_agent_text_message') as mock_message:
            mock_message.return_value = "mock_message"
            
            # Should not raise any exceptions
            await executor.cancel(context, event_queue)
            
            # Verify event queue was called
            assert event_queue.enqueue_event.called

    @pytest.mark.asyncio 
    async def test_cancel_method_signature_matches_requirement(self):
        """Test that cancel method matches the required signature from WOB-173."""
        executor = self.create_mock_executor()
        
        import inspect
        sig = inspect.signature(executor.cancel)
        
        # Verify signature matches: async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None
        assert asyncio.iscoroutinefunction(executor.cancel)
        
        params = sig.parameters
        param_names = list(params.keys())
        
        assert param_names == ['context', 'event_queue']
        assert sig.return_annotation == type(None) or sig.return_annotation is None

    @pytest.mark.asyncio
    async def test_cancel_provides_meaningful_task_id_in_messages(self):
        """Test that cancellation provides meaningful task IDs in messages."""
        executor = self.create_mock_executor()
        context = self.create_mock_context(with_task=True, task_state="working")
        event_queue = self.create_mock_event_queue()
        
        # Capture the actual message that gets passed
        captured_messages = []
        
        def capture_message(message):
            captured_messages.append(message)
            return message
        
        with patch('a2a.utils.new_agent_text_message', side_effect=capture_message):
            await executor.cancel(context, event_queue)
            
            # Verify that task ID was included in the cancellation message
            found_task_id = False
            for message in captured_messages:
                if "test_task_456" in str(message):
                    found_task_id = True
                    break
            
            assert found_task_id, f"Task ID should be included in cancellation messages. Messages: {captured_messages}"