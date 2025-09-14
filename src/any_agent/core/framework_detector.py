"""Framework detection logic for Any Agent."""

import logging
from pathlib import Path
from typing import List, Optional

from ..adapters.base import BaseFrameworkAdapter
from ..adapters.google_adk_adapter import GoogleADKAdapter
from ..adapters.langchain_adapter import LangChainAdapter
from ..adapters.langgraph_adapter import LangGraphAdapter
from ..adapters.crewai_adapter import CrewAIAdapter
from ..adapters.aws_strands_adapter import AWSStrandsAdapter

logger = logging.getLogger(__name__)


class FrameworkDetector:
    """Handles detection of AI agent frameworks."""

    def __init__(self, supported_frameworks: Optional[List[str]] = None):
        """
        Initialize framework detector.

        Args:
            supported_frameworks: List of framework names to support.
                                 If None, supports all detectable frameworks.
        """
        self.supported_frameworks = supported_frameworks or [
            "google_adk",
            "aws_strands",
            "langchain",
            "langgraph",
            "crewai",
        ]
        self.adapters: List[BaseFrameworkAdapter] = [
            GoogleADKAdapter(),
            LangChainAdapter(),
            LangGraphAdapter(),
            CrewAIAdapter(),
            AWSStrandsAdapter(),
        ]

    def detect_framework(self, agent_path: Path) -> Optional[BaseFrameworkAdapter]:
        """
        Detect which framework an agent uses.

        Args:
            agent_path: Path to agent directory

        Returns:
            Matching adapter or None if no framework detected

        Raises:
            ValueError: If detected framework is not in supported_frameworks
        """
        agent_path = Path(agent_path)

        if not agent_path.exists() or not agent_path.is_dir():
            logger.error(
                f"Agent path does not exist or is not a directory: {agent_path}"
            )
            return None

        for adapter in self.adapters:
            logger.info(f"Checking {adapter.framework_name} adapter...")
            if adapter.detect(agent_path):
                logger.info(f"Detected {adapter.framework_name} framework")

                # Check if framework is supported
                if adapter.framework_name not in self.supported_frameworks:
                    raise ValueError(f"{adapter.framework_name} is not supported yet.")

                return adapter

        logger.warning(f"No supported framework detected in {agent_path}")
        return None

    def get_supported_frameworks(self) -> List[str]:
        """Get list of currently supported frameworks."""
        return self.supported_frameworks.copy()

    def add_supported_framework(self, framework_name: str) -> None:
        """Add a framework to the supported list."""
        if framework_name not in self.supported_frameworks:
            self.supported_frameworks.append(framework_name)
            logger.info(f"Added {framework_name} to supported frameworks")

    def remove_supported_framework(self, framework_name: str) -> None:
        """Remove a framework from the supported list."""
        if framework_name in self.supported_frameworks:
            self.supported_frameworks.remove(framework_name)
            logger.info(f"Removed {framework_name} from supported frameworks")

    def get_all_detectable_frameworks(self) -> List[str]:
        """Get list of all frameworks that can be detected (regardless of support)."""
        return [adapter.framework_name for adapter in self.adapters]
