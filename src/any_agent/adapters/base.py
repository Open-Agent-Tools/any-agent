"""Base adapter interface for framework detection and adaptation."""

import ast
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentMetadata:
    """Metadata extracted from an agent."""

    name: str
    framework: str
    model: Optional[str] = None
    description: Optional[str] = None
    tools: List[str] = field(default_factory=list)
    environment_vars: Dict[str, str] = field(default_factory=dict)
    entry_point: str = "root_agent"
    local_dependencies: List[str] = field(
        default_factory=list
    )  # Local files/modules needed


@dataclass
class ValidationResult:
    """Result of agent validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class BaseFrameworkAdapter(ABC):
    """Base class for framework-specific adapters."""

    @property
    @abstractmethod
    def framework_name(self) -> str:
        """Name of the framework this adapter handles."""

    def _read_all_python_files(
        self, agent_path: Path, file_pattern: str = "*.py"
    ) -> str:
        """
        Read and combine all Python files in the agent directory.

        Args:
            agent_path: Path to the agent directory
            file_pattern: File pattern to match (default: "*.py")

        Returns:
            Combined content of all matching files
        """
        all_content = ""
        for file in agent_path.rglob(file_pattern):
            # Skip generated build artifacts in .any_agent directory
            if ".any_agent" in str(file):
                continue
            try:
                content = file.read_text(encoding="utf-8")
                all_content += content + "\n"
            except Exception as e:
                logger.debug(f"Error reading {file}: {e}")
                continue
        return all_content

    def _has_framework_imports_in_directory(
        self, agent_path: Path, import_checker: Callable[[str], bool]
    ) -> bool:
        """
        Check if any Python file in directory contains framework imports.

        Args:
            agent_path: Path to the agent directory
            import_checker: Function that checks if content contains framework imports

        Returns:
            True if framework imports are found, False otherwise
        """
        for py_file in agent_path.rglob("*.py"):
            # Skip generated build artifacts in .any_agent directory
            if ".any_agent" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                if import_checker(content):
                    return True
            except Exception as e:
                logger.debug(f"Error reading {py_file}: {e}")
                continue
        return False

    def _extract_agent_name_from_ast(self, content: str) -> Optional[str]:
        """
        Extract agent name from Agent() constructor calls in AST.

        Args:
            content: Python source code content to parse

        Returns:
            Agent name if found, None otherwise
        """
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

    def _validate_python_syntax(
        self, agent_path: Path, result: ValidationResult
    ) -> None:
        """
        Validate syntax of all Python files in the agent directory.

        Args:
            agent_path: Path to the agent directory
            result: ValidationResult to update with any errors
        """
        py_files = list(agent_path.rglob("*.py"))
        if not py_files:
            result.errors.append("No Python files found in agent directory")
            result.is_valid = False
            return

        # Check for basic syntax in Python files
        for py_file in py_files:
            # Skip generated build artifacts in .any_agent directory
            if ".any_agent" in str(py_file):
                continue
            try:
                content = py_file.read_text(encoding="utf-8")
                ast.parse(content)
            except SyntaxError as e:
                result.errors.append(f"Syntax error in {py_file.name}: {e}")
                result.is_valid = False

    @abstractmethod
    def detect(self, agent_path: Path) -> bool:
        """
        Detect if the given path contains an agent for this framework.

        Args:
            agent_path: Path to the agent directory

        Returns:
            True if this framework is detected, False otherwise
        """

    @abstractmethod
    def extract_metadata(self, agent_path: Path) -> AgentMetadata:
        """
        Extract metadata from the detected agent.

        Args:
            agent_path: Path to the agent directory

        Returns:
            AgentMetadata containing extracted information
        """

    @abstractmethod
    def validate(self, agent_path: Path) -> ValidationResult:
        """
        Validate that the agent is properly configured and functional.

        Args:
            agent_path: Path to the agent directory

        Returns:
            ValidationResult indicating success/failure and any issues
        """


@dataclass
class FrameworkConfig:
    """Configuration for framework detection and metadata extraction."""

    name: str
    import_patterns: List[str]
    required_files: List[str] = field(default_factory=list)
    special_validations: List[str] = field(default_factory=list)
    entry_point: str = "root_agent"


class ConfigurableFrameworkAdapter(BaseFrameworkAdapter):
    """
    Data-driven framework adapter that eliminates duplication.

    Subclasses only need to define framework_config and any special validation methods.
    """

    framework_config: FrameworkConfig = None  # Must be overridden by subclasses

    @property
    def framework_name(self) -> str:
        """Name of the framework this adapter handles."""
        if not self.framework_config:
            raise NotImplementedError("framework_config must be defined by subclass")
        return self.framework_config.name

    def detect(self, agent_path: Path) -> bool:
        """
        Generic detection logic using framework configuration.

        Eliminates ~95% of detection code duplication across adapters.
        """
        try:
            # Standard path validation
            if not agent_path.exists() or not agent_path.is_dir():
                logger.debug(f"Path does not exist or is not directory: {agent_path}")
                return False

            # Check required files
            for required_file in self.framework_config.required_files:
                if not (agent_path / required_file).exists():
                    logger.debug(f"Required file {required_file} not found in {agent_path}")
                    return False

            # Check framework imports using configured patterns
            if not self._has_framework_imports_in_directory(
                agent_path, self._has_configured_imports
            ):
                logger.debug(f"No {self.framework_config.name} imports found in {agent_path}")
                return False

            # Run any special validations
            for validation in self.framework_config.special_validations:
                validation_method = getattr(self, f"_validate_{validation}", None)
                if validation_method and not validation_method(agent_path):
                    logger.debug(f"Special validation {validation} failed for {agent_path}")
                    return False

            logger.info(f"{self.framework_config.name} agent detected at {agent_path}")
            return True

        except Exception as e:
            logger.error(f"Error detecting {self.framework_config.name} agent at {agent_path}: {e}")
            return False

    def _has_configured_imports(self, content: str) -> bool:
        """
        Check if content contains framework imports using configured patterns.

        Eliminates ~90% of import checking code duplication.
        """
        import re
        for pattern in self.framework_config.import_patterns:
            if re.search(pattern, content):
                return True
        return False
