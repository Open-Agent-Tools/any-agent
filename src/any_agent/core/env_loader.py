"""Environment variable loader with priority handling.

Loads environment variables from .env files with priority order:
1. CLI input (existing environment variables)
2. Agent folder .env file
3. Current working directory .env file
"""

import os
from pathlib import Path
from typing import Dict, Optional
import logging

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

logger = logging.getLogger(__name__)


class EnvironmentLoader:
    """Load environment variables with priority handling."""

    def __init__(self):
        """Initialize environment loader."""
        self.loaded_vars: Dict[str, str] = {}

    def load_env_with_priority(
        self, agent_path: Path, current_dir: Optional[Path] = None
    ) -> Dict[str, str]:
        """Load environment variables with priority order.

        Priority order:
        1. CLI input (existing environment variables)
        2. Agent folder .env file
        3. Current working directory .env file

        Args:
            agent_path: Path to agent directory
            current_dir: Current working directory (defaults to os.getcwd())

        Returns:
            Dictionary of all loaded environment variables
        """
        if current_dir is None:
            current_dir = Path.cwd()

        # Start with empty dict and track sources
        env_vars = {}
        sources_found = []

        # Load from current directory .env (lowest priority)
        current_env_file = current_dir / ".env"
        if current_env_file.exists():
            logger.info(f"Loading .env from current directory: {current_env_file}")
            env_vars.update(self._load_env_file(current_env_file))
            sources_found.append(f"current directory ({current_env_file})")

        # Load from agent folder .env (medium priority)
        agent_env_file = agent_path / ".env"
        if agent_env_file.exists():
            logger.info(f"Loading .env from agent folder: {agent_env_file}")
            env_vars.update(self._load_env_file(agent_env_file))
            sources_found.append(f"agent folder ({agent_env_file})")

        # Validate that at least one .env file was found
        if not sources_found:
            raise RuntimeError(
                f"No .env file found. Pipeline requires environment configuration.\n"
                f"Expected locations:\n"
                f"  1. Agent folder: {agent_env_file}\n"
                f"  2. Current directory: {current_env_file}\n"
                f"Please create a .env file with framework-specific environment variables."
            )

        # CLI input (existing environment) has highest priority
        cli_overrides = []
        for key in env_vars.keys():
            if key in os.environ:
                logger.info(f"Using CLI environment variable: {key}")
                env_vars[key] = os.environ[key]
                cli_overrides.append(key)

        # Also include any environment variables not in .env files
        for key, value in os.environ.items():
            if key not in env_vars:
                env_vars[key] = value

        self.loaded_vars = env_vars
        logger.info(
            f"Loaded {len(env_vars)} environment variables from: {', '.join(sources_found)}"
        )
        if cli_overrides:
            logger.info(f"CLI overrides applied: {cli_overrides}")

        return env_vars

    def _load_env_file(self, env_file_path: Path) -> Dict[str, str]:
        """Load variables from a single .env file.

        Args:
            env_file_path: Path to .env file

        Returns:
            Dictionary of variables from the file
        """
        if load_dotenv is None:
            logger.warning("python-dotenv not available - cannot load .env files")
            return {}

        env_vars = {}

        try:
            # Read .env file manually to get just the variables from this file
            with open(env_file_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        env_vars[key] = value

        except Exception as e:
            logger.error(f"Failed to load .env file {env_file_path}: {e}")

        return env_vars

    def get_framework_env_vars(self, framework: str) -> Dict[str, str]:
        """Get environment variables relevant to a specific framework.

        Args:
            framework: Framework name (e.g., 'google_adk', 'aws_strands')

        Returns:
            Dictionary of framework-relevant environment variables
        """
        framework_vars = {}

        # Common variables for all frameworks
        common_vars = [
            "AGENT_PORT",
            "MCP_SERVER_URL",
            "AGENT_ID",
        ]

        # Framework-specific variables
        framework_specific = {
            "google_adk": [
                "GOOGLE_API_KEY",
                "GOOGLE_MODEL",
                "GOOGLE_PROJECT_ID",
                "GOOGLE_LOCATION",
            ],
            "aws_strands": [
                "ANTHROPIC_API_KEY",
                "AWS_REGION",
                "AWS_ACCESS_KEY_ID",
                "AWS_SECRET_ACCESS_KEY",
            ],
            "langchain": ["OPENAI_API_KEY", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"],
            "langgraph": ["OPENAI_API_KEY", "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT"],
            "crewai": ["OPENAI_API_KEY", "CREWAI_API_KEY"],
        }

        # Collect relevant variables
        relevant_vars = common_vars + framework_specific.get(framework, [])

        for var in relevant_vars:
            if var in self.loaded_vars:
                framework_vars[var] = self.loaded_vars[var]

        return framework_vars

    def get_all_env_vars(self) -> Dict[str, str]:
        """Get all loaded environment variables from .env files and CLI.

        Returns:
            Dictionary of all environment variables loaded from all sources
        """
        return self.loaded_vars.copy()
