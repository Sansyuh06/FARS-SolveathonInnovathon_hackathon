/*  navigation.js — Hospital Graph + A* Pathfinding Engine
    Direct port of full_simulation/navigation.py */

import { HOSPITAL_NODES, HOSPITAL_EDGES } from './config.js';

// ─── Graph Data Structure ────────────────────────────────────────────────
const adjacency = {};   // { nodeName: [ { to, weight } ] }
let _built = false;

function buildGraph() {
  if (_built) return;
  for (const name of Object.keys(HOSPITAL_NODES)) {
    adjacency[name] = [];
  }
  for (const [u, v] of HOSPITAL_EDGES) {
    const [ux, uz] = HOSPITAL_NODES[u];
    const [vx, vz] = HOSPITAL_NODES[v];
    const w = Math.hypot(vx - ux, vz - uz);
    adjacency[u].push({ to: v, weight: w });
    adjacency[v].push({ to: u, weight: w });
  }
  _built = true;
}

// ─── A* Pathfinding ──────────────────────────────────────────────────────

class MinHeap {
  constructor() { this.data = []; }
  push(item) {
    this.data.push(item);
    this._bubbleUp(this.data.length - 1);
  }
  pop() {
    const top = this.data[0];
    const last = this.data.pop();
    if (this.data.length > 0) {
      this.data[0] = last;
      this._sinkDown(0);
    }
    return top;
  }
  get size() { return this.data.length; }
  _bubbleUp(i) {
    while (i > 0) {
      const parent = (i - 1) >> 1;
      if (this.data[parent].f <= this.data[i].f) break;
      [this.data[parent], this.data[i]] = [this.data[i], this.data[parent]];
      i = parent;
    }
  }
  _sinkDown(i) {
    const n = this.data.length;
    while (true) {
      let smallest = i;
      const l = 2 * i + 1, r = 2 * i + 2;
      if (l < n && this.data[l].f < this.data[smallest].f) smallest = l;
      if (r < n && this.data[r].f < this.data[smallest].f) smallest = r;
      if (smallest === i) break;
      [this.data[smallest], this.data[i]] = [this.data[i], this.data[smallest]];
      i = smallest;
    }
  }
}

function heuristic(a, b) {
  const [ax, az] = HOSPITAL_NODES[a];
  const [bx, bz] = HOSPITAL_NODES[b];
  return Math.hypot(bx - ax, bz - az);
}

/**
 * A* shortest path. Returns array of node names from start to goal (inclusive).
 * Returns [] if no path.
 */
export function aStarPath(start, goal) {
  buildGraph();
  if (!adjacency[start] || !adjacency[goal]) return [];
  if (start === goal) return [start];

  const gScore = {};
  const cameFrom = {};
  const closed = new Set();
  const heap = new MinHeap();

  gScore[start] = 0;
  heap.push({ node: start, f: heuristic(start, goal) });

  while (heap.size > 0) {
    const { node: current } = heap.pop();
    if (current === goal) {
      // reconstruct
      const path = [current];
      let c = current;
      while (cameFrom[c]) { c = cameFrom[c]; path.push(c); }
      return path.reverse();
    }
    if (closed.has(current)) continue;
    closed.add(current);

    for (const { to, weight } of adjacency[current]) {
      if (closed.has(to)) continue;
      const tentG = gScore[current] + weight;
      if (tentG < (gScore[to] ?? Infinity)) {
        gScore[to] = tentG;
        cameFrom[to] = current;
        heap.push({ node: to, f: tentG + heuristic(to, goal) });
      }
    }
  }
  return []; // no path
}

// ─── Utility Functions ───────────────────────────────────────────────────

/** Get world (x, z) for a node name. */
export function getNodePosition(name) {
  const pos = HOSPITAL_NODES[name];
  return pos ? { x: pos[0], z: pos[1] } : { x: 0, z: 0 };
}

/** Get array of (x,z) positions along a path. */
export function getWorldPath(start, goal) {
  return aStarPath(start, goal).map(n => getNodePosition(n));
}

/** Return all Room1..Room20 names. */
export function getAllRoomNodes() {
  return Array.from({ length: 20 }, (_, i) => `Room${i + 1}`);
}

/** Return all node names and positions. */
export function getAllNodes() {
  buildGraph();
  return { ...HOSPITAL_NODES };
}

/** Find closest graph node to a world position. */
export function getNearestNode(x, z) {
  buildGraph();
  let best = null, bestDist = Infinity;
  for (const [name, [nx, nz]] of Object.entries(HOSPITAL_NODES)) {
    const d = Math.hypot(nx - x, nz - z);
    if (d < bestDist) { bestDist = d; best = name; }
  }
  return best;
}

/** Get all edges as [{from, to, fromPos, toPos}]. */
export function getAllEdges() {
  buildGraph();
  return HOSPITAL_EDGES.map(([u, v]) => ({
    from: u, to: v,
    fromPos: getNodePosition(u),
    toPos: getNodePosition(v),
  }));
}
