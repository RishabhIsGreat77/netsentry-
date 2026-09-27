"""
NetSentry CLI entry point.

Run with:  python -m netsentry
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from . import __version__
from .discovery import (
    DEFAULT_PORTS,
    DEFAULT_TIMEOUT,
    discover_hosts,
)
from .network import get_network_info
from .reporter import print_results, save_csv, save_json


DEFAULT_CONFIG_PATH = "config.json"


def _load_config(path: str) -> dict[str, Any]:
    """
    Load config from JSON. Returns defaults if the file is missing.
    Raises ValueError on malformed values.
    """
    defaults: dict[str, Any] = {
        "timeout": DEFAULT_TIMEOUT,
        "ports": list(DEFAULT_PORTS),
        "output_directory": "reports",
    }
    if not path or not os.path.isfile(path):
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[!] Could not read config ({exc}). Using defaults.")
        return defaults

    if not isinstance(raw, dict):
        print("[!] Config must be a JSON object. Using defaults.")
        return defaults

    cfg = dict(defaults)

    timeout = raw.get("timeout", defaults["timeout"])
    if not isinstance(timeout, (int, float)) or timeout <= 0 or timeout > 10:
        raise ValueError("config.timeout must be a number between 0 and 10")
    cfg["timeout"] = float(timeout)

    ports = raw.get("ports", defaults["ports"])
    if (
        not isinstance(ports, list)
        or not ports
        or not all(isinstance(p, int) and 1 <= p <= 65535 for p in ports)
    ):
        raise ValueError("config.ports must be a non-empty list of valid ports")
    cfg["ports"] = list(ports)

    outdir = raw.get("output_directory", defaults["output_directory"])
    if not isinstance(outdir, str) or not outdir.strip():
        raise ValueError("config.output_directory must be a non-empty string")
    cfg["output_directory"] = outdir

    return cfg


BANNER = r"""
╔══════════════════════════════╗
║          NetSentry           ║
║   Local Network Inspector    ║
╚══════════════════════════════╝
"""


def _print_banner(info: dict[str, Any]) -> None:
    print(BANNER)
    print(f"Local IP : {info['local_ip']}")
    print(f"Network  : {info['network']}")
    print()


def _print_menu() -> None:
    print("[1] Discover devices")
    print("[2] Network information")
    print("[3] Export results")
    print("[4] Exit")
    print()


def _action_discover(
    info: dict[str, Any],
    cfg: dict[str, Any],
) -> list[dict[str, Any]]:
    print(f"\n[*] Scanning {info['network']} ...")
    print(f"    Timeout: {cfg['timeout']}s | Ports: {cfg['ports']}\n")
    try:
        devices = discover_hosts(
            info["network"],
            ports=cfg["ports"],
            timeout=cfg["timeout"],
        )
    except ValueError as exc:
        print(f"[!] {exc}")
        return []
    print_results(devices, network=info["network"])
    return devices


def _action_network_info(info: dict[str, Any]) -> None:
    print()
    print("Network information")
    print("─" * 32)
    print(f"Local IP        : {info['local_ip']}")
    print(f"Network (CIDR)  : {info['network']}")
    print(f"Netmask         : {info['netmask']}")
    print(f"Broadcast       : {info['broadcast']}")
    print(f"Usable hosts    : {info['usable_hosts']}")
    print()


def _action_export(
    devices: list[dict[str, Any]],
    info: dict[str, Any],
    cfg: dict[str, Any],
) -> None:
    if not devices:
        print("\n[!] No results to export. Run a discovery first.\n")
        return

    outdir = cfg["output_directory"]
    json_path = os.path.join(outdir, "netsentry_results.json")
    csv_path = os.path.join(outdir, "netsentry_results.csv")

    try:
        save_json(devices, json_path, network=info["network"])
        save_csv(devices, csv_path)
    except OSError as exc:
        print(f"\n[!] Export failed: {exc}\n")
        return

    print(f"\n[+] JSON written: {json_path}")
    print(f"[+] CSV written : {csv_path}\n")


def _interactive_loop(info: dict[str, Any], cfg: dict[str, Any]) -> int:
    _print_banner(info)
    devices: list[dict[str, Any]] = []

    while True:
        _print_menu()
        try:
            choice = input("Choose: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return 0

        if choice == "1":
            devices = _action_discover(info, cfg)
        elif choice == "2":
            _action_network_info(info)
        elif choice == "3":
            _action_export(devices, info, cfg)
        elif choice == "4":
            print("Goodbye.")
            return 0
        else:
            print("\n[!] Unknown option.\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="netsentry",
        description="NetSentry — local network inspector.",
    )
    parser.add_argument(
        "--config",
        default=DEFAULT_CONFIG_PATH,
        help=f"Path to config JSON (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Run discovery non-interactively and exit.",
    )
    parser.add_argument(
        "--network-info",
        action="store_true",
        help="Print network information and exit.",
    )
    parser.add_argument(
        "--export",
        metavar="DIR",
        help="Directory to export JSON + CSV (implies --discover).",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"NetSentry {__version__}",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        cfg = _load_config(args.config)
    except ValueError as exc:
        print(f"[!] Invalid config: {exc}")
        return 2

    try:
        info = get_network_info()
    except (ConnectionError, ValueError) as exc:
        print(f"[!] {exc}")
        print("    Check your network connection and try again.")
        return 1

    if args.network_info:
        _print_banner(info)
        _action_network_info(info)
        return 0

    if args.discover or args.export:
        if args.export:
            cfg["output_directory"] = args.export
        _print_banner(info)
        devices = _action_discover(info, cfg)
        if args.export and devices:
            _action_export(devices, info, cfg)
        return 0

    try:
        return _interactive_loop(info, cfg)
    except KeyboardInterrupt:
        print("\nGoodbye.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
