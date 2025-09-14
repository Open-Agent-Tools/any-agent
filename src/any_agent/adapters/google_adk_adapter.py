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
            if not self._has_adk_imports_in_directory(agent_path):
                logger.debug(f"No Google ADK imports found in {agent_path}")
                return False

            logger.info(f"Google ADK agent detected at {agent_path}")
            return True

        except Exception as e:
            logger.error(f"Error detecting ADK agent at {agent_path}: {e}")
            return False

    def _has_adk_imports_in_directory(self, agent_path: Path) -> bool:
        """Check if any Python file in the directory contains Google ADK imports."""
        for py_file in agent_path.rglob("*.py"):
            # Skip generated build artifacts in .any_agent directory
            if ".any_agent" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                if self._has_adk_imports(content):
                    return True
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue
        return False

    def _detect_complete_a2a_app(self, agent_path: Path) -> bool:
        """Detect complete A2A app with a2a_app.py file."""
        agent_file = agent_path / "a2a_app.py"

        if not agent_file.exists():
            return False

        content = agent_file.read_text(encoding="utf-8")

        # Check for ADK imports and root_agent variable or import
        return self._has_adk_imports(content) and (
            self._has_root_agent(content) or self._has_root_agent_import(content)
        )

    def _detect_minimal_adk_agent(self, agent_path: Path) -> bool:
        """Detect minimal ADK agent with agent.py + __init__.py structure."""
        agent_file = agent_path / "agent.py"
        init_file = agent_path / "__init__.py"

        if not agent_file.exists() or not init_file.exists():
            return False

        # Check agent.py for ADK imports
        agent_content = agent_file.read_text(encoding="utf-8")
        if not self._has_adk_imports(agent_content):
            return False

        # Check __init__.py for root_agent export
        init_content = init_file.read_text(encoding="utf-8")
        if not self._has_root_agent_import(init_content):
            return False

        return True

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

    def _has_root_agent(self, content: str) -> bool:
        """Check if content defines a root_agent variable."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                # Check for variable assignment: root_agent = ...
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "root_agent":
                            return True

            return False
        except SyntaxError as e:
            logger.error(f"Syntax error parsing content: {e}")
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
        all_content = ""
        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                all_content += content + "\n"
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue

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
        try:
            tree = ast.parse(content)

            # Look for Agent() constructor calls with name parameter
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if this is an Agent() call
                    if (
                        isinstance(node.func, ast.Name) and node.func.id == "Agent"
                    ) or (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "Agent"
                    ):
                        # Look for name parameter in keywords
                        for keyword in node.keywords:
                            if keyword.arg == "name" and isinstance(
                                keyword.value, ast.Constant
                            ):
                                value = keyword.value.value
                                return str(value) if value is not None else None
        except Exception as e:
            logger.debug(f"Error parsing content for agent name: {e}")

        return None

    def _is_minimal_agent(self, agent_path: Path) -> bool:
        """Determine if this is a minimal agent structure."""
        return self._detect_minimal_adk_agent(agent_path)

    def _extract_agent_name(self, agent_path: Path, is_minimal: bool = False) -> str:
        """Extract agent name from Agent() configuration."""
        if not is_minimal:
            agent_file = agent_path / "a2a_app.py"
        else:
            agent_file = agent_path / "agent.py"

        if not agent_file.exists():
            return agent_path.name

        try:
            content = agent_file.read_text(encoding="utf-8")
            tree = ast.parse(content)

            # Look for Agent() constructor calls with name parameter
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if this is an Agent() call
                    if (
                        isinstance(node.func, ast.Name) and node.func.id == "Agent"
                    ) or (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "Agent"
                    ):
                        # Look for name parameter in keywords
                        for keyword in node.keywords:
                            if keyword.arg == "name" and isinstance(
                                keyword.value, ast.Constant
                            ):
                                value = keyword.value.value
                                return (
                                    str(value) if value is not None else agent_path.name
                                )

                        # Look for name parameter in positional args (less common but possible)
                        # This would require knowing the Agent constructor signature

            # Fallback to directory name if no name found
            return agent_path.name

        except Exception as e:
            logger.warning(f"Failed to extract agent name from {agent_file}: {e}")
            return agent_path.name

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

    def _extract_agent_name_runtime_first(
        self, agent_path: Path, is_minimal: bool = False
    ) -> str:
        """Extract agent name using runtime-first approach."""
        try:
            # Try to load and inspect the actual agent object
            runtime_name = self._get_runtime_agent_name(agent_path, is_minimal)
            if runtime_name:
                return runtime_name
        except Exception as e:
            logger.debug(f"Runtime name extraction failed: {e}")

        # Fallback to static analysis
        return self._extract_agent_name(agent_path, is_minimal)

    def _get_runtime_agent_name(
        self, agent_path: Path, is_minimal: bool = False
    ) -> Optional[str]:
        """Try to load agent and get runtime name."""
        try:
            import sys
            import importlib.util

            # Add agent directory to path temporarily
            original_path = sys.path[:]
            sys.path.insert(0, str(agent_path))

            try:
                if not is_minimal:
                    # Load agent from a2a_app.py
                    agent_file = agent_path / "a2a_app.py"
                    spec = importlib.util.spec_from_file_location(
                        "temp_agent", agent_file
                    )
                    if not spec or not spec.loader:
                        return None

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Get root_agent and extract name
                    if hasattr(module, "root_agent"):
                        agent = module.root_agent
                        if hasattr(agent, "name"):
                            return agent.name
                else:
                    # Load agent from module structure (agent.py via __init__.py)
                    agent_dir_name = agent_path.name
                    spec = importlib.util.spec_from_file_location(
                        agent_dir_name, agent_path / "__init__.py"
                    )
                    if not spec or not spec.loader:
                        return None

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Get root_agent and extract name
                    if hasattr(module, "root_agent"):
                        agent = module.root_agent
                        if hasattr(agent, "name"):
                            return agent.name

            finally:
                # Restore path
                sys.path[:] = original_path

        except Exception as e:
            logger.debug(f"Could not load agent for runtime inspection: {e}")

        return None

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

    def _extract_description_best_source(
        self, agent_path: Path, content: str
    ) -> Optional[str]:
        """Extract description using best available source."""
        # 1. Try runtime agent inspection
        try:
            runtime_desc = self._get_runtime_description(agent_path)
            if runtime_desc:
                logger.debug("Using description from runtime agent")
                return runtime_desc
        except Exception as e:
            logger.debug(f"Runtime description extraction failed: {e}")

        # 2. Fallback to static analysis
        static_desc = self._extract_description(content)
        if static_desc:
            logger.debug("Using description from static analysis")
            return static_desc

        # 3. Skip if unknown
        logger.debug("Description could not be determined")
        return None

    def _get_runtime_description(self, agent_path: Path) -> Optional[str]:
        """Get description from runtime agent."""
        try:
            import sys
            import importlib.util

            # Add agent directory to path temporarily
            original_path = sys.path[:]
            sys.path.insert(0, str(agent_path))

            try:
                # Load agent module
                agent_file = agent_path / "a2a_app.py"
                spec = importlib.util.spec_from_file_location("temp_agent", agent_file)
                if not spec or not spec.loader:
                    return None

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Get root_agent and extract description
                if hasattr(module, "root_agent"):
                    agent = module.root_agent
                    if hasattr(agent, "description"):
                        return agent.description

            finally:
                # Restore path
                sys.path[:] = original_path

        except Exception:
            pass

        return None

    def _extract_tools_best_source(self, agent_path: Path, content: str) -> list[str]:
        """Extract tools using best available source."""
        # 1. Try runtime agent inspection
        try:
            runtime_tools = self._get_runtime_tools(agent_path)
            if runtime_tools:
                logger.debug(
                    f"Using tools from runtime agent: {len(runtime_tools)} tools"
                )
                return runtime_tools
        except Exception as e:
            logger.debug(f"Runtime tools extraction failed: {e}")

        # 2. Fallback to static analysis
        static_tools = self._extract_tools(content)
        if static_tools:
            logger.debug(f"Using tools from static analysis: {len(static_tools)} tools")
            return static_tools

        # 3. Return empty list if unknown
        logger.debug("Tools could not be determined")
        return []

    def _get_runtime_tools(self, agent_path: Path) -> list[str]:
        """Get tools from runtime agent."""
        try:
            import sys
            import importlib.util

            # Add agent directory to path temporarily
            original_path = sys.path[:]
            sys.path.insert(0, str(agent_path))

            try:
                # Load agent module
                agent_file = agent_path / "a2a_app.py"
                spec = importlib.util.spec_from_file_location("temp_agent", agent_file)
                if not spec or not spec.loader:
                    return []

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Get root_agent and extract tools
                if hasattr(module, "root_agent"):
                    agent = module.root_agent
                    if hasattr(agent, "tools") and agent.tools:
                        tools = []
                        for tool in agent.tools:
                            if hasattr(tool, "__class__"):
                                class_name = tool.__class__.__name__
                                if class_name == "MCPToolset":
                                    tools.append("MCP Server Tools")
                                else:
                                    # Convert class name to readable format
                                    readable_name = " ".join(
                                        re.findall("[A-Z][a-z]*", class_name)
                                    )
                                    tools.append(
                                        readable_name if readable_name else class_name
                                    )
                        return tools

            finally:
                # Restore path
                sys.path[:] = original_path

        except Exception:
            pass

        return []

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
        if not self._has_adk_imports_in_directory(agent_path):
            result.errors.append("No Google ADK imports found in directory")
            result.is_valid = False

        return result

    def _validate_complete_agent(self, agent_path: Path) -> ValidationResult:
        """Validate complete A2A agent with a2a_app.py."""
        result = ValidationResult(is_valid=True)

        # Check required files
        agent_file = agent_path / "a2a_app.py"
        if not agent_file.exists():
            result.errors.append("Missing required a2a_app.py file")
            result.is_valid = False
            return result

        # Check if a2a_app.py can be imported (basic syntax check)
        try:
            content = agent_file.read_text(encoding="utf-8")
            ast.parse(content)
        except SyntaxError as e:
            result.errors.append(f"Syntax error in a2a_app.py: {e}")
            result.is_valid = False
            return result

        # Check for root_agent variable or import
        if not self._has_root_agent(content) and not self._has_root_agent_import(
            content
        ):
            result.errors.append("Missing root_agent variable or import in a2a_app.py")
            result.is_valid = False

        # Check for ADK imports
        if not self._has_adk_imports(content):
            result.errors.append("Missing Google ADK imports in a2a_app.py")
            result.is_valid = False

        return result

    def _validate_minimal_agent(self, agent_path: Path) -> ValidationResult:
        """Validate minimal agent structure with agent.py + __init__.py."""
        result = ValidationResult(is_valid=True)

        # Check required files
        agent_file = agent_path / "agent.py"
        init_file = agent_path / "__init__.py"

        if not agent_file.exists():
            result.errors.append("Missing required agent.py file")
            result.is_valid = False

        if not init_file.exists():
            result.errors.append("Missing required __init__.py file")
            result.is_valid = False

        if not result.is_valid:
            return result

        # Check agent.py syntax and ADK imports
        try:
            agent_content = agent_file.read_text(encoding="utf-8")
            ast.parse(agent_content)

            if not self._has_adk_imports(agent_content):
                result.errors.append("Missing Google ADK imports in agent.py")
                result.is_valid = False
        except SyntaxError as e:
            result.errors.append(f"Syntax error in agent.py: {e}")
            result.is_valid = False

        # Check __init__.py syntax and root_agent import
        try:
            init_content = init_file.read_text(encoding="utf-8")
            ast.parse(init_content)

            if not self._has_root_agent_import(init_content):
                result.errors.append("Missing root_agent import in __init__.py")
                result.is_valid = False
        except SyntaxError as e:
            result.errors.append(f"Syntax error in __init__.py: {e}")
            result.is_valid = False

        return result
