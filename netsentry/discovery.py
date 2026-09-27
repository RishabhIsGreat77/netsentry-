"""
Local-subnet device discovery.

Uses non-privileged TCP connect checks against a short list of common
service ports, plus reverse DNS lookup for hostnames. No raw sockets,
no packet crafting, no privileged requirements.
"""

from __future__ import annotations

import ipaddress
import socket
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, TypedDict


class Device(TypedDict):
    ip: str
    hostname: str
    status: str


DEFAULT_PORTS: tuple[int, ...] = (80, 443, 22, 53)
DEFAULT_TIMEOUT: float = 0.5
DEFAULT_MAX_WORKERS: int = 64


def _resolve_hostname(ip: str, timeout: float = DEFAULT_TIMEOUT) -> str:
    """
    Best-effort reverse DNS. Returns "-" on failure.
    """
    try:
        socket.setdefaulttimeout(timeout)
        hostname, _, _ = socket.gethostbyaddr(ip)
        return hostname or "-"
    except (socket.herror, socket.gaierror, OSError):
        return "-"
    finally:
        socket.setdefaulttimeout(None)


def _port_open(ip: str, port: int, timeout: float) -> bool:
    """
    Return True if a TCP connection to ip:port succeeds within timeout.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((ip, port)) == 0
    except OSError:
        return False


def _host_is_reachable(
    ip: str,
    ports: Iterable[int],
    timeout: float,
) -> bool:
    """
    Return True if any of the given ports responds on the host.
    """
    for port in ports:
        if _port_open(ip, port, timeout):
            return True
    return False


def _check_host(
    ip: str,
    ports: Iterable[int],
    timeout: float,
) -> Device | None:
    """
    Probe a single host and return a Device dict if reachable, else None.
    """
    if not _host_is_reachable(ip, ports, timeout):
        return None
    return Device(
        ip=ip,
        hostname=_resolve_hostname(ip, timeout),
        status="online",
    )


def discover_hosts(
    network: str | ipaddress.IPv4Network,
    ports: Iterable[int] = DEFAULT_PORTS,
    timeout: float = DEFAULT_TIMEOUT,
    max_workers: int = DEFAULT_MAX_WORKERS,
) -> list[Device]:
    """
    Discover reachable hosts on the given IPv4 network.

    Args:
        network: CIDR string or IPv4Network (e.g. "192.168.1.0/24").
        ports: TCP ports to probe per host.
        timeout: per-connection timeout in seconds.
        max_workers: threadpool size.

    Returns:
        List of Device dicts sorted by IP.

    Raises:
        ValueError: if the network is malformed or is not IPv4.
    """
    try:
        net = (
            network
            if isinstance(network, ipaddress.IPv4Network)
            else ipaddress.IPv4Network(network, strict=False)
        )
    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError, ValueError) as exc:
        raise ValueError(f"Invalid network: {network}") from exc

    hosts = [str(h) for h in net.hosts()]
    if not hosts:
        return []

    ports = tuple(ports)
    found: list[Device] = []

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(_check_host, ip, ports, timeout): ip for ip in hosts
        }
        for fut in as_completed(futures):
            try:
                device = fut.result()
            except Exception:
                continue
            if device is not None:
                found.append(device)

    found.sort(key=lambda d: ipaddress.IPv4Address(d["ip"]))
    return found
