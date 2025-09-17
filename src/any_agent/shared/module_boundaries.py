"""Module responsibility boundaries and interface definitions.

Defines clear separation of concerns between shared modules to eliminate
overlapping responsibilities and establish proper dependency relationships.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Protocol


class TemplateGenerator(Protocol):
    """Protocol for template generation modules."""

    def generate_template(self, context: Any) -> str:
        """Generate template string from context."""
        ...


class RouteBuilder(Protocol):
    """Protocol for route building modules."""

    def build_routes(self, config: Any) -> str:
        """Build route definitions from configuration."""
        ...


class URLProvider(Protocol):
    """Protocol for URL construction modules."""

    def build_url(self, *args, **kwargs) -> str:
        """Build URL from components."""
        ...


@dataclass
class ModuleBoundary:
    """Defines the boundary and responsibilities of a module."""

    name: str
    primary_responsibility: str
    interfaces: list[str]
    dependencies: list[str]
    consumers: list[str]


class ModuleBoundaryRegistry:
    """Registry of module boundaries and their relationships."""

    def __init__(self):
        """Initialize registry with defined module boundaries."""
        self._boundaries = self._define_boundaries()

    def _define_boundaries(self) -> Dict[str, ModuleBoundary]:
        """Define the boundaries for all shared modules."""
        return {
            "url_builder": ModuleBoundary(
                name="url_builder",
                primary_responsibility="Consolidated URL construction for all deployment types",
                interfaces=["ConsolidatedURLBuilder", "get_url_builder()"],
                dependencies=["url_utils"],
                consumers=["chat_endpoints_generator", "entrypoint_templates"],
            ),
            "url_utils": ModuleBoundary(
                name="url_utils",
                primary_responsibility="Low-level URL utilities and validation",
                interfaces=[
                    "AgentURLBuilder",
                    "localhost_urls",
                    "validate_agent_url()",
                ],
                dependencies=[],
                consumers=["url_builder", "core modules"],
            ),
            "unified_ui_routes": ModuleBoundary(
                name="unified_ui_routes",
                primary_responsibility="Standardized UI route generation across frameworks",
                interfaces=[
                    "UnifiedUIRouteGenerator",
                    "UIConfig",
                    "unified_ui_generator",
                ],
                dependencies=[],
                consumers=["ui_routes_generator", "entrypoint_templates"],
            ),
            "ui_routes_generator": ModuleBoundary(
                name="ui_routes_generator",
                primary_responsibility="Legacy UI route generation interface (compatibility wrapper)",
                interfaces=["UIRoutesGenerator"],
                dependencies=["unified_ui_routes"],
                consumers=["entrypoint_templates"],
            ),
            "chat_endpoints_generator": ModuleBoundary(
                name="chat_endpoints_generator",
                primary_responsibility="Chat endpoint generation for web integration",
                interfaces=["ChatEndpointsGenerator"],
                dependencies=["url_builder"],
                consumers=["entrypoint_templates"],
            ),
            "entrypoint_templates": ModuleBoundary(
                name="entrypoint_templates",
                primary_responsibility="Framework-specific entrypoint template generation",
                interfaces=["UnifiedEntrypointGenerator", "EntrypointContext"],
                dependencies=[
                    "chat_endpoints_generator",
                    "ui_routes_generator",
                    "url_builder",
                ],
                consumers=["docker", "localhost orchestrators"],
            ),
            "strands_context_executor": ModuleBoundary(
                name="strands_context_executor",
                primary_responsibility="AWS Strands-specific A2A executor with context isolation",
                interfaces=["ContextAwareStrandsA2AExecutor"],
                dependencies=["core.context_manager"],
                consumers=["entrypoint_templates (Strands only)"],
            ),
        }

    def get_boundary(self, module_name: str) -> Optional[ModuleBoundary]:
        """Get boundary definition for a module."""
        return self._boundaries.get(module_name)

    def list_modules(self) -> list[str]:
        """List all registered modules."""
        return list(self._boundaries.keys())

    def get_dependencies(self, module_name: str) -> list[str]:
        """Get dependencies for a module."""
        boundary = self.get_boundary(module_name)
        return boundary.dependencies if boundary else []

    def get_consumers(self, module_name: str) -> list[str]:
        """Get consumers of a module."""
        boundary = self.get_boundary(module_name)
        return boundary.consumers if boundary else []

    def validate_dependency_order(self) -> list[str]:
        """Validate and return proper dependency ordering.

        Returns:
            List of modules in dependency order (dependencies first)
        """
        # Simple topological sort based on dependencies
        ordered = []
        remaining = set(self._boundaries.keys())

        while remaining:
            # Find modules with no unresolved dependencies
            ready = []
            for module in remaining:
                deps = self.get_dependencies(module)
                if not deps or all(
                    dep in ordered or dep not in remaining for dep in deps
                ):
                    ready.append(module)

            if not ready:
                # Circular dependency detected
                raise ValueError(f"Circular dependency detected among: {remaining}")

            # Sort ready modules alphabetically for consistency
            ready.sort()
            ordered.extend(ready)
            remaining -= set(ready)

        return ordered

    def detect_violations(self) -> list[str]:
        """Detect boundary violations in the current module structure.

        Returns:
            List of detected violations
        """
        violations = []

        # Check for overlapping responsibilities
        responsibilities: dict[str, list[str]] = {}
        for name, boundary in self._boundaries.items():
            resp = boundary.primary_responsibility.lower()
            for keyword in ["url", "ui", "route", "template", "chat", "context"]:
                if keyword in resp:
                    if keyword not in responsibilities:
                        responsibilities[keyword] = []
                    responsibilities[keyword].append(name)

        # Report modules with overlapping keywords (potential responsibility overlap)
        for keyword, modules in responsibilities.items():
            if len(modules) > 1 and keyword != "context":  # Context can be shared
                if not self._is_acceptable_overlap(keyword, modules):
                    violations.append(
                        f"Responsibility overlap '{keyword}': {', '.join(modules)}"
                    )

        return violations

    def _is_acceptable_overlap(self, keyword: str, modules: list[str]) -> bool:
        """Check if responsibility overlap is acceptable."""
        modules_set = set(modules)

        # URL overlap is acceptable between url_utils and url_builder (layered)
        if keyword == "url" and modules_set == {"url_utils", "url_builder"}:
            return True

        # UI overlap is acceptable between unified_ui_routes and ui_routes_generator (wrapper pattern)
        if keyword == "ui" and modules_set <= {
            "unified_ui_routes",
            "ui_routes_generator",
        }:
            return True

        # Route overlap is acceptable between UI-related modules
        if keyword == "route" and modules_set <= {
            "unified_ui_routes",
            "ui_routes_generator",
        }:
            return True

        return False


# Singleton registry
module_registry = ModuleBoundaryRegistry()


def get_module_boundary(module_name: str) -> Optional[ModuleBoundary]:
    """Get boundary definition for a module."""
    return module_registry.get_boundary(module_name)


def validate_module_dependencies() -> tuple[list[str], list[str]]:
    """Validate module dependencies and detect violations.

    Returns:
        Tuple of (dependency_order, violations)
    """
    try:
        order = module_registry.validate_dependency_order()
        violations = module_registry.detect_violations()
        return order, violations
    except ValueError as e:
        return [], [str(e)]
