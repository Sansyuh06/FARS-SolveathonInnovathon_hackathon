/*  robots.js — Robot Agent FSM
    Direct port of full_simulation/robot_agent.py */

import {
  ROBOT_COLORS, MOVE_SPEED, BATTERY_DRAIN_RATE, BATTERY_CHARGE_RATE,
  LOW_BATTERY_THRESH, TASK_EXECUTE_TIME, STATE_ICONS,
} from './config.js';
import { aStarPath, getNodePosition } from './navigation.js';

export class RobotAgent {
  static allRobots = [];

  constructor(id) {
    this.id = id;
    this.name = `R${id + 1}`;
    this.color = ROBOT_COLORS[id % ROBOT_COLORS.length];
    this.state = 'idle';
    this.battery = 100;
    this.currentTask = null;
    this.taskHistory = [];
    this.currentNode = 'ChargingDock';
    this.targetNode = null;
    this.thoughtLog = ['System initialized.'];

    // Path following
    this.pathNodes = [];
    this.pathWorld = [];  // [{x,z}, ...]
    this.pathIndex = 0;
    this.taskTimer = 0;

    // World position
    const start = getNodePosition('ChargingDock');
    this.worldX = start.x + (id - 2) * 2;  // spread out at dock
    this.worldZ = start.z;

    // Visual
    this.angle = 0; // facing direction in degrees

    RobotAgent.allRobots.push(this);
  }

  addThought(msg) {
    this.thoughtLog.push(`> ${msg}`);
    if (this.thoughtLog.length > 8) this.thoughtLog.shift();
  }

  get stateIcon() { return STATE_ICONS[this.state] || '?'; }

  // ─── State transitions ──────────────────────────────────────────────
  setState(newState) {
    if (this.state !== newState) {
      this.addThought(`State: ${this.state.toUpperCase()} → ${newState.toUpperCase()}`);
    }
    this.state = newState;
  }

  // ─── Task assignment ────────────────────────────────────────────────
  assignTask(task) {
    this.currentTask = task;
    this.targetNode = task.locationNode;
    this.pathNodes = aStarPath(this.currentNode, this.targetNode);
    this.pathWorld = this.pathNodes.map(n => getNodePosition(n));
    this.pathIndex = 0;
    this.addThought(`Task accepted: ${task.taskType}`);
    this.addThought(`Path: ${this.pathNodes.length} nodes → ${this.targetNode}`);

    if (this.pathWorld.length > 0) {
      let navState = 'navigating';
      if (task.taskType === 'guide_patient' || task.taskType === 'escort_visitor') navState = 'guiding';
      else if (task.taskType === 'deliver_medicine') navState = 'delivering';
      else if (task.taskType === 'assist_patient') navState = 'assisting';
      this.setState(navState);
    }
  }

  // ─── Per-frame update ───────────────────────────────────────────────
  update(dt) {
    if (this.state === 'idle') {
      this._checkLowBattery();
      return;
    }
    if (this.state === 'charging') {
      this._charge(dt);
      return;
    }
    if (['navigating', 'guiding', 'delivering', 'assisting', 'returning'].includes(this.state)) {
      this._followPath(dt);
    }
  }

  _followPath(dt) {
    if (this.pathIndex >= this.pathWorld.length) {
      this._arriveAtDestination(dt);
      return;
    }

    const target = this.pathWorld[this.pathIndex];
    const dx = target.x - this.worldX;
    const dz = target.z - this.worldZ;
    const dist = Math.hypot(dx, dz);

    if (dist < 0.3) {
      this.worldX = target.x;
      this.worldZ = target.z;
      if (this.pathIndex < this.pathNodes.length) {
        this.currentNode = this.pathNodes[this.pathIndex];
      }
      this.pathIndex++;
    } else {
      let speed = MOVE_SPEED * dt;
      if (speed > dist) speed = dist;
      this.worldX += (dx / dist) * speed;
      this.worldZ += (dz / dist) * speed;
      this.angle = Math.atan2(dx, dz) * (180 / Math.PI);
    }

    // Battery drain
    this.battery -= BATTERY_DRAIN_RATE * dt;
    this.battery = Math.max(0, this.battery);
    if (this.battery <= 0) this._forceReturnToCharge();
  }

  _arriveAtDestination(dt) {
    if (this.state === 'returning') {
      this.addThought('Arrived at dock. Recharging.');
      this.setState('charging');
      this.currentTask = null;
      this.pathNodes = [];
      this.pathWorld = [];
      return;
    }

    if (this.currentTask) {
      if (this.taskTimer === 0) {
        this.addThought(`Executing task at ${this.currentNode}...`);
      }
      this.taskTimer += dt;
      if (this.taskTimer >= TASK_EXECUTE_TIME) {
        this._completeTask();
        this.taskTimer = 0;
      }
    }
  }

  _completeTask() {
    if (this.currentTask) {
      this.addThought('Task completed successfully.');
      this.currentTask.status = 'completed';
      this.currentTask.completedTime = Date.now();
      this.taskHistory.push(this.currentTask);
      this.currentTask = null;
    }
    this.targetNode = null;
    this.pathNodes = [];
    this.pathWorld = [];
    this.pathIndex = 0;
    this.setState('idle');
    this._checkLowBattery();
  }

  _checkLowBattery() {
    if (this.battery < LOW_BATTERY_THRESH && this.state === 'idle') {
      this._returnToCharge();
    }
  }

  _returnToCharge() {
    this.addThought(`Low battery (${this.battery.toFixed(0)}%). Returning to dock.`);
    this.targetNode = 'ChargingDock';
    this.pathNodes = aStarPath(this.currentNode, 'ChargingDock');
    this.pathWorld = this.pathNodes.map(n => getNodePosition(n));
    this.pathIndex = 0;
    this.setState('returning');
  }

  _forceReturnToCharge() {
    if (this.currentTask) {
      this.currentTask.status = 'pending';
      this.currentTask = null;
    }
    this._returnToCharge();
  }

  _charge(dt) {
    this.battery += BATTERY_CHARGE_RATE * dt * 100;
    if (this.battery >= 100) {
      this.battery = 100;
      this.addThought('Fully charged. Ready for tasks.');
      this.setState('idle');
    }
  }

  // ─── Info ───────────────────────────────────────────────────────────
  isAvailable() {
    return this.state === 'idle' && this.battery > LOW_BATTERY_THRESH;
  }

  getInfo() {
    return {
      id: this.id,
      name: this.name,
      color: this.color,
      state: this.state,
      stateIcon: this.stateIcon,
      battery: Math.round(this.battery * 10) / 10,
      currentTask: this.currentTask ? `${this.currentTask.taskType} → ${this.currentTask.locationNode}` : 'None',
      location: this.currentNode,
      tasksCompleted: this.taskHistory.length,
      thoughts: this.thoughtLog.slice(-6).join('\n'),
      worldX: this.worldX,
      worldZ: this.worldZ,
      pathWorld: this.pathWorld.slice(this.pathIndex),
    };
  }
}
