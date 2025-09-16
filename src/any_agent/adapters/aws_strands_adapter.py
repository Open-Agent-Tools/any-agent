"""AWS Strands framework adapter for Any Agent."""

import ast
import logging
import re
from pathlib import Path
from typing import Optional

from .base import AgentMetadata, BaseFrameworkAdapter, ValidationResult

logger = logging.getLogger(__name__)


class AWSStrandsAdapter(BaseFrameworkAdapter):
    """Adapter for AWS Strands agents."""

    @property
    def framework_name(self) -> str:
        return "aws_strands"

    def detect(self, agent_path: Path) -> bool:
        """
        Detect AWS Strands agent by checking:
        1. Contains Strands imports (strands, strands-agents)
        2. Has typical patterns (Agent, tool decorator, etc.)
        """
        try:
            if not agent_path.exists() or not agent_path.is_dir():
                logger.debug(f"Path does not exist or is not directory: {agent_path}")
                return False

            # Check for Strands imports anywhere in the directory
            if not self._has_framework_imports_in_directory(agent_path, self._has_strands_imports):
                logger.debug(f"No Strands imports found in {agent_path}")
                return False

            logger.info(f"AWS Strands agent detected at {agent_path}")
            return True

        except Exception as e:
            logger.error(f"Error detecting AWS Strands agent at {agent_path}: {e}")
            return False


    def _has_strands_imports(self, content: str) -> bool:
        """Check if content contains Strands imports."""
        strands_import_patterns = [
            r"from\s+strands",
            r"import\s+strands",
            r"strands-agents",
            r"strands_tools",
            r"@tool",  # Common Strands decorator
        ]

        for pattern in strands_import_patterns:
            if re.search(pattern, content):
                return True
        return False

    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """Extract metadata from AWS Strands agent."""
        # Try to extract agent name from the agent definition first
        agent_name = self._extract_agent_name_from_files(agent_path)
        if not agent_name:
            agent_name = agent_path.name.replace("_", " ").title()

        metadata = AgentMetadata(
            name=agent_name,
            framework=self.framework_name,
            entry_point="root_agent",
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
        all_content = self._aggregate_file_contents(agent_path)

        # Use agent.py content primarily, fall back to all content
        primary_content = agent_content if agent_content else all_content

        metadata.model = self._extract_model(primary_content)
        metadata.description = self._extract_description(primary_content, agent_name)
        metadata.tools = self._extract_tools(primary_content)
        metadata.environment_vars = self._extract_environment_vars(primary_content)
        metadata.local_dependencies = self._extract_local_dependencies(agent_path)

        return metadata

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
        """Extract description from AWS Strands agent content."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Check if this is an Agent() call
                    if (
                        isinstance(node.func, ast.Name) and node.func.id == "Agent"
                    ) or (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "Agent"
                    ):
                        # Look for description parameter
                        for keyword in node.keywords:
                            if keyword.arg == "description" and isinstance(
                                keyword.value, ast.Constant
                            ):
                                return str(keyword.value.value)
        except Exception:
            pass

        # Fallback descriptions based on patterns
        if "Agent" in content and "@tool" in content:
            return f"{agent_name} with custom tools"
        elif "Agent" in content:
            return f"{agent_name} built with AWS Strands"
        return None

    def _extract_environment_vars(self, content: str) -> dict[str, str]:
        """Extract environment variables referenced in the content."""
        env_vars = {}

        # Look for common environment variable patterns
        env_patterns = [
            (r'os\.getenv\(["\']([^"\']+)["\'](?:,\s*["\']([^"\']*)["\'])?', "getenv"),
            (r'os\.environ\[["\']([^"\']+)["\']\]', "environ"),
        ]

        for pattern, method in env_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                env_name = match.group(1)
                default_value = (
                    match.group(2) if len(match.groups()) > 1 and match.group(2) else ""
                )
                env_vars[env_name] = default_value or "required"

        return env_vars

    def _extract_tools(self, content: str) -> list[str]:
        """Extract tool information from Strands content."""
        tools = []

        if "@tool" in content:
            tools.append("Custom Tools")

        if "calculator" in content:
            tools.append("Calculator")

        if "MCPClient" in content:
            tools.append("MCP Integration")

        if "load_tools_from_directory" in content:
            tools.append("Directory Tools")

        return tools

    def _extract_local_dependencies(self, agent_path: Path) -> list[str]:
        """Extract local module dependencies that need to be included in the container."""
        local_deps = []

        for py_file in agent_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")

                # Parse imports to find local dependencies
                import_deps = self._find_local_imports(content, agent_path)
                local_deps.extend(import_deps)

            except Exception as e:
                logger.debug(f"Error reading {py_file} for dependencies: {e}")
                continue

        # Remove duplicates and return
        return list(set(local_deps))

    def _find_local_imports(self, content: str, agent_path: Path) -> list[str]:
        """Find local imports in the content that reference files outside the agent directory."""
        local_imports = []

        import_patterns = [
            # from utilities import ...
            r"from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import",
            # import utilities
            r"import\s+([a-zA-Z_][a-zA-Z0-9_]*)",
        ]

        for pattern in import_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                module_name = match.group(1)

                # Skip standard library and third-party imports
                if module_name in [
                    "os",
                    "sys",
                    "pathlib",
                    "logging",
                    "dotenv",
                    "ast",
                    "re",
                ]:
                    continue
                if module_name.startswith("strands"):
                    continue

                # Check if this is a local file in parent directory
                parent_dir = agent_path.parent
                potential_file = parent_dir / f"{module_name}.py"

                if potential_file.exists():
                    local_imports.append(str(potential_file))
                    logger.info(f"Found local dependency: {potential_file}")

        return local_imports

    def validate(self, agent_path: Path) -> ValidationResult:
        """Validate AWS Strands agent structure and dependencies."""
        result = ValidationResult(is_valid=True)

        # Check for required files
        init_file = agent_path / "__init__.py"
        agent_file = agent_path / "agent.py"

        if not init_file.exists():
            result.errors.append("Missing required __init__.py file")
            result.is_valid = False

        if not agent_file.exists():
            result.errors.append("Missing required agent.py file")
            result.is_valid = False

        if not result.is_valid:
            return result

        # Validate __init__.py structure
        try:
            init_content = init_file.read_text(encoding="utf-8")
            ast.parse(init_content)

            if not self._has_root_agent_import(init_content):
                result.errors.append("__init__.py must import and expose root_agent")
                result.is_valid = False
        except SyntaxError as e:
            result.errors.append(f"Syntax error in __init__.py: {e}")
            result.is_valid = False

        # Validate agent.py structure
        try:
            agent_content = agent_file.read_text(encoding="utf-8")
            ast.parse(agent_content)

            if not self._has_strands_imports(agent_content):
                result.errors.append("agent.py must import from strands framework")
                result.is_valid = False

            if not self._has_root_agent_definition(agent_content):
                result.errors.append("agent.py must define root_agent variable")
                result.is_valid = False

        except SyntaxError as e:
            result.errors.append(f"Syntax error in agent.py: {e}")
            result.is_valid = False

        # Check for environment variable requirements
        if result.is_valid:
            self._validate_environment_requirements(agent_content, result)

        return result

    def _has_root_agent_import(self, content: str) -> bool:
        """Check if content imports root_agent from agent module."""
        import_patterns = [
            r"from\s+agent\s+import\s+root_agent",
            r"from\s+\.agent\s+import\s+root_agent",
            r"import.*root_agent",
        ]

        for pattern in import_patterns:
            if re.search(pattern, content):
                return True
        return False

    def _has_root_agent_definition(self, content: str) -> bool:
        """Check if content defines root_agent variable."""
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id == "root_agent":
                            return True
            return False
        except Exception:
            return False

    def _validate_environment_requirements(
        self, content: str, result: ValidationResult
    ):
        """Validate environment variable requirements based on model type."""
        # Check for model types that require API keys
        if "AnthropicModel" in content:
            if not self._check_env_var_reference(content, "ANTHROPIC_API_KEY"):
                result.warnings.append(
                    "AnthropicModel detected but no ANTHROPIC_API_KEY environment variable reference found"
                )

        if "BedrockModel" in content:
            result.warnings.append(
                "BedrockModel detected - ensure AWS credentials are configured"
            )

        if "OpenAIModel" in content or "ChatOpenAI" in content:
            if not self._check_env_var_reference(content, "OPENAI_API_KEY"):
                result.warnings.append(
                    "OpenAI model detected but no OPENAI_API_KEY environment variable reference found"
                )

    def _check_env_var_reference(self, content: str, env_var: str) -> bool:
        """Check if content references a specific environment variable."""
        patterns = [
            rf'os\.getenv\(["\'{env_var}["\']',
            rf'os\.environ\[["\'{env_var}["\']\]',
            rf'getenv\(["\'{env_var}["\']',
        ]

        for pattern in patterns:
            if re.search(pattern, content):
                return True
        return False
