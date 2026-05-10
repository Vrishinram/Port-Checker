/**
 * Port Status Checker — Frontend Logic
 * Communicates with Flask backend via /api/scan
 */

const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => [...document.querySelectorAll(sel)];

// ── DOM refs ──────────────────────────────────────────────────────────────────
const hostInput    = $("#host-input");
const portsInput   = $("#ports-input");
const timeoutInput = $("#timeout-input");
const scanBtn      = $("#scan-btn");
const errorToast   = $("#error-toast");
const errorMsg     = $("#error-msg");
const resultsCard  = $("#results-card");
const resultsBody  = $("#results-body");

// ── Presets ───────────────────────────────────────────────────────────────────
const PRESETS = {
  web:      [80, 443, 8080, 8443],
  database: [3306, 5432, 1433, 1521, 27017, 6379],
  email:    [25, 110, 143, 465, 587, 993, 995],
  remote:   [22, 23, 3389, 5900],
  common:   [20, 21, 22, 23, 25, 53, 80, 110, 143, 443, 465, 587, 993, 995,
             1433, 1521, 3306, 3389, 5432, 5900, 6379, 8080, 8443, 27017],
};

$$(".preset-chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    const key = chip.dataset.preset;
    if (!PRESETS[key]) return;

    // Toggle active state
    const isActive = chip.classList.contains("preset-chip--active");
    $$(".preset-chip").forEach((c) => c.classList.remove("preset-chip--active"));

    if (isActive) {
      portsInput.value = "";
    } else {
      chip.classList.add("preset-chip--active");
      portsInput.value = PRESETS[key].join(", ");
    }
    portsInput.focus();
  });
});

// Clear preset highlight when user manually edits ports
portsInput.addEventListener("input", () => {
  $$(".preset-chip").forEach((c) => c.classList.remove("preset-chip--active"));
});

// ── Helpers ───────────────────────────────────────────────────────────────────
function parsePorts(raw) {
  const ports = new Set();
  const parts = raw.split(/[\s,]+/).filter(Boolean);
  for (const part of parts) {
    if (part.includes("-")) {
      const [a, b] = part.split("-").map(Number);
      if (!isNaN(a) && !isNaN(b) && a <= b) {
        for (let i = a; i <= b; i++) ports.add(i);
      }
    } else {
      const n = Number(part);
      if (!isNaN(n) && n >= 1 && n <= 65535) ports.add(n);
    }
  }
  return [...ports].sort((a, b) => a - b);
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorToast.classList.add("visible");
  setTimeout(() => errorToast.classList.remove("visible"), 5000);
}

function setLoading(on) {
  scanBtn.disabled = on;
  scanBtn.classList.toggle("scan-btn--loading", on);
}

// ── Status helpers ────────────────────────────────────────────────────────────
function statusIcon(status) {
  const dot = `<span class="status-dot"></span>`;
  return `<span class="status-badge status-badge--${status}">${dot}${status}</span>`;
}

// ── Render results ────────────────────────────────────────────────────────────
function renderResults(data) {
  // Meta
  $("#meta-host").textContent     = `${data.host} (${data.ip})`;
  $("#meta-ports").textContent    = data.summary.total;
  $("#meta-duration").textContent = `${data.elapsed}s`;

  // Summary pills
  $("#sum-open").textContent     = data.summary.open;
  $("#sum-closed").textContent   = data.summary.closed;
  $("#sum-filtered").textContent = data.summary.filtered;
  $("#sum-error").textContent    = data.summary.error;

  // Hide zero-count pills
  $(".summary-pill--filtered").style.display = data.summary.filtered ? "" : "none";
  $(".summary-pill--error").style.display    = data.summary.error    ? "" : "none";

  // Table rows
  resultsBody.innerHTML = "";
  data.results.forEach((r, i) => {
    const tr = document.createElement("tr");
    tr.style.animationDelay = `${i * 30}ms`;
    tr.innerHTML = `
      <td class="port-cell">${r.port}</td>
      <td>${statusIcon(r.status)}</td>
      <td class="service-cell">${r.service}</td>
      <td class="latency-cell">${r.latency != null ? r.latency + ' ms' : '—'}</td>
      <td class="detail-cell">${r.detail}</td>
    `;
    resultsBody.appendChild(tr);
  });

  resultsCard.classList.add("visible");
  resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

// ── Scan ──────────────────────────────────────────────────────────────────────
async function runScan() {
  errorToast.classList.remove("visible");
  resultsCard.classList.remove("visible");

  const host    = hostInput.value.trim() || "localhost";
  const ports   = parsePorts(portsInput.value);
  const timeout = parseFloat(timeoutInput.value) || 2;

  if (ports.length === 0) {
    showError("Please enter at least one valid port number (1–65535).");
    return;
  }
  if (ports.length > 1024) {
    showError("Maximum 1 024 ports per scan. Please narrow your range.");
    return;
  }

  setLoading(true);

  try {
    const res = await fetch("/api/scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ host, ports, timeout }),
    });
    const json = await res.json();
    if (!res.ok) {
      showError(json.error || `Server error (${res.status})`);
      return;
    }
    renderResults(json);
  } catch (err) {
    showError("Network error — is the server running?");
    console.error(err);
  } finally {
    setLoading(false);
  }
}

scanBtn.addEventListener("click", runScan);

// Allow Enter key to trigger scan from any input
[hostInput, portsInput, timeoutInput].forEach((el) => {
  el.addEventListener("keydown", (e) => {
    if (e.key === "Enter") { e.preventDefault(); runScan(); }
  });
});
