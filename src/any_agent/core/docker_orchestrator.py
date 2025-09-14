"""Main orchestrator for Any Agent framework operations."""

import asyncio
import json
import logging
import subprocess
import time
import requests
from pathlib import Path
from typing import Any, Dict, Optional

from ..adapters.base import BaseFrameworkAdapter, AgentMetadata, ValidationResult
from ..docker.docker_generator import UnifiedDockerfileGenerator
from ..api.helmsman_integration import HelsmanClient, create_helmsman_registration
from .port_checker import PortChecker
from .agent_context import AgentContextManager
from .framework_detector import FrameworkDetector
from .env_loader import EnvironmentLoader

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """Main orchestrator for detecting, wrapping, and deploying agents."""

    def __init__(self):
        """Initialize orchestrator with available adapters."""
        # Initialize framework detector with Google ADK and AWS Strands supported
        self.framework_detector = FrameworkDetector(
            supported_frameworks=["google_adk", "aws_strands"]
        )
        self.docker_generator = UnifiedDockerfileGenerator()
        self.env_loader = EnvironmentLoader()

    def detect_framework(self, agent_path: Path) -> Optional[BaseFrameworkAdapter]:
        """
        Detect which framework an agent uses.

        Args:
            agent_path: Path to agent directory

        Returns:
            Matching adapter or None if no framework detected
        """
        return self.framework_detector.detect_framework(agent_path)

    def validate_agent(
        self, agent_path: Path, adapter: BaseFrameworkAdapter
    ) -> ValidationResult:
        """
        Validate agent using the detected adapter.

        Args:
            agent_path: Path to agent directory
            adapter: Framework adapter to use

        Returns:
            ValidationResult with success/failure status
        """
        logger.info(f"Validating agent using {adapter.framework_name} adapter...")
        return adapter.validate(agent_path)

    def extract_metadata(
        self, agent_path: Path, adapter: BaseFrameworkAdapter
    ) -> AgentMetadata:
        """
        Extract agent metadata.

        Args:
            agent_path: Path to agent directory
            adapter: Framework adapter to use

        Returns:
            AgentMetadata containing agent information
        """
        logger.info(f"Extracting metadata using {adapter.framework_name} adapter...")
        return adapter.extract_metadata(agent_path)

    def create_docker_image(
        self,
        agent_path: Path,
        metadata: AgentMetadata,
        output_dir: Optional[Path] = None,
        add_ui: bool = False,
        port: int = 8080,
        base_image: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create Docker image for the agent.

        Args:
            agent_path: Path to agent directory
            metadata: Agent metadata
            output_dir: Output directory for build context

        Returns:
            Dict with image_name and build_context_path
        """
        if output_dir is None:
            output_dir = agent_path / ".any_agent"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Ensure agent directory has .gitignore for build artifacts
        self._ensure_agent_gitignore(agent_path)

        logger.info("Creating Docker build context...")
        build_context = self.docker_generator.create_build_context(
            agent_path,
            output_dir,
            metadata,
            add_ui=add_ui,
            port=port,
            base_image=base_image,
        )

        # Generate image name
        image_name = (
            f"{metadata.name.lower().replace('_', '-').replace(' ', '-')}-agent"
        )

        logger.info(f"Building Docker image: {image_name}")
        build_cmd = [
            "docker",
            "build",
            "-t",
            f"{image_name}:latest",
            str(build_context),
        ]

        try:
            result = subprocess.run(
                build_cmd, check=True, capture_output=True, text=True
            )
            logger.info(f"Docker build successful: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Docker build failed: {e.stderr}")
            raise RuntimeError(f"Docker build failed: {e.stderr}")

        return {"image_name": image_name, "build_context_path": str(build_context)}

    def start_container(
        self, image_name: str, port: int = 8080, agent_name: Optional[str] = None
    ) -> str:
        """
        Start Docker container with proper networking.

        Args:
            image_name: Name of Docker image
            port: Port to expose
            agent_name: Agent name for consistent container naming

        Returns:
            Container ID
        """
        # Use agent name if provided, otherwise fall back to image name
        if agent_name:
            container_name = (
                f"{agent_name.lower().replace('_', '-').replace(' ', '-')}-agent"
            )
        else:
            container_name = f"{image_name}-container"

        # Stop and remove existing container if it exists
        try:
            subprocess.run(
                ["docker", "stop", container_name], check=False, capture_output=True
            )
            subprocess.run(
                ["docker", "rm", container_name], check=False, capture_output=True
            )
        except Exception:
            pass  # Ignore errors if container doesn't exist

        # Ensure any-agent network exists for inter-container communication
        try:
            subprocess.run(
                [
                    "docker",
                    "network",
                    "create",
                    "--driver",
                    "bridge",
                    "any-agent-network",
                ],
                check=False,
                capture_output=True,
            )
        except Exception:
            pass  # Network might already exist

        logger.info(f"Starting container: {container_name}")
        run_cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            "any-agent-network",
            "--add-host",
            "host.docker.internal:host-gateway",  # Enable host access across platforms
            "-p",
            f"{port}:{port}",
        ]

        # Always set AGENT_PORT
        run_cmd.extend(["-e", f"AGENT_PORT={port}"])

        # Add all environment variables from .env files and CLI
        if hasattr(self, "framework_env_vars"):
            for key, value in self.framework_env_vars.items():
                if key != "AGENT_PORT":  # Skip AGENT_PORT since we already set it
                    # Transform localhost URLs for Docker networking
                    if isinstance(value, str) and "localhost" in value:
                        # Replace localhost with host.docker.internal for container access
                        docker_value = value.replace(
                            "localhost", "host.docker.internal"
                        )
                        logger.info(
                            f"🐳 Transformed {key}: localhost -> host.docker.internal"
                        )
                        run_cmd.extend(["-e", f"{key}={docker_value}"])
                    else:
                        run_cmd.extend(["-e", f"{key}={value}"])
                    logger.debug(
                        f"Setting environment variable: {key}={value[:10]}..."
                        if len(value) > 10
                        else f"{key}={value}"
                    )
        else:
            raise RuntimeError(
                "No environment variables loaded. Pipeline requires .env file with agent configuration. "
                "Expected .env file locations: 1) CLI environment, 2) agent directory, 3) current directory"
            )

        run_cmd.append(f"{image_name}:latest")

        try:
            result = subprocess.run(run_cmd, check=True, capture_output=True, text=True)
            container_id = result.stdout.strip()
            logger.info(f"Container started successfully: {container_id}")
            return container_id
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start container: {e.stderr}")
            raise RuntimeError(f"Failed to start container: {e.stderr}")

    def wait_for_container_health(self, port: int = 8080, timeout: int = 60) -> bool:
        """
        Wait for container to become healthy.

        Args:
            port: Port to check
            timeout: Timeout in seconds

        Returns:
            True if healthy, False if timeout
        """
        logger.info(f"Waiting for container health on port {port}...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=5)
                if response.status_code == 200:
                    logger.info("Container is healthy!")
                    return True
            except requests.exceptions.RequestException:
                pass  # Continue waiting

            time.sleep(2)

        logger.error(f"Container health check timed out after {timeout} seconds")
        return False

    def test_agent_interaction(
        self, port: int = 8080, skip_a2a_test: bool = False, a2a_test_timeout: int = 30
    ) -> Dict[str, Any]:
        """
        Test agent interaction including HTTP endpoints and A2A protocol.

        Args:
            port: Port to connect to
            skip_a2a_test: Skip A2A protocol testing
            a2a_test_timeout: Timeout for A2A tests in seconds

        Returns:
            Dict with test results including both HTTP and A2A tests
        """
        logger.info("Testing agent interaction...")

        results = {}

        # HTTP Tests (existing functionality)
        logger.info("Running HTTP endpoint tests...")
        results["http_tests"] = self._test_http_endpoints(port)

        # A2A Protocol Tests (new functionality)
        if not skip_a2a_test:
            logger.info("Running A2A protocol tests...")
            results["a2a_tests"] = asyncio.run(
                self._test_a2a_protocol(port, a2a_test_timeout)
            )
        else:
            logger.info("Skipping A2A protocol tests (--skip-a2a-test flag)")
            results["a2a_tests"] = {
                "success": True,
                "skipped": True,
                "reason": "A2A testing disabled via CLI flag",
            }

        return results

    def _test_http_endpoints(self, port: int) -> Dict[str, Any]:
        """Test HTTP endpoints (existing functionality extracted)."""
        results = {}

        # Test health endpoint
        try:
            health_response = requests.get(
                f"http://localhost:{port}/health", timeout=10
            )
            results["health_check"] = (
                health_response.json()
                if health_response.status_code == 200
                else {"error": "Health check failed"}
            )
        except Exception as e:
            results["health_check"] = {"error": str(e)}

        # Test describe endpoint
        try:
            describe_response = requests.get(
                f"http://localhost:{port}/describe", timeout=10
            )
            if describe_response.status_code == 200:
                content_type = describe_response.headers.get("content-type", "")
                if content_type.startswith("text/html"):
                    # UI is enabled - HTML response is expected
                    results["describe"] = {
                        "status": "success",
                        "type": "html",
                        "ui_enabled": True,
                    }
                else:
                    # JSON response expected when UI is disabled
                    try:
                        results["describe"] = describe_response.json()
                    except Exception:
                        results["describe"] = {"status": "success", "type": "text"}
            else:
                results["describe"] = {"error": "Describe failed"}
        except Exception as e:
            results["describe"] = {"error": str(e)}

        # Test agent card endpoint
        try:
            agent_card_response = requests.get(
                f"http://localhost:{port}/.well-known/agent.json", timeout=10
            )
            if agent_card_response.status_code == 200:
                try:
                    agent_card = agent_card_response.json()
                    # Basic validation of agent card structure
                    if isinstance(agent_card, dict) and "name" in agent_card:
                        results["agent_card"] = {
                            "status": "success",
                            "name": agent_card.get("name"),
                            "version": agent_card.get("version"),
                            "capabilities": agent_card.get("capabilities", []),
                        }
                    else:
                        results["agent_card"] = {
                            "error": "Invalid agent card structure"
                        }
                except json.JSONDecodeError:
                    results["agent_card"] = {
                        "error": "Invalid JSON in agent card response"
                    }
            else:
                results["agent_card"] = {
                    "error": f"Agent card endpoint failed with status {agent_card_response.status_code}"
                }
        except Exception as e:
            results["agent_card"] = {"error": str(e)}

        return results

    async def _test_a2a_protocol(self, port: int, timeout: int) -> Dict[str, Any]:
        """Test A2A protocol compliance."""
        try:
            from ..validation.a2a_message_validator import A2AMessageValidator

            # Check if A2A validation is available
            if not A2AMessageValidator.is_a2a_validation_available():
                return {
                    "success": False,
                    "error": "A2A validation unavailable - install a2a-sdk>=0.1.0",
                    "recommendation": "pip install a2a-sdk>=0.1.0",
                }

            # A2A SDK should be framework-agnostic - let it handle different implementations
            # The universal a2a-sdk client should work with both Google ADK and AWS Strands

            validator = A2AMessageValidator(timeout=timeout)
            return await validator.validate_agent_a2a_protocol(port)

        except ImportError as e:
            return {
                "success": False,
                "error": f"A2A validation module import failed: {e}",
                "recommendation": "Ensure a2a-sdk is properly installed",
            }
        except Exception as e:
            logger.error(f"A2A protocol testing failed: {e}")
            return {
                "success": False,
                "error": f"A2A validation failed: {e}",
                "details": {"error_type": type(e).__name__},
            }

    def register_with_helmsman(
        self,
        metadata: AgentMetadata,
        port: int,
        agent_path: str,
        helmsman_url: str = "http://localhost:7080",
        agent_id: Optional[str] = None,
        environment: str = "development",
    ) -> Dict[str, Any]:
        """
        Register agent with Helmsman service.

        Args:
            metadata: Agent metadata
            port: Port where agent is running
            helmsman_url: Helmsman service URL
            agent_id: Custom agent identifier
            environment: Deployment environment

        Returns:
            Dict with registration results
        """
        logger.info("Step 8: Helmsman Registration")

        try:
            # Create Helmsman client
            client = HelsmanClient(base_url=helmsman_url)

            # Check if Helmsman is available
            if not client.health_check():
                raise RuntimeError(
                    f"Helmsman service not available at {helmsman_url}. "
                    f"Please verify:\n"
                    f"  1. Helmsman is running and accessible\n"
                    f"  2. Health endpoint responds: {helmsman_url}/api/health\n"
                    f"  3. Network connectivity allows access to {helmsman_url}"
                )

            # Create registration
            root_url = f"http://localhost:{port}"
            container_name = (
                f"{metadata.name.lower().replace('_', '-').replace(' ', '-')}-agent"
            )
            docker_endpoint = f"http://{container_name}:{port}"

            registration = create_helmsman_registration(
                metadata=metadata,
                root_url=root_url,
                docker_endpoint=docker_endpoint,
                agent_id=agent_id,
                environment=environment,
            )

            # Register with Helmsman
            response = client.register_agent(registration)

            # Update context with Helmsman registration info
            context_manager = AgentContextManager(Path(agent_path))
            context_manager.update_build_info(
                helmsman_agent_id=response.get("id"), helmsman_url=helmsman_url
            )

            return {
                "success": True,
                "agent_name": registration.name,
                "helmsman_url": helmsman_url,
                "root_url": root_url,
                "registration_response": response,
            }

        except Exception as e:
            logger.error(f"Helmsman registration failed: {e}")
            return {"error": str(e), "helmsman_url": helmsman_url}

    def run_full_pipeline(
        self,
        agent_path: str,
        output_dir: Optional[str] = None,
        port: int = 8080,
        build: bool = True,
        run: bool = True,
        helmsman_enabled: bool = False,
        helmsman_url: str = "http://localhost:7080",
        agent_id: Optional[str] = None,
        environment: str = "development",
        add_ui: bool = False,
        skip_a2a_test: bool = False,
        a2a_test_timeout: int = 30,
        base_image: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the complete pipeline from detection to deployment.

        Args:
            agent_path: Path to agent directory
            output_dir: Output directory for build artifacts
            port: Port to run container on

        Returns:
            Dict with results from each step
        """
        results: Dict[str, Any] = {"success": False, "steps": {}}
        agent_path_obj = Path(agent_path)

        try:
            # Step 0: Check port availability early
            logger.info("Step 0: Port Availability Check")
            if not PortChecker.is_port_available(port):
                port_info = PortChecker.get_port_info(port)
                error_msg = f"Port {port} is not available"
                if port_info.get("status") == "in_use":
                    error_msg += " (already in use)"
                elif port_info.get("status") == "permission_denied":
                    error_msg += " (permission denied - try a port > 1024)"

                # Suggest alternative ports
                alternative_port = PortChecker.find_available_port(port + 1, port + 100)
                if alternative_port:
                    error_msg += f". Try --port {alternative_port}"

                results["steps"]["port_check"] = {
                    "error": error_msg,
                    "port_info": port_info,
                    "suggested_port": alternative_port,
                }
                return results

            results["steps"]["port_check"] = {
                "success": True,
                "port": port,
                "status": "available",
            }

            # Initialize context manager for tracking
            context_manager = AgentContextManager(agent_path_obj)
            # Step 1: Detect framework
            logger.info("Step 1: Framework Detection")
            adapter = self.detect_framework(agent_path_obj)
            if not adapter:
                results["steps"]["detection"] = {
                    "error": "No supported framework detected"
                }
                return results

            # Store framework name for use in testing
            self.framework = adapter.framework_name

            # Load environment variables with priority order
            self.env_loader.load_env_with_priority(agent_path_obj)
            self.framework_env_vars = self.env_loader.get_all_env_vars()

            results["steps"]["detection"] = {
                "success": True,
                "framework": adapter.framework_name,
            }

            # Step 2: Validate agent
            logger.info("Step 2: Agent Validation")
            validation = self.validate_agent(agent_path_obj, adapter)
            if not validation.is_valid:
                results["steps"]["validation"] = {
                    "error": "Agent validation failed",
                    "errors": validation.errors,
                    "warnings": validation.warnings,
                }
                return results

            results["steps"]["validation"] = {
                "success": True,
                "warnings": validation.warnings,
            }

            # Step 3: Extract metadata
            logger.info("Step 3: Metadata Extraction")
            metadata = self.extract_metadata(agent_path_obj, adapter)
            results["steps"]["metadata"] = {
                "success": True,
                "agent_name": metadata.name,
                "framework": metadata.framework,
                "model": metadata.model,
            }

            # Update context with initial build information
            context_manager.update_build_info(
                agent_name=metadata.name,
                framework=metadata.framework,
                model=metadata.model,
                port=port,
                custom_agent_name=agent_id,  # Store CLI --agent-name override
            )

            # Step 4: Create Docker image (conditional)
            if build:
                logger.info("Step 4: Docker Image Creation")
                docker_info = self.create_docker_image(
                    agent_path_obj,
                    metadata,
                    Path(output_dir) if output_dir else None,
                    add_ui=add_ui,
                    port=port,
                    base_image=base_image,
                )
                results["steps"]["docker_build"] = {
                    "success": True,
                    "image_name": docker_info["image_name"],
                    "build_context": docker_info["build_context_path"],
                }
                image_name = docker_info["image_name"]

                # Update context with Docker build info
                context_manager.update_build_info(
                    image_name=image_name,
                    build_context_path=str(docker_info["build_context_path"]),
                )
            else:
                logger.info("Step 4: Skipping Docker Image Creation (--no-build)")
                results["steps"]["docker_build"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "--no-build flag",
                }
                # Assume image exists with standard naming
                image_name = f"{metadata.name.lower().replace('_', '-')}-agent"

            # Step 5: Start container (conditional)
            if run:
                logger.info("Step 5: Container Startup")
                container_id = self.start_container(image_name, port, metadata.name)
                container_name = (
                    f"{metadata.name.lower().replace('_', '-').replace(' ', '-')}-agent"
                )
                results["steps"]["container_start"] = {
                    "success": True,
                    "container_id": container_id,
                    "port": port,
                    "container_name": container_name,
                }

                # Update context with container info
                context_manager.update_container_info(
                    container_name, container_id, port
                )

                # Step 6: Health check (only if running)
                logger.info("Step 6: Health Check")
                is_healthy = self.wait_for_container_health(port)
                if not is_healthy:
                    results["steps"]["health_check"] = {
                        "error": "Container health check failed"
                    }
                    return results

                results["steps"]["health_check"] = {"success": True}

                # Step 7: End-to-end test (only if running)
                logger.info("Step 7: End-to-End Test")
                test_results = self.test_agent_interaction(
                    port, skip_a2a_test, a2a_test_timeout
                )
                results["steps"]["e2e_test"] = {
                    "success": True,
                    "test_results": test_results,
                }
            else:
                logger.info("Step 5: Skipping Container Startup (--no-run)")
                results["steps"]["container_start"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "--no-run flag",
                }
                results["steps"]["health_check"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "--no-run flag",
                }
                results["steps"]["e2e_test"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "--no-run flag",
                }

            # Step 8: Helmsman registration (optional, requires running container)
            if helmsman_enabled and run:
                logger.info("Step 8: Helmsman Registration")
                helmsman_result = self.register_with_helmsman(
                    metadata=metadata,
                    port=port,
                    agent_path=agent_path,
                    helmsman_url=helmsman_url,
                    agent_id=agent_id,
                    environment=environment,
                )
            elif helmsman_enabled and not run:
                logger.info("Step 8: Skipping Helmsman Registration (requires --run)")
                results["steps"]["helmsman_registration"] = {
                    "success": True,
                    "skipped": True,
                    "reason": "Requires running container (--no-run was used)",
                }
                helmsman_result = None
            else:
                helmsman_result = None

            if helmsman_result:
                if "error" in helmsman_result:
                    # Helmsman registration failed, but don't fail the entire pipeline
                    results["steps"]["helmsman_registration"] = {
                        "error": helmsman_result["error"],
                        "helmsman_url": helmsman_result["helmsman_url"],
                    }
                    logger.warning(
                        f"Helmsman registration failed, but pipeline continues: {helmsman_result['error']}"
                    )
                else:
                    results["steps"]["helmsman_registration"] = {
                        "success": True,
                        "agent_name": helmsman_result["agent_name"],
                        "helmsman_url": helmsman_result["helmsman_url"],
                        "root_url": helmsman_result["root_url"],
                    }

                    # Update context with Helmsman info
                    if "agent_id" in helmsman_result:
                        context_manager.update_helmsman_info(
                            helmsman_result["agent_id"], helmsman_result["helmsman_url"]
                        )
                    logger.info("Agent successfully registered with Helmsman")

            results["success"] = True
            logger.info("Full pipeline completed successfully!")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["error"] = str(e)
            results["steps"]["error"] = {"error": str(e)}

        return results

    def _ensure_agent_gitignore(self, agent_path: Path) -> None:
        """Ensure agent directory has .gitignore for build artifacts.

        Args:
            agent_path: Path to agent directory
        """
        gitignore_path = agent_path / ".gitignore"
        gitignore_content = """# Any Agent Framework build artifacts
.any_agent/

# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so

# Environment files
.env
.env.local
.env.*.local

# IDE files
.vscode/
.idea/
*.swp
*.swo

# OS files
.DS_Store
Thumbs.db
"""

        if not gitignore_path.exists():
            gitignore_path.write_text(gitignore_content)
            logger.info(f"Created .gitignore in agent directory: {gitignore_path}")
        else:
            # Check if .any_agent/ is already in the .gitignore
            content = gitignore_path.read_text()
            if ".any_agent/" not in content:
                # Append the .any_agent/ entry
                with open(gitignore_path, "a") as f:
                    f.write("\n# Any Agent Framework build artifacts\n.any_agent/\n")
                logger.info(
                    f"Added .any_agent/ to existing .gitignore: {gitignore_path}"
                )
