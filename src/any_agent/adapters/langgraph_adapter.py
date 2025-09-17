"""LangGraph framework adapter for Any Agent - Configurable approach."""

import logging
from pathlib import Path
from typing import Optional

from .base import (
    AgentMetadata,
    ConfigurableFrameworkAdapter,
    FrameworkConfig,
    ValidationResult
)

logger = logging.getLogger(__name__)


class LangGraphAdapter(ConfigurableFrameworkAdapter):
    """
    Adapter for LangGraph agents.

    Uses configurable approach to eliminate code duplication.
    This implementation is ~95% less code than the original pattern-based approach.
    """

    framework_config = FrameworkConfig(
        name="langgraph",
        import_patterns=[
            r"from\s+langgraph",
            r"import\s+langgraph",
            r"StateGraph",
            r"MessagesState",
            r"from\s+@langchain/langgraph",  # TypeScript/JavaScript pattern
        ],
        required_files=[],  # No required files for LangGraph
        special_validations=[],  # No special validations needed
        entry_point="graph"
    )

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from LangGraph agent."""
        all_content = self._read_all_python_files(agent_path)

        metadata = AgentMetadata(
            name=agent_path.name.replace("_", " ").title(),
            framework=self.framework_name,
            entry_point=self.framework_config.entry_point,
        )

        metadata.model = self._extract_model(all_content)
        metadata.description = self._extract_description(all_content)
        metadata.tools = self._extract_tools(all_content)

        return metadata

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate LangGraph agent."""
        errors = []
        warnings = []

        # Check if we can detect the agent
        if not self.detect(agent_path):
            errors.append("LangGraph agent detection failed")

        # Check for at least one Python file with LangGraph imports
        if not self._has_framework_imports_in_directory(agent_path, self._has_configured_imports):
            errors.append("No LangGraph imports found in agent directory")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    # Helper methods for metadata extraction
    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from LangGraph content."""
        import re
        model_patterns = [
            r'ChatOpenAI\([^)]*model\s*=\s*["\']([^"\']+)["\']',
            r'ChatAnthropic\([^)]*model\s*=\s*["\']([^"\']+)["\']',
            r'model\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in model_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from LangGraph agent content."""
        if "StateGraph" in content and "workflow" in content.lower():
            return "LangGraph workflow agent"
        return None

    def _extract_tools(self, content: str) -> list:
        """Extract tool information from LangGraph content."""
        tools = []

        if "ToolNode" in content:
            tools.append("Tool Nodes")

        if "tools_condition" in content:
            tools.append("Conditional Tools")

        if "create_react_agent" in content:
            tools.append("ReAct Agent Tools")

        return tools
