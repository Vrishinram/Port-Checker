# ⚡ Port  Checker

A beautiful, modern web application to check whether TCP ports on any host are **open** or **closed**. Built with **Flask** and **vanilla JavaScript**, featuring a premium dark-themed UI with real-time scanning, concurrent port checks, and animated results.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0+-000000?logo=flask&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🎯 What It Does

Enter a **hostname** (or IP address) and one or more **port numbers**, and the tool will tell you which ports are accepting connections and which are not. This is useful for:

- **Network troubleshooting** — verify if a service is reachable
- **Server administration** — confirm firewall rules are working
- **Development** — check if your dev server is actually listening
- **Learning** — understand how systems communicate over TCP/IP

---

## ✨ Features

| Feature | Description |
|---|---|
| 🌐 **Web Interface** | Premium dark-mode UI with glassmorphism, gradients, and micro-animations |
| ⚡ **Concurrent Scanning** | Scans up to 50 ports simultaneously using thread pools |
| 🏷️ **Quick Presets** | One-click port sets: Web, Database, Email, Remote, All Common |
| 📊 **Rich Results** | Color-coded status badges, per-port latency, service name detection |
| 🔢 **Flexible Input** | Single ports, comma-separated lists, or ranges (e.g. `20-25`) |
| ⏱️ **Configurable Timeout** | Adjustable per-scan timeout (0.5s – 10s) |
| 📱 **Responsive** | Works on desktop and mobile screens |
| ⌨️ **Keyboard Shortcut** | Press `Enter` in any input field to start the scan |
| 🐍 **CLI Mode** | Includes a standalone CLI script for terminal-based scanning |

---

## 🖼️ Status Legend

| Badge | Meaning |
|---|---|
| 🟢 **Open** | Port is accepting connections — a service is listening |
| 🔴 **Closed** | Port refused the connection — nothing is listening |
| 🟡 **Filtered** | Connection timed out — likely blocked by a firewall |
| 🔵 **Error** | Could not complete the check (DNS failure, network error, etc.) |

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.10+** installed on your system
- **pip** (Python package manager)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/port-status-checker.git
cd port-status-checker

# 2. (Optional) Create a virtual environment
python -m venv venv
source venv/bin/activate        # Linux / macOS
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the Web App

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

### Run the CLI Version

```bash
# Interactive mode (prompts for input)
python port_checker.py

# Command-line flags
python port_checker.py -p 80 443 8080          # Check specific ports
python port_checker.py -H 192.168.1.1 -p 22    # Remote host
python port_checker.py -r 20-80                 # Port range
python port_checker.py -p 3306 -t 5             # Custom 5s timeout
```

---

## 📁 Project Structure

```
port-status-checker/
├── app.py                  # Flask backend with REST API
├── port_checker.py         # Standalone CLI scanner
├── requirements.txt        # Python dependencies
├── README.md
├── templates/
│   └── index.html          # Main web page
└── static/
    ├── css/
    │   └── style.css       # Design system & styles
    └── js/
        └── app.js          # Frontend logic
```

---

## 🔌 API Reference

### `POST /api/scan`

Scan one or more ports on a host.

**Request Body** (JSON):

```json
{
  "host": "example.com",
  "ports": [80, 443, 8080],
  "timeout": 2
}
```

**Response** (JSON):

```json
{
  "host": "example.com",
  "ip": "93.184.216.34",
  "elapsed": 0.45,
  "summary": {
    "total": 3,
    "open": 2,
    "closed": 1,
    "filtered": 0,
    "error": 0
  },
  "results": [
    {
      "port": 80,
      "status": "open",
      "service": "HTTP",
      "latency": 42.3,
      "detail": "Connection accepted"
    }
  ]
}
```

### `GET /api/presets`

Returns preset port groups (web, database, email, remote, common).

---

## 🛠️ How It Works

1. **Frontend** sends a JSON payload to `/api/scan` with the target host, ports, and timeout.
2. **Backend** resolves the hostname, validates inputs, then spawns a thread pool (`ThreadPoolExecutor`).
3. Each thread opens a **TCP socket** (`socket.connect_ex`) to test a single port.
4. Results are collected, sorted, and returned as JSON with status, service name, and latency.
5. **Frontend** renders the results with animated table rows, color-coded badges, and summary pills.

---

## ⚠️ Important Notes

- This tool performs **TCP connect scans** — it fully establishes (or attempts) a connection. This is the safest and most portable scan type.
- Always have **permission** before scanning hosts you don't own.
- Firewalls may cause ports to appear as "filtered" (timeout) rather than "closed".
- The maximum scan size is **1,024 ports** per request to prevent abuse.

---

## 📄 License

This project is open-source under the [MIT License](LICENSE).

---

<p align="center">
  Built with ❤️ using Flask &amp; vanilla JavaScript
</p>
