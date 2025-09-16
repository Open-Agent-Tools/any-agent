"""LangGraph framework adapter for Any Agent."""

import logging
import re
from pathlib import Path
from typing import Optional

from .base import AgentMetadata, BaseFrameworkAdapter, ValidationResult

logger = logging.getLogger(__name__)


class LangGraphAdapter(BaseFrameworkAdapter):
    """Adapter for LangGraph agents."""

    @property
    def framework_name(self) -> str:
        return "langgraph"

    def detect(self, agent_path: Path) -> bool:
        """
        Detect LangGraph agent by checking:
        1. Contains LangGraph imports (langgraph, @langchain/langgraph)
        2. Has typical patterns (StateGraph, MessagesState, etc.)
        """
        try:
            if not agent_path.exists() or not agent_path.is_dir():
                logger.debug(f"Path does not exist or is not directory: {agent_path}")
                return False

            # Check for LangGraph imports anywhere in the directory
            if not self._has_framework_imports_in_directory(
                agent_path, self._has_langgraph_imports
            ):
                logger.debug(f"No LangGraph imports found in {agent_path}")
                return False

            logger.info(f"LangGraph agent detected at {agent_path}")
            return True

        except Exception as e:
            logger.error(f"Error detecting LangGraph agent at {agent_path}: {e}")
            return False

    def _has_langgraph_imports(self, content: str) -> bool:
        """Check if content contains LangGraph imports."""
        langgraph_import_patterns = [
            r"from\s+langgraph",
            r"import\s+langgraph",
            r"StateGraph",
            r"MessagesState",
            r"from\s+@langchain/langgraph",  # TypeScript/JavaScript pattern
        ]

        for pattern in langgraph_import_patterns:
            if re.search(pattern, content):
                return True
        return False

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from LangGraph agent."""
        metadata = AgentMetadata(
            name=agent_path.name.replace("_", " ").title(),
            framework=self.framework_name,
            entry_point="graph",
        )

        # Extract from all Python files in the directory
        all_content = self._read_all_python_files(agent_path)

        metadata.model = self._extract_model(all_content)
        metadata.description = self._extract_description(all_content)
        metadata.tools = self._extract_tools(all_content)

        return metadata

    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from LangGraph content."""
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

    def _extract_tools(self, content: str) -> list[str]:
        """Extract tool information from LangGraph content."""
        tools = []

        if "ToolNode" in content:
            tools.append("Tool Nodes")

        if "tools_condition" in content:
            tools.append("Conditional Tools")

        if "create_react_agent" in content:
            tools.append("ReAct Agent Tools")

        return tools

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate LangGraph agent structure and dependencies."""
        result = ValidationResult(is_valid=True)

        # Check for LangGraph imports anywhere in the directory
        if not self._has_framework_imports_in_directory(
            agent_path, self._has_langgraph_imports
        ):
            result.errors.append("No LangGraph imports found in directory")
            result.is_valid = False

        # Check Python syntax
        self._validate_python_syntax(agent_path, result)

        return result
