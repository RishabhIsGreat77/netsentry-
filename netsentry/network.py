"""
Local network information utilities.

Determines the local IPv4 address, the subnet it lives on, and returns
structured network info. Uses Python's `ipaddress` and `socket` modules only.
"""

from __future__ import annotations

import ipaddress
import socket
from typing import TypedDict


class NetworkInfo(TypedDict):
    local_ip: str
    network: str
    netmask: str
    broadcast: str
    usable_hosts: int


def get_local_ip() -> str:
    """
    Return the local IPv4 address used for outbound traffic.

    Opens a UDP socket to a public address (no packets are actually sent
    for connectionless UDP) and reads back the kernel-chosen source IP.

    Raises:
        ConnectionError: if no route to any external address exists.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError as exc:
        raise ConnectionError(f"Unable to determine local IP: {exc}") from exc
    finally:
        sock.close()


def get_network(local_ip: str | None = None) -> ipaddress.IPv4Network:
    """
    Return the IPv4 network (subnet) the local host belongs to.

    Uses `/24` as the assumed prefix when the local IP is supplied without a
    real netmask (common on consumer networks, and safe for a local-only tool).

    Args:
        local_ip: optional IPv4 string. If omitted, get_local_ip() is used.

    Raises:
        ValueError: if the IP is malformed.
        ConnectionError: if the local IP cannot be determined.
    """
    ip_str = local_ip or get_local_ip()
    try:
        ip = ipaddress.IPv4Address(ip_str)
    except ipaddress.AddressValueError as exc:
        raise ValueError(f"Invalid IPv4 address: {ip_str}") from exc

    return ipaddress.IPv4Network(f"{ip}/24", strict=False)


def get_network_info(local_ip: str | None = None) -> NetworkInfo:
    """
    Return a dict describing the local network.

    Contains:
        local_ip, network (CIDR), netmask, broadcast, usable_hosts.
    """
    ip_str = local_ip or get_local_ip()
    network = get_network(ip_str)

    return NetworkInfo(
        local_ip=ip_str,
        network=str(network),
        netmask=str(network.netmask),
        broadcast=str(network.broadcast_address),
        usable_hosts=max(network.num_addresses - 2, 0),
    )
