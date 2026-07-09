/*  config.js — FARS Digital-Twin Simulation Constants
    Direct port of navigation.py + hospital_world.py + robot_agent.py constants */

// ─── Hospital Graph Nodes  { name: [x, z] } ────────────────────────────
export const HOSPITAL_NODES = {
  // Main spine
  Entrance:      [0, -30],
  Reception:     [0, -20],
  MainHall:      [0, 0],
  HallNorth:     [0, 15],
  ChargingDock:  [0, -10],

  // West wing
  WestCorr1:     [-20, 0],
  WestCorr2:     [-20, 15],
  Pharmacy:      [-30, 0],
  StaffOffice:   [-30, 15],

  // East wing
  EastCorr1:     [20, 0],
  EastCorr2:     [20, 15],
  WaitingHall:   [30, 0],
  EmergencyRoom: [30, 15],

  // ICU corridor (north)
  ICU_Corr:      [0, 28],
  ICU1:          [-12, 32],
  ICU2:          [-4, 32],
  ICU3:          [4, 32],
  ICU4:          [12, 32],

  // West room corridors
  RoomCorrW1:    [-20, -10],
  RoomCorrW2:    [-20, -20],

  // East room corridors
  RoomCorrE1:    [20, -10],
  RoomCorrE2:    [20, -20],
};

// Generate patient rooms (Room1-Room10 west, Room11-Room20 east)
for (let i = 1; i <= 10; i++) {
  const row = Math.floor((i - 1) / 2);
  const side = (i % 2 === 1) ? -1 : 1;
  HOSPITAL_NODES[`Room${i}`] = [-28 + side * 6, -8 - row * 5];
}
for (let i = 11; i <= 20; i++) {
  const row = Math.floor((i - 11) / 2);
  const side = (i % 2 === 1) ? -1 : 1;
  HOSPITAL_NODES[`Room${i}`] = [22 + side * 6, -8 - row * 5];
}

// ─── Graph Edges ─────────────────────────────────────────────────────────
export const HOSPITAL_EDGES = [
  // Main spine
  ['Entrance', 'Reception'],
  ['Reception', 'ChargingDock'],
  ['ChargingDock', 'MainHall'],
  ['Reception', 'MainHall'],
  ['MainHall', 'HallNorth'],

  // West wing
  ['MainHall', 'WestCorr1'],
  ['WestCorr1', 'Pharmacy'],
  ['WestCorr1', 'WestCorr2'],
  ['WestCorr2', 'StaffOffice'],
  ['HallNorth', 'WestCorr2'],

  // East wing
  ['MainHall', 'EastCorr1'],
  ['EastCorr1', 'WaitingHall'],
  ['EastCorr1', 'EastCorr2'],
  ['EastCorr2', 'EmergencyRoom'],
  ['HallNorth', 'EastCorr2'],

  // ICU
  ['HallNorth', 'ICU_Corr'],
  ['ICU_Corr', 'ICU1'],
  ['ICU_Corr', 'ICU2'],
  ['ICU_Corr', 'ICU3'],
  ['ICU_Corr', 'ICU4'],

  // West room corridors
  ['WestCorr1', 'RoomCorrW1'],
  ['RoomCorrW1', 'RoomCorrW2'],

  // West rooms to corridors
  ...Array.from({length: 5}, (_, i) => ['RoomCorrW1', `Room${i + 1}`]),
  ...Array.from({length: 5}, (_, i) => ['RoomCorrW2', `Room${i + 6}`]),

  // East room corridors
  ['EastCorr1', 'RoomCorrE1'],
  ['RoomCorrE1', 'RoomCorrE2'],

  // East rooms to corridors
  ...Array.from({length: 5}, (_, i) => ['RoomCorrE1', `Room${i + 11}`]),
  ...Array.from({length: 5}, (_, i) => ['RoomCorrE2', `Room${i + 16}`]),
];

// ─── Zone Colors (for rendering) ────────────────────────────────────────
export const ZONE_COLORS = {
  Room:          '#4682b4',
  ICU:           '#c83c3c',
  Pharmacy:      '#3cb371',
  EmergencyRoom: '#ff8c00',
  WaitingHall:   '#ba55d3',
  StaffOffice:   '#6495ed',
  Reception:     '#dcdcdc',
  ChargingDock:  '#ffd700',
  MainHall:      '#a9a9a9',
  Entrance:      '#c0c0c0',
  Corridor:      '#787878',
};

