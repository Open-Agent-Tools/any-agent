"""Agent removal functionality for cleaning up Docker and Helmsman artifacts."""

import docker
import logging
import psutil
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .agent_context import AgentContextManager, AgentBuildContext
from ..api.helmsman_integration import HelsmanClient

logger = logging.getLogger(__name__)


@dataclass
class RemovalReport:
    """Report of removal operation results."""

    success: bool
    agent_name: str
    containers_removed: int = 0
    containers_failed: int = 0
    images_removed: int = 0
    images_failed: int = 0
    helmsman_removed: int = 0
    helmsman_failed: int = 0
    build_contexts_removed: int = 0
    build_contexts_failed: int = 0
    localhost_servers_removed: int = 0
    localhost_servers_failed: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return (
            self.containers_removed
            + self.images_removed
            + self.helmsman_removed
            + self.build_contexts_removed
            + self.localhost_servers_removed
        )

    @property
    def total_failed(self) -> int:
        return (
            self.containers_failed
            + self.images_failed
            + self.helmsman_failed
            + self.build_contexts_failed
            + self.localhost_servers_failed
        )


@dataclass
class AgentArtifacts:
    """Collection of agent artifacts found for removal."""

    containers: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    helmsman_records: List[Dict[str, Any]]
    build_contexts: List[Path]
    localhost_servers: List[Dict[str, Any]]
    context_info: Optional[AgentBuildContext] = None

    @property
    def has_artifacts(self) -> bool:
        return bool(
            self.containers
            or self.images
            or self.helmsman_records
            or self.build_contexts
            or self.localhost_servers
        )

    @property
    def summary(self) -> Dict[str, int]:
        return {
            "containers": len(self.containers),
            "images": len(self.images),
            "helmsman_records": len(self.helmsman_records),
            "build_contexts": len(self.build_contexts),
            "localhost_servers": len(self.localhost_servers),
        }


