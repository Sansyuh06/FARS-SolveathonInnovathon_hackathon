/*  app.js — DOM / UI Controller + Dashboard
    Bridges the simulation state to the HTML dashboard panels */

import { Simulation } from './simulation.js';
import { Renderer } from './renderer.js';
import { TASK_TYPES } from './config.js';

// ─── Boot ─────────────────────────────────────────────────────────────────
const sim = new Simulation();
const canvas = document.getElementById('sim-canvas');
const renderer = new Renderer(canvas);

// ─── DOM refs ─────────────────────────────────────────────────────────────
const $clock       = document.getElementById('sim-clock');
const $speedBtns   = document.querySelectorAll('.speed-btn');
const $pauseBtn    = document.getElementById('btn-pause');
const $resetBtn    = document.getElementById('btn-reset');

// KPI
const $kpiRobots   = document.getElementById('kpi-robots');
const $kpiAssisted = document.getElementById('kpi-assisted');
const $kpiTasks    = document.getElementById('kpi-tasks');
const $kpiResponse = document.getElementById('kpi-response');
const $kpiPending  = document.getElementById('kpi-pending');
const $kpiActive   = document.getElementById('kpi-active');

// Panels
const $robotList   = document.getElementById('robot-list');
const $taskQueue   = document.getElementById('task-queue');
const $activeList  = document.getElementById('active-tasks');
const $iotList     = document.getElementById('iot-list');
const $eventLog    = document.getElementById('event-log');

// Inspector
const $inspector       = document.getElementById('inspector-panel');
const $inspectorTitle  = document.getElementById('inspector-title');
const $inspectorBody   = document.getElementById('inspector-body');
const $inspectorClose  = document.getElementById('inspector-close');

// Tabs
const $tabs = document.querySelectorAll('.tab-btn');
const $tabPanels = document.querySelectorAll('.tab-panel');

// ─── Tab Switching ────────────────────────────────────────────────────────
$tabs.forEach(btn => {
  btn.addEventListener('click', () => {
    const target = btn.dataset.tab;
    $tabs.forEach(b => b.classList.remove('active'));
    $tabPanels.forEach(p => p.classList.remove('active'));
    btn.classList.add('active');
    document.getElementById(`tab-${target}`).classList.add('active');
  });
});

// ─── Speed Controls ───────────────────────────────────────────────────────
$speedBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    const speed = parseInt(btn.dataset.speed);
    sim.setSpeed(speed);
    $speedBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});

// ─── Pause / Resume ───────────────────────────────────────────────────────
$pauseBtn.addEventListener('click', () => {
  if (sim.running) {
    sim.pause();
    $pauseBtn.textContent = '▶ Resume';
    $pauseBtn.classList.add('paused');
  } else {
    sim.resume();
    $pauseBtn.textContent = '⏸ Pause';
    $pauseBtn.classList.remove('paused');
  }
});

// ─── Reset ────────────────────────────────────────────────────────────────
$resetBtn.addEventListener('click', () => {
  sim.reset();
  $eventLog.innerHTML = '';
  renderer.selectedRobot = null;
  $inspector.classList.remove('visible');
  sim.start();
  $pauseBtn.textContent = '⏸ Pause';
  $pauseBtn.classList.remove('paused');
});

// ─── Canvas Click → Select Robot ──────────────────────────────────────────
canvas.addEventListener('click', e => {
  const rect = canvas.getBoundingClientRect();
  const sx = e.clientX - rect.left;
  const sy = e.clientY - rect.top;
  const hit = renderer.hitTestRobot(sx, sy, sim);
  if (hit !== null) {
    renderer.selectedRobot = hit;
    renderer.autoFollow = true;
    showInspector(hit);
  } else {
    renderer.selectedRobot = null;
    renderer.autoFollow = false;
    $inspector.classList.remove('visible');
  }
});

// ─── Inspector ────────────────────────────────────────────────────────────
$inspectorClose.addEventListener('click', () => {
  renderer.selectedRobot = null;
  renderer.autoFollow = false;
  $inspector.classList.remove('visible');
});

function showInspector(idx) {
  $inspector.classList.add('visible');
  updateInspector(idx);
}

function updateInspector(idx) {
  const robot = sim.robots[idx];
  if (!robot) return;
  const info = robot.getInfo();
  $inspectorTitle.innerHTML = `<span style="color:${info.color}">●</span> ${info.name} Inspector`;

  const batColor = info.battery > 50 ? '#10b981' : info.battery > 20 ? '#f59e0b' : '#ef4444';
  $inspectorBody.innerHTML = `
    <div class="insp-row"><span class="insp-label">State</span><span class="state-badge state-${info.state}">${info.stateIcon}</span></div>
    <div class="insp-row"><span class="insp-label">Battery</span>
      <div class="bat-bar-wrap"><div class="bat-bar" style="width:${info.battery}%;background:${batColor}"></div></div>
      <span class="bat-pct">${info.battery}%</span>
    </div>
    <div class="insp-row"><span class="insp-label">Location</span><span>${info.location}</span></div>
    <div class="insp-row"><span class="insp-label">Task</span><span class="insp-task">${info.currentTask}</span></div>
    <div class="insp-row"><span class="insp-label">Completed</span><span>${info.tasksCompleted} tasks</span></div>
    <div class="insp-thought">
      <div class="thought-header">AI Thought Stream</div>
      <pre class="thought-log">${info.thoughts}</pre>
    </div>
  `;
}

