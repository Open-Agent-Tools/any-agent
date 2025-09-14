"""Base adapter interface for framework detection and adaptation."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


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
