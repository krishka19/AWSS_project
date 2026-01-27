const els = {
  startBtn: document.getElementById("startBtn"),
  stopBtn: document.getElementById("stopBtn"),

  statusPill: document.getElementById("statusPill"),
  statusText: document.getElementById("statusText"),

  uptimeTag: document.getElementById("uptimeTag"),
  lastSeenTag: document.getElementById("lastSeenTag"),

  camState: document.getElementById("camState"),
  sensorState: document.getElementById("sensorState"),
  procState: document.getElementById("procState"),

  visionImg: document.getElementById("visionImg"),
  visionMode: document.getElementById("visionMode"),
  visionTime: document.getElementById("visionTime"),

  classPill: document.getElementById("classPill"),
  classIcon: document.getElementById("classIcon"),
  classText: document.getElementById("classText"),

  confText: document.getElementById("confText"),
  confFill: document.getElementById("confFill"),

  bigCategory: document.getElementById("bigCategory"),
  bigReason: document.getElementById("bigReason"),
  miniConfidence: document.getElementById("miniConfidence"),
  miniTime: document.getElementById("miniTime"),
  miniImage: document.getElementById("miniImage"),
  lastTag: document.getElementById("lastTag"),

  timeline: document.getElementById("timeline"),
};

let startedAtISO = null;

function fmtTime(iso) {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleString();
}

function fmtUptime(startedAt) {
  if (!startedAt) return "uptime 00:00";
  const start = new Date(startedAt).getTime();
  const now = Date.now();
  const sec = Math.max(0, Math.floor((now - start) / 1000));
  const mm = String(Math.floor(sec / 60)).padStart(2, "0");
  const ss = String(sec % 60).padStart(2, "0");
  return `uptime ${mm}:${ss}`;
}

function setRunningUI(isRunning) {
  els.statusText.textContent = isRunning ? "RUNNING" : "STOPPED";
  els.statusPill.classList.toggle("running", isRunning);

  els.visionMode.textContent = isRunning ? "SCANNING" : "STANDBY";
  els.procState.textContent = isRunning ? "Running" : "Idle";

  // dots: camera/sensor always shown as ready for demo
  els.camState.textContent = "Ready";
  els.sensorState.textContent = isRunning ? "Active" : "Idle";
}

function clearBinHighlights() {
  document.querySelectorAll(".bin").forEach(b => b.classList.remove("active"));
}

function highlightBin(category) {
  clearBinHighlights();
  if (!category) return;
  const bin = document.querySelector(`.bin[data-bin="${category}"]`);
  if (bin) {
    bin.classList.add("active");
  }
}

function categoryIcon(category) {
  if (category === "RECYCLING") return "♻️";
  if (category === "COMPOST") return "🌱";
  if (category === "GARBAGE") return "🗑️";
  if (category === "ERROR") return "⚠️";
  return "⏳";
}

function eventBarColor(category) {
  if (category === "RECYCLING") return "rgba(57,255,176,.9)";
  if (category === "COMPOST") return "rgba(201,160,122,.95)";
  if (category === "GARBAGE") return "rgba(184,188,199,.95)";
  if (category === "ERROR") return "rgba(255,94,138,.95)";
  return "rgba(106,168,255,.9)";
}

function updateDetection(last) {
  if (!last) {
    els.lastSeenTag.textContent = "waiting…";
    els.lastTag.textContent = "—";
    els.bigCategory.textContent = "—";
    els.bigReason.textContent = "No detection yet.";
    els.miniConfidence.textContent = "—%";
    els.miniTime.textContent = "—";
    els.miniImage.textContent = "—";
    els.classIcon.textContent = "⏳";
    els.classText.textContent = "Awaiting Bag";
    els.confText.textContent = "—%";
    els.confFill.style.width = "0%";
    highlightBin(null);
    return;
  }

  const cat = last.category || "UNKNOWN";
  const conf = Math.round((last.confidence || 0) * 100);
  const reason = last.reason || "—";
  const ts = last.timestamp || null;

  els.lastSeenTag.textContent = ts ? `last seen ${fmtTime(ts)}` : "updated";
  els.lastTag.textContent = cat;
  els.bigCategory.textContent = cat;
  els.bigReason.textContent = reason;

  els.miniConfidence.textContent = `${conf}%`;
  els.miniTime.textContent = fmtTime(ts);
  els.miniImage.textContent = last.image_path ? "Available" : "—";

  els.classIcon.textContent = categoryIcon(cat);
  els.classText.textContent = cat;

  els.confText.textContent = `${conf}%`;
  els.confFill.style.width = `${Math.max(0, Math.min(100, conf))}%`;

  highlightBin(cat);

  // update vision overlay timestamp
  els.visionTime.textContent = ts ? fmtTime(ts) : "—";

  // refresh image (cache-bust)
  if (last.image_path) {
    els.visionImg.src = `/latest-image?ts=${Date.now()}`;
  }
}

function renderTimeline(history) {
  els.timeline.innerHTML = "";

  if (!history || history.length === 0) {
    const empty = document.createElement("div");
    empty.className = "event";
    empty.innerHTML = `
      <div class="event-bar" style="background:${eventBarColor("UNKNOWN")}"></div>
      <div class="event-main">
        <div class="event-title">No events yet</div>
        <div class="event-sub">Start the system to begin logging detections.</div>
      </div>
      <div class="event-right">
        <span class="pill">—</span>
      </div>
    `;
    els.timeline.appendChild(empty);
    return;
  }

  history.forEach(item => {
    const cat = item.category || "UNKNOWN";
    const conf = Math.round((item.confidence || 0) * 100);
    const ts = item.timestamp || null;

    const el = document.createElement("div");
    el.className = "event";
    el.innerHTML = `
      <div class="event-bar" style="background:${eventBarColor(cat)}"></div>
      <div class="event-main">
        <div class="event-title">${categoryIcon(cat)} ${cat}</div>
        <div class="event-sub">${item.reason || "—"}</div>
      </div>
      <div class="event-right">
        <span class="pill">${conf}%</span>
        <div class="event-sub" style="margin-top:6px">${ts ? fmtTime(ts) : "—"}</div>
      </div>
    `;
    els.timeline.appendChild(el);
  });
}

async function apiPost(url) {
  await fetch(url, { method: "POST" });
}

async function refresh() {
  const res = await fetch("/api/status");
  const data = await res.json();

  // running state
  setRunningUI(!!data.running);

  // startedAt for uptime if your API has it. If not, we still show uptime based on "first time running"
  if (data.startedAt) startedAtISO = data.startedAt;
  if (!startedAtISO && data.running) startedAtISO = new Date().toISOString();
  if (!data.running) startedAtISO = null;

  els.uptimeTag.textContent = fmtUptime(startedAtISO);

  // detection + timeline
  updateDetection(data.last);
  renderTimeline(data.history || []);
}

els.startBtn.addEventListener("click", async () => {
  await apiPost("/api/start");
  await refresh();
});

els.stopBtn.addEventListener("click", async () => {
  await apiPost("/api/stop");
  await refresh();
});

// initial image placeholder so it doesn't look broken
els.visionImg.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(`
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="700">
    <rect width="100%" height="100%" fill="rgba(7,10,18,0.25)"/>
    <text x="50%" y="50%" fill="rgba(159,176,214,0.8)" font-family="Arial" font-size="28" text-anchor="middle">
      Waiting for capture…
    </text>
  </svg>
`);

refresh();
setInterval(refresh, 1000);
