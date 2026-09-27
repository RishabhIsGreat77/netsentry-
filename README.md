# NetSentry

A defensive, local-network inspection and device-discovery CLI tool.

NetSentry helps you see which devices are reachable on your own local
network — the kind of visibility you'd want before hardening a home
router, debugging a lab, or documenting the devices in your house.

It is **read-only, non-privileged, and local-only**. It does not exploit,
attack, harvest credentials, or reach beyond your detected subnet.

---

## Features

- Detects the local IPv4 address.
- Determines the local IPv4 subnet (`/24`).
- Displays network information (IP, CIDR, netmask, broadcast, usable hosts).
- Discovers reachable devices on the local subnet via conservative TCP probes.
- Resolves hostnames via reverse DNS when available.
- Clean terminal table output.
- JSON and CSV export.
- Graceful handling of network errors and timeouts.
- Optional JSON config file.
- Unit tests using the standard library.

---

## Requirements

- Python 3.10 or newer (uses `X | Y` type unions).
- No external dependencies.
- Works on Linux, macOS, and Windows.
- No administrator/root privileges required.

---

## Installation

```bash
git clone <repository-url>
cd netsentry
python -m netsentry
```

Optional: copy the example config.

```bash
cp config.example.json config.json
```

---

## Usage

### Interactive mode

```bash
python -m netsentry
```

```
╔══════════════════════════════╗
║          NetSentry           ║
║   Local Network Inspector    ║
╚══════════════════════════════╝

Local IP : 192.168.1.10
Network  : 192.168.1.0/24

[1] Discover devices
[2] Network information
[3] Export results
[4] Exit

Choose:
```

### Non-interactive

```bash
# Just print network information
python -m netsentry --network-info

# Run a discovery and exit
python -m netsentry --discover

# Run a discovery and export JSON + CSV
python -m netsentry --export reports

# Use a custom config file
python -m netsentry --config /path/to/config.json
```

### Example output

```
NetSentry
────────────────────────────────────────────────

Network: 192.168.1.0/24

IP              Hostname                Status
────────────────────────────────────────────────
192.168.1.1     router                   ONLINE
192.168.1.5     phone                    ONLINE
192.168.1.10    laptop                   ONLINE

3 device(s) found.
```

---

## Project Structure

```
netsentry/
├── netsentry/
│   ├── __init__.py      # package metadata
│   ├── __main__.py      # `python -m netsentry` entry
│   ├── main.py          # CLI, config loading, menu, orchestration
│   ├── network.py       # local IP, subnet, network info
│   ├── discovery.py     # TCP-connect device discovery + reverse DNS
│   └── reporter.py      # terminal table, JSON export, CSV export
├── tests/
│   ├── test_network.py
│   ├── test_discovery.py
│   └── test_reporter.py
├── README.md
├── requirements.txt
├── LICENSE
├── .gitignore
└── config.example.json
```

Every file has a single responsibility. `main.py` wires the pieces
together; it does not contain discovery or export logic itself.

---

## Testing

```bash
python -m unittest discover -s tests
```

Tests mock sockets and network calls, so they do not touch real devices.

---

## Output Formats

### Terminal

Fixed-width table with IP, hostname, and status columns.

### JSON

```json
{
    "network": "192.168.1.0/24",
    "devices": [
        {
            "ip": "192.168.1.1",
            "hostname": "router",
            "status": "online"
        }
    ]
}
```

### CSV

```
ip,hostname,status
192.168.1.1,router,online
192.168.1.5,phone,online
```

Reports are written to `reports/` by default and excluded via `.gitignore`.

---

## Configuration

`config.example.json`:

```json
{
    "timeout": 0.5,
    "ports": [80, 443, 22, 53],
    "output_directory": "reports"
}
```

- `timeout` — per-connection timeout in seconds (`0 < timeout <= 10`).
- `ports` — non-empty list of TCP ports to probe per host.
- `output_directory` — where JSON/CSV exports are written.

If `config.json` is absent, defaults are used. Malformed values are
rejected with a clear message.

---

## Limitations

V1 is a **basic local-network device-discovery tool**. It does not:

- identify services on open ports,
- fingerprint operating systems,
- track devices over time,
- reach beyond the detected local subnet.

Hosts that block all four default ports will not appear. Reverse DNS
may fail on networks without local resolver entries — the tool writes
`-` in the hostname column in that case.

---

## Responsible Use

NetSentry is intended for:

- your own devices,
- your own home or lab network,
- or any network where you have **explicit written authorization** to inspect.

Do not point NetSentry at networks you do not own or administer.

---

## Roadmap

### V1.1
- Better CLI experience
- Improved configuration handling
- Scan history
- Better terminal formatting

### V2
- Service identification
- Device-change detection
- Basic defensive security reports

### V3
- SQLite database
- Historical device tracking
- Web dashboard
- Optional notifications

V1 stays focused on simple, safe local device discovery. Future versions
build on top without changing the V1 contract.

---

## License

MIT License. See [LICENSE](LICENSE) for the full text.

You are free to use, modify, and distribute this project. Attribution
is appreciated but not required.