class AgentRemover:
    """Handles removal of all agent artifacts from Docker and Helmsman."""

    def __init__(self):
        """Initialize the agent remover."""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Failed to connect to Docker: {e}")
            self.docker_client = None

        self.helmsman_client = HelsmanClient()

    def find_agent_artifacts(
        self, agent_name: str, context_manager: Optional[AgentContextManager] = None
    ) -> AgentArtifacts:
        """
        Find all artifacts associated with an agent.

        Args:
            agent_name: Name of the agent to find artifacts for
            context_manager: Optional context manager for precise artifact tracking

        Returns:
            AgentArtifacts containing all found artifacts
        """
        artifacts = AgentArtifacts(
            containers=[],
            images=[],
            helmsman_records=[],
            build_contexts=[],
            localhost_servers=[],
        )

        # Try to get context information first
        context_info = None
        if context_manager:
            context_info = context_manager.load_context()
            artifacts.context_info = context_info

        # Find Docker containers
        if self.docker_client:
            artifacts.containers = self._find_containers(agent_name, context_info)
            artifacts.images = self._find_images(agent_name, context_info)

        # Find Helmsman records
        artifacts.helmsman_records = self._find_helmsman_records(
            agent_name, context_info
        )

        # Find build contexts
        artifacts.build_contexts = self._find_build_contexts(agent_name, context_info)

        # Find localhost development servers
        artifacts.localhost_servers = self._find_localhost_servers(
            agent_name, context_info
        )

        return artifacts

    def _find_containers(
        self, agent_name: str, context: Optional[AgentBuildContext]
    ) -> List[Dict[str, Any]]:
        """Find all containers associated with the agent."""
        containers: List[Dict[str, Any]] = []

        if not self.docker_client:
            return containers

        try:
            # If we have context, look for specific container first
            if context and context.container_id:
                try:
                    container = self.docker_client.containers.get(context.container_id)
                    containers.append(
                        {
                            "id": container.id,
                            "name": container.name,
                            "status": container.status,
                            "source": "context",
                        }
                    )
                except docker.errors.NotFound:
                    logger.debug(
                        f"Container {context.container_id} from context not found"
                    )

            # Also search by naming pattern to catch any variations
            pattern = f"{agent_name.lower().replace('_', '-')}-agent"
            all_containers = self.docker_client.containers.list(all=True)

            for container in all_containers:
                if pattern in container.name.lower():
                    # Avoid duplicates if we already found it via context
                    if not any(c["id"] == container.id for c in containers):
                        containers.append(
                            {
                                "id": container.id,
                                "name": container.name,
                                "status": container.status,
                                "source": "pattern_match",
                            }
                        )

        except Exception as e:
            logger.error(f"Error finding containers for {agent_name}: {e}")

        return containers

    def _find_images(
        self, agent_name: str, context: Optional[AgentBuildContext]
    ) -> List[Dict[str, Any]]:
        """Find all images associated with the agent."""
        images: List[Dict[str, Any]] = []

        if not self.docker_client:
            return images

        try:
            # If we have context, look for specific image first
            if context and context.image_id:
                try:
                    image = self.docker_client.images.get(context.image_id)
                    images.append(
                        {
                            "id": image.id,
                            "tags": image.tags,
                            "size": getattr(image.attrs, "Size", 0),
                            "source": "context",
                        }
                    )
                except docker.errors.ImageNotFound:
                    logger.debug(f"Image {context.image_id} from context not found")

            # Also search by naming pattern
            pattern = f"{agent_name.lower().replace('_', '-')}-agent"
            all_images = self.docker_client.images.list()

            for image in all_images:
                for tag in image.tags:
                    if pattern in tag.lower():
                        # Avoid duplicates
                        if not any(img["id"] == image.id for img in images):
                            images.append(
                                {
                                    "id": image.id,
                                    "tags": image.tags,
                                    "size": getattr(image.attrs, "Size", 0),
                                    "source": "pattern_match",
                                }
                            )
                            break

        except Exception as e:
            logger.error(f"Error finding images for {agent_name}: {e}")

        return images

    def _find_helmsman_records(
        self, agent_name: str, context: Optional[AgentBuildContext]
    ) -> List[Dict[str, Any]]:
        """Find all Helmsman records associated with the agent."""
        records = []

        try:
            # If we have context, look for specific registration first
            if context and context.helmsman_agent_id:
                try:
                    # Try to get specific agent by ID
                    agent_info = self.helmsman_client.get_agent(
                        context.helmsman_agent_id
                    )
                    if agent_info:
                        records.append(
                            {
                                "id": agent_info["id"],
                                "name": agent_info["name"],
                                "status": agent_info.get("status", "unknown"),
                                "source": "context",
                            }
                        )
                except Exception as e:
                    logger.debug(
                        f"Helmsman agent {context.helmsman_agent_id} from context not found: {e}"
                    )

            # Also search by agent name to catch any variations
            all_agents = self.helmsman_client.list_agents()
            if all_agents:
                for agent in all_agents.get("agents", []):
                    if agent.get("name") == agent_name:
                        # Avoid duplicates
                        if not any(r["id"] == agent["id"] for r in records):
                            records.append(
                                {
                                    "id": agent["id"],
                                    "name": agent["name"],
                                    "status": agent.get("status", "unknown"),
                                    "source": "name_match",
                                }
                            )

        except Exception as e:
            logger.error(f"Error finding Helmsman records for {agent_name}: {e}")

        return records

    def _find_build_contexts(
        self, agent_name: str, context: Optional[AgentBuildContext]
    ) -> List[Path]:
        """Find build context directories that can be cleaned up."""
        contexts = []

        try:
            # Check context-specific path first
            if context and context.build_context_path:
                path = Path(context.build_context_path)
                if path.exists():
                    contexts.append(path)

            # Also check common temporary locations
            temp_patterns = [
                f"/tmp/{agent_name}-docker-context",
                f"/tmp/{agent_name.lower().replace('_', '-')}-docker-context",
            ]

            for pattern in temp_patterns:
                path = Path(pattern)
                if path.exists() and path not in contexts:
                    contexts.append(path)

        except Exception as e:
            logger.error(f"Error finding build contexts for {agent_name}: {e}")

        return contexts

    def _find_localhost_servers(
        self, agent_name: str, context: Optional[AgentBuildContext]
    ) -> List[Dict[str, Any]]:
        """Find localhost development servers running for the agent."""
        servers = []

        try:
            # Search for uvicorn processes that match the agent
            for proc in psutil.process_iter(["pid", "name", "cmdline", "cwd"]):
                try:
                    proc_info = proc.info

                    # Skip if not a Python process or no cmdline
                    if not proc_info["cmdline"]:
                        continue

                    cmdline = " ".join(proc_info["cmdline"])

                    # Look for uvicorn processes running localhost_app
                    if "uvicorn" in cmdline and "localhost_app:app" in cmdline:
                        # Check if it's related to our agent by examining the working directory
                        cwd = proc_info.get("cwd")
                        if cwd:
                            cwd_path = Path(cwd)
                            # Check if the working directory contains the agent name or is in .any_agent
                            if agent_name.lower() in str(
                                cwd_path
                            ).lower() or ".any_agent" in str(cwd_path):
                                # Extract port from command line
                                port = None
                                try:
                                    cmdline_parts = proc_info["cmdline"]
                                    if "--port" in cmdline_parts:
                                        port_idx = cmdline_parts.index("--port")
                                        if port_idx + 1 < len(cmdline_parts):
                                            port = int(cmdline_parts[port_idx + 1])
                                except (ValueError, IndexError):
                                    pass

                                servers.append(
                                    {
                                        "pid": proc_info["pid"],
                                        "name": proc_info.get("name", "python"),
                                        "cmdline": cmdline,
                                        "cwd": cwd,
                                        "port": port,
                                        "source": "process_scan",
                                    }
                                )

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
                    # Process may have disappeared or be inaccessible
                    continue

        except Exception as e:
            logger.error(f"Error finding localhost servers for {agent_name}: {e}")

        return servers

    def remove_agent(
        self,
        agent_name: str,
        context_manager: Optional[AgentContextManager] = None,
        dry_run: bool = False,
    ) -> RemovalReport:
        """
        Remove all traces of an agent.

        Args:
            agent_name: Name of the agent to remove
            context_manager: Optional context manager for tracking
            dry_run: If True, only report what would be removed

        Returns:
            RemovalReport with detailed results
        """
        report = RemovalReport(success=False, agent_name=agent_name)

        # Find all artifacts
        artifacts = self.find_agent_artifacts(agent_name, context_manager)

        if not artifacts.has_artifacts:
            report.warnings.append(f"No artifacts found for agent '{agent_name}'")
            report.success = True
            return report

        if dry_run:
            # Just report what would be removed
            report.success = True
            return report

        # Remove containers
        removal_log: List[Dict[str, Any]] = []
        for container_info in artifacts.containers:
            self._remove_container(container_info, report, removal_log)

        # Remove images
        for image_info in artifacts.images:
            self._remove_image(image_info, report, removal_log)

        # Remove Helmsman records
        for record in artifacts.helmsman_records:
            self._remove_helmsman_record(record, report, removal_log)

        # Remove build contexts
        for context_path in artifacts.build_contexts:
            self._remove_build_context(context_path, report, removal_log)

        # Remove localhost development servers
        for server_info in artifacts.localhost_servers:
            self._remove_localhost_server(server_info, report, removal_log)

        # Update context file
        if context_manager:
            try:
                context_manager.mark_removed(removal_log)
                removal_log.append(
                    {
                        "type": "context_update",
                        "status": "success",
                        "message": "Updated context file with removal status",
                    }
                )
            except Exception as e:
                report.warnings.append(f"Failed to update context file: {e}")
                removal_log.append(
                    {"type": "context_update", "status": "failed", "error": str(e)}
                )

        # Determine overall success
        report.success = report.total_removed > 0 or report.total_failed == 0

        return report

    def _remove_container(
        self, container_info: Dict[str, Any], report: RemovalReport, log: List[Dict]
    ) -> bool:
        """Remove a single container."""
        container_id = container_info["id"]
        container_name = container_info["name"]

        try:
            if not self.docker_client:
                raise Exception("Docker client not available")

            container = self.docker_client.containers.get(container_id)

            # Stop if running
            if container.status == "running":
                container.stop(timeout=10)
                log.append(
                    {
                        "type": "container_stop",
                        "id": container_id,
                        "name": container_name,
                        "status": "success",
                    }
                )

            # Remove container
            container.remove()
            report.containers_removed += 1
            log.append(
                {
                    "type": "container_remove",
                    "id": container_id,
                    "name": container_name,
                    "status": "success",
                }
            )
            return True

        except Exception as e:
            error_msg = f"Failed to remove container {container_name}: {e}"
            report.errors.append(error_msg)
            report.containers_failed += 1
            log.append(
                {
                    "type": "container_remove",
                    "id": container_id,
                    "name": container_name,
                    "status": "failed",
                    "error": str(e),
                }
            )
            return False

    def _remove_image(
        self, image_info: Dict[str, Any], report: RemovalReport, log: List[Dict]
    ) -> bool:
        """Remove a single image."""
        image_id = image_info["id"]
        image_tags = image_info.get("tags", [])

        try:
            if not self.docker_client:
                raise Exception("Docker client not available")

            self.docker_client.images.remove(image_id, force=True)
            report.images_removed += 1
            log.append(
                {
                    "type": "image_remove",
                    "id": image_id,
                    "tags": image_tags,
                    "status": "success",
                }
            )
            return True

        except Exception as e:
            error_msg = f"Failed to remove image {image_id}: {e}"
            report.errors.append(error_msg)
            report.images_failed += 1
            log.append(
                {
                    "type": "image_remove",
                    "id": image_id,
                    "tags": image_tags,
                    "status": "failed",
                    "error": str(e),
                }
            )
            return False

    def _remove_helmsman_record(
        self, record: Dict[str, Any], report: RemovalReport, log: List[Dict]
    ) -> bool:
        """Remove a Helmsman registration."""
        agent_id = record["id"]
        agent_name = record["name"]

        try:
            success = self.helmsman_client.delete_agent(agent_id)
            if success:
                report.helmsman_removed += 1
                log.append(
                    {
                        "type": "helmsman_remove",
                        "id": agent_id,
                        "name": agent_name,
                        "status": "success",
                    }
                )
                return True
            else:
                raise Exception("Delete operation returned false")

        except Exception as e:
            error_msg = f"Failed to remove Helmsman record {agent_name}: {e}"
            report.errors.append(error_msg)
            report.helmsman_failed += 1
            log.append(
                {
                    "type": "helmsman_remove",
                    "id": agent_id,
                    "name": agent_name,
                    "status": "failed",
                    "error": str(e),
                }
            )
            return False

    def _remove_build_context(
        self, context_path: Path, report: RemovalReport, log: List[Dict]
    ) -> bool:
        """Remove a build context directory."""
        try:
            if context_path.is_dir():
                shutil.rmtree(context_path)
                report.build_contexts_removed += 1
                log.append(
                    {
                        "type": "build_context_remove",
                        "path": str(context_path),
                        "status": "success",
                    }
                )
                return True
            else:
                report.warnings.append(
                    f"Build context path is not a directory: {context_path}"
                )
                return False

        except Exception as e:
            error_msg = f"Failed to remove build context {context_path}: {e}"
            report.errors.append(error_msg)
            report.build_contexts_failed += 1
            log.append(
                {
                    "type": "build_context_remove",
                    "path": str(context_path),
                    "status": "failed",
                    "error": str(e),
                }
            )
            return False

    def _remove_localhost_server(
        self, server_info: Dict[str, Any], report: RemovalReport, log: List[Dict]
    ) -> bool:
        """Remove a localhost development server."""
        pid = server_info["pid"]
        port = server_info.get("port", "unknown")
        cmdline = server_info.get("cmdline", "")

        try:
            # Try to get the process and terminate it gracefully
            proc = psutil.Process(pid)

            # First try graceful termination
            proc.terminate()

            # Wait up to 5 seconds for graceful shutdown
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                # If it doesn't terminate gracefully, force kill
                proc.kill()
                proc.wait(timeout=2)

            report.localhost_servers_removed += 1
            log.append(
                {
                    "type": "localhost_server_remove",
                    "pid": pid,
                    "port": port,
                    "cmdline": cmdline,
                    "status": "success",
                }
            )
            return True

        except psutil.NoSuchProcess:
            # Process already dead
            report.localhost_servers_removed += 1
            log.append(
                {
                    "type": "localhost_server_remove",
                    "pid": pid,
                    "port": port,
                    "cmdline": cmdline,
                    "status": "success",
                    "message": "Process already terminated",
                }
            )
            return True

        except Exception as e:
            error_msg = (
                f"Failed to remove localhost server (PID {pid}, port {port}): {e}"
            )
            report.errors.append(error_msg)
            report.localhost_servers_failed += 1
            log.append(
                {
                    "type": "localhost_server_remove",
                    "pid": pid,
                    "port": port,
                    "cmdline": cmdline,
                    "status": "failed",
                    "error": str(e),
                }
            )
            return False