// ─── Event Log ────────────────────────────────────────────────────────────
sim.onEvent(entry => {
  const div = document.createElement('div');
  div.className = `log-entry log-${entry.type}`;
  const mins = Math.floor(entry.time / 60);
  const secs = Math.floor(entry.time % 60);
  const ts = `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  div.innerHTML = `<span class="log-time">[${ts}]</span> <span class="log-type">[${entry.type.toUpperCase()}]</span> ${entry.message}`;
  $eventLog.appendChild(div);
  // Auto-scroll
  $eventLog.scrollTop = $eventLog.scrollHeight;
  // Limit DOM nodes
  while ($eventLog.children.length > 150) $eventLog.removeChild($eventLog.firstChild);
});

// ─── Update Loop ──────────────────────────────────────────────────────────
let _uiFrameCount = 0;

sim.onTick(() => {
  // Render canvas
  renderer.render(sim);

  _uiFrameCount++;
  if (_uiFrameCount % 3 !== 0) return;  // throttle DOM updates to ~20fps

  // Clock
  const t = sim.elapsedTime;
  const h = Math.floor(t / 3600);
  const m = Math.floor((t % 3600) / 60);
  const s = Math.floor(t % 60);
  $clock.textContent = `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;

  // KPIs
  const metrics = sim.getMetrics();
  $kpiRobots.textContent = `${metrics.activeRobots} / ${metrics.totalRobots}`;
  $kpiAssisted.textContent = metrics.patientsAssisted;
  $kpiTasks.textContent = metrics.completed;
  $kpiResponse.textContent = `${metrics.avgResponseTime}s`;
  $kpiPending.textContent = metrics.pending;
  $kpiActive.textContent = metrics.active;

  // Robot cards
  $robotList.innerHTML = sim.robots.map((r, i) => {
    const info = r.getInfo();
    const batColor = info.battery > 50 ? '#10b981' : info.battery > 20 ? '#f59e0b' : '#ef4444';
    const sel = renderer.selectedRobot === i ? 'selected' : '';
    return `
      <div class="robot-card ${sel}" data-idx="${i}" style="--robot-color:${info.color}">
        <div class="rc-header">
          <span class="rc-dot" style="background:${info.color}"></span>
          <span class="rc-name">${info.name}</span>
          <span class="state-badge state-${info.state}">${info.stateIcon}</span>
        </div>
        <div class="rc-bat">
          <div class="rc-bat-bar" style="width:${info.battery}%;background:${batColor}"></div>
        </div>
        <div class="rc-meta">${info.location} · ${info.battery}%</div>
      </div>`;
  }).join('');

  // Click robot cards
  $robotList.querySelectorAll('.robot-card').forEach(card => {
    card.addEventListener('click', () => {
      const idx = parseInt(card.dataset.idx);
      renderer.selectedRobot = idx;
      renderer.autoFollow = true;
      showInspector(idx);
    });
  });

  // Task queue
  const queue = sim.taskManager.getQueueDisplay(10);
  $taskQueue.innerHTML = queue.length > 0
    ? queue.map(t => `<div class="task-item p${t.priority}">${t.text}</div>`).join('')
    : '<div class="empty-state">No pending tasks</div>';

  // Active tasks
  const active = sim.taskManager.getActiveDisplay(8);
  $activeList.innerHTML = active.length > 0
    ? active.map(t => `<div class="task-item active">${t.text}</div>`).join('')
    : '<div class="empty-state">No active tasks</div>';

  // IoT devices
  $iotList.innerHTML = sim.iot.getDeviceList().map(d => {
    const statusClass = d.status === 'online' ? 'online' : d.status === 'triggered' ? 'triggered' : 'capturing';
    return `
      <div class="iot-card">
        <span class="iot-dot ${statusClass}" style="opacity:${0.4 + d.activity * 0.6}"></span>
        <span class="iot-type">${d.type}</span>
        <span class="iot-loc">${d.location}</span>
        <span class="iot-status">${d.status}</span>
      </div>`;
  }).join('');

  // Update inspector if open
  if (renderer.selectedRobot !== null && $inspector.classList.contains('visible')) {
    updateInspector(renderer.selectedRobot);
  }
});

// ─── Auto-start ───────────────────────────────────────────────────────────
sim.start();
