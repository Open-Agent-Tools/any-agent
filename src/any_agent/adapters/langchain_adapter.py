"""LangChain framework adapter for Any Agent."""

import ast
import logging
import re
from pathlib import Path
from typing import Optional

from .base import AgentMetadata, BaseFrameworkAdapter, ValidationResult

logger = logging.getLogger(__name__)


class LangChainAdapter(BaseFrameworkAdapter):
    """Adapter for LangChain agents."""

    @property
    def framework_name(self) -> str:
        return "langchain"

    def detect(self, agent_path: Path) -> bool:
        """
        Detect LangChain agent by checking:
        1. Contains LangChain imports (langchain, langchain_core, etc.)
        2. Has typical agent patterns (Agent, LangChainAgent, etc.)
        """
        try:
            if not agent_path.exists() or not agent_path.is_dir():
                logger.debug(f"Path does not exist or is not a directory: {agent_path}")
                return False

            # Check for LangChain imports anywhere in the directory
            if not self._has_langchain_imports_in_directory(agent_path):
                logger.debug(f"No LangChain imports found in {agent_path}")
                return False

            logger.info(f"LangChain agent detected at {agent_path}")
            return True

        except Exception as e:
            logger.error(f"Error detecting LangChain agent at {agent_path}: {e}")
            return False

    def _has_langchain_imports_in_directory(self, agent_path: Path) -> bool:
        """Check if any Python file in the directory contains LangChain imports."""
        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                if self._has_langchain_imports(content):
                    return True
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue
        return False

    def _has_langchain_imports(self, content: str) -> bool:
        """Check if content contains LangChain imports."""
        langchain_import_patterns = [
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
        ]

        for pattern in langchain_import_patterns:
            if re.search(pattern, content):
                return True
        return False

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from LangChain agent."""
        # Extract from all Python files in the directory
        all_content = ""
        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                all_content += content + "\n"
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue

        metadata = AgentMetadata(
            name=agent_path.name.replace("_", " ").title(),
            framework=self.framework_name,
            entry_point="main",
        )

        # Extract metadata from combined content
        metadata.model = self._extract_model(all_content)
        metadata.description = self._extract_description(all_content)
        metadata.tools = self._extract_tools(all_content)

        return metadata

    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from LangChain content."""
        # Look for common model patterns in LangChain
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
        # Look for description patterns
        desc_patterns = [
            r'description\s*=\s*["\']([^"\']+)["\']',
            r'"""([^"]+)"""',  # Docstrings
            r"'''([^']+)'''",
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, content)
            if match:
                desc = match.group(1).strip()
                if desc and len(desc) > 10:  # Filter out short descriptions
                    return desc

        return None

    def _extract_tools(self, content: str) -> list[str]:
        """Extract tool information from LangChain content."""
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

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate LangChain agent structure and dependencies."""
        result = ValidationResult(is_valid=True)

        # Check for LangChain imports anywhere in the directory
        if not self._has_langchain_imports_in_directory(agent_path):
            result.errors.append("No LangChain imports found in directory")
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
