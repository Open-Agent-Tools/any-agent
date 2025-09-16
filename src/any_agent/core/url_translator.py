"""URL translation for containerized deployments.

Translates localhost URLs in environment variables to work inside Docker containers
by converting localhost references to appropriate Docker networking hosts.

The URLTranslator is integrated into the Any Agent Docker pipeline to automatically
translate URLs that reference host machine services so they work from inside containers.

Key Features:
- Platform-specific Docker host detection (host.docker.internal on macOS/Windows, 172.17.0.1 on Linux)
- Conservative translation - only translates known host service environment variables
- Detailed logging of all translations for debugging
- Preserves non-localhost URLs unchanged

Integration Points:
- docker_orchestrator.py: Automatically translates environment variables before container startup
- Supports Google ADK MCP servers, Helmsman services, and other explicitly named host services
"""

import logging
import platform
import re
from typing import Any, Dict, Tuple
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)


class URLTranslator:
    """Translates localhost URLs for Docker container networking."""

    def __init__(self):
        """Initialize URL translator with platform detection."""
        self._docker_host = self._detect_docker_host()

    def _detect_docker_host(self) -> str:
        """Detect the appropriate Docker host based on platform.

        Returns:
            Docker host address for accessing host machine from container
        """
        system = platform.system().lower()

        if system in ("darwin", "windows"):
            # macOS and Windows Docker Desktop
            return "host.docker.internal"
        else:
            # Linux - use Docker bridge gateway
            return "172.17.0.1"

    def translate_env_vars_for_docker(
        self, env_vars: Dict[str, str]
    ) -> Tuple[Dict[str, str], Dict[str, Dict[str, Any]]]:
        """Translate environment variables for Docker deployment.

        Only translates URLs that are known to reference host machine services
        that need to be accessible from inside Docker containers.

        Args:
            env_vars: Original environment variables from .env files

        Returns:
            Tuple of (translated_vars, translation_log)
            - translated_vars: Environment variables with translated URLs
            - translation_log: Record of what was translated for debugging
        """
        translated_vars = env_vars.copy()
        translation_log = {}

        # ONLY translate environment variables that are known to reference
        # host machine services that containers need to access
        host_service_vars = [
            "MCP_SERVER_URL",  # MCP servers typically run on host
            "MCP_HTTP_URL",  # MCP HTTP endpoint on host
            "HELMSMAN_URL",  # Helmsman runs on host
            "HELMSMAN_MCP_URL",  # Helmsman MCP endpoint on host
        ]

        # Additional variables that might reference host services
        # but require explicit opt-in via naming convention
        potential_host_vars = [
            "HOST_API_URL",  # Explicitly marked as host service
            "HOST_SERVICE_URL",  # Explicitly marked as host service
            "EXTERNAL_API_URL",  # Could be host or truly external
        ]

        for var_name in host_service_vars:
            if var_name in env_vars:
                original_url = env_vars[var_name]
                translated_url = self._translate_url(original_url)

                if translated_url != original_url:
                    translated_vars[var_name] = translated_url
                    translation_log[var_name] = {
                        "original": original_url,
                        "translated": translated_url,
                        "docker_host": self._docker_host,
                        "reason": "known host service",
                    }
                    logger.info(
                        f"Translated {var_name}: {original_url} → {translated_url}"
                    )

        # Check potential host variables with explicit naming
        for var_name in potential_host_vars:
            if var_name in env_vars:
                original_url = env_vars[var_name]
                if self._looks_like_localhost_url(original_url):
                    translated_url = self._translate_url(original_url)
                    if translated_url != original_url:
                        translated_vars[var_name] = translated_url
                        translation_log[var_name] = {
                            "original": original_url,
                            "translated": translated_url,
                            "docker_host": self._docker_host,
                            "reason": "explicit host variable naming",
                        }
                        logger.info(
                            f"Translated {var_name}: {original_url} → {translated_url}"
                        )

        if translation_log:
            logger.info(
                f"Applied Docker URL translations for {len(translation_log)} variables"
            )
            logger.debug("URL translation only applied to known host services")
        else:
            logger.debug("No host service URLs found requiring translation")

        return translated_vars, translation_log

    def _translate_url(self, url: str) -> str:
        """Translate a single URL for Docker networking.

        Args:
            url: Original URL string

        Returns:
            Translated URL string
        """
        if not url or not isinstance(url, str):
            return url

        try:
            parsed = urlparse(url)

            # Only translate localhost and 127.0.0.1
            if parsed.hostname in ("localhost", "127.0.0.1"):
                # Replace hostname with Docker host
                new_netloc = parsed.netloc.replace(parsed.hostname, self._docker_host)

                # Reconstruct URL with new hostname
                translated_parsed = parsed._replace(netloc=new_netloc)
                return urlunparse(translated_parsed)

        except Exception as e:
            logger.debug(f"Could not parse URL '{url}': {e}")

        return url

    def _looks_like_localhost_url(self, value: str) -> bool:
        """Check if a string looks like a localhost URL.

        Args:
            value: String to check

        Returns:
            True if string appears to be a localhost URL
        """
        if not isinstance(value, str):
            return False

        # Detect localhost URLs - starts with http/https and contains localhost
        url_pattern = re.compile(
            r"^https?://(?:localhost|127\.0\.0\.1)(?::\d+)?(?:/.*)?$", re.IGNORECASE
        )
        return bool(url_pattern.match(value.strip()))

    def get_docker_host(self) -> str:
        """Get the detected Docker host for this platform.

        Returns:
            Docker host address
        """
        return self._docker_host

    def create_docker_env_file(
        self, translated_vars: Dict[str, str], output_path: str
    ) -> str:
        """Create a .env file with translated variables for Docker.

        Args:
            translated_vars: Environment variables with translated URLs
            output_path: Path where to write the Docker .env file

        Returns:
            Content of the created .env file
        """
        env_content = "# Docker-translated environment variables\n"
        env_content += "# Generated by Any Agent URL Translator\n"
        env_content += f"# Docker host: {self._docker_host}\n\n"

        for key, value in sorted(translated_vars.items()):
            # Escape any quotes in values
            escaped_value = value.replace('"', '\\"')
            env_content += f'{key}="{escaped_value}"\n'

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(env_content)
            logger.info(f"Created Docker .env file: {output_path}")
        except Exception as e:
            logger.error(f"Failed to create Docker .env file: {e}")
            raise

        return env_content
