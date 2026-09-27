"""
Presentation and export for NetSentry results.

Terminal table, JSON export, CSV export. Stdlib only.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Iterable, TypedDict


class Device(TypedDict):
    ip: str
    hostname: str
    status: str


_IP_WIDTH = 16
_HOST_WIDTH = 24
_STATUS_WIDTH = 10


def print_results(devices: Iterable[Device], network: str = "") -> None:
    """
    Print discovered devices as a readable terminal table.
    """
    devices = list(devices)
    print()
    print("NetSentry")
    print("─" * 48)
    print()
    if network:
        print(f"Network: {network}")
        print()

    header = (
        f"{'IP':<{_IP_WIDTH}}"
        f"{'Hostname':<{_HOST_WIDTH}}"
        f"{'Status':<{_STATUS_WIDTH}}"
    )
    print(header)
    print("─" * (len(header)))

    for dev in devices:
        print(
            f"{dev.get('ip', '-'):<{_IP_WIDTH}}"
            f"{dev.get('hostname', '-'):<{_HOST_WIDTH}}"
            f"{dev.get('status', 'unknown').upper():<{_STATUS_WIDTH}}"
        )

    print()
    print(f"{len(devices)} device(s) found.")
    print()


def _ensure_dir(path: str) -> None:
    """Create the parent directory for a file path if needed."""
    parent = os.path.dirname(os.path.abspath(path))
    if parent and not os.path.isdir(parent):
        os.makedirs(parent, exist_ok=True)


def save_json(
    devices: Iterable[Device],
    filename: str,
    network: str = "",
) -> str:
    """
    Write results to JSON. Returns the path written.
    """
    payload = {
        "network": network,
        "devices": list(devices),
    }
    _ensure_dir(filename)
    try:
        with open(filename, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=4)
    except OSError as exc:
        raise OSError(f"Failed to write JSON to {filename}: {exc}") from exc
    return filename


def save_csv(devices: Iterable[Device], filename: str) -> str:
    """
    Write results to CSV with headers: ip, hostname, status.
    Returns the path written.
    """
    _ensure_dir(filename)
    try:
        with open(filename, "w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(
                fh,
                fieldnames=["ip", "hostname", "status"],
            )
            writer.writeheader()
            for dev in devices:
                writer.writerow({
                    "ip": dev.get("ip", ""),
                    "hostname": dev.get("hostname", ""),
                    "status": dev.get("status", ""),
                })
    except OSError as exc:
        raise OSError(f"Failed to write CSV to {filename}: {exc}") from exc
    return filename
