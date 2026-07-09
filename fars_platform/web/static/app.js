const API = window.location.origin;

function el(id) { return document.getElementById(id); }

async function fetchJSON(path, options) {
  const r = await fetch(API + path, options);
  return r.json();
}

function renderMetrics(data) {
  const grid = el("metrics-grid");
  const sim = data.simulation || {};
  const items = [
    ["Registered", data.registered_users],
    ["Attendance today", data.attendance_today],
    ["Access granted", data.access_granted],
    ["Access denied", data.access_denied],
    ["Devices online", data.devices_online],
    ["Robots active", sim.robots_active ?? "-"],
    ["Tasks completed", sim.tasks_completed ?? "-"],
    ["Avg response (s)", sim.avg_response_sec ?? "-"],
  ];
  grid.innerHTML = items.map(([lbl, val]) =>
    `<div class="metric"><div class="val">${val}</div><div class="lbl">${lbl}</div></div>`
  ).join("");
}

async function loadDevices() {
  const list = await fetchJSON("/api/devices");
  el("devices-list").innerHTML = list.map(d =>
    `<li>${d.id} — ${d.device_type} @ ${d.location} [${d.status}]</li>`
  ).join("") || "<li>No devices</li>";
}

async function loadAttendance() {
  const list = await fetchJSON("/api/attendance");
  el("attendance-list").innerHTML = list.map(a =>
    `<li>${a.recorded_at} — ${a.name || a.student_id} @ ${a.location}</li>`
  ).join("") || "<li>No records yet</li>";
}

async function loadAccess() {
  const list = await fetchJSON("/api/access");
  el("access-list").innerHTML = list.map(a =>
    `<li class="${a.granted ? "granted" : "denied"}">${a.recorded_at} — ${a.student_id || "unknown"} — ${a.reason}</li>`
  ).join("") || "<li>No access events</li>";
}

function renderEvents(events) {
  const list = events || [];
  el("events-list").innerHTML = list.map(e =>
    `<li>[${e.category}] ${e.message} (${e.recorded_at})</li>`
  ).join("") || "<li>No events</li>";
}

async function refresh() {
  try {
    const data = await fetchJSON("/api/analytics");
    renderMetrics(data);
    renderEvents(data.recent_events);
    el("status").textContent = "Live";
    el("status").className = "badge ok";
    await Promise.all([loadDevices(), loadAttendance(), loadAccess()]);
  } catch (e) {
    el("status").textContent = "Offline";
    console.error(e);
  }
}

el("cmd-btn").onclick = async () => {
  const text = el("cmd-input").value.trim();
  if (!text) return;
  const res = await fetchJSON("/api/command", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  el("feedback").textContent = res.ok ? `Command queued: ${text}` : "Command failed";
  el("cmd-input").value = "";
};

el("voice-btn").onclick = async () => {
  const text = el("voice-input").value.trim() || "assist patient in room 3";
  const res = await fetchJSON("/api/voice", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  el("feedback").textContent = res.ok ? `Voice: ${text}` : "Voice failed";
};

el("scan-btn").onclick = async () => {
  const res = await fetchJSON("/api/scan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ location: "Entrance" }),
  });
  const name = res.student?.name || "unknown";
  el("feedback").textContent = res.granted
    ? `Access granted: ${name}`
    : `Access denied: ${res.recognition?.reason || "unknown"}`;
  refresh();
};

refresh();
setInterval(refresh, 3000);

function connectRLWebsocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = protocol + '//' + window.location.host + '/ws/rl';
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    el("rl-ep").textContent = data.episode;
    el("rl-rew").textContent = data.reward;
    el("rl-loss").textContent = data.loss;
    el("rl-stab").textContent = data.gait_stability;
  };
  
  ws.onclose = () => {
    setTimeout(connectRLWebsocket, 3000);
  };
}

connectRLWebsocket();
