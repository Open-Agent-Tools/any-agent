"""Google ADK framework adapter for Any Agent."""

import ast
import logging
import os
import re
from pathlib import Path
from typing import Optional

from .base import AgentMetadata, BaseFrameworkAdapter, ValidationResult

logger = logging.getLogger(__name__)


class GoogleADKAdapter(BaseFrameworkAdapter):
    """Adapter for Google Agent Development Kit (ADK) agents."""

    @property
    def framework_name(self) -> str:
        return "google_adk"

    def detect(self, agent_path: Path) -> bool:
        """
        Detect Google ADK agent by checking:
        1. Has __init__.py that exposes root_agent
        2. Contains Google ADK imports somewhere in the codebase
        """
        try:
            # Check if directory has __init__.py
            init_file = agent_path / "__init__.py"
            if not init_file.exists():
                logger.debug(f"No __init__.py found in {agent_path}")
                return False

            # Check if __init__.py exposes root_agent
            init_content = init_file.read_text(encoding="utf-8")
            if not self._has_root_agent_import(init_content):
                logger.debug(f"__init__.py does not expose root_agent in {agent_path}")
                return False

            # Check for ADK imports anywhere in the directory
            if not self._has_framework_imports_in_directory(agent_path, self._has_adk_imports):
                logger.debug(f"No Google ADK imports found in {agent_path}")
                return False

            logger.info(f"Google ADK agent detected at {agent_path}")
            return True

        except Exception as e:
            logger.error(f"Error detecting ADK agent at {agent_path}: {e}")
            return False




    def _has_adk_imports(self, content: str) -> bool:
        """Check if content contains Google ADK imports."""
        adk_import_patterns = [
            r"from\s+google\.adk",
            r"import\s+google\.adk",
        ]

        for pattern in adk_import_patterns:
            if re.search(pattern, content):
                return True
        return False


    def _has_root_agent_import(self, content: str) -> bool:
        """Check if content imports root_agent from agent module."""
        try:
            # Check for various root_agent import patterns - be specific to avoid false positives
            import_patterns = [
                r"from\s+\.agent\s+import\s+root_agent",  # Relative import
                r"from\s+\.agent\s+import\s+.*root_agent",
                r"from\s+[\w\.]+agent\s+import\s+root_agent",  # Absolute import ending with 'agent'
                r"from\s+[\w\.]+\s+import\s+root_agent",  # Any module importing root_agent
            ]

            for pattern in import_patterns:
                if re.search(pattern, content):
                    return True

            return False
        except Exception as e:
            logger.error(f"Error checking root_agent import: {e}")
            return False

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from ADK agent."""
        # Extract from all Python files in the directory
        all_content = self._aggregate_file_contents(agent_path)

        metadata = AgentMetadata(
            name=self._extract_agent_name_from_directory(agent_path),
            framework=self.framework_name,
            entry_point="root_agent",
        )

        # Extract metadata from combined content
        metadata.model = self._extract_model_best_source(all_content)
        metadata.description = self._extract_description(all_content)
        metadata.tools = self._extract_tools(all_content)
        metadata.local_dependencies = self._detect_local_dependencies(
            agent_path, all_content
        )

        return metadata

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

        # Fall back to directory name
        return agent_path.name.replace("_", " ").title()

    def _extract_agent_name_from_content(self, content: str) -> Optional[str]:
        """Extract agent name from Agent() constructor in content."""
        return self._extract_agent_name_from_ast(content)



    def _extract_model(self, content: str) -> Optional[str]:
        """Extract model name from agent content."""
        # First look for direct string model= parameter in Agent() calls
        model_pattern = r'model\s*=\s*["\']([^"\']+)["\']'
        match = re.search(model_pattern, content)
        if match:
            return match.group(1)

        # Look for model= with variable reference
        var_pattern = r"model\s*=\s*([A-Z_][A-Z0-9_]*)"
        var_match = re.search(var_pattern, content)
        if var_match:
            var_name = var_match.group(1)
            # Look for the variable definition
            var_def_pattern = rf'{var_name}\s*=\s*["\']([^"\']+)["\']'
            var_def_match = re.search(var_def_pattern, content)
            if var_def_match:
                return var_def_match.group(1)

            # Look for environment variable default
            env_pattern = rf'{var_name}\s*=\s*os\.getenv\(["\'][^"\']*["\'],\s*["\']([^"\']+)["\']'
            env_match = re.search(env_pattern, content)
            if env_match:
                return env_match.group(1)

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from agent content."""
        # Look for description= parameter in Agent() calls
        desc_pattern = r'description\s*=\s*["\']([^"\']+)["\']'
        match = re.search(desc_pattern, content)
        if match:
            return match.group(1)
        return None

    def _extract_tools(self, content: str) -> list[str]:
        """Extract tool information from agent content."""
        tools = []

        # Look for import statements to identify tools
        if "MCPToolset" in content:
            tools.append("MCP Server Tools")

        if "load_all_datetime_tools" in content:
            tools.append("Date/Time Tools")

        # Look for other common ADK tools
        tool_patterns = [
            (r"from google\.adk\.tools\..*search", "Search Tools"),
            (r"from google\.adk\.tools\..*code", "Code Tools"),
            (r"from google\.adk\.tools\..*web", "Web Tools"),
        ]

        for pattern, tool_name in tool_patterns:
            if re.search(pattern, content):
                tools.append(tool_name)

        return tools



    def _extract_model_best_source(self, content: str) -> Optional[str]:
        """Extract model using best available source."""
        # 1. Try environment variable (most dynamic)
        env_model = os.getenv("GOOGLE_MODEL")
        if env_model:
            logger.debug(f"Using model from environment: {env_model}")
            return env_model.strip("\"'")

        # 2. Try runtime agent inspection
        try:
            runtime_model = self._get_runtime_model()
            if runtime_model:
                logger.debug(f"Using model from runtime: {runtime_model}")
                return runtime_model
        except Exception as e:
            logger.debug(f"Runtime model extraction failed: {e}")

        # 3. Fallback to static analysis
        static_model = self._extract_model(content)
        if static_model:
            logger.debug(f"Using model from static analysis: {static_model}")
            return static_model

        # 4. Skip if unknown
        logger.debug("Model could not be determined from any source")
        return None

    def _get_runtime_model(self) -> Optional[str]:
        """Get model from environment at runtime."""
        return os.getenv("GOOGLE_MODEL", "").strip("\"'") or None





    def _detect_local_dependencies(self, agent_path: Path, content: str) -> list[str]:
        """Detect local agent dependencies by analyzing import statements."""
        dependencies = []

        try:
            # Parse the content to find import statements
            tree = ast.parse(content)

            # Get the parent directory (where sibling agents would be)
            parent_dir = agent_path.parent

            for node in ast.walk(tree):
                # Look for import statements
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module_name = alias.name
                        # Check if this matches a sibling directory
                        potential_dep = parent_dir / module_name
                        if potential_dep.is_dir() and potential_dep != agent_path:
                            # Check if it has __init__.py (is a Python package)
                            if (potential_dep / "__init__.py").exists():
                                dep_path = str(potential_dep)
                                if dep_path not in dependencies:
                                    dependencies.append(dep_path)
                                    logger.info(
                                        f"Detected local dependency: {module_name}"
                                    )

                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module_name = node.module
                        # Handle relative imports
                        if module_name.startswith(".."):
                            # Go up two levels for .. imports
                            base_module = module_name[2:]  # Remove '..'
                            if base_module:
                                potential_dep = parent_dir / base_module
                                if (
                                    potential_dep.is_dir()
                                    and potential_dep != agent_path
                                ):
                                    if (potential_dep / "__init__.py").exists():
                                        dep_path = str(potential_dep)
                                        if dep_path not in dependencies:
                                            dependencies.append(dep_path)
                                            logger.info(
                                                f"Detected local dependency (relative): {base_module}"
                                            )
                        elif not module_name.startswith("."):
                            # Direct module name (like 'Theta_Gang_Wheel_Agent')
                            potential_dep = parent_dir / module_name
                            if potential_dep.is_dir() and potential_dep != agent_path:
                                if (potential_dep / "__init__.py").exists():
                                    dep_path = str(potential_dep)
                                    if dep_path not in dependencies:
                                        dependencies.append(dep_path)
                                        logger.info(
                                            f"Detected local dependency: {module_name}"
                                        )

        except Exception as e:
            logger.warning(f"Error detecting local dependencies: {e}")

        return dependencies

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate Google ADK agent structure and dependencies."""
        result = ValidationResult(is_valid=True)

        # Check that __init__.py exists and exposes root_agent
        init_file = agent_path / "__init__.py"
        if not init_file.exists():
            result.errors.append("Missing required __init__.py file")
            result.is_valid = False
        else:
            init_content = init_file.read_text(encoding="utf-8")
            if not self._has_root_agent_import(init_content):
                result.errors.append("__init__.py must expose root_agent")
                result.is_valid = False

        # Check for ADK imports anywhere in the directory
        if not self._has_framework_imports_in_directory(agent_path, self._has_adk_imports):
            result.errors.append("No Google ADK imports found in directory")
            result.is_valid = False

        return result


