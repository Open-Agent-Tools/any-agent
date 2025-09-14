"""Test the port checker functionality."""

import socket
import pytest
from unittest.mock import patch

from any_agent.core.port_checker import PortChecker


class TestPortChecker:
    """Test port availability checking functionality."""

    def test_port_available_when_free(self):
        """Test port is reported as available when free."""
        # Find a definitely free port by binding to 0
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as temp_sock:
            temp_sock.bind(("localhost", 0))
            free_port = temp_sock.getsockname()[1]

        # Now check that port (it should be available again)
        assert PortChecker.is_port_available(free_port)

    def test_port_unavailable_when_bound(self):
        """Test port is reported as unavailable when bound."""
        # Bind to a port
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("localhost", 0))
            bound_port = sock.getsockname()[1]

            # Port should be unavailable while bound
            assert not PortChecker.is_port_available(bound_port)

    def test_find_available_port_in_range(self):
        """Test finding an available port in a range."""
        port = PortChecker.find_available_port(9000, 9100)

        assert port is not None
        assert 9000 <= port <= 9100
        assert PortChecker.is_port_available(port)

    def test_find_available_port_none_when_all_busy(self):
        """Test returns None when no ports available in range."""
        with patch.object(PortChecker, "is_port_available", return_value=False):
            port = PortChecker.find_available_port(8000, 8002)
            assert port is None

    def test_check_multiple_ports(self):
        """Test checking multiple ports at once."""
        # Get some free ports
        free_ports = []
        for _ in range(3):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("localhost", 0))
                free_ports.append(sock.getsockname()[1])

        # Should all be available
        available = PortChecker.check_multiple_ports(free_ports)
        assert len(available) == len(free_ports)
        assert set(available) == set(free_ports)

    def test_get_port_info_available(self):
        """Test getting detailed port information for available port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("localhost", 0))
            free_port = sock.getsockname()[1]

        info = PortChecker.get_port_info(free_port)

        assert info["port"] == free_port
        assert info["host"] == "localhost"
        assert info["available"] is True
        assert info["error"] is None

    def test_get_port_info_unavailable(self):
        """Test getting detailed port information for unavailable port."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("localhost", 0))
            busy_port = sock.getsockname()[1]

            info = PortChecker.get_port_info(busy_port)

            assert info["port"] == busy_port
            assert info["host"] == "localhost"
            assert info["available"] is False
            assert info["error"] is not None
            assert "status" in info

    def test_permission_denied_port(self):
        """Test handling of permission denied (privileged ports)."""
        # Port 80 typically requires admin privileges
        if PortChecker.is_port_available(80):
            pytest.skip("Port 80 is available (running as admin?)")

        info = PortChecker.get_port_info(80)

        assert info["available"] is False
        assert info["error"] is not None
        # On some systems, low ports may give permission denied
        if "Permission denied" in info["error"]:
            assert info["status"] == "permission_denied"
