/*  simulation.js — Master Simulation Loop
    Wires together all subsystems, drives the autonomous digital twin */

import { NUM_ROBOTS, NUM_PATIENTS, NUM_DOCTORS, NUM_NURSES, NUM_VISITORS } from './config.js';
import { getAllRoomNodes } from './navigation.js';
import { RobotAgent } from './robots.js';
import { HumanAgent } from './humans.js';
import { TaskManager } from './tasks.js';
import { IoTSimulator } from './iot.js';

export class Simulation {
  constructor() {
    this.robots = [];
    this.humans = [];
    this.taskManager = new TaskManager();
    this.iot = new IoTSimulator();
    this.patientsAssisted = 0;
    this.running = false;
    this.speed = 1;           // 1x, 2x, 5x
    this.elapsedTime = 0;     // simulation seconds
    this._lastTimestamp = 0;
    this._eventLog = [];      // [{time, type, message}]
    this._onEvent = null;
    this._animFrameId = null;
    this._onTick = null;      // called every frame with (sim) for rendering

    this._init();
  }

  _init() {
    // Clear static arrays
    RobotAgent.allRobots = [];
    HumanAgent.allHumans = [];
    HumanAgent._idCounter = 0;

    // Spawn robots
    for (let i = 0; i < NUM_ROBOTS; i++) {
      this.robots.push(new RobotAgent(i));
    }

    // Spawn patients
    const rooms = getAllRoomNodes();
    for (let i = 0; i < NUM_PATIENTS; i++) {
      const room = rooms[i % rooms.length];
      this.humans.push(new HumanAgent('patient', room));
    }

    // Spawn doctors
    for (let i = 0; i < NUM_DOCTORS; i++) {
      this.humans.push(new HumanAgent('doctor'));
    }

    // Spawn nurses
    for (let i = 0; i < NUM_NURSES; i++) {
      this.humans.push(new HumanAgent('nurse'));
    }

    // Spawn visitors
    for (let i = 0; i < NUM_VISITORS; i++) {
      this.humans.push(new HumanAgent('visitor'));
    }

    // Wire event handlers
    this.taskManager.onEvent((type, msg) => this._logEvent(type, msg));
    this.iot.onEvent((type, msg) => this._logEvent(type, msg));
    this.iot.onSecurityAlert((device) => {
      this.taskManager.createTask('security_check', device.node, 4, `Security check at ${device.location}`);
    });

    this._logEvent('system', 'FARS Digital Twin initialized.');
    this._logEvent('system', `Spawned ${this.robots.length} robots, ${this.humans.length} human agents.`);
  }

  _logEvent(type, message) {
    const entry = {
      time: this.elapsedTime,
      realTime: Date.now(),
      type,
      message,
    };
    this._eventLog.push(entry);
    if (this._eventLog.length > 200) this._eventLog.splice(0, this._eventLog.length - 200);
    if (this._onEvent) this._onEvent(entry);
  }

  onEvent(fn) { this._onEvent = fn; }
  onTick(fn) { this._onTick = fn; }

  // ─── Controls ───────────────────────────────────────────────────────
  start() {
    if (this.running) return;
    this.running = true;
    this._lastTimestamp = performance.now();
    this._logEvent('system', 'Simulation started.');
    this._loop(performance.now());
  }

  pause() {
    this.running = false;
    if (this._animFrameId) cancelAnimationFrame(this._animFrameId);
    this._logEvent('system', 'Simulation paused.');
  }

  resume() {
    if (this.running) return;
    this.running = true;
    this._lastTimestamp = performance.now();
    this._logEvent('system', 'Simulation resumed.');
    this._loop(performance.now());
  }

  setSpeed(s) {
    this.speed = s;
    this._logEvent('system', `Speed set to ${s}x.`);
  }

  reset() {
    this.pause();
    this.robots = [];
    this.humans = [];
    this.taskManager = new TaskManager();
    this.iot = new IoTSimulator();
    this.patientsAssisted = 0;
    this.elapsedTime = 0;
    this._eventLog = [];
    this._init();
  }

  // ─── Main Loop ──────────────────────────────────────────────────────
  _loop(timestamp) {
    if (!this.running) return;
    const realDt = (timestamp - this._lastTimestamp) / 1000;
    this._lastTimestamp = timestamp;
    const dt = Math.min(realDt, 0.1) * this.speed;  // cap to prevent spiral

    this.elapsedTime += dt;
    this._tick(dt);

    if (this._onTick) this._onTick(this);

    this._animFrameId = requestAnimationFrame(ts => this._loop(ts));
  }

  _tick(dt) {
    // 1. Update human agents
    for (const h of this.humans) h.update(dt);

    // 2. IoT device tick
    this.iot.update(dt, this.humans);

    // 3. Auto-generate tasks from patient requests
    this.taskManager.autoGenerateFromHumans(this.humans);

    // 4. Assign pending tasks to available robots
    this.taskManager.assignTasks(this.robots);

    // 5. Update robots
    for (const r of this.robots) r.update(dt);

    // 6. Check completed tasks
    const newlyCompleted = this.taskManager.checkCompleted(this.robots);
    for (const t of newlyCompleted) {
      this.patientsAssisted++;
      // Clear patient help flag
      for (const h of this.humans) {
        if (h.currentNode === t.locationNode && h.needsHelp) {
          h.fulfillHelp();
          break;
        }
      }
    }
  }

  // ─── Getters for UI ─────────────────────────────────────────────────
  getMetrics() {
    const m = this.taskManager.getMetrics();
    const activeRobots = this.robots.filter(r => r.state !== 'idle' && r.state !== 'charging').length;
    return {
      ...m,
      activeRobots,
      totalRobots: this.robots.length,
      patientsAssisted: this.patientsAssisted,
      elapsedTime: this.elapsedTime,
    };
  }

  getEventLog(count = 50) {
    return this._eventLog.slice(-count);
  }
}
