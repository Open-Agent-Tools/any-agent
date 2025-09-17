"""Agent removal functionality for cleaning up Docker and Helmsman artifacts."""

import docker
import logging
import psutil
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .agent_context import AgentContextManager, AgentBuildContext, LocalhostServerInfo, DockerInstanceInfo
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
        Find all artifacts associated with an agent using ONLY context information.
        No more risky process scanning or pattern matching.

        Args:
            agent_name: Name of the agent to find artifacts for
            context_manager: Context manager for precise artifact tracking (required)

        Returns:
            AgentArtifacts containing all found artifacts from context
        """
        artifacts = AgentArtifacts(
            containers=[],
            images=[],
            helmsman_records=[],
            build_contexts=[],
            localhost_servers=[],
        )

        # Context is now REQUIRED for safe removal
        if not context_manager:
            logger.warning("No context manager provided - cannot safely identify artifacts")
            return artifacts

        context_info = context_manager.load_context()
        if not context_info:
            logger.warning("No context found - no artifacts to remove")
            return artifacts

        artifacts.context_info = context_info

        # Use ONLY context information for safe, precise targeting
        artifacts.containers = self._find_containers_from_context(context_info)
        artifacts.images = self._find_images_from_context(context_info)
        artifacts.helmsman_records = self._find_helmsman_records_from_context(context_info)
        artifacts.build_contexts = self._find_build_contexts_from_context(context_info)
        artifacts.localhost_servers = self._find_localhost_servers_from_context(context_info)

        return artifacts

    def _find_containers_from_context(
        self, context: AgentBuildContext
    ) -> List[Dict[str, Any]]:
        """Find containers using ONLY context information."""
        containers: List[Dict[str, Any]] = []

        if not self.docker_client:
            return containers

        try:
            # Check multi-instance Docker containers first
            if context.docker_instances:
                for docker_info in context.docker_instances:
                    try:
                        container = self.docker_client.containers.get(docker_info.container_id)
                        containers.append(
                            {
                                "id": container.id,
                                "name": container.name,
                                "status": container.status,
                                "source": "context_docker_instances",
                                "port": docker_info.port,
                            }
                        )
                    except docker.errors.NotFound:
                        logger.warning(f"Container {docker_info.container_id} (port {docker_info.port}) from context not found")

            # Check legacy single Docker instance (for backward compatibility)
            elif context.docker_instance:
                try:
                    container = self.docker_client.containers.get(context.docker_instance.container_id)
                    containers.append(
                        {
                            "id": container.id,
                            "name": container.name,
                            "status": container.status,
                            "source": "context_docker_instance",
                            "port": context.docker_instance.port,
                        }
                    )
                except docker.errors.NotFound:
                    logger.warning(
                        f"Container {context.docker_instance.container_id} from context not found"
                    )
            # Fallback to legacy context fields
            elif context.container_id:
                try:
                    container = self.docker_client.containers.get(context.container_id)
                    containers.append(
                        {
                            "id": container.id,
                            "name": container.name,
                            "status": container.status,
                            "source": "context_legacy",
                            "port": context.port,
                        }
                    )
                except docker.errors.NotFound:
                    logger.warning(
                        f"Container {context.container_id} from legacy context not found"
                    )

        except Exception as e:
            logger.error(f"Error finding containers from context: {e}")

        return containers

    def _find_images_from_context(
        self, context: AgentBuildContext
    ) -> List[Dict[str, Any]]:
        """Find images using ONLY context information."""
        images: List[Dict[str, Any]] = []

        if not self.docker_client:
            return images

        try:
            # Check multi-instance Docker images first
            if context.docker_instances:
                for docker_info in context.docker_instances:
                    try:
                        image = self.docker_client.images.get(docker_info.image_id)
                        images.append(
                            {
                                "id": image.id,
                                "tags": image.tags,
                                "size": getattr(image.attrs, "Size", 0),
                                "source": "context_docker_instances",
                                "port": docker_info.port,
                            }
                        )
                    except docker.errors.ImageNotFound:
                        logger.warning(f"Image {docker_info.image_id} (port {docker_info.port}) from context not found")

            # Check legacy single Docker instance (for backward compatibility)
            elif context.docker_instance:
                try:
                    image = self.docker_client.images.get(context.docker_instance.image_id)
                    images.append(
                        {
                            "id": image.id,
                            "tags": image.tags,
                            "size": getattr(image.attrs, "Size", 0),
                            "source": "context_docker_instance",
                            "port": context.docker_instance.port,
                        }
                    )
                except docker.errors.ImageNotFound:
                    logger.warning(
                        f"Image {context.docker_instance.image_id} from context not found"
                    )
            # Fallback to legacy context fields
            elif context.image_id:
                try:
                    image = self.docker_client.images.get(context.image_id)
                    images.append(
                        {
                            "id": image.id,
                            "tags": image.tags,
                            "size": getattr(image.attrs, "Size", 0),
                            "source": "context_legacy",
                            "port": context.port,
                        }
                    )
                except docker.errors.ImageNotFound:
                    logger.warning(f"Image {context.image_id} from legacy context not found")

        except Exception as e:
            logger.error(f"Error finding images from context: {e}")

        return images

    def _find_helmsman_records_from_context(
        self, context: AgentBuildContext
    ) -> List[Dict[str, Any]]:
        """Find Helmsman records using ONLY context information."""
        records = []

        try:
            # Use only context information
            if context.helmsman_agent_id:
                try:
                    # Try to get specific agent by ID from context
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
                    logger.warning(
                        f"Helmsman agent {context.helmsman_agent_id} from context not found: {e}"
                    )

        except Exception as e:
            logger.error(f"Error finding Helmsman records from context: {e}")

        return records

    def _find_build_contexts_from_context(
        self, context: AgentBuildContext
    ) -> List[Path]:
        """Find build context directories using ONLY context information."""
        contexts = []

        try:
            # Use only context information
            if context.build_context_path:
                path = Path(context.build_context_path)
                if path.exists():
                    contexts.append(path)
                else:
                    logger.warning(f"Build context path from context does not exist: {path}")

        except Exception as e:
            logger.error(f"Error finding build contexts from context: {e}")

        return contexts

    def _find_localhost_servers_from_context(
        self, context: AgentBuildContext
    ) -> List[Dict[str, Any]]:
        """Find localhost servers using ONLY context information - no process scanning."""
        servers = []

        try:
            # Check multi-instance localhost servers first
            if context.localhost_servers:
                for server_info in context.localhost_servers:
                    try:
                        proc = psutil.Process(server_info.pid)
                        if proc.is_running():
                            servers.append(
                                {
                                    "pid": server_info.pid,
                                    "name": "uvicorn",
                                    "cmdline": server_info.command_line or f"uvicorn localhost_app:app --port {server_info.port}",
                                    "cwd": server_info.working_directory,
                                    "port": server_info.port,
                                    "source": "context_localhost_servers",
                                }
                            )
                        else:
                            logger.info(f"Process {server_info.pid} (port {server_info.port}) from context is no longer running")
                    except psutil.NoSuchProcess:
                        logger.info(f"Process {server_info.pid} (port {server_info.port}) from context no longer exists")

            # Check legacy single localhost server (for backward compatibility)
            elif context.localhost_server:
                try:
                    proc = psutil.Process(context.localhost_server.pid)
                    if proc.is_running():
                        servers.append(
                            {
                                "pid": context.localhost_server.pid,
                                "name": "uvicorn",
                                "cmdline": context.localhost_server.command_line or f"uvicorn localhost_app:app --port {context.localhost_server.port}",
                                "cwd": context.localhost_server.working_directory,
                                "port": context.localhost_server.port,
                                "source": "context_localhost_server",
                            }
                        )
                    else:
                        logger.info(f"Process {context.localhost_server.pid} from context is no longer running")
                except psutil.NoSuchProcess:
                    logger.info(f"Process {context.localhost_server.pid} from context no longer exists")

        except Exception as e:
            logger.error(f"Error finding localhost servers from context: {e}")

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
