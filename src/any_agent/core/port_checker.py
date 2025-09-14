"""Port availability checker for Any Agent framework."""

import socket
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


class PortChecker:
    """Utility class for checking port availability."""

    @staticmethod
    def is_port_available(port: int, host: str = "localhost") -> bool:
        """
        Check if a port is available for binding.
        Docker containers need to bind to 0.0.0.0, so we check multiple interfaces.

        Args:
            port: Port number to check
            host: Host to check on (default: localhost)

        Returns:
            True if port is available, False if in use
        """
        # Check localhost/127.0.0.1 first
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.bind((host, port))
        except OSError as e:
            logger.debug(f"Port {port} not available on {host}: {e}")
            return False

        # Also check 0.0.0.0 since Docker containers bind to all interfaces
        if host != "0.0.0.0":
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    sock.bind(("0.0.0.0", port))
            except OSError as e:
                logger.debug(f"Port {port} not available on 0.0.0.0: {e}")
                return False

        logger.debug(f"Port {port} is available")
        return True

    @staticmethod
    def find_available_port(
        start_port: int = 8000, end_port: int = 9000, host: str = "localhost"
    ) -> Optional[int]:
        """
        Find an available port in the given range.

        Args:
            start_port: Start of port range to search
            end_port: End of port range to search
            host: Host to check on

        Returns:
            Available port number or None if no ports available
        """
        for port in range(start_port, end_port + 1):
            if PortChecker.is_port_available(port, host):
                return port
        return None

    @staticmethod
    def check_multiple_ports(ports: List[int], host: str = "localhost") -> List[int]:
        """
        Check multiple ports for availability.

        Args:
            ports: List of ports to check
            host: Host to check on

        Returns:
            List of available ports
        """
        available = []
        for port in ports:
            if PortChecker.is_port_available(port, host):
                available.append(port)
        return available

    @staticmethod
    def get_port_info(port: int, host: str = "localhost") -> dict:
        """
        Get detailed information about a port.

        Args:
            port: Port to check
            host: Host to check on

        Returns:
            Dict with port status and details
        """
        info = {"port": port, "host": host, "available": False, "error": None}

        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sock.settimeout(1.0)  # 1 second timeout
                sock.bind((host, port))
                info["available"] = True
        except OSError as e:
            info["error"] = str(e)
            # Try to get more specific error information
            if "Address already in use" in str(e):
                info["status"] = "in_use"
            elif "Permission denied" in str(e):
                info["status"] = "permission_denied"
            else:
                info["status"] = "other_error"

        return info
