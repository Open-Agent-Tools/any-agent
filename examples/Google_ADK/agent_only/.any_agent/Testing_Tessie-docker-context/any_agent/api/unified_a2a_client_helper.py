"""Unified A2A Client Helper based on official a2a-sdk patterns.

This implementation follows the validated patterns from PRD/generic_a2a_client_design.md
and consolidates all framework-specific clients into a single, consistent interface.
"""

import logging
import json
from typing import Any, Dict, List, Optional

try:
    # Official a2a-sdk imports following PRD patterns
    from a2a.client import ClientFactory, A2ACardResolver, ClientConfig
    from a2a.client.helpers import create_text_message_object
    from a2a.types import Role

    A2A_SDK_AVAILABLE = True
except ImportError:
    A2A_SDK_AVAILABLE = False

import httpx

logger = logging.getLogger(__name__)


class UnifiedA2AClientHelper:
    """Unified A2A client helper using official a2a-sdk patterns.

    This client works consistently across all agent frameworks:
    - Google ADK
    - AWS Strands
    - LangChain
    - CrewAI
    - Other A2A-compliant agents
    """

    def __init__(self, timeout: int = 30):
        """Initialize unified A2A client helper.

        Args:
            timeout: Timeout for A2A operations
        """
        self.timeout = timeout

        # Suppress verbose logging from A2A SDK components
        if A2A_SDK_AVAILABLE:
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("a2a.client.card_resolver").setLevel(logging.WARNING)
            logging.getLogger("a2a.client").setLevel(logging.WARNING)

    async def get_agent_info(self, agent_url: str) -> Dict[str, Any]:
        """Get agent information via A2A protocol.

        Uses official A2ACardResolver pattern from PRD.

        Args:
            agent_url: URL of the A2A agent

        Returns:
            Agent info dict with name and connection status

        Raises:
            Exception: If connection or card retrieval fails
        """
        if not A2A_SDK_AVAILABLE:
            raise ImportError(
                "a2a-sdk not available - install with: pip install a2a-sdk>=0.1.0"
            )

        async with httpx.AsyncClient(timeout=self.timeout) as httpx_client:
            # Step 1: Fetch Agent Card using A2ACardResolver (official pattern)
            logger.info(f"Fetching agent card from: {agent_url}")
            resolver = A2ACardResolver(httpx_client=httpx_client, base_url=agent_url)
            agent_card = await resolver.get_agent_card()
            logger.info(f"✅ Agent card retrieved: {agent_card.name}")

            return {
                "name": getattr(agent_card, "name", "Unknown Agent"),
                "description": getattr(agent_card, "description", None),
                "protocol_version": getattr(agent_card, "protocol_version", "unknown"),
                "card": agent_card,
            }

    async def send_message(
        self,
        agent_url: str,
        message_content: str,
        context_id: Optional[str] = None,
        reference_task_ids: Optional[List[str]] = None,
        parent_message_id: Optional[str] = None,
    ) -> List[str]:
        """Send message to agent via A2A protocol using official SDK patterns.

        Follows the complete client creation and message sending pattern from PRD.
        Supports multi-turn conversations with context preservation.

        Args:
            agent_url: URL of the A2A agent
            message_content: User message content
            context_id: Context ID to maintain session state (optional)
            reference_task_ids: List of previous task IDs for context (optional)
            parent_message_id: ID of message being replied to (optional)

        Returns:
            List of response texts from agent

        Raises:
            Exception: If message sending fails
        """
        if not A2A_SDK_AVAILABLE:
            raise ImportError("a2a-sdk not available")

        async with httpx.AsyncClient(timeout=self.timeout) as httpx_client:
            # Step 1: Create A2A client using official pattern
            client, agent_card = await self._create_a2a_client(agent_url, httpx_client)

            try:
                # Step 2: Create message using official helper with Role enum
                message = create_text_message_object(
                    role=Role.user,  # CRITICAL: Use Role.user for user messages
                    content=message_content,
                )

                # Step 2b: Add context fields for multi-turn conversation support
                if context_id:
                    message.context_id = context_id
                    logger.info(f"🔑 ADDED context_id: {context_id}")

                if reference_task_ids:
                    message.reference_task_ids = reference_task_ids
                    logger.info(f"📝 ADDED reference_task_ids: {reference_task_ids}")

                if parent_message_id:
                    # Note: parent_message_id might not be directly supported, will check later
                    # For now, focus on context_id which is the primary field
                    logger.info(
                        f"📎 Parent message ID noted: {parent_message_id} (may need alternative approach)"
                    )

                logger.info(
                    "✅ Message created with official helper and context fields"
                )

                # DEBUG: Log the complete message structure
                if hasattr(message, "model_dump"):
                    try:
                        message_data = message.model_dump(
                            mode="json", exclude_none=True
                        )
                        logger.info(
                            f"🔍 COMPLETE MESSAGE DATA: {json.dumps(message_data, indent=2)}"
                        )
                    except Exception as debug_e:
                        logger.warning(
                            f"Failed to dump message for debugging: {debug_e}"
                        )

                logger.info(
                    f"🎯 SENDING MESSAGE TO AGENT WITH context_id='{context_id}'"
                )

                # Step 3: Send message using client.send_message() - official pattern
                all_responses = []
                response_count = 0

                # Official pattern: client.send_message returns AsyncIterator
                async for response in client.send_message(message):
                    response_count += 1
                    logger.info(f"📨 Received response type: {type(response)}")

                    # Extract response content using official model_dump pattern
                    response_text = self._extract_response_content(response)
                    if response_text:
                        all_responses.append(response_text)

                    # Limit responses to prevent hanging on streaming agents
                    if response_count >= 15:  # Handle AWS Strands streaming responses
                        break

                logger.info(
                    f"✅ Received {len(all_responses)} text responses from agent"
                )

                # For streaming agents (like AWS Strands), return only the final/longest response
                # to avoid UI showing partial/repeated content
                if len(all_responses) > 1:
                    # Filter out fallback responses like "Task completed: Task"
                    meaningful_responses = [
                        r
                        for r in all_responses
                        if not r.startswith("Task completed:")
                        and not r.startswith("Response:")
                    ]

                    if meaningful_responses:
                        # Find the longest meaningful response (likely the final complete one)
                        final_response = max(meaningful_responses, key=len)
                        logger.info(
                            f"🔄 Streaming agent detected, returning final meaningful response (length: {len(final_response)})"
                        )
                        return [final_response]
                    else:
                        # Fall back to longest response even if it's a fallback message
                        final_response = max(all_responses, key=len)
                        logger.info(
                            f"⚠️ Only fallback responses available, returning longest (length: {len(final_response)})"
                        )
                        return [final_response]
                else:
                    # Single response (like Google ADK), return as-is
                    return all_responses

            finally:
                # Always close the client (official pattern)
                await client.close()
                logger.info("✅ A2A client closed")

    async def _create_a2a_client(self, base_url: str, httpx_client: httpx.AsyncClient):
        """Create A2A client using official patterns from PRD.

        Args:
            base_url: Agent base URL
            httpx_client: HTTP client for communication

        Returns:
            Tuple of (client, agent_card)
        """
        # Step 1: Fetch Agent Card using A2ACardResolver
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=base_url)
        agent_card = await resolver.get_agent_card()

        # Step 2: Create ClientConfig with httpx_client (disable streaming for clean responses)
        client_config = ClientConfig(httpx_client=httpx_client, streaming=False)

        # Step 3: Create ClientFactory
        factory = ClientFactory(config=client_config)

        # Step 4: Create client using factory.create(card)
        client = factory.create(card=agent_card)
        logger.info(f"✅ A2A client created: {type(client)}")

        return client, agent_card

    def _extract_response_content(self, response: Any) -> Optional[str]:
        """Extract text content from A2A response using official model_dump pattern.

        Handles responses from all agent frameworks:
        - Google ADK: Single response with artifacts
        - AWS Strands: Streaming responses with progressive artifacts
        - Other frameworks: Various response formats

        Args:
            response: A2A response object

        Returns:
            Text content or None if not extractable
        """
        try:
            logger.debug(
                f"🔍 Response type: {type(response)}, hasattr model_dump: {hasattr(response, 'model_dump')}"
            )

            # Official pattern: use model_dump if available
            if hasattr(response, "model_dump"):
                response_data = response.model_dump(mode="json", exclude_none=True)
                logger.debug(f"📋 Response data keys: {list(response_data.keys())}")
                logger.debug(f"📋 Full response data: {response_data}")

                # Extract agent response from artifacts (primary response location)
                if "artifacts" in response_data:
                    logger.debug(
                        f"🎯 Found artifacts: {len(response_data.get('artifacts', []))}"
                    )
                    for artifact in response_data.get("artifacts", []):
                        for part in artifact.get("parts", []):
                            if "text" in part and part["text"].strip():
                                logger.debug(
                                    f"✅ Extracted from artifacts: {part['text'][:100]}..."
                                )
                                return part["text"]

                # Fallback: extract from direct message parts
                if "parts" in response_data:
                    for part in response_data.get("parts", []):
                        if "text" in part and part["text"].strip():
                            logger.debug(
                                f"✅ Extracted from parts: {part['text'][:100]}..."
                            )
                            return part["text"]

                # Additional extraction for framework-specific formats
                return self._extract_from_framework_specific_format(response_data)

            # Handle tuple responses (Google ADK task objects)
            elif isinstance(response, tuple) and len(response) >= 1:
                logger.debug(f"🔍 Tuple response with {len(response)} items")
                task_obj = response[0]
                logger.debug(
                    f"🔍 Task object type: {type(task_obj)}, has artifacts: {hasattr(task_obj, 'artifacts')}"
                )

                # First, try using model_dump on the task object itself
                if hasattr(task_obj, "model_dump"):
                    try:
                        task_data = task_obj.model_dump(mode="json", exclude_none=True)
                        logger.debug(f"📋 Task data keys: {list(task_data.keys())}")

                        # Extract from task artifacts (Google ADK pattern)
                        if "artifacts" in task_data:
                            logger.debug(
                                f"🎯 Found {len(task_data['artifacts'])} artifacts in task"
                            )
                            for artifact in task_data.get("artifacts", []):
                                if "parts" in artifact:
                                    for part in artifact.get("parts", []):
                                        if "text" in part and part["text"].strip():
                                            logger.debug(
                                                f"✅ Extracted from task artifact parts: {part['text'][:100]}..."
                                            )
                                            return part["text"]

                        # Extract from history (alternative location)
                        if "history" in task_data:
                            for msg in task_data.get("history", []):
                                if msg.get("role") == "agent" and "parts" in msg:
                                    for part in msg.get("parts", []):
                                        if "text" in part and part["text"].strip():
                                            logger.debug(
                                                f"✅ Extracted from task history: {part['text'][:100]}..."
                                            )
                                            return part["text"]

                        # Extract from task status (ADK specific location)
                        if "status" in task_data and isinstance(
                            task_data["status"], dict
                        ):
                            status = task_data["status"]
                            if "message" in status and isinstance(
                                status["message"], dict
                            ):
                                status_msg = status["message"]
                                if "parts" in status_msg:
                                    for part in status_msg.get("parts", []):
                                        if "text" in part and part["text"].strip():
                                            logger.debug(
                                                f"✅ Extracted from task status message: {part['text'][:100]}..."
                                            )
                                            return part["text"]

                    except Exception as e:
                        logger.warning(f"Failed to extract via task model_dump: {e}")

                # Fallback: Direct attribute access
                if hasattr(task_obj, "artifacts") and task_obj.artifacts:
                    logger.debug(f"🎯 Task has {len(task_obj.artifacts)} artifacts")
                    for artifact in task_obj.artifacts:
                        logger.debug(
                            f"🔍 Artifact type: {type(artifact)}, content attrs: {[attr for attr in dir(artifact) if not attr.startswith('_')]}"
                        )
                        if hasattr(artifact, "content") and isinstance(
                            artifact.content, str
                        ):
                            logger.debug(
                                f"✅ Extracted from task artifact content: {artifact.content[:100]}..."
                            )
                            return artifact.content
                        elif hasattr(artifact, "text") and isinstance(
                            artifact.text, str
                        ):
                            logger.debug(
                                f"✅ Extracted from task artifact text: {artifact.text[:100]}..."
                            )
                            return artifact.text
                        elif hasattr(artifact, "parts"):
                            for part in artifact.parts:
                                if hasattr(part, "text") and isinstance(part.text, str):
                                    logger.debug(
                                        f"✅ Extracted from task artifact parts: {part.text[:100]}..."
                                    )
                                    return part.text

                # Check task status directly (ADK pattern)
                if hasattr(task_obj, "status") and task_obj.status:
                    logger.debug(f"🎯 Task has status: {type(task_obj.status)}")
                    if hasattr(task_obj.status, "message") and task_obj.status.message:
                        status_msg = task_obj.status.message
                        logger.debug(f"🔍 Status message type: {type(status_msg)}")
                        if hasattr(status_msg, "parts") and status_msg.parts:
                            for part in status_msg.parts:
                                if hasattr(part, "text") and isinstance(part.text, str):
                                    logger.debug(
                                        f"✅ Extracted from task status message parts: {part.text[:100]}..."
                                    )
                                    return part.text

                logger.warning(
                    f"⚠️ No extractable content found in task object: {type(task_obj).__name__}"
                )
                # Skip generic task completion messages as they don't provide value to users
                return None

            # Handle direct string responses
            elif isinstance(response, str) and response.strip():
                return response

            # Handle dict responses
            elif isinstance(response, dict):
                return self._extract_from_dict_response(response)

            # Default fallback for unknown response types
            logger.warning(f"⚠️ Unknown response type: {type(response)}")
            return f"Response: {type(response).__name__}"

        except Exception as e:
            logger.warning(f"Failed to extract response content: {e}")
            return f"Response received (extraction failed): {type(response).__name__}"

    def _extract_from_framework_specific_format(
        self, response_data: Dict[str, Any]
    ) -> Optional[str]:
        """Extract text from framework-specific response formats.

        Args:
            response_data: Response data dictionary

        Returns:
            Extracted text or None
        """
        # Common response fields across frameworks
        text_fields = ["content", "text", "message", "response", "output", "result"]

        for field in text_fields:
            if field in response_data:
                value = response_data[field]
                if isinstance(value, str) and value.strip():
                    return value
                elif isinstance(value, list) and value:
                    # Handle array of content parts
                    for item in value:
                        if isinstance(item, dict) and "text" in item:
                            text = item["text"]
                            if isinstance(text, str) and text.strip():
                                return text
                        elif isinstance(item, str) and item.strip():
                            return item
                elif isinstance(value, dict):
                    # Recursive extraction for nested content
                    nested_text = self._extract_from_dict_response(value)
                    if nested_text:
                        return nested_text

        return None

    def _extract_from_dict_response(
        self, response_dict: Dict[str, Any]
    ) -> Optional[str]:
        """Extract text from dictionary response.

        Args:
            response_dict: Dictionary response

        Returns:
            Extracted text or None
        """
        text_fields = ["content", "text", "message", "response", "output"]

        for field in text_fields:
            if field in response_dict:
                value = response_dict[field]
                if isinstance(value, str) and value.strip():
                    return value

        return None

    async def cancel_task(self, agent_url: str, session_id: str) -> Dict[str, Any]:
        """Cancel an ongoing task using A2A protocol cancellation.

        Args:
            agent_url: The A2A agent URL to send cancel request to
            session_id: The session identifier for the task to cancel

        Returns:
            Cancellation result dictionary with success status and details

        Note:
            This method sends a cancellation request to the A2A agent. The agent
            implementation determines how to handle the cancellation gracefully.
        """
        try:
            logger.info(
                f"Sending cancel request to agent {agent_url} for session {session_id}"
            )

            if not A2A_SDK_AVAILABLE:
                return {
                    "success": False,
                    "error": "A2A SDK not available - install with: pip install a2a-sdk>=0.1.0",
                    "session_id": session_id,
                }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                try:
                    # Create A2A client for the agent
                    a2a_client = await self._create_a2a_client(agent_url, client)

                    if not a2a_client:
                        return {
                            "success": False,
                            "error": f"Failed to create A2A client for {agent_url}",
                            "session_id": session_id,
                        }

                    # Check if the A2A client supports cancellation
                    if hasattr(a2a_client, "cancel") and callable(
                        getattr(a2a_client, "cancel")
                    ):
                        # Use the A2A client's cancel method if available
                        cancel_result = await a2a_client.cancel(context_id=session_id)

                        logger.info(
                            f"A2A cancel request completed for session {session_id}"
                        )

                        return {
                            "success": True,
                            "message": "Cancel request sent successfully via A2A protocol",
                            "session_id": session_id,
                            "cancel_result": cancel_result,
                        }
                    else:
                        # Fallback: Send a cancel message as a regular A2A message
                        logger.warning(
                            "A2A client does not support direct cancellation, using message fallback"
                        )

                        cancel_message = create_text_message_object(
                            role=Role.USER,
                            content="CANCEL_TASK",  # Standard cancellation signal
                            context_id=session_id,
                        )

                        response = await a2a_client.send_message(cancel_message)

                        return {
                            "success": True,
                            "message": "Cancel request sent as A2A message",
                            "session_id": session_id,
                            "response": response,
                        }

                except Exception as a2a_error:
                    logger.error(f"A2A cancel request failed: {a2a_error}")
                    return {
                        "success": False,
                        "error": f"A2A cancel failed: {str(a2a_error)}",
                        "session_id": session_id,
                    }

        except Exception as e:
            logger.error(f"Failed to send cancel request to {agent_url}: {e}")
            return {
                "success": False,
                "error": f"Cancel request failed: {str(e)}",
                "session_id": session_id,
            }

    def cleanup_session(self, session_id: str, agent_url: str) -> None:
        """Clean up session-specific resources and connections.

        Args:
            session_id: Session identifier to clean up
            agent_url: Agent URL that was connected to

        Note:
            This is a best-effort cleanup method. If the underlying A2A client
            doesn't support session cleanup, this will log a warning but not fail.
        """
        try:
            logger.info(f"Cleaning up A2A session {session_id} for agent {agent_url}")

            # Currently, a2a-sdk doesn't have explicit session cleanup methods
            # This is a placeholder for future enhancements or framework-specific cleanup

            # For now, we just log the cleanup attempt
            logger.debug(f"A2A session cleanup completed for {session_id}")

        except Exception as e:
            logger.warning(f"A2A session cleanup warning for {session_id}: {e}")

    @staticmethod
    def is_available() -> bool:
        """Check if unified A2A client is available.

        Returns:
            True if a2a-sdk is available
        """
        return A2A_SDK_AVAILABLE
