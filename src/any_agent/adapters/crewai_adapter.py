"""CrewAI framework adapter for Any Agent."""

import ast
import logging
import re
from pathlib import Path
from typing import Optional

from .base import AgentMetadata, BaseFrameworkAdapter, ValidationResult

logger = logging.getLogger(__name__)


class CrewAIAdapter(BaseFrameworkAdapter):
    """Adapter for CrewAI agents."""

    @property
    def framework_name(self) -> str:
        return "crewai"

    def detect(self, agent_path: Path) -> bool:
        """
        Detect CrewAI agent by checking:
        1. Contains CrewAI imports (crewai, crewai_tools)
        2. Has typical patterns (Agent, Task, Crew, etc.)
        """
        try:
            if not agent_path.exists() or not agent_path.is_dir():
                logger.debug(f"Path does not exist or is not directory: {agent_path}")
                return False

            # Check for CrewAI imports anywhere in the directory
            if not self._has_crewai_imports_in_directory(agent_path):
                logger.debug(f"No CrewAI imports found in {agent_path}")
                return False

            logger.info(f"CrewAI agent detected at {agent_path}")
            return True

        except Exception as e:
            logger.error(f"Error detecting CrewAI agent at {agent_path}: {e}")
            return False

    def _has_crewai_imports_in_directory(self, agent_path: Path) -> bool:
        """Check if any Python file in the directory contains CrewAI imports."""
        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if self._has_crewai_imports(content):
                    return True
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue
        return False

    def _has_crewai_imports(self, content: str) -> bool:
        """Check if content contains CrewAI imports."""
        crewai_import_patterns = [
            r"from\s+crewai",
            r"import\s+crewai",
            r"from\s+crewai_tools",
            r"import\s+crewai_tools",
        ]

        for pattern in crewai_import_patterns:
            if re.search(pattern, content):
                return True
        return False

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from CrewAI agent."""
        metadata = AgentMetadata(
            name=agent_path.name.replace("_", " ").title(),
            framework=self.framework_name,
            entry_point="crew",
        )

        # Extract from all Python files in the directory
        all_content = ""
        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                all_content += content + "\n"
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue

        metadata.model = self._extract_model(all_content)
        metadata.description = self._extract_description(all_content)
        metadata.tools = self._extract_tools(all_content)

        return metadata

    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from CrewAI content."""
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

    def _extract_tools(self, content: str) -> list[str]:
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

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate CrewAI agent structure and dependencies."""
        result = ValidationResult(is_valid=True)

        # Check for CrewAI imports anywhere in the directory
        if not self._has_crewai_imports_in_directory(agent_path):
            result.errors.append("No CrewAI imports found in directory")
            result.is_valid = False

        # Check if any Python files exist
        py_files = list(agent_path.rglob("*.py"))
        if not py_files:
            result.errors.append("No Python files found in agent directory")
            result.is_valid = False

        # Check for basic syntax in Python files
        for py_file in py_files:
            try:
                content = py_file.read_text(encoding="utf-8")
                ast.parse(content)
            except SyntaxError as e:
                result.errors.append(f"Syntax error in {py_file.name}: {e}")
                result.is_valid = False

        return result
