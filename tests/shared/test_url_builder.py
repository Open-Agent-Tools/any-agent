"""Tests for consolidated URL builder."""

import os
from unittest.mock import patch
import pytest

from src.any_agent.shared.url_builder import (
    ConsolidatedURLBuilder,
    get_url_builder,
    docker_url_builder,
    localhost_url_builder
)


class TestConsolidatedURLBuilder:
    """Test ConsolidatedURLBuilder functionality."""

    def test_localhost_default_agent_url(self):
        """Test localhost URL generation."""
        builder = ConsolidatedURLBuilder("localhost")
        url = builder.default_agent_url(8080)
        assert url == "http://localhost:8080"

    def test_docker_default_agent_url(self):
        """Test docker URL generation."""
        builder = ConsolidatedURLBuilder("docker")
        url = builder.default_agent_url(8080)
        assert url == "http://localhost:8080"

    @patch.dict(os.environ, {"AGENT_PORT": "9000"})
    def test_default_agent_url_with_env(self):
        """Test URL generation with environment port."""
        builder = ConsolidatedURLBuilder("docker")
        url = builder.default_agent_url()
        assert url == "http://localhost:9000"

    def test_agent_url_with_fallback_provided(self):
        """Test fallback when URL is provided."""
        builder = ConsolidatedURLBuilder("docker")
        url = builder.agent_url_with_fallback("http://custom:1234")
        assert url == "http://custom:1234"

    def test_agent_url_with_fallback_none(self):
        """Test fallback when URL is None."""
        builder = ConsolidatedURLBuilder("localhost")
        url = builder.agent_url_with_fallback(None, 8080)
        assert url == "http://localhost:8080"

    def test_build_chat_endpoint_urls(self):
        """Test building chat-related URLs."""
        builder = ConsolidatedURLBuilder("localhost")
        urls = builder.build_chat_endpoint_urls(8080)
        expected = {
            "agent_base": "http://localhost:8080",
            "health": "http://localhost:8080/health",
            "agent_card": "http://localhost:8080/.well-known/agent-card.json"
        }
        assert urls == expected

    @patch.dict(os.environ, {"AGENT_PORT": "invalid"})
    def test_get_environment_port_invalid(self):
        """Test environment port with invalid value."""
        builder = ConsolidatedURLBuilder("docker")
        port = builder.get_environment_port(3000)
        assert port == 3000

    @patch.dict(os.environ, {"AGENT_PORT": "7777"})
    def test_get_environment_port_valid(self):
        """Test environment port with valid value."""
        builder = ConsolidatedURLBuilder("docker")
        port = builder.get_environment_port(3000)
        assert port == 7777


class TestFactoryFunctions:
    """Test factory functions and singletons."""

    def test_get_url_builder_localhost(self):
        """Test getting localhost URL builder."""
        builder = get_url_builder("localhost")
        assert isinstance(builder, ConsolidatedURLBuilder)
        assert builder.deployment_type == "localhost"

    def test_get_url_builder_docker(self):
        """Test getting docker URL builder."""
        builder = get_url_builder("docker")
        assert isinstance(builder, ConsolidatedURLBuilder)
        assert builder.deployment_type == "docker"

    def test_singletons_exist(self):
        """Test that singleton instances exist."""
        assert docker_url_builder.deployment_type == "docker"
        assert localhost_url_builder.deployment_type == "localhost"

    def test_singleton_consistency(self):
        """Test that get_url_builder returns consistent instances."""
        builder1 = get_url_builder("localhost")
        builder2 = get_url_builder("localhost")
        assert builder1 is builder2