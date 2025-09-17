"""Tests for module boundary validation."""

import pytest

from src.any_agent.shared.module_boundaries import (
    ModuleBoundary,
    ModuleBoundaryRegistry,
    module_registry,
    get_module_boundary,
    validate_module_dependencies
)


class TestModuleBoundary:
    """Test ModuleBoundary dataclass."""

    def test_module_boundary_creation(self):
        """Test creating a module boundary."""
        boundary = ModuleBoundary(
            name="test_module",
            primary_responsibility="Test module functionality",
            interfaces=["TestInterface"],
            dependencies=["other_module"],
            consumers=["consumer_module"]
        )

        assert boundary.name == "test_module"
        assert boundary.primary_responsibility == "Test module functionality"
        assert boundary.interfaces == ["TestInterface"]
        assert boundary.dependencies == ["other_module"]
        assert boundary.consumers == ["consumer_module"]


class TestModuleBoundaryRegistry:
    """Test ModuleBoundaryRegistry functionality."""

    def test_registry_initialization(self):
        """Test registry initializes with predefined boundaries."""
        registry = ModuleBoundaryRegistry()
        modules = registry.list_modules()

        expected_modules = {
            "url_builder",
            "url_utils",
            "unified_ui_routes",
            "ui_routes_generator",
            "chat_endpoints_generator",
            "entrypoint_templates",
            "strands_context_executor"
        }

        assert set(modules) == expected_modules

    def test_get_boundary_existing(self):
        """Test getting boundary for existing module."""
        registry = ModuleBoundaryRegistry()
        boundary = registry.get_boundary("url_builder")

        assert boundary is not None
        assert boundary.name == "url_builder"
        assert "Consolidated URL construction" in boundary.primary_responsibility
        assert "url_utils" in boundary.dependencies

    def test_get_boundary_nonexistent(self):
        """Test getting boundary for non-existent module."""
        registry = ModuleBoundaryRegistry()
        boundary = registry.get_boundary("nonexistent_module")

        assert boundary is None

    def test_get_dependencies(self):
        """Test getting dependencies for a module."""
        registry = ModuleBoundaryRegistry()
        deps = registry.get_dependencies("url_builder")

        assert "url_utils" in deps

    def test_get_consumers(self):
        """Test getting consumers for a module."""
        registry = ModuleBoundaryRegistry()
        consumers = registry.get_consumers("url_builder")

        # url_builder should be consumed by chat_endpoints_generator
        assert "chat_endpoints_generator" in consumers

    def test_validate_dependency_order(self):
        """Test dependency order validation."""
        registry = ModuleBoundaryRegistry()
        order = registry.validate_dependency_order()

        # url_utils should come before url_builder
        url_utils_idx = order.index("url_utils")
        url_builder_idx = order.index("url_builder")
        assert url_utils_idx < url_builder_idx

        # unified_ui_routes should come before ui_routes_generator
        unified_idx = order.index("unified_ui_routes")
        wrapper_idx = order.index("ui_routes_generator")
        assert unified_idx < wrapper_idx

        # Dependencies should come before their consumers
        chat_idx = order.index("chat_endpoints_generator")
        template_idx = order.index("entrypoint_templates")
        assert chat_idx < template_idx

    def test_detect_violations_none_expected(self):
        """Test that no violations are detected in well-designed boundaries."""
        registry = ModuleBoundaryRegistry()
        violations = registry.detect_violations()

        # Should have no violations in our consolidated architecture
        assert len(violations) == 0, f"Unexpected violations: {violations}"

    def test_acceptable_overlap(self):
        """Test that acceptable overlaps are not flagged as violations."""
        registry = ModuleBoundaryRegistry()

        # URL overlap between url_utils and url_builder is acceptable
        assert registry._is_acceptable_overlap("url", ["url_utils", "url_builder"])

        # UI overlap between unified and wrapper is acceptable
        assert registry._is_acceptable_overlap("ui", ["unified_ui_routes", "ui_routes_generator"])

        # Other overlaps are not acceptable
        assert not registry._is_acceptable_overlap("template", ["module1", "module2"])


class TestSingletonAccess:
    """Test singleton registry access functions."""

    def test_get_module_boundary(self):
        """Test getting module boundary via singleton function."""
        boundary = get_module_boundary("url_utils")

        assert boundary is not None
        assert boundary.name == "url_utils"
        assert "Low-level URL utilities" in boundary.primary_responsibility

    def test_get_nonexistent_boundary(self):
        """Test getting non-existent boundary via singleton function."""
        boundary = get_module_boundary("nonexistent")
        assert boundary is None

    def test_validate_module_dependencies(self):
        """Test module dependency validation via singleton function."""
        order, violations = validate_module_dependencies()

        # Should return valid order
        assert len(order) > 0
        assert "url_utils" in order
        assert "url_builder" in order

        # Should have no violations
        assert len(violations) == 0, f"Unexpected violations: {violations}"

    def test_singleton_consistency(self):
        """Test that singleton returns consistent results."""
        boundary1 = get_module_boundary("url_builder")
        boundary2 = module_registry.get_boundary("url_builder")

        assert boundary1 == boundary2


class TestBoundaryDefinitions:
    """Test specific boundary definitions for correctness."""

    def test_url_utils_boundary(self):
        """Test url_utils boundary definition."""
        boundary = get_module_boundary("url_utils")

        assert boundary.name == "url_utils"
        assert len(boundary.dependencies) == 0  # Foundational module
        assert "AgentURLBuilder" in boundary.interfaces
        assert "localhost_urls" in boundary.interfaces

    def test_entrypoint_templates_boundary(self):
        """Test entrypoint_templates boundary definition."""
        boundary = get_module_boundary("entrypoint_templates")

        assert boundary.name == "entrypoint_templates"
        assert "chat_endpoints_generator" in boundary.dependencies
        assert "ui_routes_generator" in boundary.dependencies
        assert "url_builder" in boundary.dependencies

    def test_strands_context_executor_boundary(self):
        """Test strands_context_executor boundary definition."""
        boundary = get_module_boundary("strands_context_executor")

        assert boundary.name == "strands_context_executor"
        assert "AWS Strands-specific" in boundary.primary_responsibility
        assert "core.context_manager" in boundary.dependencies