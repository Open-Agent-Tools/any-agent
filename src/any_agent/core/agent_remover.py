"""Agent removal functionality for cleaning up Docker artifacts (Helmsman-free version)."""

import docker
import logging
import psutil
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from .agent_context import (
    AgentContextManager,
    AgentBuildContext,
)

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
            + self.build_contexts_removed
            + self.localhost_servers_removed
        )

    @property
    def total_failed(self) -> int:
        return (
            self.containers_failed
            + self.images_failed
            + self.build_contexts_failed
            + self.localhost_servers_failed
        )


@dataclass
class AgentArtifacts:
    """Collection of agent artifacts found for removal."""

    containers: List[Dict[str, Any]]
    images: List[Dict[str, Any]]
    build_contexts: List[Path]
    localhost_servers: List[Dict[str, Any]]
    context_info: Optional[AgentBuildContext] = None

    @property
    def has_artifacts(self) -> bool:
        return bool(
            self.containers
            or self.images
            or self.build_contexts
            or self.localhost_servers
        )

    @property
    def summary(self) -> Dict[str, int]:
        return {
            "containers": len(self.containers),
            "images": len(self.images),
            "build_contexts": len(self.build_contexts),
            "localhost_servers": len(self.localhost_servers),
        }


class AgentRemover:
    """Handles removal of all agent artifacts from Docker (Helmsman-free version)."""

    def __init__(self):
        """Initialize the agent remover."""
        try:
            self.docker_client = docker.from_env()
        except Exception as e:
            logger.warning(f"Failed to connect to Docker: {e}")
            self.docker_client = None

    def find_agent_artifacts(self, agent_name: str, context_manager: Optional[AgentContextManager]) -> AgentArtifacts:
        """Find all artifacts associated with an agent."""
        containers = []
        images = []
        build_contexts = []
        localhost_servers = []
        context_info = None

        # Load context if available
        if context_manager:
            context_info = context_manager.load_context()

        # Find containers from context
        containers.extend(self._find_containers_from_context(agent_name, context_info))

        # Find images from context
        images.extend(self._find_images_from_context(agent_name, context_info))

        # Find build contexts from context
        build_contexts.extend(self._find_build_contexts_from_context(agent_name, context_info))

        # Find localhost servers from context
        localhost_servers.extend(self._find_localhost_servers_from_context(agent_name, context_info))

        # Also search Docker directly by name patterns
        containers.extend(self._find_containers_by_name(agent_name))
        images.extend(self._find_images_by_name(agent_name))

        return AgentArtifacts(
            containers=containers,
            images=images,
            build_contexts=build_contexts,
            localhost_servers=localhost_servers,
            context_info=context_info,
        )

    def _find_containers_from_context(self, agent_name: str, context: Optional[AgentBuildContext]) -> List[Dict[str, Any]]:
        """Find containers from agent context."""
        containers = []
        if not context or not self.docker_client:
            return containers

        try:
            # Check top-level container_id field first
            if hasattr(context, 'container_id') and context.container_id:
                try:
                    container = self.docker_client.containers.get(context.container_id)
                    containers.append({
                        "id": container.id,
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    })
                except docker.errors.NotFound:
                    logger.warning(f"Container {context.container_id} from context not found")

            # Check multi-instance containers
            for instance in context.docker_instances:
                if instance.container_id:
                    try:
                        container = self.docker_client.containers.get(instance.container_id)
                        containers.append({
                            "id": container.id,
                            "name": container.name,
                            "status": container.status,
                            "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                        })
                    except docker.errors.NotFound:
                        logger.warning(f"Container {instance.container_id} from context not found")

            # Check legacy single instance
            if context.docker_instance and context.docker_instance.container_id:
                try:
                    container = self.docker_client.containers.get(context.docker_instance.container_id)
                    containers.append({
                        "id": container.id,
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    })
                except docker.errors.NotFound:
                    logger.warning(f"Container {context.docker_instance.container_id} from context not found")

        except Exception as e:
            logger.warning(f"Error finding containers from context: {e}")

        return containers

    def _find_images_from_context(self, agent_name: str, context: Optional[AgentBuildContext]) -> List[Dict[str, Any]]:
        """Find images from agent context."""
        images = []
        if not context or not self.docker_client:
            return images

        try:
            # Check top-level image_name field first (images are found by name, not ID)
            if hasattr(context, 'image_name') and context.image_name:
                try:
                    image = self.docker_client.images.get(context.image_name)
                    images.append({
                        "id": image.id,
                        "tags": image.tags,
                        "size": image.attrs.get("Size", 0),
                    })
                except docker.errors.ImageNotFound:
                    logger.warning(f"Image {context.image_name} from context not found")

            # Check multi-instance images
            for instance in context.docker_instances:
                if instance.image_id:
                    try:
                        image = self.docker_client.images.get(instance.image_id)
                        images.append({
                            "id": image.id,
                            "tags": image.tags,
                            "size": image.attrs.get("Size", 0),
                        })
                    except docker.errors.ImageNotFound:
                        logger.warning(f"Image {instance.image_id} from context not found")

            # Check legacy single instance
            if context.docker_instance and context.docker_instance.image_id:
                try:
                    image = self.docker_client.images.get(context.docker_instance.image_id)
                    images.append({
                        "id": image.id,
                        "tags": image.tags,
                        "size": image.attrs.get("Size", 0),
                    })
                except docker.errors.ImageNotFound:
                    logger.warning(f"Image {context.docker_instance.image_id} from context not found")

        except Exception as e:
            logger.warning(f"Error finding images from context: {e}")

        return images

    def _find_build_contexts_from_context(self, agent_name: str, context: Optional[AgentBuildContext]) -> List[Path]:
        """Find build contexts from agent context."""
        build_contexts = []
        if not context:
            return build_contexts

        if context.build_context_path and Path(context.build_context_path).exists():
            build_contexts.append(Path(context.build_context_path))

        return build_contexts

    def _find_localhost_servers_from_context(self, agent_name: str, context: Optional[AgentBuildContext]) -> List[Dict[str, Any]]:
        """Find localhost servers from agent context."""
        servers = []
        if not context:
            return servers

        try:
            # Check multi-instance servers
            for server in context.localhost_servers:
                if server.pid and psutil.pid_exists(server.pid):
                    try:
                        process = psutil.Process(server.pid)
                        servers.append({
                            "pid": server.pid,
                            "port": server.port,
                            "status": process.status(),
                            "command": " ".join(process.cmdline()[:3]) + "..." if process.cmdline() else "unknown",
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        logger.warning(f"Process {server.pid} from context not accessible")

            # Check legacy single server
            if context.localhost_server and context.localhost_server.pid:
                if psutil.pid_exists(context.localhost_server.pid):
                    try:
                        process = psutil.Process(context.localhost_server.pid)
                        servers.append({
                            "pid": context.localhost_server.pid,
                            "port": context.localhost_server.port,
                            "status": process.status(),
                            "command": " ".join(process.cmdline()[:3]) + "..." if process.cmdline() else "unknown",
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        logger.warning(f"Process {context.localhost_server.pid} from context not accessible")

        except Exception as e:
            logger.warning(f"Error finding localhost servers from context: {e}")

        return servers

    def _find_containers_by_name(self, agent_name: str) -> List[Dict[str, Any]]:
        """Find containers by name patterns."""
        containers = []
        if not self.docker_client:
            return containers

        try:
            all_containers = self.docker_client.containers.list(all=True)
            for container in all_containers:
                if self._is_agent_container(container, agent_name):
                    containers.append({
                        "id": container.id,
                        "name": container.name,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else container.image.id[:12],
                    })
        except Exception as e:
            logger.warning(f"Error finding containers by name: {e}")

        return containers

    def _find_images_by_name(self, agent_name: str) -> List[Dict[str, Any]]:
        """Find images by name patterns."""
        images = []
        if not self.docker_client:
            return images

        try:
            all_images = self.docker_client.images.list()
            for image in all_images:
                if self._is_agent_image(image, agent_name):
                    images.append({
                        "id": image.id,
                        "tags": image.tags,
                        "size": image.attrs.get("Size", 0),
                    })
        except Exception as e:
            logger.warning(f"Error finding images by name: {e}")

        return images

    def _is_agent_container(self, container, agent_name: str) -> bool:
        """Check if container belongs to the agent."""
        # Check container name
        if agent_name.lower() in container.name.lower():
            return True

        # Check image tags
        if container.image.tags:
            for tag in container.image.tags:
                if agent_name.lower() in tag.lower():
                    return True

        return False

    def _is_agent_image(self, image, agent_name: str) -> bool:
        """Check if image belongs to the agent."""
        if not image.tags:
            return False

        for tag in image.tags:
            if agent_name.lower() in tag.lower():
                return True

        return False

    def remove_agent(self, agent_name: str, context_manager: Optional[AgentContextManager], force: bool = False) -> RemovalReport:
        """Remove all agent artifacts and return detailed report."""
        report = RemovalReport(success=True, agent_name=agent_name)

        # Find all artifacts first
        artifacts = self.find_agent_artifacts(agent_name, context_manager)

        # Remove containers
        for container in artifacts.containers:
            try:
                if self.docker_client:
                    docker_container = self.docker_client.containers.get(container["id"])
                    docker_container.stop(timeout=10)
                    docker_container.remove(force=force)
                    report.containers_removed += 1
                    logger.info(f"Removed container: {container['name']}")
                else:
                    raise Exception("Docker client not available")
            except Exception as e:
                report.containers_failed += 1
                report.errors.append(f"Failed to remove container {container['name']}: {e}")
                report.success = False

        # Remove images
        for image in artifacts.images:
            try:
                if self.docker_client:
                    self.docker_client.images.remove(image["id"], force=force)
                    report.images_removed += 1
                    logger.info(f"Removed image: {image['tags'][0] if image['tags'] else image['id'][:12]}")
                else:
                    raise Exception("Docker client not available")
            except Exception as e:
                report.images_failed += 1
                report.errors.append(f"Failed to remove image {image['id'][:12]}: {e}")
                report.success = False

        # Stop localhost servers
        for server in artifacts.localhost_servers:
            try:
                if psutil.pid_exists(server["pid"]):
                    process = psutil.Process(server["pid"])
                    process.terminate()
                    process.wait(timeout=10)
                    report.localhost_servers_removed += 1
                    logger.info(f"Stopped localhost server: PID {server['pid']}")
                else:
                    report.localhost_servers_removed += 1
                    logger.info(f"Localhost server PID {server['pid']} already stopped")
            except Exception as e:
                report.localhost_servers_failed += 1
                report.errors.append(f"Failed to stop localhost server PID {server['pid']}: {e}")
                report.success = False

        # Remove build contexts
        for build_context in artifacts.build_contexts:
            try:
                if build_context.exists():
                    shutil.rmtree(build_context)
                    report.build_contexts_removed += 1
                    logger.info(f"Removed build context: {build_context}")
                else:
                    report.build_contexts_removed += 1
                    logger.info(f"Build context {build_context} already removed")
            except Exception as e:
                report.build_contexts_failed += 1
                report.errors.append(f"Failed to remove build context {build_context}: {e}")
                report.success = False

        # Mark as removed in context
        if context_manager:
            try:
                context_manager.mark_removed([{
                    "containers_removed": report.containers_removed,
                    "images_removed": report.images_removed,
                    "localhost_servers_removed": report.localhost_servers_removed,
                    "build_contexts_removed": report.build_contexts_removed,
                }])
            except Exception as e:
                report.warnings.append(f"Failed to update context: {e}")

        return report

    def list_all_agents(self) -> List[Dict[str, Any]]:
        """List all agents that can be removed across the system."""
        agents = []

        if not self.docker_client:
            logger.warning("Docker not available for listing agents")
            return agents

        try:
            # Find containers with any-agent labels or patterns
            containers = self.docker_client.containers.list(all=True)
            for container in containers:
                if self._is_any_agent_container(container):
                    agents.append({
                        "type": "docker_container",
                        "name": container.name,
                        "id": container.id,
                        "status": container.status,
                        "image": container.image.tags[0] if container.image.tags else container.image.id,
                    })

            # Find images with any-agent patterns
            images = self.docker_client.images.list()
            for image in images:
                if self._is_any_agent_image(image):
                    agents.append({
                        "type": "docker_image",
                        "name": image.tags[0] if image.tags else image.id[:12],
                        "id": image.id,
                        "status": "available",
                        "size": image.attrs.get("Size", 0),
                    })

        except Exception as e:
            logger.error(f"Error listing Docker agents: {e}")

        return agents

    def _is_any_agent_container(self, container) -> bool:
        """Check if container was created by any-agent."""
        # Check container name patterns
        name_patterns = ["any-agent", "adk-agent", "strands-agent", "langchain-agent"]
        if any(pattern in container.name.lower() for pattern in name_patterns):
            return True

        # Check image tags
        if container.image.tags:
            for tag in container.image.tags:
                if any(pattern in tag.lower() for pattern in name_patterns):
                    return True

        # Check labels
        labels = container.labels or {}
        return any(
            key.startswith("any-agent") or
            "any-agent" in str(value).lower()
            for key, value in labels.items()
        )

    def _is_any_agent_image(self, image) -> bool:
        """Check if image was created by any-agent."""
        if not image.tags:
            return False

        name_patterns = ["any-agent", "adk-agent", "strands-agent", "langchain-agent"]
        return any(
            any(pattern in tag.lower() for pattern in name_patterns)
            for tag in image.tags
        )

