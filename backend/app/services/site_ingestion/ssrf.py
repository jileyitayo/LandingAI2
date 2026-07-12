"""SSRF guard for user-supplied URLs.

validate_url() must pass before ANY outbound request, including every
stylesheet/script sub-fetch and every manually-followed redirect hop.
Residual risk: DNS rebinding between validation and connect is accepted
(no IP-pinned transport); mitigated by http(s)-only, port allowlist,
byte caps and timeouts in the extractor.
"""

import asyncio
import ipaddress
import logging
from typing import Optional, Tuple
from urllib.parse import urlparse, urlunparse

logger = logging.getLogger(__name__)

ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_PORTS = {80, 443, 8080, 8443}
BLOCKED_HOSTS = {"localhost"}
BLOCKED_HOST_SUFFIXES = (".local", ".internal", ".localhost")


def _is_forbidden_ip(ip_str: str) -> bool:
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return True
    return (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local  # covers 169.254.169.254 metadata endpoint
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


async def validate_url(url: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate a URL for outbound fetching.

    Returns (ok, reason, normalized_url). reason is None when ok.
    """
    url = (url or "").strip().rstrip(").,;\"'")
    try:
        parsed = urlparse(url)
    except ValueError:
        return False, "invalid_url", None

    if parsed.scheme not in ALLOWED_SCHEMES:
        return False, "scheme_not_allowed", None
    if not parsed.hostname:
        return False, "invalid_url", None
    if parsed.username or parsed.password:
        return False, "credentials_in_url", None

    try:
        port = parsed.port
    except ValueError:
        return False, "invalid_url", None
    if port is not None and port not in ALLOWED_PORTS:
        return False, "port_not_allowed", None

    host = parsed.hostname.lower().rstrip(".")
    if host in BLOCKED_HOSTS or host.endswith(BLOCKED_HOST_SUFFIXES):
        return False, "blocked_host", None

    # Literal IP in the URL — check without DNS.
    try:
        ipaddress.ip_address(host.strip("[]"))
        if _is_forbidden_ip(host.strip("[]")):
            return False, "private_address", None
    except ValueError:
        # Hostname: resolve and reject if ANY address (v4 or v6) is internal.
        try:
            loop = asyncio.get_running_loop()
            infos = await asyncio.wait_for(
                loop.getaddrinfo(host, port or 443), timeout=5.0
            )
        except (OSError, asyncio.TimeoutError):
            return False, "dns_failure", None
        addresses = {info[4][0] for info in infos}
        if not addresses or any(_is_forbidden_ip(a) for a in addresses):
            return False, "private_address", None

    normalized = urlunparse(parsed)
    return True, None, normalized
