/*  humans.js — Human Agent Behaviors
    Direct port of full_simulation/human_agents.py */

import { HUMAN_COLORS, HUMAN_LOCATIONS } from './config.js';
import { getNodePosition, getAllRoomNodes, aStarPath } from './navigation.js';

export class HumanAgent {
  static allHumans = [];
  static _idCounter = 0;

  constructor(agentType, assignedRoom = null) {
    HumanAgent._idCounter++;
    this.id = HumanAgent._idCounter;
    this.agentType = agentType;
    this.state = 'idle';          // idle, walking, waiting, requesting_help
    this.assignedRoom = assignedRoom;
    this.needsHelp = false;
    this.helpRequestType = null;
    this.color = HUMAN_COLORS[agentType];

    // Home location
    if (assignedRoom) {
      this.homeNode = assignedRoom;
    } else if (HUMAN_LOCATIONS[agentType]) {
      const locs = HUMAN_LOCATIONS[agentType];
      this.homeNode = locs[Math.floor(Math.random() * locs.length)];
    } else {
      const rooms = getAllRoomNodes();
      this.homeNode = rooms[Math.floor(Math.random() * rooms.length)];
    }

    this.currentNode = this.homeNode;

    // World position
    const start = getNodePosition(this.homeNode);
    this.worldX = start.x + (Math.random() - 0.5) * 3;
    this.worldZ = start.z + (Math.random() - 0.5) * 3;

    // Path following
    this.pathNodes = [];
    this.pathWorld = [];
    this.pathIndex = 0;

    // Timers
    this.idleTimer = 3 + Math.random() * 9;
    this.helpTimer = agentType === 'patient' ? (15 + Math.random() * 30) : 999999;
    this.statusText = '';
    this.statusTimer = 0;

    HumanAgent.allHumans.push(this);
  }

  update(dt) {
    // Status text fade
    if (this.statusTimer > 0) {
      this.statusTimer -= dt;
      if (this.statusTimer <= 0) this.statusText = '';
    }

    switch (this.state) {
      case 'idle':      this._idleBehavior(dt); break;
      case 'walking':   this._walk(dt); break;
      case 'waiting':   this._wait(dt); break;
      case 'requesting_help': break; // stay in place
    }
  }

  _idleBehavior(dt) {
    this.idleTimer -= dt;
    if (this.idleTimer <= 0) {
      this._startWandering();
      this.idleTimer = 5 + Math.random() * 10;
    }

    // Patients may request help
    if (this.agentType === 'patient') {
      this.helpTimer -= dt;
      if (this.helpTimer <= 0 && !this.needsHelp) {
        this._requestHelp();
        this.helpTimer = 30 + Math.random() * 60;
      }
    }
  }

  _startWandering() {
    let target;
    if (this.agentType === 'patient') {
      target = Math.random() < 0.7
        ? this.homeNode
        : ['WaitingHall', 'MainHall', this.homeNode][Math.floor(Math.random() * 3)];
    } else if (HUMAN_LOCATIONS[this.agentType]) {
      const locs = [...HUMAN_LOCATIONS[this.agentType], this.homeNode];
      target = locs[Math.floor(Math.random() * locs.length)];
    } else {
      target = ['MainHall', 'WaitingHall', 'Reception'][Math.floor(Math.random() * 3)];
    }

    this.pathNodes = aStarPath(this.currentNode, target);
    this.pathWorld = this.pathNodes.map(n => getNodePosition(n));
    this.pathIndex = 0;

    if (this.pathWorld.length > 1) {
      this.state = 'walking';
    }
  }

  _walk(dt) {
    if (this.pathIndex >= this.pathWorld.length) {
      this.state = 'idle';
      if (this.pathNodes.length > 0) {
        this.currentNode = this.pathNodes[this.pathNodes.length - 1];
      }
      return;
    }

    const target = this.pathWorld[this.pathIndex];
    const dx = target.x - this.worldX;
    const dz = target.z - this.worldZ;
    const dist = Math.hypot(dx, dz);

    const speed = 3.0 * dt;
    if (dist < 0.5) {
      this.worldX = target.x;
      this.worldZ = target.z;
      if (this.pathIndex < this.pathNodes.length) {
        this.currentNode = this.pathNodes[this.pathIndex];
      }
      this.pathIndex++;
    } else {
      const move = Math.min(speed, dist);
      this.worldX += (dx / dist) * move;
      this.worldZ += (dz / dist) * move;
    }
  }

  _wait(dt) {
    this.idleTimer -= dt;
    if (this.idleTimer <= 0) {
      this.state = 'idle';
      this.statusText = '';
    }
  }

  _requestHelp() {
    this.needsHelp = true;
    this.helpRequestType = ['assist_patient', 'deliver_medicine', 'guide_patient'][Math.floor(Math.random() * 3)];
    this.state = 'requesting_help';
    this.statusText = '!';
  }

  fulfillHelp() {
    this.needsHelp = false;
    this.helpRequestType = null;
    this.state = 'idle';
    this.statusText = '✓';
    this.statusTimer = 3;
  }

  getInfo() {
    return {
      id: this.id,
      type: this.agentType,
      color: this.color,
      state: this.state,
      location: this.currentNode,
      needsHelp: this.needsHelp,
      worldX: this.worldX,
      worldZ: this.worldZ,
      statusText: this.statusText,
    };
  }
}
