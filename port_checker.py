#!/usr/bin/env python3
"""
Port Status Checker
───────────────────
A utility to check whether a specific port on a given host is open or closed.
Supports scanning single ports, multiple ports, or a range of ports with
optional timeout configuration.

Usage:
    python port_checker.py                          # Interactive mode
    python port_checker.py -p 80                    # Check port 80 on localhost
    python port_checker.py -H 192.168.1.1 -p 22    # Check port 22 on a remote host
    python port_checker.py -p 80 443 8080           # Check multiple ports
    python port_checker.py -r 20-25                 # Check a range of ports
    python port_checker.py -p 80 -t 5               # Custom timeout (seconds)
"""

import argparse
import socket
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ── ANSI colour codes ──────────────────────────────────────────────────────────
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def print_banner() -> None:
    """Display an ASCII art banner."""
    banner = f"""
{CYAN}{BOLD}╔══════════════════════════════════════════╗
║         ⚡  Port Status Checker  ⚡      ║
╚══════════════════════════════════════════╝{RESET}
{DIM}  Check if ports are open or closed on
  any host quickly and efficiently.{RESET}
"""
    print(banner)


def check_port(host: str, port: int, timeout: float = 2.0) -> dict:
    """
    Check whether a single port on the given host is open.

    Parameters
    ----------
    host : str
        Hostname or IP address to check.
    port : int
        Port number (1–65535).
    timeout : float
        Connection timeout in seconds.

    Returns
    -------
    dict
        A dictionary with keys: host, port, status ('open' | 'closed'), detail.
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            if result == 0:
                # Try to grab the service name for extra context
                try:
                    service = socket.getservbyport(port, "tcp")
                except OSError:
                    service = "unknown"
                return {
                    "host": host,
                    "port": port,
                    "status": "open",
                    "service": service,
                    "detail": "Connection successful",
                }
            else:
                return {
                    "host": host,
                    "port": port,
                    "status": "closed",
                    "service": "—",
                    "detail": f"Connection refused (code {result})",
                }
    except socket.gaierror:
        return {
            "host": host,
            "port": port,
            "status": "error",
            "service": "—",
            "detail": "Hostname could not be resolved",
        }
    except socket.timeout:
        return {
            "host": host,
            "port": port,
            "status": "closed",
            "service": "—",
            "detail": "Connection timed out",
        }
    except OSError as exc:
        return {
            "host": host,
            "port": port,
            "status": "error",
            "service": "—",
            "detail": str(exc),
        }


def resolve_host(host: str) -> str | None:
    """Resolve a hostname to an IP address, returning None on failure."""
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


def format_result(result: dict) -> str:
    """Return a colour-coded, human-readable line for a single result."""
    port_str = f"{result['port']:>5}"
    if result["status"] == "open":
        icon = f"{GREEN}● OPEN  {RESET}"
    elif result["status"] == "closed":
        icon = f"{RED}○ CLOSED{RESET}"
    else:
        icon = f"{YELLOW}⚠ ERROR {RESET}"

    return (
        f"  {icon}  "
        f"Port {BOLD}{port_str}{RESET}  │  "
        f"Service: {CYAN}{result['service']:15}{RESET}  │  "
        f"{DIM}{result['detail']}{RESET}"
    )


def scan_ports(host: str, ports: list[int], timeout: float = 2.0) -> list[dict]:
    """
    Scan multiple ports concurrently and return results sorted by port number.
    """
    results: list[dict] = []
    max_workers = min(50, len(ports))  # cap threads for safety

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(check_port, host, port, timeout): port
            for port in ports
        }
        for future in as_completed(futures):
            results.append(future.result())

    results.sort(key=lambda r: r["port"])
    return results


def print_results(results: list[dict]) -> None:
    """Pretty-print scan results with a summary."""
    print(f"\n{BOLD}{'─' * 72}{RESET}")
    print(f"{BOLD}  SCAN RESULTS{RESET}")
    print(f"{BOLD}{'─' * 72}{RESET}")

    for r in results:
        print(format_result(r))

    open_count = sum(1 for r in results if r["status"] == "open")
    closed_count = sum(1 for r in results if r["status"] == "closed")
    error_count = sum(1 for r in results if r["status"] == "error")

    print(f"{BOLD}{'─' * 72}{RESET}")
    summary_parts = [
        f"{GREEN}{open_count} open{RESET}",
        f"{RED}{closed_count} closed{RESET}",
    ]
    if error_count:
        summary_parts.append(f"{YELLOW}{error_count} errors{RESET}")
    print(f"  Summary: {' │ '.join(summary_parts)}  "
          f"(total {len(results)} port{'s' if len(results) != 1 else ''})")
    print()


def parse_port_range(range_str: str) -> list[int]:
    """Parse a 'start-end' string into a list of port numbers."""
    try:
        parts = range_str.split("-")
        if len(parts) != 2:
            raise ValueError
        start, end = int(parts[0]), int(parts[1])
        if not (1 <= start <= 65535 and 1 <= end <= 65535 and start <= end):
            raise ValueError
        return list(range(start, end + 1))
    except ValueError:
        print(f"{RED}Error:{RESET} Invalid port range '{range_str}'. "
              f"Use format: START-END (e.g. 20-25)")
        sys.exit(1)


def interactive_mode() -> None:
    """Run the checker in interactive (prompt-based) mode."""
    print_banner()

    # ── Host ───────────────────────────────────────────────────────────────
    host = input(f"  {CYAN}Enter host{RESET} [localhost]: ").strip() or "localhost"
    ip = resolve_host(host)
    if ip is None:
        print(f"\n  {RED}✗ Could not resolve host '{host}'.{RESET}")
        sys.exit(1)
    print(f"  {DIM}Resolved to {ip}{RESET}")

    # ── Ports ──────────────────────────────────────────────────────────────
    port_input = input(
        f"  {CYAN}Enter port(s){RESET} (e.g. 80, 80 443, or 20-25): "
    ).strip()
    if not port_input:
        print(f"  {RED}✗ No port specified.{RESET}")
        sys.exit(1)

    if "-" in port_input and " " not in port_input:
        ports = parse_port_range(port_input)
    else:
        try:
            ports = [int(p) for p in port_input.replace(",", " ").split()]
            for p in ports:
                if not 1 <= p <= 65535:
                    raise ValueError(f"Port {p} out of range")
        except ValueError as exc:
            print(f"  {RED}✗ Invalid port input: {exc}{RESET}")
            sys.exit(1)

    # ── Timeout ────────────────────────────────────────────────────────────
    timeout_input = input(
        f"  {CYAN}Timeout in seconds{RESET} [2]: "
    ).strip() or "2"
    try:
        timeout = float(timeout_input)
        if timeout <= 0:
            raise ValueError
    except ValueError:
        print(f"  {RED}✗ Invalid timeout value.{RESET}")
        sys.exit(1)

    # ── Scan ───────────────────────────────────────────────────────────────
    print(f"\n  {DIM}Scanning {host} ({ip}) …{RESET}")
    start_time = time.perf_counter()
    results = scan_ports(host, ports, timeout)
    elapsed = time.perf_counter() - start_time

    print_results(results)
    print(f"  {DIM}Scan completed in {elapsed:.2f}s{RESET}\n")


def cli_mode() -> None:
    """Run the checker using command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Port Status Checker — quickly test if ports are open or closed.",
        epilog="Examples:\n"
               "  %(prog)s -p 80\n"
               "  %(prog)s -H 192.168.1.1 -p 22 443\n"
               "  %(prog)s -r 80-90 -t 3\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-H", "--host",
        default="localhost",
        help="Target hostname or IP (default: localhost)",
    )
    parser.add_argument(
        "-p", "--ports",
        nargs="+",
        type=int,
        help="One or more port numbers to check",
    )
    parser.add_argument(
        "-r", "--range",
        dest="port_range",
        help="Port range to scan, e.g. 20-25",
    )
    parser.add_argument(
        "-t", "--timeout",
        type=float,
        default=2.0,
        help="Connection timeout in seconds (default: 2)",
    )
    args = parser.parse_args()

    print_banner()

    host = args.host
    ip = resolve_host(host)
    if ip is None:
        print(f"  {RED}✗ Could not resolve host '{host}'.{RESET}")
        sys.exit(1)
    print(f"  {BOLD}Host:{RESET} {host} ({ip})")

    # Determine port list
    ports: list[int] = []
    if args.ports:
        ports.extend(args.ports)
    if args.port_range:
        ports.extend(parse_port_range(args.port_range))
    if not ports:
        parser.error("You must specify at least one port via -p or -r.")

    # Validate port range
    for p in ports:
        if not 1 <= p <= 65535:
            print(f"  {RED}✗ Port {p} is out of valid range (1–65535).{RESET}")
            sys.exit(1)

    ports = sorted(set(ports))  # deduplicate & sort
    print(f"  {BOLD}Ports:{RESET} {', '.join(map(str, ports))}")
    print(f"  {BOLD}Timeout:{RESET} {args.timeout}s")
    print(f"  {DIM}Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")

    start_time = time.perf_counter()
    results = scan_ports(host, ports, args.timeout)
    elapsed = time.perf_counter() - start_time

    print_results(results)
    print(f"  {DIM}Scan completed in {elapsed:.2f}s{RESET}\n")


# ── Entry point ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        if len(sys.argv) > 1:
            cli_mode()
        else:
            interactive_mode()
    except KeyboardInterrupt:
        print(f"\n\n  {YELLOW}Scan cancelled by user.{RESET}\n")
        sys.exit(130)
