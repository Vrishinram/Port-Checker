"""
Port Status Checker — Web Application
──────────────────────────────────────
Flask backend that exposes a REST API for scanning ports on remote or local
hosts.  The frontend communicates via JSON.
"""

import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


# ── Helpers ────────────────────────────────────────────────────────────────────

COMMON_PORTS = {
    20: "FTP Data",
    21: "FTP",
    22: "SSH",
    23: "Telnet",
    25: "SMTP",
    53: "DNS",
    80: "HTTP",
    110: "POP3",
    143: "IMAP",
    443: "HTTPS",
    465: "SMTPS",
    587: "SMTP (TLS)",
    993: "IMAPS",
    995: "POP3S",
    1433: "MSSQL",
    1521: "Oracle DB",
    3306: "MySQL",
    3389: "RDP",
    5432: "PostgreSQL",
    5900: "VNC",
    6379: "Redis",
    8080: "HTTP Alt",
    8443: "HTTPS Alt",
    27017: "MongoDB",
}


def _service_name(port: int) -> str:
    """Return a human-friendly service name for a port."""
    if port in COMMON_PORTS:
        return COMMON_PORTS[port]
    try:
        return socket.getservbyport(port, "tcp")
    except OSError:
        return "Unknown"


def check_port(host: str, port: int, timeout: float = 2.0) -> dict:
    """Check a single TCP port."""
    start = time.perf_counter()
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            code = s.connect_ex((host, port))
            latency = round((time.perf_counter() - start) * 1000, 1)
            if code == 0:
                return {
                    "port": port,
                    "status": "open",
                    "service": _service_name(port),
                    "latency": latency,
                    "detail": "Connection accepted",
                }
            return {
                "port": port,
                "status": "closed",
                "service": _service_name(port),
                "latency": latency,
                "detail": f"Refused (code {code})",
            }
    except socket.gaierror:
        return {
            "port": port,
            "status": "error",
            "service": _service_name(port),
            "latency": None,
            "detail": "DNS resolution failed",
        }
    except socket.timeout:
        latency = round((time.perf_counter() - start) * 1000, 1)
        return {
            "port": port,
            "status": "filtered",
            "service": _service_name(port),
            "latency": latency,
            "detail": "Connection timed out",
        }
    except OSError as exc:
        return {
            "port": port,
            "status": "error",
            "service": _service_name(port),
            "latency": None,
            "detail": str(exc),
        }


def resolve_host(host: str) -> str | None:
    try:
        return socket.gethostbyname(host)
    except socket.gaierror:
        return None


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/scan", methods=["POST"])
def api_scan():
    data = request.get_json(silent=True) or {}
    host = (data.get("host") or "localhost").strip()
    raw_ports = data.get("ports", [])
    timeout = float(data.get("timeout", 2))

    # Validate host
    ip = resolve_host(host)
    if ip is None:
        return jsonify({"error": f"Cannot resolve host '{host}'"}), 400

    # Validate ports
    ports: list[int] = []
    for p in raw_ports:
        try:
            p = int(p)
            if 1 <= p <= 65535:
                ports.append(p)
        except (ValueError, TypeError):
            pass
    if not ports:
        return jsonify({"error": "No valid ports specified"}), 400
    ports = sorted(set(ports))

    if len(ports) > 1024:
        return jsonify({"error": "Max 1024 ports per scan"}), 400

    # Clamp timeout
    timeout = max(0.5, min(timeout, 10))

    # Scan
    results = []
    workers = min(50, len(ports))
    scan_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futs = {pool.submit(check_port, host, p, timeout): p for p in ports}
        for f in as_completed(futs):
            results.append(f.result())
    results.sort(key=lambda r: r["port"])
    elapsed = round(time.perf_counter() - scan_start, 2)

    return jsonify({
        "host": host,
        "ip": ip,
        "elapsed": elapsed,
        "results": results,
        "summary": {
            "total": len(results),
            "open": sum(1 for r in results if r["status"] == "open"),
            "closed": sum(1 for r in results if r["status"] == "closed"),
            "filtered": sum(1 for r in results if r["status"] == "filtered"),
            "error": sum(1 for r in results if r["status"] == "error"),
        },
    })


@app.route("/api/presets")
def presets():
    """Return handy port presets for the UI."""
    return jsonify({
        "web": [80, 443, 8080, 8443],
        "database": [3306, 5432, 1433, 1521, 27017, 6379],
        "email": [25, 110, 143, 465, 587, 993, 995],
        "remote": [22, 23, 3389, 5900],
        "common": sorted(COMMON_PORTS.keys()),
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
