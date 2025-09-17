"""URL translation for containerized deployments.

Translates localhost URLs in environment variables to work inside Docker containers
by converting localhost references to appropriate Docker networking hosts.

The URLTranslator is integrated into the Any Agent Docker pipeline to automatically
translate URLs that reference host machine services so they work from inside containers.

Key Features:
- Platform-specific Docker host detection (host.docker.internal on macOS/Windows, 172.17.0.1 on Linux)
- Universal translation - translates ALL localhost URLs found in environment variables
- Detailed logging of all translations for debugging
- Preserves non-localhost URLs unchanged

Integration Points:
- docker_orchestrator.py: Automatically translates environment variables before container startup
- Supports any service running on localhost that containers need to access
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

        Translates ALL localhost URLs in environment variables to work inside Docker containers.
        This ensures any service running on the host machine is accessible from containers.

        Args:
            env_vars: Original environment variables from .env files

        Returns:
            Tuple of (translated_vars, translation_log)
            - translated_vars: Environment variables with translated URLs
            - translation_log: Record of what was translated for debugging
        """
        translated_vars = env_vars.copy()
        translation_log = {}

        # Check ALL environment variables for localhost URLs that point to Docker services
        for variable_name, value in env_vars.items():
            if self._looks_like_localhost_url(value):
                # Only translate URLs that point to Docker services
                if self._is_docker_service(value):
                    original_url = value
                    translated_url = self._translate_url(original_url)

                    if translated_url != original_url:
                        translated_vars[variable_name] = translated_url
                        translation_log[variable_name] = {
                            "original": original_url,
                            "translated": translated_url,
                            "docker_host": self._docker_host,
                            "reason": "Docker service detected",
                        }
                        logger.info(
                            f"Translated {variable_name}: {original_url} → {translated_url} (Docker service)"
                        )
                else:
                    logger.debug(
                        f"Skipping {variable_name}: {value} (not a Docker service)"
                    )

        if translation_log:
            logger.info(
                f"Applied Docker URL translations for {len(translation_log)} variables"
            )
        else:
            logger.debug("No localhost URLs found requiring translation")

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

    def _is_docker_service(self, url: str) -> bool:
        """Check if a URL points to a service running in Docker.

        This method attempts to detect if the target service is containerized
        by checking common indicators.

        Args:
            url: URL to check

        Returns:
            True if the service appears to be running in Docker
        """
        if not self._looks_like_localhost_url(url):
            return False

        try:
            import subprocess
            import socket
            from urllib.parse import urlparse

            parsed = urlparse(url)
            port = parsed.port

            if not port:
                return False

            # Check if we can connect to the service
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)  # 1 second timeout
                result = sock.connect_ex(("localhost", port))
                sock.close()

                if result != 0:
                    # Service not running
                    return False

            except Exception:
                return False

            # Try to detect if it's a Docker container by checking docker ps
            try:
                docker_result = subprocess.run(
                    ["docker", "ps", "--format", "{{.Ports}}"],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if docker_result.returncode == 0:
                    # Look for port mappings that match our target port
                    for line in docker_result.stdout.strip().split("\n"):
                        if f":{port}->" in line or f"0.0.0.0:{port}" in line:
                            logger.debug(f"Found Docker container exposing port {port}")
                            return True

            except (
                subprocess.TimeoutExpired,
                FileNotFoundError,
                subprocess.SubprocessError,
            ):
                # Docker not available or command failed
                pass

            # Additional heuristics could be added here:
            # - Check for docker-compose services
            # - Check container networking
            # - Look for specific service patterns

        except Exception as e:
            logger.debug(f"Error checking if {url} is Docker service: {e}")

        return False

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
