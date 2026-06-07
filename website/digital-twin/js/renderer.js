/*  renderer.js — 2.5D Isometric Canvas Renderer
    Draws the hospital floor plan, agents, paths, and effects */

import { HOSPITAL_NODES, ZONE_COLORS, ZONE_SIZES, HUMAN_COLORS } from './config.js';
import { getAllEdges } from './navigation.js';

// ─── Isometric Transform ─────────────────────────────────────────────────
const ISO_ANGLE = Math.PI / 6;   // 30 degrees
const COS_A = Math.cos(ISO_ANGLE);
const SIN_A = Math.sin(ISO_ANGLE);
const SCALE_BASE = 8;

export class Renderer {
  constructor(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext('2d');

    // Camera
    this.camX = 0;
    this.camY = 0;
    this.zoom = 1;
    this._targetZoom = 1;

    // Interaction
    this._dragging = false;
    this._dragStartX = 0;
    this._dragStartY = 0;
    this._dragCamX = 0;
    this._dragCamY = 0;
    this.selectedRobot = null;
    this.autoFollow = false;

    // Cache
    this._edges = getAllEdges();
    this._time = 0;

    this._setupEvents();
    this._resize();
    window.addEventListener('resize', () => this._resize());
  }

  _resize() {
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.canvas.width = rect.width * devicePixelRatio;
    this.canvas.height = rect.height * devicePixelRatio;
    this.canvas.style.width = rect.width + 'px';
    this.canvas.style.height = rect.height + 'px';
    this.ctx.scale(devicePixelRatio, devicePixelRatio);
    this.W = rect.width;
    this.H = rect.height;
  }

  _setupEvents() {
    this.canvas.addEventListener('mousedown', e => {
      if (e.button === 0) {
        this._dragging = true;
        this._dragStartX = e.clientX;
        this._dragStartY = e.clientY;
        this._dragCamX = this.camX;
        this._dragCamY = this.camY;
      }
    });
    window.addEventListener('mousemove', e => {
      if (this._dragging) {
        this.camX = this._dragCamX + (e.clientX - this._dragStartX);
        this.camY = this._dragCamY + (e.clientY - this._dragStartY);
        this.autoFollow = false;
      }
    });
    window.addEventListener('mouseup', () => { this._dragging = false; });
    this.canvas.addEventListener('wheel', e => {
      e.preventDefault();
      this._targetZoom *= e.deltaY > 0 ? 0.9 : 1.1;
      this._targetZoom = Math.max(0.3, Math.min(3, this._targetZoom));
      this.autoFollow = false;
    }, { passive: false });
  }

  /** World (x, z) → screen (sx, sy) */
  worldToScreen(wx, wz) {
    const s = SCALE_BASE * this.zoom;
    const ix = (wx - wz) * COS_A * s;
    const iy = (wx + wz) * SIN_A * s * 0.5;
    return {
      x: ix + this.W / 2 + this.camX,
      y: iy + this.H / 2 + this.camY,
    };
  }

  /** Screen → world (approximate inverse) */
  screenToWorld(sx, sy) {
    const s = SCALE_BASE * this.zoom;
    const cx = sx - this.W / 2 - this.camX;
    const cy = sy - this.H / 2 - this.camY;
    const a = cx / (COS_A * s);
    const b = cy / (SIN_A * s * 0.5);
    return { x: (a + b) / 2, z: (b - a) / 2 };
  }

  // ─── Main Render ────────────────────────────────────────────────────
  render(sim) {
    this._time += 0.016;
    this.zoom += (this._targetZoom - this.zoom) * 0.1;

    // Auto-follow selected robot
    if (this.autoFollow && this.selectedRobot !== null) {
      const r = sim.robots[this.selectedRobot];
      if (r) {
        const target = this.worldToScreen(r.worldX, r.worldZ);
        this.camX += (this.W / 2 - target.x) * 0.05;
        this.camY += (this.H / 2 - target.y) * 0.05;
      }
    }

    const ctx = this.ctx;
    ctx.save();
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);

    // Background
    ctx.fillStyle = '#0a0e1a';
    ctx.fillRect(0, 0, this.W, this.H);

    // Draw layers
    this._drawGrid(ctx);
    this._drawCorridors(ctx);
    this._drawZones(ctx, sim);
    this._drawNodeLabels(ctx);
    this._drawHumans(ctx, sim);
    this._drawRobotPaths(ctx, sim);
    this._drawRobots(ctx, sim);
    this._drawIoTIndicators(ctx, sim);

