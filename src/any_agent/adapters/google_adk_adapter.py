"""Google ADK framework adapter for Any Agent - Configurable approach."""

import logging
from pathlib import Path
from typing import Optional

from .base import (
    AgentMetadata,
    ConfigurableFrameworkAdapter,
    FrameworkConfig,
    ValidationResult,
)

logger = logging.getLogger(__name__)


class GoogleADKAdapter(ConfigurableFrameworkAdapter):
    """
    Adapter for Google Agent Development Kit (ADK) agents.

    Uses configurable approach to eliminate code duplication.
    This implementation is ~95% less code than the original pattern-based approach.
    """

    framework_config = FrameworkConfig(
        name="google_adk",
        import_patterns=[
            r"from\s+google\.adk",
            r"import\s+google\.adk",
        ],
        required_files=["__init__.py"],
        special_validations=["has_root_agent_import"],
        entry_point="root_agent",
    )

    def _validate_has_root_agent_import(self, agent_path: Path) -> bool:
        """Special validation: Check if __init__.py exposes root_agent."""
        import re

        try:
            init_file = agent_path / "__init__.py"
            init_content = init_file.read_text(encoding="utf-8")

            # Check for various root_agent import patterns
            import_patterns = [
                r"from\s+\.agent\s+import\s+root_agent",  # Relative import
                r"from\s+\.agent\s+import\s+.*root_agent",
                r"from\s+[\w\.]+agent\s+import\s+root_agent",  # Absolute import ending with 'agent'
                r"from\s+[\w\.]+\s+import\s+root_agent",  # Any module importing root_agent
            ]

            for pattern in import_patterns:
                if re.search(pattern, init_content):
                    return True
            return False

        except Exception as e:
            logger.error(f"Error checking root_agent import: {e}")
            return False

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from ADK agent."""
        all_content = self._read_all_python_files(agent_path)

        metadata = AgentMetadata(
            name=self._extract_agent_name_from_directory(agent_path),
            framework=self.framework_name,
            entry_point=self.framework_config.entry_point,
        )

        # Extract metadata from combined content
        metadata.model = self._extract_model_best_source(all_content)
        metadata.description = self._extract_description(all_content)
        metadata.instruction = self._extract_instruction(all_content)
        metadata.tools = self._extract_tools_from_content(all_content)
        metadata.local_dependencies = self._extract_local_dependencies(agent_path)

        return metadata

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate ADK agent."""
        errors: list[str] = []
        warnings: list[str] = []

        # Check if we can detect the agent
        if not self.detect(agent_path):
            errors.append("Agent detection failed")

        # Check for __init__.py with root_agent
        init_file = agent_path / "__init__.py"
        if not init_file.exists():
            errors.append("Missing required __init__.py file")
        elif not self._validate_has_root_agent_import(agent_path):
            errors.append("__init__.py does not expose root_agent")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )

    # Helper methods for metadata extraction
    def _extract_agent_name_from_directory(self, agent_path: Path) -> str:
        """Extract agent name from directory and Python files."""
        # Try to extract from Agent() calls in any Python file
        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                name = self._extract_agent_name_from_content(content)
                if name:
                    return name
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue

        # Fallback to directory name
        return agent_path.name

    def _extract_agent_name_from_content(self, content: str) -> Optional[str]:
        """Extract agent name from Agent() constructor."""
        import re

        # Look for Agent(name="...") patterns
        patterns = [
            r'Agent\(\s*name\s*=\s*["\']([^"\']+)["\']',
            r'name\s*=\s*["\']([^"\']+)["\'].*Agent\(',
        ]
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None

    def _extract_model_best_source(self, content: str) -> Optional[str]:
        """Extract model from content."""
        import re

        # Look for model parameter in Agent() constructor
        # This handles: Agent(model="gemini-1.5-flash", ...)
        agent_model_pattern = r'Agent\([^)]*model\s*=\s*["\']([^"\']+)["\']'
        match = re.search(agent_model_pattern, content, re.DOTALL)
        if match:
            return match.group(1)

        # Look for model parameter with variable reference: Agent(model=SOME_VAR, ...)
        # Then find that variable's value
        agent_var_pattern = r"Agent\([^)]*model\s*=\s*([A-Z_][A-Z0-9_]*)"
        match = re.search(agent_var_pattern, content, re.DOTALL)
        if match:
            var_name = match.group(1)
            # Look for the variable definition with getenv default
            var_patterns = [
                rf'{var_name}\s*=\s*os\.getenv\([^,]+,\s*["\']([^"\']+)["\']',
                rf'{var_name}\s*=\s*["\']([^"\']+)["\']',
            ]
            for pattern in var_patterns:
                var_match = re.search(pattern, content)
                if var_match:
                    return var_match.group(1)

        # Fallback: direct model assignment anywhere
        direct_pattern = r'model\s*=\s*["\']([^"\']+)["\']'
        match = re.search(direct_pattern, content)
        if match:
            return match.group(1)

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from content."""
        import re

        desc_patterns = [
            r"description\s*=\s*['\"]([^'\"]+)['\"]",
            r"DESCRIPTION\s*=\s*['\"]([^'\"]+)['\"]",
        ]
        for pattern in desc_patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)
        return None

    def _extract_instruction(self, content: str) -> Optional[str]:
        """Extract agent instructions/system prompt from content."""
        import re

        # Common variable names for system prompts/instructions
        instruction_var_names = [
            "agent_instruction",
            "agent_instructions",
            "SYSTEM_PROMPT",
            "system_prompt",
            "PROMPT",
            "prompt",
            "INSTRUCTION",
            "instruction",
            "AGENT_PROMPT",
            "agent_prompt",
        ]

        # First, check if Agent() uses any of these variables: instruction=VARIABLE_NAME
        agent_var_pattern = r"Agent\([^)]*instruction\s*=\s*([A-Za-z_][A-Za-z0-9_]*)"
        match = re.search(agent_var_pattern, content, re.DOTALL)
        if match:
            var_name = match.group(1)
            # Look for that variable's definition
            for quote_style in ['"""', '"', "'"]:
                var_pattern = rf"{re.escape(var_name)}\s*=\s*{re.escape(quote_style)}(.*?){re.escape(quote_style)}"
                var_match = re.search(var_pattern, content, re.DOTALL)
                if var_match:
                    return var_match.group(1).strip()

        # Look for any common instruction variable definitions
        for var_name in instruction_var_names:
            for quote_style in ['"""', '"', "'"]:
                pattern = rf"{re.escape(var_name)}\s*=\s*{re.escape(quote_style)}(.*?){re.escape(quote_style)}"
                match = re.search(pattern, content, re.DOTALL)
                if match:
                    return match.group(1).strip()

        # Look for direct instruction assignment in Agent() constructor
        agent_direct_patterns = [
            r'Agent\([^)]*instruction\s*=\s*"""([^"]*?)"""',
            r'Agent\([^)]*instruction\s*=\s*"([^"]*?)"',
            r"Agent\([^)]*instruction\s*=\s*\'([^\']*?)\'",
        ]

        for pattern in agent_direct_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()

        # Fallback: any instruction assignment
        fallback_patterns = [
            r'instruction\s*=\s*"""([^"]*?)"""',
            r'instruction\s*=\s*"([^"]*?)"',
            r"instruction\s*=\s*\'([^\']*?)\'",
        ]

        for pattern in fallback_patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                return match.group(1).strip()

        return None

    def _extract_tools_from_content(self, content: str) -> list:
        """Extract tools from content."""
        # Basic implementation for now
        return []

    def _extract_local_dependencies(self, agent_path: Path) -> list:
        """Extract local dependencies from Python files."""
        module_names = []
        file_paths = []

        # Look for local imports in all Python files
        for py_file in agent_path.rglob("*.py"):
            if ".any_agent" in str(py_file):  # Skip generated files
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                # Look for relative imports: from .module_name import ...
                import re

                local_imports = re.findall(r"from\s+\.(\w+)", content)
                module_names.extend(local_imports)

                # Also look for relative imports with multiple levels: from ..parent.module import ...
                multi_level_imports = re.findall(r"from\s+\.+(\w+(?:\.\w+)*)", content)
                module_names.extend(multi_level_imports)

            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")

        # Convert module names to file paths
        unique_modules = list(set(module_names))  # Remove duplicates
        for module_name in unique_modules:
            # Look for corresponding .py files
            module_file = agent_path / f"{module_name}.py"
            if module_file.exists():
                file_paths.append(str(module_file))
            else:
                # Try as directory with __init__.py
                module_dir = agent_path / module_name
                if module_dir.exists() and module_dir.is_dir():
                    file_paths.append(str(module_dir))

        return file_paths
