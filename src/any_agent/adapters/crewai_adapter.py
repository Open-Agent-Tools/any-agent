"""CrewAI framework adapter for Any Agent - Configurable approach."""

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


class CrewAIAdapter(ConfigurableFrameworkAdapter):
    """
    Adapter for CrewAI agents.

    Uses configurable approach to eliminate code duplication.
    This implementation is ~95% less code than the original pattern-based approach.
    """

    framework_config = FrameworkConfig(
        name="crewai",
        import_patterns=[
            r"from\s+crewai",
            r"import\s+crewai",
            r"from\s+crewai_tools",
            r"import\s+crewai_tools",
        ],
        required_files=[],  # No required files for CrewAI
        special_validations=[],  # No special validations needed
        entry_point="crew"
    )

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from CrewAI agent."""
        all_content = self._read_all_python_files(agent_path)

        metadata = AgentMetadata(
            name=agent_path.name.replace("_", " ").title(),
            framework=self.framework_name,
            entry_point=self.framework_config.entry_point,
        )

        metadata.model = self._extract_model(all_content)
        metadata.description = self._extract_description(all_content)
        metadata.instruction = None  # TODO: Extract CrewAI agent instructions
        metadata.tools = self._extract_tools(all_content)

        return metadata

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate CrewAI agent."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check if we can detect the agent
        if not self.detect(agent_path):
            errors.append("CrewAI agent detection failed")

        # Check for at least one Python file with CrewAI imports
        if not self._has_framework_imports_in_directory(agent_path, self._has_configured_imports):
            errors.append("No CrewAI imports found in agent directory")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    # Helper methods for metadata extraction
    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from CrewAI content."""
        import re
        model_patterns = [
            r'llm\s*=\s*[^(]*\([^)]*model\s*=\s*["\']([^"\']+)["\']',
            r'model\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in model_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from CrewAI agent content."""
        if "Crew" in content and "agents" in content:
            return "CrewAI multi-agent system"
        return None

    def _extract_tools(self, content: str) -> list:
        """Extract tool information from CrewAI content."""
        tools = []

        # Common CrewAI tools
        tool_patterns = [
            ("SerperDevTool", "Web Search"),
            ("FileReadTool", "File Reading"),
            ("DirectoryReadTool", "Directory Reading"),
            ("WebsiteSearchTool", "Website Search"),
            ("DallETool", "Image Generation"),
            ("CrewaiEnterpriseTools", "Enterprise Tools"),
        ]

        for tool_class, tool_name in tool_patterns:
            if tool_class in content:
                tools.append(tool_name)

        return tools