// Zone tile sizes (for the renderer)
export const ZONE_SIZES = {
  Reception:     [8, 8],
  WaitingHall:   [8, 8],
  EmergencyRoom: [8, 8],
  Pharmacy:      [8, 8],
  StaffOffice:   [8, 8],
  MainHall:      [12, 10],
  ChargingDock:  [8, 6],
  Entrance:      [8, 4],
  ICU_Corr:      [20, 3],
};

// ─── Robot Config ────────────────────────────────────────────────────────
export const NUM_ROBOTS         = 5;
export const ROBOT_COLORS       = ['#00c8ff', '#ff6464', '#64ff64', '#ffc832', '#c864ff'];
export const ROBOT_NAMES        = ['R1', 'R2', 'R3', 'R4', 'R5'];
export const MOVE_SPEED         = 8.0;
export const BATTERY_DRAIN_RATE = 0.03;   // per second while moving
export const BATTERY_CHARGE_RATE= 0.15;   // per second while charging
export const LOW_BATTERY_THRESH = 15.0;
export const TASK_EXECUTE_TIME  = 3.0;    // seconds at destination

export const STATE_ICONS = {
  idle:       'IDLE',
  navigating: 'NAV',
  guiding:    'GUIDE',
  delivering: 'DELIV',
  assisting:  'ASSIST',
  charging:   'CHRG',
  returning:  'RTN',
};

// ─── Human Agent Config ──────────────────────────────────────────────────
export const NUM_PATIENTS = 20;
export const NUM_DOCTORS  = 5;
export const NUM_NURSES   = 5;
export const NUM_VISITORS = 3;

export const HUMAN_COLORS = {
  patient: '#ffdc64',
  doctor:  '#50c878',
  nurse:   '#64b4ff',
  visitor: '#c882ff',
};

export const HUMAN_LOCATIONS = {
  patient: null, // assigned dynamically
  doctor:  ['MainHall', 'ICU1', 'ICU2', 'ICU3', 'ICU4', 'EmergencyRoom'],
  nurse:   ['Pharmacy', 'MainHall', 'WaitingHall'],
  visitor: ['Reception', 'WaitingHall', 'MainHall'],
};

// ─── Task Config ─────────────────────────────────────────────────────────
export const TASK_TYPES = {
  guide_patient:    'Guide Patient',
  assist_patient:   'Assist Patient',
  deliver_medicine: 'Deliver Medicine',
  escort_visitor:   'Escort Visitor',
  check_room:       'Check Room',
  security_check:   'Security Check',
};

// ─── IoT Device Definitions ─────────────────────────────────────────────
export const IOT_DEVICES = [
  { id: 'ir-entrance',    type: 'IR Sensor',     location: 'Entrance',  node: 'Entrance' },
  { id: 'ir-main',        type: 'IR Sensor',     location: 'Main Hall', node: 'MainHall' },
  { id: 'ir-reception',   type: 'IR Sensor',     location: 'Reception', node: 'Reception' },
  { id: 'cam-entrance',   type: 'Camera',        location: 'Entrance',  node: 'Entrance' },
  { id: 'cam-main',       type: 'Camera',        location: 'Main Hall', node: 'MainHall' },
  { id: 'cam-reception',  type: 'Camera',        location: 'Reception', node: 'Reception' },
  { id: 'esp32-gateway',  type: 'ESP32 Gateway', location: 'Server Room', node: 'MainHall' },
  { id: 'ble-beacon-1',   type: 'BLE Beacon',    location: 'Reception', node: 'Reception' },
  { id: 'wifi-ap',        type: 'WiFi AP',       location: 'Campus',    node: 'MainHall' },
];

// Simulated student database for face recognition
export const STUDENT_DB = [
  { id: 'SIT001', name: 'Rohit Vijay',       dept: 'CSE', year: 2 },
  { id: 'SIT002', name: 'Akash Santhnu',     dept: 'CSE', year: 2 },
  { id: 'SIT003', name: 'Priya Sharma',      dept: 'ECE', year: 3 },
  { id: 'SIT004', name: 'Karthik Rajan',     dept: 'CSE', year: 2 },
  { id: 'SIT005', name: 'Divya Lakshmi',     dept: 'IT',  year: 3 },
  { id: 'SIT006', name: 'Mohammed Irfan',    dept: 'CSE', year: 2 },
];

// ─── UI Theme Colors ─────────────────────────────────────────────────────
export const THEME = {
  bgPrimary:   '#0a0e1a',
  bgSecondary: '#111827',
  bgPanel:     'rgba(17, 24, 39, 0.85)',
  accent:      '#00d4ff',
  success:     '#10b981',
  warning:     '#f59e0b',
  danger:      '#ef4444',
  textPrimary: '#e5e7eb',
  textMuted:   '#6b7280',
  border:      'rgba(0, 212, 255, 0.15)',
};
