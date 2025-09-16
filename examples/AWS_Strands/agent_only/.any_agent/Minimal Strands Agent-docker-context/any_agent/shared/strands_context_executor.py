"""Context-aware Strands A2A executor for session isolation."""

import logging
from strands.multiagent.a2a.executor import StrandsA2AExecutor
from a2a.server.agent_execution import RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

logger = logging.getLogger(__name__)


class ContextAwareStrandsA2AExecutor(StrandsA2AExecutor):
    """Custom executor that passes context_id to context-aware agents."""

    async def _execute_streaming(self, context: RequestContext, updater):
        """Execute request in streaming mode with context isolation."""
        logger.info("Executing request with context isolation")
        user_input = context.get_user_input()

        # Extract context_id from the request context
        context_id = context.context_id
        logger.info(f"🔑 Extracted context_id from RequestContext: {context_id}")

        try:
            # Check if agent supports context isolation
            if hasattr(self.agent, "_context_aware_wrapper") and hasattr(
                self.agent, "__call__"
            ):
                # Call context-aware agent with context_id
                logger.info(
                    f"🎯 Calling context-aware agent with context_id: {context_id}"
                )

                # For context-aware agents, call directly with context_id
                if hasattr(self.agent, "stream_async_with_context"):
                    # If agent has context-aware streaming
                    async for event in self.agent.stream_async_with_context(
                        user_input, context_id=context_id
                    ):
                        await self._handle_streaming_event(event, updater)
                else:
                    # Fall back to non-streaming call then simulate streaming
                    result = self.agent(user_input, context_id=context_id)
                    # Simulate streaming event
                    if hasattr(result, "content"):
                        content = result.content
                    else:
                        content = str(result)

                    # Send as streaming data
                    await self._handle_streaming_event({"data": content}, updater)

                    # Send final result
                    await self._handle_streaming_event({"result": result}, updater)
            else:
                # Original behavior for non-context-aware agents
                logger.warning(
                    "Agent does not support context isolation, using original streaming"
                )
                async for event in self.agent.stream_async(user_input):
                    await self._handle_streaming_event(event, updater)

        except Exception:
            logger.exception("Error in context-aware streaming execution")

    def extract_structured_message_data(self, context: RequestContext):
        """Extract structured message with role, parts, messageId, taskId, contextId"""
        import json

        message_data = {}

        try:
            if hasattr(context, "message") and hasattr(context.message, "parts"):
                for part in context.message.parts:
                    if (
                        hasattr(part, "kind")
                        and part.kind == "text"
                        and hasattr(part, "text")
                    ):
                        message_data["text"] = part.text
                        break

            # Extract metadata
            if hasattr(context, "message"):
                message = context.message
                message_data["messageId"] = getattr(message, "messageId", None)
                message_data["taskId"] = getattr(message, "taskId", None)
                message_data["contextId"] = getattr(message, "contextId", None)
                message_data["role"] = getattr(message, "role", "user")

            # Fallback to direct content if available
            if not message_data.get("text"):
                if hasattr(context, "content"):
                    message_data["text"] = context.content
                elif hasattr(context, "get_user_input"):
                    message_data["text"] = context.get_user_input()

            logger.info(
                f"📝 Extracted message data: {json.dumps(message_data, indent=2)}"
            )
            return message_data

        except Exception as e:
            logger.warning(f"Error extracting structured message data: {e}")
            # Fallback to basic extraction
            return {
                "text": context.get_user_input()
                if hasattr(context, "get_user_input")
                else "Default query"
            }

    async def execute_stream(self, context: RequestContext, event_queue: EventQueue):
        """Execute agent request with streaming via event queue"""

        logger.info("🚀 Starting execute_stream with context isolation")

        try:
            # Extract structured message data
            message_data = self.extract_structured_message_data(context)
            query = message_data.get("text", "Default query")
            context_id = message_data.get("contextId") or context.context_id

            logger.info(f"🔑 Using context_id: {context_id}")
            logger.info(f"📝 Processing query: {query[:100]}...")

            # Check if agent supports context isolation and streaming
            if hasattr(self.agent, "_context_aware_wrapper") and hasattr(
                self.agent, "__call__"
            ):
                logger.info("🎯 Using context-aware agent for streaming")

                if hasattr(self.agent, "stream_async"):
                    # Use streaming if available
                    async for chunk in self.agent.stream_async(
                        query, context_id=context_id
                    ):
                        if isinstance(chunk, dict) and chunk.get("content"):
                            event_queue.enqueue_event(
                                new_agent_text_message(chunk["content"])
                            )
                        elif isinstance(chunk, str):
                            event_queue.enqueue_event(new_agent_text_message(chunk))
                else:
                    # Fallback to non-streaming
                    result = self.agent(query, context_id=context_id)
                    content = str(result)
                    event_queue.enqueue_event(new_agent_text_message(content))
            else:
                # Original behavior for non-context-aware agents
                logger.warning("⚠️  Agent does not support context isolation")
                if hasattr(self.agent, "stream_async"):
                    async for chunk in self.agent.stream_async(query):
                        if isinstance(chunk, dict) and chunk.get("content"):
                            event_queue.enqueue_event(
                                new_agent_text_message(chunk["content"])
                            )
                        elif isinstance(chunk, str):
                            event_queue.enqueue_event(new_agent_text_message(chunk))
                else:
                    result = self.agent(query)
                    content = str(result)
                    event_queue.enqueue_event(new_agent_text_message(content))

            logger.info("✅ execute_stream completed successfully")

        except Exception as e:
            error_msg = f"❌ Error during streaming execution: {str(e)}"
            logger.error(error_msg)
            event_queue.enqueue_event(new_agent_text_message(error_msg))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Cancel an ongoing execution.

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
        """

        logger.info("🛑 Cancel method called for task cancellation")

        try:
            task = context.current_task
            task_id = task.id if task else "unknown"
            context_id = (
                context.context_id if hasattr(context, "context_id") else "unknown"
            )

            logger.info(f"🔑 Cancelling task {task_id} with context {context_id}")

            # Check if there's an active task to cancel
            if not task:
                logger.warning("⚠️  No active task found to cancel")
                event_queue.enqueue_event(
                    new_agent_text_message("No active task to cancel")
                )
                return

            # Check if task is already completed
            if hasattr(task, "status") and hasattr(task.status, "state"):
                state = str(task.status.state)
                if state in ["completed", "cancelled", "failed"]:
                    logger.warning(f"⚠️  Task already in final state: {state}")
                    event_queue.enqueue_event(
                        new_agent_text_message(f"Task already {state}, cannot cancel")
                    )
                    return

            # Attempt to cancel any context-aware agent operations
            if hasattr(self.agent, "_context_aware_wrapper"):
                logger.info("🎯 Attempting to cancel context-aware agent operations")

                # If the agent has context-specific instances, try to clean them up
                if (
                    hasattr(self.agent, "context_agents")
                    and hasattr(self.agent.context_agents, "__contains__")
                    and context_id in self.agent.context_agents
                ):
                    logger.info(
                        f"🧹 Cleaning up context-specific agent instance for {context_id}"
                    )
                    # Remove the context-specific agent instance to stop any ongoing operations
                    del self.agent.context_agents[context_id]

            # Send cancellation confirmation message
            cancellation_message = f"Task {task_id} has been successfully cancelled"
            event_queue.enqueue_event(new_agent_text_message(cancellation_message))

            logger.info(f"✅ Task {task_id} cancellation completed successfully")

        except Exception as e:
            # Handle any errors during cancellation gracefully
            error_msg = f"⚠️  Error during task cancellation: {str(e)}"
            logger.error(error_msg)

            # Still send a cancellation message even if there were errors
            try:
                event_queue.enqueue_event(
                    new_agent_text_message("Task cancellation attempted with errors")
                )
            except Exception:
                # If we can't even send a message, just log it
                logger.error("Failed to send cancellation message to event queue")