    ctx.restore();
  }

  // ─── Grid ───────────────────────────────────────────────────────────
  _drawGrid(ctx) {
    ctx.strokeStyle = 'rgba(40, 50, 70, 0.3)';
    ctx.lineWidth = 0.5;
    for (let i = -40; i <= 40; i += 5) {
      const a = this.worldToScreen(i, -40);
      const b = this.worldToScreen(i, 40);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
      const c = this.worldToScreen(-40, i);
      const d = this.worldToScreen(40, i);
      ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(d.x, d.y); ctx.stroke();
    }
  }

  // ─── Corridors ──────────────────────────────────────────────────────
  _drawCorridors(ctx) {
    ctx.strokeStyle = 'rgba(100, 120, 150, 0.25)';
    ctx.lineWidth = 2 * this.zoom;
    for (const edge of this._edges) {
      const a = this.worldToScreen(edge.fromPos.x, edge.fromPos.z);
      const b = this.worldToScreen(edge.toPos.x, edge.toPos.z);
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
  }

  // ─── Zones ──────────────────────────────────────────────────────────
  _drawZones(ctx) {
    const s = SCALE_BASE * this.zoom;
    for (const [name, [wx, wz]] of Object.entries(HOSPITAL_NODES)) {
      let zoneColor = '#505868';
      let size = [5, 5];

      if (name.startsWith('Room')) { zoneColor = ZONE_COLORS.Room; size = [5, 4]; }
      else if (name.startsWith('ICU') && name !== 'ICU_Corr') { zoneColor = ZONE_COLORS.ICU; size = [6, 5]; }
      else if (name.startsWith('RoomCorr') || name.startsWith('WestCorr') || name.startsWith('EastCorr') || name === 'HallNorth') {
        zoneColor = ZONE_COLORS.Corridor; size = [4, 4];
      }
      else if (ZONE_SIZES[name]) {
        size = ZONE_SIZES[name];
        for (const key of Object.keys(ZONE_COLORS)) {
          if (name.startsWith(key) || name === key) { zoneColor = ZONE_COLORS[key]; break; }
        }
      }

      // Draw isometric tile
      const hw = size[0] / 2, hd = size[1] / 2;
      const tl = this.worldToScreen(wx - hw, wz - hd);
      const tr = this.worldToScreen(wx + hw, wz - hd);
      const br = this.worldToScreen(wx + hw, wz + hd);
      const bl = this.worldToScreen(wx - hw, wz + hd);

      ctx.fillStyle = zoneColor + '40';
      ctx.strokeStyle = zoneColor + '80';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(tl.x, tl.y);
      ctx.lineTo(tr.x, tr.y);
      ctx.lineTo(br.x, br.y);
      ctx.lineTo(bl.x, bl.y);
      ctx.closePath();
      ctx.fill();
      ctx.stroke();
    }
  }

  // ─── Node Labels ────────────────────────────────────────────────────
  _drawNodeLabels(ctx) {
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    const fontSize = Math.max(7, 9 * this.zoom);
    ctx.font = `600 ${fontSize}px 'Inter', sans-serif`;

    for (const [name, [wx, wz]] of Object.entries(HOSPITAL_NODES)) {
      // Skip corridor nodes
      if (name.startsWith('RoomCorr') || name.startsWith('WestCorr') || name.startsWith('EastCorr') || name === 'HallNorth') continue;

      const pos = this.worldToScreen(wx, wz);
      let label = name;
      if (name.startsWith('Room')) label = `R${name.slice(4)}`;
      else if (name === 'ICU_Corr') label = 'ICU';
      else if (name === 'ChargingDock') label = '⚡ Dock';
      else if (name === 'EmergencyRoom') label = 'ER';

      // Glow
      ctx.fillStyle = 'rgba(255,255,255,0.7)';
      ctx.fillText(label, pos.x, pos.y - 6 * this.zoom);
    }
  }

  // ─── Humans ─────────────────────────────────────────────────────────
  _drawHumans(ctx, sim) {
    const r = 3 * this.zoom;
    for (const h of sim.humans) {
      const pos = this.worldToScreen(h.worldX, h.worldZ);

      // Body dot
      ctx.fillStyle = h.color;
      ctx.globalAlpha = 0.7;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;

      // Help request indicator
      if (h.needsHelp) {
        const pulse = Math.sin(this._time * 5) * 0.3 + 0.7;
        ctx.fillStyle = `rgba(255, 60, 60, ${pulse})`;
        ctx.font = `bold ${12 * this.zoom}px 'Inter', sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText('!', pos.x, pos.y - 10 * this.zoom);
      }

      // Fulfilled status
      if (h.statusText === '✓') {
        ctx.fillStyle = '#10b981';
        ctx.font = `bold ${10 * this.zoom}px 'Inter', sans-serif`;
        ctx.textAlign = 'center';
        ctx.fillText('✓', pos.x, pos.y - 10 * this.zoom);
      }
    }
  }

  // ─── Robot Paths ────────────────────────────────────────────────────
  _drawRobotPaths(ctx, sim) {
    for (const robot of sim.robots) {
      const info = robot.getInfo();
      if (info.pathWorld.length < 2) continue;

      ctx.strokeStyle = robot.color + '60';
      ctx.lineWidth = 2 * this.zoom;
      ctx.setLineDash([4 * this.zoom, 4 * this.zoom]);
      ctx.beginPath();
      const start = this.worldToScreen(robot.worldX, robot.worldZ);
      ctx.moveTo(start.x, start.y);
      for (const wp of info.pathWorld) {
        const p = this.worldToScreen(wp.x, wp.z);
        ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  // ─── Robots ─────────────────────────────────────────────────────────
  _drawRobots(ctx, sim) {
    const baseSize = 6 * this.zoom;

    for (let i = 0; i < sim.robots.length; i++) {
      const robot = sim.robots[i];
      const pos = this.worldToScreen(robot.worldX, robot.worldZ);
      const selected = this.selectedRobot === i;

      // Selection ring
      if (selected) {
        const pulse = 12 * this.zoom + Math.sin(this._time * 4) * 2 * this.zoom;
        ctx.strokeStyle = robot.color + '80';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, pulse, 0, Math.PI * 2);
        ctx.stroke();
      }

      // Robot glow
      const glowAlpha = robot.state === 'idle' ? 0.1 : 0.3;
      const gradient = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, baseSize * 2);
      gradient.addColorStop(0, robot.color + Math.floor(glowAlpha * 255).toString(16).padStart(2, '0'));
      gradient.addColorStop(1, 'transparent');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, baseSize * 2, 0, Math.PI * 2);
      ctx.fill();

      // Robot body (hexagonal shape)
      ctx.fillStyle = robot.color;
      ctx.beginPath();
      for (let a = 0; a < 6; a++) {
        const angle = (a * Math.PI / 3) - Math.PI / 6;
        const px = pos.x + Math.cos(angle) * baseSize;
        const py = pos.y + Math.sin(angle) * baseSize;
        if (a === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.fill();

      // Inner circle
      ctx.fillStyle = '#0a0e1a';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, baseSize * 0.5, 0, Math.PI * 2);
      ctx.fill();

      // State dot
      const stateColors = {
        idle: '#10b981', navigating: '#00d4ff', guiding: '#ffd700',
        delivering: '#ff8c00', assisting: '#ff69b4', charging: '#ffd700',
        returning: '#a0a0a0',
      };
      ctx.fillStyle = stateColors[robot.state] || '#fff';
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, baseSize * 0.3, 0, Math.PI * 2);
      ctx.fill();

      // Name label
      ctx.fillStyle = '#fff';
      ctx.font = `bold ${9 * this.zoom}px 'Inter', sans-serif`;
      ctx.textAlign = 'center';
      ctx.fillText(robot.name, pos.x, pos.y - baseSize - 4 * this.zoom);

      // State label
      ctx.fillStyle = '#a0b0c0';
      ctx.font = `${7 * this.zoom}px 'JetBrains Mono', monospace`;
      ctx.fillText(robot.stateIcon, pos.x, pos.y + baseSize + 8 * this.zoom);

      // Battery bar
      const barW = 20 * this.zoom;
      const barH = 3 * this.zoom;
      const barX = pos.x - barW / 2;
      const barY = pos.y + baseSize + 12 * this.zoom;
      ctx.fillStyle = '#1a1a2e';
      ctx.fillRect(barX, barY, barW, barH);
      const batPct = robot.battery / 100;
      const batColor = batPct > 0.5 ? '#10b981' : batPct > 0.2 ? '#f59e0b' : '#ef4444';
      ctx.fillStyle = batColor;
      ctx.fillRect(barX, barY, barW * batPct, barH);
    }
  }

  // ─── IoT Indicators ────────────────────────────────────────────────
  _drawIoTIndicators(ctx, sim) {
    for (const device of sim.iot.devices) {
      if (device.activity <= 0) continue;
      const nodePos = HOSPITAL_NODES[device.node];
      if (!nodePos) continue;
      const pos = this.worldToScreen(nodePos[0], nodePos[1]);

      // Pulse ring
      const radius = (15 + device.activity * 10) * this.zoom;
      ctx.strokeStyle = device.type === 'Camera'
        ? `rgba(0, 212, 255, ${device.activity * 0.5})`
        : `rgba(245, 158, 11, ${device.activity * 0.5})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
      ctx.stroke();
    }
  }

  // ─── Hit testing ────────────────────────────────────────────────────
  hitTestRobot(screenX, screenY, sim) {
    for (let i = 0; i < sim.robots.length; i++) {
      const r = sim.robots[i];
      const pos = this.worldToScreen(r.worldX, r.worldZ);
      if (Math.hypot(screenX - pos.x, screenY - pos.y) < 15 * this.zoom) {
        return i;
      }
    }
    return null;
  }
}
