"""AWS Strands framework adapter for Any Agent - Configurable approach."""

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


class AWSStrandsAdapter(ConfigurableFrameworkAdapter):
    """
    Adapter for AWS Strands agents.

    Uses configurable approach to eliminate code duplication.
    This implementation is ~95% less code than the original pattern-based approach.
    """

    framework_config = FrameworkConfig(
        name="aws_strands",
        import_patterns=[
            r"from\s+strands",
            r"import\s+strands",
            r"strands-agents",
            r"strands_tools",
            r"@tool",  # Common Strands decorator
        ],
        required_files=[],  # No required files for Strands
        special_validations=[],  # No special validations needed
        entry_point="root_agent"
    )

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from AWS Strands agent."""
        # Try to extract agent name from the agent definition first
        agent_name = self._extract_agent_name_from_files(agent_path)
        if not agent_name:
            agent_name = agent_path.name.replace("_", " ").title()

        metadata = AgentMetadata(
            name=agent_name,
            framework=self.framework_name,
            entry_point=self.framework_config.entry_point,
        )

        # Extract from agent.py specifically for better accuracy
        agent_file = agent_path / "agent.py"
        agent_content = ""
        if agent_file.exists():
            try:
                agent_content = agent_file.read_text(encoding="utf-8")
            except Exception as e:
                logger.debug(f"Error reading agent.py: {e}")

        # Extract from all Python files as fallback
        all_content = self._read_all_python_files(agent_path)

        # Use agent.py content primarily, fall back to all content
        primary_content = agent_content if agent_content else all_content

        metadata.model = self._extract_model(primary_content)
        metadata.description = self._extract_description(primary_content, agent_name)
        metadata.instruction = None  # TODO: Extract Strands agent instructions
        metadata.tools = self._extract_tools(primary_content)
        metadata.environment_vars = self._extract_environment_vars(primary_content)
        metadata.local_dependencies = self._extract_local_dependencies(agent_path)

        return metadata

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate AWS Strands agent."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check if we can detect the agent
        if not self.detect(agent_path):
            errors.append("AWS Strands agent detection failed")

        # Check for at least one Python file with Strands imports
        if not self._has_framework_imports_in_directory(agent_path, self._has_configured_imports):
            errors.append("No Strands imports found in agent directory")

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    # Helper methods for metadata extraction
    def _extract_agent_name_from_files(self, agent_path: Path) -> Optional[str]:
        """Extract agent name from Agent() constructor in agent.py."""
        agent_file = agent_path / "agent.py"
        if not agent_file.exists():
            return None

        try:
            content = agent_file.read_text(encoding="utf-8")
            return self._extract_agent_name_from_ast(content)
        except Exception as e:
            logger.debug(f"Error extracting agent name: {e}")

        return None

    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from Strands content."""
        import re
        model_patterns = [
            # Specific model constructors with model_id parameter
            r'BedrockModel\([^)]*model_id\s*=\s*["\']([^"\']+)["\']',
            r'OllamaModel\([^)]*model_id\s*=\s*["\']([^"\']+)["\']',
            r'LlamaAPIModel\([^)]*model_id\s*=\s*["\']([^"\']+)["\']',
            r'AnthropicModel\([^)]*model_id\s*=\s*["\']([^"\']+)["\']',
            # Generic model parameter
            r'model_id\s*=\s*["\']([^"\']+)["\']',
            r'model\s*=\s*["\']([^"\']+)["\']',
        ]

        for pattern in model_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1)

        return None

    def _extract_description(self, content: str, agent_name: str) -> Optional[str]:
        """Extract description from Strands content."""
        import re
        # Look for description patterns
        desc_patterns = [
            r'description\s*=\s*["\']([^"\']+)["\']',
            r'DESCRIPTION\s*=\s*["\']([^"\']+)["\']',
            r'"""([^"]{10,100})"""',  # Simple docstring extraction
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1).strip()

        return None

    def _extract_tools(self, content: str) -> list:
        """Extract tools from Strands content."""
        import re
        tools = []

        # Look for @tool decorated functions
        tool_pattern = r'@tool[^\n]*\ndef\s+(\w+)\s*\('
        matches = re.finditer(tool_pattern, content, re.MULTILINE)

        for match in matches:
            tools.append(match.group(1))

        return tools

    def _extract_environment_vars(self, content: str) -> dict:
        """Extract environment variables from content."""
        import re
        env_vars = {}

        # Look for os.getenv() calls
        env_pattern = r'os\.getenv\(\s*["\']([^"\']+)["\']'
        matches = re.finditer(env_pattern, content)

        for match in matches:
            env_var = match.group(1)
            env_vars[env_var] = ""  # Value will be set at runtime

        return env_vars

    def _extract_local_dependencies(self, agent_path: Path) -> list:
        """Extract local dependencies."""
        dependencies = []

        # Look for local imports
        for py_file in agent_path.rglob("*.py"):
            if ".any_agent" in str(py_file):  # Skip generated files
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                # Look for relative imports
                import re
                local_imports = re.findall(r'from\s+\.(\w+)', content)
                dependencies.extend(local_imports)
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")

        return list(set(dependencies))  # Remove duplicates