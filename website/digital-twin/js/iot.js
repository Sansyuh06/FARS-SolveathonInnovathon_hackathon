/*  iot.js — IoT Device Simulation
    Simulates IR sensors, cameras, face recognition, BLE beacons */

import { IOT_DEVICES, STUDENT_DB } from './config.js';

export class IoTSimulator {
  constructor() {
    this.devices = IOT_DEVICES.map(d => ({
      ...d,
      status: 'online',
      lastTriggered: 0,
      cooldown: 8 + Math.random() * 7,   // 8-15s between triggers
      timer: Math.random() * 5,           // stagger initial triggers
      activity: 0,                        // 0-1 for visual pulse
    }));

    this.attendanceLog = [];
    this._onEvent = null;
    this._onFaceScan = null;
    this._onSecurityAlert = null;
  }

  onEvent(fn) { this._onEvent = fn; }
  onFaceScan(fn) { this._onFaceScan = fn; }
  onSecurityAlert(fn) { this._onSecurityAlert = fn; }

  _emit(type, msg) {
    if (this._onEvent) this._onEvent(type, msg);
  }

  update(dt, humanAgents) {
    for (const device of this.devices) {
      // Decay activity indicator
      device.activity = Math.max(0, device.activity - dt * 2);

      device.timer += dt;
      if (device.timer < device.cooldown) continue;
      device.timer = 0;
      device.cooldown = 8 + Math.random() * 7;

      // Check if any human agent is near this device's node
      const nearbyHuman = humanAgents.find(h => h.currentNode === device.node);

      if (device.type === 'IR Sensor') {
        if (nearbyHuman) {
          device.status = 'triggered';
          device.activity = 1;
          this._emit('iot', `[IR] Motion detected at ${device.location}`);
          // Reset to online after a moment
          setTimeout(() => { device.status = 'online'; }, 2000);
        }
      }

      else if (device.type === 'Camera') {
        if (nearbyHuman) {
          device.status = 'capturing';
          device.activity = 1;

          // 85% chance: recognized face; 15% chance: unknown
          if (Math.random() < 0.85) {
            const student = STUDENT_DB[Math.floor(Math.random() * STUDENT_DB.length)];
            this._emit('face', `[Scan] ${student.name} (${student.id}) recognized at ${device.location}`);
            this.attendanceLog.push({
              studentId: student.id,
              name: student.name,
              location: device.location,
              time: Date.now(),
            });
            if (this._onFaceScan) this._onFaceScan(student, device);
          } else {
            this._emit('security', `[Security] Unknown face detected at ${device.location}!`);
            if (this._onSecurityAlert) this._onSecurityAlert(device);
          }

          setTimeout(() => { device.status = 'online'; }, 3000);
        }
      }

      else if (device.type === 'ESP32 Gateway') {
        device.activity = 0.5;
        // heartbeat — just update status
        device.status = 'online';
      }

      else if (device.type === 'BLE Beacon') {
        if (nearbyHuman) {
          device.activity = 0.8;
          this._emit('iot', `[BLE] Proximity event at ${device.location}`);
        }
      }

      else if (device.type === 'WiFi AP') {
        device.activity = 0.3;
        device.status = 'online';
      }
    }
  }

  getDeviceList() {
    return this.devices.map(d => ({
      id: d.id,
      type: d.type,
      location: d.location,
      status: d.status,
      activity: d.activity,
    }));
  }

  getRecentAttendance(count = 10) {
    return this.attendanceLog.slice(-count);
  }
}
