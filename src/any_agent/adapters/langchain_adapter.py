"""LangChain framework adapter for Any Agent - Configurable approach."""

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


class LangChainAdapter(ConfigurableFrameworkAdapter):
    """
    Adapter for LangChain agents.

    Uses configurable approach to eliminate code duplication.
    This implementation is ~95% less code than the original pattern-based approach.
    """

    framework_config = FrameworkConfig(
        name="langchain",
        import_patterns=[
            r"from\s+langchain",
            r"import\s+langchain",
            r"from\s+langchain_core",
            r"import\s+langchain_core",
            r"from\s+langchain_community",
            r"import\s+langchain_community",
            r"from\s+langchain_openai",
            r"import\s+langchain_openai",
            r"from\s+langchain_anthropic",
            r"import\s+langchain_anthropic",
        ],
        required_files=[],  # No required files for LangChain
        special_validations=[],  # No special validations needed
        entry_point="main"
    )

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from LangChain agent."""
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
        """Validate LangChain agent."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check if we can detect the agent
        if not self.detect(agent_path):
            errors.append("LangChain agent detection failed")

        # Check for at least one Python file with LangChain imports
        if not self._has_framework_imports_in_directory(agent_path, self._has_configured_imports):
            errors.append("No LangChain imports found in agent directory")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    # Helper methods for metadata extraction
    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from LangChain content."""
        import re
        model_patterns = [
            r'model\s*=\s*["\']([^"\']+)["\']',
            r'model_name\s*=\s*["\']([^"\']+)["\']',
            r'ChatOpenAI\([^)]*model\s*=\s*["\']([^"\']+)["\']',
            r'OpenAI\([^)]*model\s*=\s*["\']([^"\']+)["\']',
            r'ChatAnthropic\([^)]*model\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in model_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from LangChain agent content."""
        import re
        description_patterns = [
            r'description\s*=\s*["\']([^"\']+)["\']',
            r'"""([^"]+)"""',  # Docstrings
            r"'''([^']+)'''",
        ]

        for pattern in description_patterns:
            match = re.search(pattern, content)
            if match:
                desc = match.group(1).strip()
                if desc and len(desc) > 10:  # Filter out short descriptions
                    return desc

        return None

    def _extract_tools(self, content: str) -> list:
        """Extract tool information from LangChain content."""
        import re
        tools = []

        # Look for common LangChain tools
        if "DuckDuckGoSearchRun" in content:
            tools.append("DuckDuckGo Search")

        if "WikipediaQueryRun" in content:
            tools.append("Wikipedia")

        if "PythonREPLTool" in content:
            tools.append("Python REPL")

        if "ShellTool" in content:
            tools.append("Shell Tool")

        # Look for custom tools
        if re.search(r"@tool", content):
            tools.append("Custom Tools")

        if re.search(r"class.*Tool", content):
            tools.append("Custom Tool Classes")

        return tools
