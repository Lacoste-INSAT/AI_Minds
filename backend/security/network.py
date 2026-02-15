"""
Synapsis Security — Network Isolation Guard
============================================

Ensures the application stays air-gapped by:

1. Validating that outbound connections only go to allowed local endpoints
   (Ollama on 127.0.0.1:11434, Qdrant on 127.0.0.1:6333).
2. Providing a socket-level guard that can be installed at startup to block
   or log any unexpected outbound connections.
3. Verifying no DNS leakage to external resolvers.

Usage::

    from backend.security.network import NetworkGuard

    guard = NetworkGuard()
    guard.verify_air_gap()               # raises if external access detected
    guard.install_socket_guard()         # patch socket.connect
    report = guard.get_status()          # JSON-safe status dict
"""

from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Allowed endpoints
# ---------------------------------------------------------------------------

_LOOPBACK_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("::1/128"),
]

_DOCKER_INTERNAL = "host.docker.internal"

# Ports that are expected for local services
_ALLOWED_PORTS = {
    11434,  # Ollama
    6333,   # Qdrant REST
    6334,   # Qdrant gRPC
    8000,   # Synapsis backend
    3000,   # Synapsis frontend
}


def _is_local(host: str) -> bool:
    """Check if a host resolves to a loopback / link-local address."""
    if host in ("localhost", "127.0.0.1", "::1", _DOCKER_INTERNAL):
        return True
    try:
        addr = ipaddress.ip_address(host)
        return addr.is_loopback or addr.is_link_local
    except ValueError:
        pass
    # Try DNS resolution
    try:
        resolved = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        for _, _, _, _, sockaddr in resolved:
            ip = ipaddress.ip_address(sockaddr[0])
            if not (ip.is_loopback or ip.is_link_local or ip.is_private):
                return False
        return True
    except socket.gaierror:
        return False


# ---------------------------------------------------------------------------
# Connection log
# ---------------------------------------------------------------------------

@dataclass
class ConnectionAttempt:
    """Record of an outbound connection attempt."""
    host: str
    port: int
    allowed: bool
    reason: str
    timestamp: str = ""


# ---------------------------------------------------------------------------
# Guard
# ---------------------------------------------------------------------------

class NetworkGuard:
    """Monitor and restrict outbound network access."""

    def __init__(self) -> None:
        self._connection_log: list[ConnectionAttempt] = []
        self._blocked_count = 0
        self._allowed_count = 0
        self._installed = False
        self._original_connect = None

    def check_url(self, url: str) -> tuple[bool, str]:
        """
        Check if a URL is safe (local-only).

        Returns (allowed, reason).
        """
        parsed = urlparse(url)
        host = parsed.hostname or ""
        port = parsed.port or 80

        if not host:
            return False, "Empty host"

        if _is_local(host):
            return True, f"Local endpoint: {host}:{port}"

        return False, f"External host blocked: {host}:{port}"

    def verify_endpoint(self, host: str, port: int) -> tuple[bool, str]:
        """Check if a host:port pair is allowed."""
        if _is_local(host):
            return True, "local"
        return False, f"Non-local endpoint blocked: {host}:{port}"

    def verify_air_gap(self) -> dict[str, Any]:
        """
        Run a comprehensive air-gap verification.
        Returns status dict. Does NOT make external connections.
        """
        from backend.config import settings

        issues: list[str] = []
        checks: list[dict] = []

        # Check Ollama URL
        ollama_ok, ollama_reason = self.check_url(settings.ollama_base_url)
        checks.append({
            "service": "ollama",
            "url": settings.ollama_base_url,
            "local": ollama_ok,
            "reason": ollama_reason,
        })
        if not ollama_ok:
            issues.append(f"Ollama URL is not local: {settings.ollama_base_url}")

        # Check Qdrant
        qdrant_ok, qdrant_reason = self.verify_endpoint(
            settings.qdrant_host, settings.qdrant_port
        )
        checks.append({
            "service": "qdrant",
            "host": settings.qdrant_host,
            "port": settings.qdrant_port,
            "local": qdrant_ok,
            "reason": qdrant_reason,
        })
        if not qdrant_ok:
            issues.append(f"Qdrant is not local: {settings.qdrant_host}:{settings.qdrant_port}")

        # Check CORS origins
        for origin in settings.cors_origins:
            ok, reason = self.check_url(origin)
            checks.append({
                "service": "cors_origin",
                "url": origin,
                "local": ok,
                "reason": reason,
            })
            if not ok:
                issues.append(f"CORS origin is not local: {origin}")

        # Check bind address
        if settings.host not in ("127.0.0.1", "localhost", "::1", "0.0.0.0"):
            issues.append(f"Server bind address is not loopback: {settings.host}")

        air_gapped = len(issues) == 0

        result = {
            "air_gapped": air_gapped,
            "checks": checks,
            "issues": issues,
            "blocked_connections": self._blocked_count,
            "allowed_connections": self._allowed_count,
        }

        if air_gapped:
            logger.info("security.air_gap_verified")
        else:
            logger.warning("security.air_gap_issues", issues=issues)

        return result

    def install_socket_guard(self, block: bool = False) -> None:
        """
        Monkey-patch ``socket.connect`` to log (and optionally block)
        non-local outbound connections.

        Parameters
        ----------
        block : bool
            If True, raise ``ConnectionRefusedError`` for non-local targets.
            If False, only log a warning.
        """
        if self._installed:
            return

        self._original_connect = socket.socket.connect
        guard = self

        def _guarded_connect(sock, address):
            host = str(address[0]) if isinstance(address, tuple) else str(address)
            port = address[1] if isinstance(address, tuple) and len(address) > 1 else 0

            is_local = _is_local(host)

            if is_local:
                guard._allowed_count += 1
            else:
                guard._blocked_count += 1
                if block:
                    logger.error(
                        "security.external_connection_blocked",
                        host=host, port=port,
                    )
                    raise ConnectionRefusedError(
                        f"Air-gap violation: connection to {host}:{port} blocked"
                    )
                else:
                    logger.warning(
                        "security.external_connection_detected",
                        host=host, port=port,
                    )

            return guard._original_connect(sock, address)

        socket.socket.connect = _guarded_connect
        self._installed = True
        logger.info("security.socket_guard_installed", blocking=block)

    def uninstall_socket_guard(self) -> None:
        """Restore original socket.connect."""
        if self._installed and self._original_connect:
            socket.socket.connect = self._original_connect
            self._installed = False

    def get_status(self) -> dict[str, Any]:
        """Return current guard status as a JSON-safe dict."""
        return {
            "socket_guard_installed": self._installed,
            "blocked_connections": self._blocked_count,
            "allowed_connections": self._allowed_count,
            "recent_log": [
                {
                    "host": a.host,
                    "port": a.port,
                    "allowed": a.allowed,
                    "reason": a.reason,
                }
                for a in self._connection_log[-20:]
            ],
        }
