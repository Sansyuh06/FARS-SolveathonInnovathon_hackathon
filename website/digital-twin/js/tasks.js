/*  tasks.js — Task Manager + Priority Scheduler
    Direct port of full_simulation/task_manager.py */

import { TASK_TYPES } from './config.js';
import { getNodePosition } from './navigation.js';

let _taskIdCounter = 0;

export class Task {
  constructor(taskType, locationNode, priority = 1, description = '') {
    _taskIdCounter++;
    this.id = _taskIdCounter;
    this.taskType = taskType;
    this.locationNode = locationNode;
    this.priority = priority;       // 1=low, 2=med, 3=high, 4=urgent
    this.description = description;
    this.status = 'pending';        // pending, assigned, in_progress, completed
    this.assignedRobot = null;
    this.createdTime = Date.now();
    this.completedTime = null;
  }

  toString() {
    const label = TASK_TYPES[this.taskType] || this.taskType;
    return `[P${this.priority}] ${label} → ${this.locationNode}`;
  }
}


export class TaskManager {
  constructor() {
    this.taskQueue = [];       // pending tasks
    this.activeTasks = [];     // currently being executed
    this.completedTasks = [];  // finished
    this.totalResponseTime = 0;
    this.systemAlerts = [];
    this._onEvent = null;      // callback for event log
  }

  /** Register event callback: fn(eventType, message) */
  onEvent(fn) { this._onEvent = fn; }

  _emit(type, msg) {
    if (this._onEvent) this._onEvent(type, msg);
  }

  // ─── Task creation ──────────────────────────────────────────────────
  createTask(taskType, locationNode, priority = 1, description = '') {
    const task = new Task(taskType, locationNode, priority, description);
    this.taskQueue.push(task);
    const label = TASK_TYPES[taskType] || taskType;
    this.addAlert(`New task: ${label} → ${locationNode}`);
    this._emit('task', `New task queued: P${priority} ${label} → ${locationNode}`);
    return task;
  }

  // ─── Auto-generate from human agents ────────────────────────────────
  autoGenerateFromHumans(humanAgents) {
    for (const human of humanAgents) {
      if (human.needsHelp && human.helpRequestType) {
        // Check if we already have a pending/active task for this location
        const existing = [...this.taskQueue, ...this.activeTasks].some(
          t => t.locationNode === human.currentNode && (t.status === 'pending' || t.status === 'assigned')
        );
        if (!existing) {
          const desc = `${human.agentType.charAt(0).toUpperCase() + human.agentType.slice(1)} in ${human.currentNode} needs help`;
          let priority = 2;
          if (human.helpRequestType === 'deliver_medicine') priority = 3;
          if (human.helpRequestType === 'guide_patient') priority = 1;

          this.createTask(human.helpRequestType, human.currentNode, priority, desc);
          this._emit('alert', `Patient_${human.id} triggered ${TASK_TYPES[human.helpRequestType] || human.helpRequestType} in ${human.currentNode}`);
        }
      }
    }
  }

  // ─── Task assignment (priority scoring) ─────────────────────────────
  assignTasks(robots) {
    const pending = this.taskQueue
      .filter(t => t.status === 'pending')
      .sort((a, b) => b.priority - a.priority);

    const available = robots.filter(r => r.isAvailable());

    for (const task of pending) {
      if (available.length === 0) break;

      let bestRobot = null;
      let bestScore = -Infinity;
      const tPos = getNodePosition(task.locationNode);

      for (const robot of available) {
        const distance = Math.hypot(tPos.x - robot.worldX, tPos.z - robot.worldZ);
        const score = (5 * task.priority) - (1 * distance) + (0.5 * robot.battery);
        if (score > bestScore) {
          bestScore = score;
          bestRobot = robot;
        }
      }

      if (bestRobot) {
        task.status = 'assigned';
        task.assignedRobot = bestRobot.id;
        bestRobot.assignTask(task);

        const idx = this.taskQueue.indexOf(task);
        if (idx > -1) this.taskQueue.splice(idx, 1);
        this.activeTasks.push(task);
        available.splice(available.indexOf(bestRobot), 1);

        const label = TASK_TYPES[task.taskType] || task.taskType;
        this._emit('dispatch', `${bestRobot.name} dispatched to ${task.locationNode} (${label})`);
      }
    }
  }

  // ─── Completion tracking ────────────────────────────────────────────
  checkCompleted(robots) {
    const newlyCompleted = [];
    for (let i = this.activeTasks.length - 1; i >= 0; i--) {
      const task = this.activeTasks[i];
      if (task.status === 'completed') {
        this.activeTasks.splice(i, 1);
        this.completedTasks.push(task);
        if (task.completedTime && task.createdTime) {
          this.totalResponseTime += (task.completedTime - task.createdTime) / 1000;
        }
        newlyCompleted.push(task);
        const label = TASK_TYPES[task.taskType] || task.taskType;
        this._emit('completed', `R${task.assignedRobot + 1} completed ${label} at ${task.locationNode}`);
      }
    }
    return newlyCompleted;
  }

  // ─── Metrics ────────────────────────────────────────────────────────
  getMetrics() {
    const completed = this.completedTasks.length;
    const avgTime = completed > 0 ? this.totalResponseTime / completed : 0;
    return {
      pending: this.taskQueue.length,
      active: this.activeTasks.length,
      completed,
      avgResponseTime: Math.round(avgTime * 10) / 10,
    };
  }

  getQueueDisplay(max = 8) {
    return this.taskQueue.slice(0, max).map(t => {
      const label = TASK_TYPES[t.taskType] || t.taskType;
      return { priority: t.priority, text: `P${t.priority} ${label} → ${t.locationNode}` };
    });
  }

  getActiveDisplay(max = 5) {
    return this.activeTasks.slice(0, max).map(t => {
      const label = TASK_TYPES[t.taskType] || t.taskType;
      const rName = t.assignedRobot !== null ? `R${t.assignedRobot + 1}` : '?';
      return { robot: rName, text: `${rName}: ${label}` };
    });
  }

  // ─── Alerts ─────────────────────────────────────────────────────────
  addAlert(msg) {
    this.systemAlerts.push(msg);
    if (this.systemAlerts.length > 30) this.systemAlerts.splice(0, this.systemAlerts.length - 30);
  }

  getRecentAlerts(count = 5) {
    return this.systemAlerts.slice(-count);
  }
}
