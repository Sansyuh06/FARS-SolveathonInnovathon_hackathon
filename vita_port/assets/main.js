// =============================================================================
// FARSVERSE POCKET -- NVIDIA OMNIVERSE USD COMPOSER EDITION (PS VITA)
// =============================================================================

const font = Font.load_font_file("app0:/assets/segoeui.ttf");

// Helper: 32-bit RGBA color for Vita2D
function rgba(r, g, b, a = 255) {
    return (
        ((a & 255) << 24) |
        ((b & 255) << 16) |
        ((g & 255) << 8) |
        (r & 255)
    ) >>> 0;
}

// -----------------------------------------------------------------------------
// NVIDIA OMNIVERSE COLOR PALETTE
// -----------------------------------------------------------------------------
const OMNI_DARKEST    = rgba(22, 22, 22, 255);   // Title bar, deep charcoal #161616
const OMNI_BG         = rgba(28, 28, 28, 255);   // Viewport & panel background #1c1c1c
const OMNI_PANEL      = rgba(36, 36, 36, 255);   // Docks & sidebars #242424
const OMNI_PANEL_ALT  = rgba(44, 44, 44, 255);   // Secondary headers & tab rows #2c2c2c
const OMNI_BORDER     = rgba(54, 54, 54, 255);   // Structural dividers #363636
const OMNI_BORDER_HI  = rgba(75, 75, 75, 255);   // Active outlines

const NV_GREEN        = rgba(118, 185, 0, 255);  // NVIDIA Signature Green #76B900
const NV_GREEN_DIM    = rgba(65, 105, 0, 255);
const OMNI_ORANGE     = rgba(243, 156, 18, 255); // Omniverse USD selection glow
const OMNI_ORANGE_DIM = rgba(160, 95, 10, 255);
const OMNI_RED        = rgba(235, 60, 60, 255);
const OMNI_BLUE       = rgba(60, 140, 240, 255);
const OMNI_CYAN       = rgba(0, 210, 240, 255);
const OMNI_YELLOW     = rgba(240, 205, 40, 255);

const TEXT_BRIGHT     = rgba(245, 245, 245, 255);
const TEXT_REGULAR    = rgba(200, 200, 200, 255);
const TEXT_MUTED      = rgba(140, 140, 140, 255);
const TEXT_DIM        = rgba(90, 90, 90, 255);

// -----------------------------------------------------------------------------
// APPLICATION & SIMULATION STATE
// -----------------------------------------------------------------------------
let running = true;
let simTime = 0.0;
let hostIp = "192.168.0.135";
let hostPort = 8080;
let hostOnline = false;

// Side panel mode: "stage" (prims in scene) vs "models" (predefined 3D model library)
let sideTab = "models"; // Default to predefined 3D models on side
let selectedModelIdx = 0;
let selectedPrimIdx  = 0;
let selectedMissionIdx = 0;
let activeBottomTab = "console";

// 3D Perspective Viewport Area (X: 32 to 665, Y: 58 to 390)
const VP_X  = 32;
const VP_Y  = 58;
const VP_W  = 633;
const VP_H  = 332;
const VP_CX = VP_X + Math.floor(VP_W / 2); // 348
const VP_CY = VP_Y + Math.floor(VP_H / 2); // 224
const FOCAL = 340.0;

// 3D Camera Look-At Orbit Parameters
let orbitYaw   = 0.55;  // ~31 degrees azimuth
let orbitPitch = 0.42;  // ~24 degrees elevation
let camDist    = 185.0; // Distance to focus target
let targetX    = 0.0;
let targetY    = 8.0;
let targetZ    = 0.0;

let camX = 0.0, camY = 0.0, camZ = 0.0;
let Fx = 0.0, Fy = 0.0, Fz = 0.0;
let Rx = 0.0, Ry = 0.0, Rz = 0.0;
let Ux = 0.0, Uy = 0.0, Uz = 0.0;

// Side 3D Model Preview Viewport Area (X: 672 to 952, Y: 180 to 295)
const PREV_CX    = 812;
const PREV_CY    = 238;
const PREV_FOCAL = 145.0;
const PREV_DIST  = 40.0;
let previewTurntableAngle = 0.0;

// Console Log Stream
const consoleLogs = [
    "[USD Composer 2023.2.5] Stage loaded: IsaacWarehouse.usd",
    "[RTX Real-Time] 3D CAD engine active at 960x544@60Hz",
    "[3D Library] 7 Predefined 3D CAD meshes mounted on side",
    "[Physics] PhysX 5.1 robotics solver active (60 Hz)"
];

function addLog(msg) {
    const t = simTime.toFixed(1) + "s";
    consoleLogs.unshift("[" + t + "] " + msg);
    if (consoleLogs.length > 7) consoleLogs.pop();
}

// -----------------------------------------------------------------------------
// PREDEFINED 3D MODELS CATALOG (Available on the side panel)
// -----------------------------------------------------------------------------
const predefinedModels = [
    {
        id: "MDL-CARTER",
        name: "AMR Carter Logistics",
        category: "Robotics / AMRs",
        type: "Mesh",
        vertices: 32,
        faces: 18,
        dims: "120 x 85 x 45 cm",
        mass: "145 kg",
        mat: "OmniPBR_IndustrialMetal",
        desc: "Heavy autonomous transport chassis with rotating LiDAR",
        color: NV_GREEN
    },
    {
        id: "MDL-PUMP",
        name: "Vacuum Compressor Pump",
        category: "Machinery / Plant",
        type: "Mesh",
        vertices: 48,
        faces: 26,
        dims: "180 x 110 x 140 cm",
        mass: "380 kg",
        mat: "OmniPBR_CastIron_Green",
        desc: "Industrial compressor pump with twin pistons & tank",
        color: rgba(110, 140, 100, 255)
    },
    {
        id: "MDL-UVC",
        name: "Hospital UV-C Sterilizer",
        category: "Medical Robotics",
        type: "Mesh",
        vertices: 36,
        faces: 20,
        dims: "60 x 60 x 165 cm",
        mass: "68 kg",
        mat: "OmniPBR_QuartzSanitize",
        desc: "High-intensity ultraviolet disinfection lamp tower",
        color: rgba(190, 110, 255, 255)
    },
    {
        id: "MDL-CRASH",
        name: "Emergency Crash Cart",
        category: "Hospital Props",
        type: "Mesh",
        vertices: 40,
        faces: 22,
        dims: "90 x 65 x 110 cm",
        mass: "42 kg",
        mat: "OmniPBR_MedicalSteel",
        desc: "Resuscitation emergency trolley with defibrillator rack",
        color: OMNI_RED
    },
    {
        id: "MDL-RACK",
        name: "High-Bay Storage Rack",
        category: "Warehouse Logistics",
        type: "Xform / Mesh",
        vertices: 56,
        faces: 28,
        dims: "300 x 120 x 450 cm",
        mass: "620 kg",
        mat: "OmniPBR_GalvanizedSteel",
        desc: "Structural steel pallet racking unit with cross-bracing",
        color: rgba(70, 115, 175, 255)
    },
    {
        id: "MDL-CRATE",
        name: "Pallet Cargo Crate",
        category: "Cargo / Freight",
        type: "Mesh",
        vertices: 24,
        faces: 12,
        dims: "120 x 80 x 85 cm",
        mass: "210 kg",
        mat: "OmniPBR_WoodCardboard",
        desc: "Heavy wooden shipping pallet with reinforced container",
        color: rgba(170, 130, 80, 255)
    },
    {
        id: "MDL-BOLLARD",
        name: "Safety Hazard Bollard",
        category: "Facility Safety",
        type: "Mesh",
        vertices: 16,
        faces: 8,
        dims: "30 x 30 x 100 cm",
        mass: "55 kg",
        mat: "OmniPBR_HazardYellow",
        desc: "Impact-resistant guard post with hazard caution stripes",
        color: OMNI_YELLOW
    }
];

// -----------------------------------------------------------------------------
// ACTIVE USD PRIMS IN WAREHOUSE SCENE
// -----------------------------------------------------------------------------
const robots = [
    {
        id: "AMR-01",
        name: "Carter Heavy-01",
        modelId: "MDL-CARTER",
        primPath: "/World/Robots/AMR_01_HeavyLogistics",
        x: 0.0, y: 0.0, z: -15.0,
        tx: 0.0, tz: -15.0,
        rotY: 0.0,
        speed: 1.15,
        battery: 94.5,
        state: "NAVIGATING",
        task: "Medication Delivery -> ICU-2",
        color: NV_GREEN
    },
    {
        id: "AMR-02",
        name: "Courier Bot-02",
        modelId: "MDL-CARTER",
        primPath: "/World/Robots/AMR_02_Courier",
        x: -45.0, y: 0.0, z: 20.0,
        tx: -45.0, tz: 20.0,
        rotY: 1.2,
        speed: 0.85,
        battery: 88.0,
        state: "PATROLLING",
        task: "Corridor Routine Inspection",
        color: OMNI_CYAN
    },
    {
        id: "AMR-03",
        name: "UV-C Tower-03",
        modelId: "MDL-UVC",
        primPath: "/World/Robots/AMR_03_Sterilizer",
        x: 45.0, y: 0.0, z: 25.0,
        tx: 45.0, tz: 25.0,
        rotY: -0.8,
        speed: 0.65,
        battery: 76.2,
        state: "STERILIZING",
        task: "Emergency Ward UV-C Sweep",
        color: rgba(190, 110, 255, 255)
    },
    {
        id: "AMR-04",
        name: "Patient Escort-04",
        modelId: "MDL-CARTER",
        primPath: "/World/Robots/AMR_04_Escort",
        x: -15.0, y: 0.0, z: -45.0,
        tx: -15.0, tz: -45.0,
        rotY: 2.1,
        speed: 0.95,
        battery: 64.8,
        state: "NAVIGATING",
        task: "Escort to Room 12",
        color: OMNI_BLUE
    },
    {
        id: "AMR-05",
        name: "Crash Cart-05",
        modelId: "MDL-CRASH",
        primPath: "/World/Props/Emergency_Crash_Cart",
        x: 35.0, y: 0.0, z: -35.0,
        tx: 35.0, tz: -35.0,
        rotY: 3.14,
        speed: 1.40,
        battery: 52.1,
        state: "PATROLLING",
        task: "Perimeter Sector Scan",
        color: OMNI_ORANGE
    }
];

const sceneProps = [
    {
        id: "PUMP-01",
        name: "Compressor_Pump",
        modelId: "MDL-PUMP",
        primPath: "/World/Machinery/Industrial_Compressor_Pump",
        x: 20.0, y: 0.0, z: 0.0,
        tx: 20.0, tz: 0.0,
        rotY: 0.0,
        speed: 0.0,
        battery: 100.0,
        state: "ONLINE",
        task: "Pneumatic Pressure Station",
        color: rgba(110, 140, 100, 255)
    },
    {
        id: "RACK-01",
        name: "RackLarge_A1_A7",
        modelId: "MDL-RACK",
        primPath: "/World/Environment/Racks/RackLarge_A1_A7",
        x: -60.0, y: 0.0, z: 0.0,
        tx: -60.0, tz: 0.0,
        rotY: 0.0,
        speed: 0.0,
        battery: 100.0,
        state: "STATIC",
        task: "High-Bay Pallet Storage Rack",
        color: rgba(70, 115, 175, 255)
    }
];

const allScenePrims = [...robots, ...sceneProps];

// Mission Roster
const availableMissions = [
    { title: "PATROL CORRIDORS", loc: "Aisle_A", desc: "Routine security inspection", priority: "NORMAL" },
    { title: "DELIVER PHARMACEUTICALS", loc: "Pharmacy", desc: "Transport scheduled meds to ICU", priority: "HIGH" },
    { title: "PATIENT CALL: ROOM 5", loc: "Room_5", desc: "Nurse call button response", priority: "URGENT" },
    { title: "STERILIZE EMERGENCY WARD", loc: "ER_Ward", desc: "Automated UV-C cycle", priority: "NORMAL" },
    { title: "ICU CRITICAL ASSIST", loc: "ICU_1", desc: "Emergency crash cart assist", priority: "CRITICAL" },
    { title: "RETURN TO CHARGING DOCK", loc: "Dock_1", desc: "Autonomous inductive recharge", priority: "LOW" },
    { title: "ISAAC SIM AI PATH DISPATCH", loc: "Hub", desc: "Host LLM (phi3:mini) navigation", priority: "AI" }
];

// Text drawing helper
function drawText(x, y, str, size = 12, color = TEXT_REGULAR) {
    try {
        Font.font_draw_text(font, Math.floor(x), Math.floor(y), color, size, String(str));
    } catch (e) {
        // Fallback
    }
}

// -----------------------------------------------------------------------------
// MATHEMATICALLY EXACT 3D LOOK-AT CAMERA & PERSPECTIVE PROJECTION
// -----------------------------------------------------------------------------
function updateCameraVectors() {
    // 1. Camera eye position in world space
    const cosP = Math.cos(orbitPitch);
    const sinP = Math.sin(orbitPitch);
    const cosY = Math.cos(orbitYaw);
    const sinY = Math.sin(orbitYaw);

    camX = targetX + camDist * sinY * cosP;
    camY = targetY + camDist * sinP;
    camZ = targetZ + camDist * cosY * cosP;

    // 2. Normalized Forward vector F (points from camera TO target)
    const invDist = 1.0 / camDist;
    Fx = (targetX - camX) * invDist;
    Fy = (targetY - camY) * invDist;
    Fz = (targetZ - camZ) * invDist;

    // 3. Normalized Right vector R = normalize(F x Up_world) where Up_world = (0, 1, 0)
    const rLen = Math.sqrt(Fz * Fz + Fx * Fx);
    if (rLen > 0.0001) {
        Rx = Fz / rLen;
        Ry = 0.0;
        Rz = -Fx / rLen;
    } else {
        Rx = 1.0; Ry = 0.0; Rz = 0.0;
    }

    // 4. Normalized Up vector U = R x F
    Ux = Ry * Fz - Rz * Fy;
    Uy = Rz * Fx - Rx * Fz;
    Uz = Rx * Fy - Ry * Fx;
}

// Project world point (wx, wy, wz) into 2D viewport coordinates
function project3D(wx, wy, wz) {
    const dx = wx - camX;
    const dy = wy - camY;
    const dz = wz - camZ;

    // Transform into camera coordinate frame
    const camRight = dx * Rx + dy * Ry + dz * Rz;
    const camUp    = dx * Ux + dy * Uy + dz * Uz;
    const camDepth = dx * Fx + dy * Fy + dz * Fz;

    if (camDepth <= 5.0) return null; // Near clipping plane

    const sx = VP_CX + (camRight / camDepth) * FOCAL;
    const sy = VP_CY - (camUp / camDepth) * FOCAL; // Screen Y is inverted

    // Viewport bounds test
    if (sx < VP_X - 20 || sx > VP_X + VP_W + 20 || sy < VP_Y - 20 || sy > VP_Y + VP_H + 20) {
        return null;
    }

    return { x: sx, y: sy, depth: camDepth };
}

function drawLine3D(x1, y1, z1, x2, y2, z2, color) {
    const p1 = project3D(x1, y1, z1);
    const p2 = project3D(x2, y2, z2);
    if (!p1 || !p2) return;
    Screen.draw_line(p1.x, p1.y, p2.x, p2.y, color);
}

// Draw 3D Box in world space
function drawBox3D(cx, cy, cz, sx, sy, sz, rotY, color, outlineColor = 0) {
    const hx = sx / 2;
    const hy = sy / 2;
    const hz = sz / 2;
    const cosR = Math.cos(rotY);
    const sinR = Math.sin(rotY);

    function rotateCorner(lx, ly, lz) {
        const rx = lx * cosR - lz * sinR;
        const rz = lx * sinR + lz * cosR;
        return project3D(cx + rx, cy + ly, cz + rz);
    }

    const v = [
        rotateCorner(-hx, -hy, -hz), // 0: Bottom back left
        rotateCorner( hx, -hy, -hz), // 1: Bottom back right
        rotateCorner( hx, -hy,  hz), // 2: Bottom front right
        rotateCorner(-hx, -hy,  hz), // 3: Bottom front left
        rotateCorner(-hx,  hy, -hz), // 4: Top back left
        rotateCorner( hx,  hy, -hz), // 5: Top back right
        rotateCorner( hx,  hy,  hz), // 6: Top front right
        rotateCorner(-hx,  hy,  hz)  // 7: Top front left
    ];

    const edges = [
        [0, 1], [1, 2], [2, 3], [3, 0], // Bottom loop
        [4, 5], [5, 6], [6, 7], [7, 4], // Top loop
        [0, 4], [1, 5], [2, 6], [3, 7]  // Vertical struts
    ];

    for (let i = 0; i < edges.length; i++) {
        const pA = v[edges[i][0]];
        const pB = v[edges[i][1]];
        if (pA && pB) {
            Screen.draw_line(pA.x, pA.y, pB.x, pB.y, color);
            if (outlineColor !== 0) {
                Screen.draw_line(pA.x + 1, pA.y, pB.x + 1, pB.y, outlineColor);
                Screen.draw_line(pA.x, pA.y + 1, pB.x, pB.y + 1, outlineColor);
            }
        }
    }
}

// Draw 3D Transform Gizmo at origin of selected prim
function drawTransformGizmo(gx, gy, gz) {
    const origin = project3D(gx, gy, gz);
    if (!origin) return;

    const len = 22.0;

    // X Axis: Red
    const pX = project3D(gx + len, gy, gz);
    if (pX) {
        Screen.draw_line(origin.x, origin.y, pX.x, pX.y, rgba(240, 60, 60, 255));
        Screen.draw_line(origin.x, origin.y + 1, pX.x, pX.y + 1, rgba(240, 60, 60, 255));
        Screen.draw_rectangle(pX.x - 3, pX.y - 3, 6, 6, rgba(240, 60, 60, 255));
    }

    // Y Axis: Green (Up)
    const pY = project3D(gx, gy + len, gz);
    if (pY) {
        Screen.draw_line(origin.x, origin.y, pY.x, pY.y, NV_GREEN);
        Screen.draw_line(origin.x + 1, origin.y, pY.x + 1, pY.y, NV_GREEN);
        Screen.draw_rectangle(pY.x - 3, pY.y - 3, 6, 6, NV_GREEN);
    }

    // Z Axis: Blue
    const pZ = project3D(gx, gy, gz + len);
    if (pZ) {
        Screen.draw_line(origin.x, origin.y, pZ.x, pZ.y, rgba(50, 140, 255, 255));
        Screen.draw_line(origin.x + 1, origin.y + 1, pZ.x + 1, pZ.y + 1, rgba(50, 140, 255, 255));
        Screen.draw_rectangle(pZ.x - 3, pZ.y - 3, 6, 6, rgba(50, 140, 255, 255));
    }

    // Origin Pivot Cube
    Screen.draw_rectangle(origin.x - 3, origin.y - 3, 6, 6, rgba(255, 255, 255, 255));
}

// -----------------------------------------------------------------------------
// MAIN 3D SCENE RENDERING (GROUND GRID, ROBOTS, RACKS, MACHINERY)
// -----------------------------------------------------------------------------
function renderMain3DScene() {
    // 1. Perspective Ground Floor Grid (Omniverse Isaac Sim CAD Grid)
    const gridColor    = rgba(45, 45, 45, 255);
    const subGridColor = rgba(36, 36, 36, 255);
    const axisColorX   = rgba(190, 50, 50, 220);  // Red X-axis
    const axisColorZ   = rgba(50, 110, 200, 220); // Blue Z-axis

    const extent = 90.0;
    const step   = 15.0;

    for (let c = -extent; c <= extent; c += step) {
        // Grid lines parallel to Z
        const colZ = (c === 0) ? axisColorZ : ((Math.abs(c) % 30 === 0) ? gridColor : subGridColor);
        drawLine3D(c, 0, -extent, c, 0, extent, colZ);

        // Grid lines parallel to X
        const colX = (c === 0) ? axisColorX : ((Math.abs(c) % 30 === 0) ? gridColor : subGridColor);
        drawLine3D(-extent, 0, c, extent, 0, c, colX);
    }

    // 2. High-Bay Warehouse Pallet Racks (Left & Right Aisles)
    const rackCols = [ -60.0, 60.0 ];
    for (let r = 0; r < rackCols.length; r++) {
        const rx = rackCols[r];
        const isRackSelected = (selectedPrimIdx === 6 && r === 0);
        const rackBeamCol = isRackSelected ? OMNI_ORANGE : rgba(50, 95, 145, 255);
        const shelfBeams  = rgba(220, 125, 30, 255);

        // 6 Vertical Steel Posts
        const uprights = [
            { x: rx - 7, z: -45 }, { x: rx + 7, z: -45 },
            { x: rx - 7, z:   0 }, { x: rx + 7, z:   0 },
            { x: rx - 7, z:  45 }, { x: rx + 7, z:  45 }
        ];

        for (let u = 0; u < uprights.length; u++) {
            drawLine3D(uprights[u].x, 0, uprights[u].z, uprights[u].x, 34, uprights[u].z, rackBeamCol);
        }

        // Horizontal Shelf Levels (Y = 11, 22, 33)
        for (let lvl = 11; lvl <= 33; lvl += 11) {
            drawLine3D(rx - 7, lvl, -45, rx + 7, lvl, -45, shelfBeams);
            drawLine3D(rx - 7, lvl,   0, rx + 7, lvl,   0, shelfBeams);
            drawLine3D(rx - 7, lvl,  45, rx + 7, lvl,  45, shelfBeams);

            drawLine3D(rx - 7, lvl, -45, rx - 7, lvl, 45, shelfBeams);
            drawLine3D(rx + 7, lvl, -45, rx + 7, lvl, 45, shelfBeams);

            // Diagonal cross-braces
            drawLine3D(rx - 7, lvl - 11, -45, rx - 7, lvl, 0, rgba(60, 60, 60, 255));
            drawLine3D(rx + 7, lvl - 11,   0, rx + 7, lvl, 45, rgba(60, 60, 60, 255));

            // Pallets & Cargo Crates stored on shelf levels
            drawBox3D(rx, lvl + 4, -22, 11, 7, 16, 0, rgba(150, 115, 70, 255), isRackSelected ? OMNI_ORANGE : 0);
            drawBox3D(rx, lvl + 4,  22, 11, 7, 16, 0, rgba(120, 140, 95, 255), isRackSelected ? OMNI_ORANGE : 0);
        }

        // Safety Bollards at rack ends (Hazard Yellow/Black)
        drawBox3D(rx + (r === 0 ? 11 : -11), 4, -50, 3, 8, 3, 0, OMNI_YELLOW);
        drawBox3D(rx + (r === 0 ? 11 : -11), 4,  50, 3, 8, 3, 0, OMNI_YELLOW);
    }

    // 3. Industrial Vacuum Compressor Pump (From Isaac Warehouse Showcase)
    const pump = sceneProps[0];
    const isPumpSelected = (selectedPrimIdx === 5);
    const pumpOutline = isPumpSelected ? OMNI_ORANGE : 0;
    const pumpBodyCol = rgba(95, 125, 90, 255);

    // Horizontal Reservoir Tank Cylinder
    drawBox3D(pump.x, 7.0, pump.z, 22, 11, 11, 0, pumpBodyCol, pumpOutline);
    // Twin Compressor Pump Heads on Top
    drawBox3D(pump.x - 4, 15.0, pump.z, 8, 6, 8, 0, rgba(65, 75, 70, 255), pumpOutline);
    drawBox3D(pump.x + 5, 16.0, pump.z, 6, 8, 6, 0, rgba(55, 65, 60, 255), pumpOutline);
    // Vertical Support Legs
    drawLine3D(pump.x - 8, 0, pump.z - 4, pump.x - 8, 4, pump.z - 4, rgba(40, 40, 40, 255));
    drawLine3D(pump.x + 8, 0, pump.z - 4, pump.x + 8, 4, pump.z - 4, rgba(40, 40, 40, 255));
    drawLine3D(pump.x - 8, 0, pump.z + 4, pump.x - 8, 4, pump.z + 4, rgba(40, 40, 40, 255));
    drawLine3D(pump.x + 8, 0, pump.z + 4, pump.x + 8, 4, pump.z + 4, rgba(40, 40, 40, 255));

    if (isPumpSelected) {
        drawTransformGizmo(pump.x, 0.0, pump.z);
    }

    // 4. Predefined 3D Autonomous Mobile Robots (AMRs) in Scene
    robots.forEach((bot, idx) => {
        const isBotSelected = (selectedPrimIdx === idx);
        const botOutline = isBotSelected ? OMNI_ORANGE : 0;
        const chassisCol = isBotSelected ? rgba(45, 50, 55, 255) : rgba(34, 38, 44, 255);

        if (bot.modelId === "MDL-CARTER") {
            // AMR Carter Chassis: Lower Box + Upper Housing + Rotating LiDAR
            drawBox3D(bot.x, 3.0, bot.z, 10, 4.5, 14, bot.rotY, chassisCol, botOutline);
            drawBox3D(bot.x, 6.0, bot.z, 8, 2.0, 11, bot.rotY, bot.color, botOutline);

            // Rotating LiDAR Scanner
            const lidarY = 8.5;
            drawBox3D(bot.x, lidarY, bot.z, 3.5, 2.5, 3.5, simTime * 4.0, rgba(20, 20, 20, 255), botOutline);

            // Red Laser Sensor Beams
            const lBeamX = Math.cos(simTime * 4.0) * 16.0;
            const lBeamZ = Math.sin(simTime * 4.0) * 16.0;
            drawLine3D(bot.x, lidarY, bot.z, bot.x + lBeamX, lidarY, bot.z + lBeamZ, rgba(240, 50, 50, 160));
        } else if (bot.modelId === "MDL-UVC") {
            // Hospital UV-C Sterilizer: Cylindrical Base + Lamp Tower
            drawBox3D(bot.x, 3.5, bot.z, 9, 5.0, 9, bot.rotY, chassisCol, botOutline);
            drawBox3D(bot.x, 12.0, bot.z, 4, 13.0, 4, bot.rotY, rgba(200, 140, 255, 255), botOutline);
            drawBox3D(bot.x, 19.0, bot.z, 7, 2.0, 7, bot.rotY, rgba(40, 40, 40, 255), botOutline);
        } else if (bot.modelId === "MDL-CRASH") {
            // Medical Crash Cart: Tiered Mobile Cabinet
            drawBox3D(bot.x, 5.0, bot.z, 8, 8.0, 11, bot.rotY, rgba(220, 60, 60, 255), botOutline);
            drawBox3D(bot.x, 10.5, bot.z, 6, 3.0, 8, bot.rotY, rgba(240, 240, 240, 255), botOutline);
        }

        // Front Headlight Glow
        const fwdX = Math.sin(bot.rotY) * 7.5;
        const fwdZ = Math.cos(bot.rotY) * 7.5;
        const ledPos = project3D(bot.x + fwdX, 3.5, bot.z + fwdZ);
        if (ledPos) {
            Screen.draw_rectangle(ledPos.x - 2, ledPos.y - 2, 4, 4, bot.color);
        }

        // Draw Transform Gizmo if selected
        if (isBotSelected) {
            drawTransformGizmo(bot.x, 0.0, bot.z);
        }
    });

    // 5. Mini 3D Axis Orientation Tripod in Bottom-Left Corner
    const tripodCX = VP_X + 26;
    const tripodCY = VP_Y + VP_H - 26;
    const tLen = 14.0;
    const cosY = Math.cos(orbitYaw);
    const sinY = Math.sin(orbitYaw);
    const cosP = Math.cos(orbitPitch);
    const sinP = Math.sin(orbitPitch);

    // Tripod X (Red)
    const tx_x = cosY * tLen;
    const tx_y = (-sinY * sinP) * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX + tx_x, tripodCY - tx_y, rgba(240, 60, 60, 255));
    drawText(tripodCX + tx_x + 2, tripodCY - tx_y - 4, "X", 10, rgba(240, 60, 60, 255));

    // Tripod Y (Green, Up)
    const ty_y = cosP * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX, tripodCY - ty_y, NV_GREEN);
    drawText(tripodCX + 2, tripodCY - ty_y - 4, "Y", 10, NV_GREEN);

    // Tripod Z (Blue)
    const tz_x = -sinY * tLen;
    const tz_y = (-cosY * sinP) * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX + tz_x, tripodCY - tz_y, rgba(50, 140, 255, 255));
    drawText(tripodCX + tz_x + 2, tripodCY - tz_y - 4, "Z", 10, rgba(50, 140, 255, 255));

    drawText(tripodCX - 12, tripodCY + 14, "cm [grid]", 9, TEXT_DIM);
}

// -----------------------------------------------------------------------------
// DEDICATED PREDEFINED 3D MODEL PREVIEWER (SPINNING TURNTABLE ON SIDE PANEL)
// -----------------------------------------------------------------------------
function projectTurntable(lx, ly, lz, angle) {
    // Turntable rotation around Y
    const cosA = Math.cos(angle);
    const sinA = Math.sin(angle);
    const rx = lx * cosA - lz * sinA;
    const rz = lx * sinA + lz * cosA;

    // Pitch tilt 0.35 rad (~20 degrees elevation)
    const cosP = Math.cos(0.35);
    const sinP = Math.sin(0.35);
    const ry = ly * cosP - rz * sinP;
    const depth = ly * sinP + rz * cosP + PREV_DIST;

    if (depth <= 2.0) return null;

    const sx = PREV_CX + (rx / depth) * PREV_FOCAL;
    const sy = PREV_CY - (ry / depth) * PREV_FOCAL;
    return { x: sx, y: sy };
}

function drawPreviewBox(cx, cy, cz, sx, sy, sz, angle, color, fill = false) {
    const hx = sx / 2, hy = sy / 2, hz = sz / 2;
    const v = [
        projectTurntable(cx - hx, cy - hy, cz - hz, angle),
        projectTurntable(cx + hx, cy - hy, cz - hz, angle),
        projectTurntable(cx + hx, cy - hy, cz + hz, angle),
        projectTurntable(cx - hx, cy - hy, cz + hz, angle),
        projectTurntable(cx - hx, cy + hy, cz - hz, angle),
        projectTurntable(cx + hx, cy + hy, cz - hz, angle),
        projectTurntable(cx + hx, cy + hy, cz + hz, angle),
        projectTurntable(cx - hx, cy + hy, cz + hz, angle)
    ];

    const edges = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ];

    for (let i = 0; i < edges.length; i++) {
        const pA = v[edges[i][0]];
        const pB = v[edges[i][1]];
        if (pA && pB) {
            Screen.draw_line(pA.x, pA.y, pB.x, pB.y, color);
        }
    }
}

function renderSideModelPreview(model) {
    // 3D Turntable circular grid at base
    const numPoints = 12;
    const rad = 14.0;
    let prevPt = null;
    for (let i = 0; i <= numPoints; i++) {
        const a = (i / numPoints) * Math.PI * 2;
        const pt = projectTurntable(Math.cos(a) * rad, -10.0, Math.sin(a) * rad, previewTurntableAngle);
        if (prevPt && pt) {
            Screen.draw_line(prevPt.x, prevPt.y, pt.x, pt.y, rgba(60, 60, 60, 255));
        }
        prevPt = pt;
    }

    const angle = previewTurntableAngle;
    const mdlColor = model.color;

    // Render detailed 3D geometry based on selected predefined model
    if (model.id === "MDL-CARTER") {
        // AMR Carter 3D Chassis + Wheels + Rotating LiDAR
        drawPreviewBox(0, -6, 0, 16, 6, 22, angle, mdlColor);
        drawPreviewBox(0, -1, 0, 13, 4, 17, angle, rgba(220, 220, 220, 255));
        drawPreviewBox(0, 4, 0, 6, 4, 6, angle, rgba(30, 30, 30, 255));
        // LiDAR laser emitter
        const lPt = projectTurntable(Math.cos(simTime * 5.0) * 12, 4, Math.sin(simTime * 5.0) * 12, angle);
        const lBase = projectTurntable(0, 4, 0, angle);
        if (lPt && lBase) Screen.draw_line(lBase.x, lBase.y, lPt.x, lPt.y, OMNI_RED);
    } else if (model.id === "MDL-PUMP") {
        // Industrial Compressor Pump: Tank + Cylinders + Base
        drawPreviewBox(0, -4, 0, 24, 11, 11, angle, mdlColor);
        drawPreviewBox(-4, 5, 0, 8, 7, 8, angle, rgba(70, 80, 75, 255));
        drawPreviewBox(5, 6, 0, 6, 9, 6, angle, rgba(60, 70, 65, 255));
        // Support feet
        drawPreviewBox(-9, -10, 0, 2, 3, 10, angle, rgba(50, 50, 50, 255));
        drawPreviewBox(9, -10, 0, 2, 3, 10, angle, rgba(50, 50, 50, 255));
    } else if (model.id === "MDL-UVC") {
        // Hospital UV-C Sterilizer Tower
        drawPreviewBox(0, -8, 0, 12, 5, 12, angle, rgba(50, 50, 50, 255));
        drawPreviewBox(0, 2, 0, 5, 16, 5, angle, mdlColor);
        drawPreviewBox(0, 11, 0, 9, 3, 9, angle, rgba(40, 40, 40, 255));
    } else if (model.id === "MDL-CRASH") {
        // Medical Crash Cart
        drawPreviewBox(0, -3, 0, 12, 12, 16, angle, mdlColor);
        drawPreviewBox(0, 5, 0, 9, 4, 12, angle, rgba(240, 240, 240, 255));
        drawPreviewBox(-5, 9, -5, 2, 6, 2, angle, rgba(180, 180, 180, 255)); // IV pole
    } else if (model.id === "MDL-RACK") {
        // High-Bay Rack
        drawPreviewBox(0, 0, 0, 14, 24, 28, angle, mdlColor);
        drawPreviewBox(0, -4, 0, 10, 4, 18, angle, rgba(160, 120, 70, 255)); // Cargo crate
    } else if (model.id === "MDL-CRATE") {
        // Wooden Pallet & Crate
        drawPreviewBox(0, -8, 0, 18, 3, 18, angle, rgba(140, 100, 60, 255)); // Pallet
        drawPreviewBox(0, 0, 0, 14, 13, 14, angle, mdlColor);                 // Container
    } else if (model.id === "MDL-BOLLARD") {
        // Safety Bollard
        drawPreviewBox(0, -8, 0, 8, 2, 8, angle, rgba(50, 50, 50, 255));
        drawPreviewBox(0, 1, 0, 5, 16, 5, angle, mdlColor);
    }
}

// -----------------------------------------------------------------------------
// COMPLETE OMNIVERSE USD COMPOSER UI RENDERING
// -----------------------------------------------------------------------------
function render() {
    Screen.start_drawing();
    Screen.clear(24, 24, 24, 255);

    // 1. TOP WINDOW TITLE BAR (Y: 0 to 22)
    Screen.draw_rectangle(0, 0, 960, 22, OMNI_DARKEST);
    Screen.draw_line(0, 22, 960, 22, OMNI_BORDER);

    // NVIDIA Omniverse Green Hexagon Logo
    Screen.draw_rectangle(8, 5, 12, 12, NV_GREEN);
    Screen.draw_rectangle(11, 8, 6, 6, OMNI_DARKEST);

    // Stage Name & Path
    drawText(26, 16, "USD Composer 2023.2.5 | omniverse://localhost/IsaacWarehouse/IsaacWarehouse.usd (read-only)*", 11, TEXT_MUTED);

    // Right Status Badges
    const badgeX = 760;
    Screen.draw_rectangle(badgeX, 4, 46, 14, rgba(30, 65, 15, 255));
    Screen.draw_rectangle(badgeX + 5, 8, 5, 5, NV_GREEN);
    drawText(badgeX + 15, 15, "LIVE", 10, TEXT_BRIGHT);

    Screen.draw_rectangle(badgeX + 52, 4, 76, 14, rgba(65, 20, 20, 255));
    drawText(badgeX + 58, 15, "CACHE: OFF", 10, OMNI_RED);

    drawText(904, 15, "_   [ ]   X", 11, TEXT_MUTED);

    // 2. MAIN MENU BAR (Y: 22 to 40)
    Screen.draw_rectangle(0, 22, 960, 18, OMNI_PANEL);
    Screen.draw_line(0, 40, 960, 40, OMNI_BORDER);

    const menus = [ "File", "Edit", "Create", "Window", "Tools", "Layout", "Help" ];
    let menuX = 12;
    menus.forEach(m => {
        drawText(menuX, 35, m, 11, TEXT_REGULAR);
        menuX += 44;
    });

    // 3. VIEWPORT SUB-TOOLBAR (Y: 40 to 58)
    Screen.draw_rectangle(0, 40, 960, 18, OMNI_PANEL_ALT);
    Screen.draw_line(0, 58, 960, 58, OMNI_BORDER);

    // RTX Real-Time Pill
    Screen.draw_rectangle(38, 43, 110, 13, rgba(20, 20, 20, 255));
    Screen.draw_rectangle(43, 47, 5, 5, NV_GREEN);
    drawText(53, 53, "RTX - Real-Time", 10, TEXT_BRIGHT);

    // Camera & Lights Dropdowns
    Screen.draw_rectangle(154, 43, 75, 13, rgba(20, 20, 20, 255));
    drawText(160, 53, "Camera  v", 10, TEXT_REGULAR);

    Screen.draw_rectangle(235, 43, 90, 13, rgba(20, 20, 20, 255));
    drawText(242, 53, "Stage Lights v", 10, TEXT_REGULAR);

    drawText(710, 53, "60.0 FPS | Vulkan 1.3 | VRAM: 142MB", 10, TEXT_DIM);

    // 4. LEFT VERTICAL TOOL PALETTE (X: 0 to 32, Y: 58 to 390)
    Screen.draw_rectangle(0, 58, 32, 332, OMNI_PANEL);
    Screen.draw_line(32, 58, 32, 390, OMNI_BORDER);

    const tools = [
        { icon: "^", active: true },
        { icon: "+", active: false },
        { icon: "O", active: false },
        { icon: "#", active: false },
        { icon: "U", active: false },
        { icon: ">", active: false },
        { icon: "||", active: false }
    ];

    tools.forEach((tl, i) => {
        const ty = 64 + i * 28;
        if (tl.active) {
            Screen.draw_rectangle(4, ty, 24, 22, rgba(243, 156, 18, 50));
            Screen.draw_rectangle(4, ty, 2, 22, OMNI_ORANGE);
            drawText(12, ty + 16, tl.icon, 13, OMNI_ORANGE);
        } else {
            drawText(12, ty + 16, tl.icon, 12, TEXT_MUTED);
        }
    });

    // 5. MAIN 3D PERSPECTIVE VIEWPORT (X: 32 to 665, Y: 58 to 390)
    Screen.draw_rectangle(VP_X, VP_Y, VP_W, VP_H, rgba(20, 20, 20, 255));
    renderMain3DScene();

    // Viewport Perimeter Divider Lines
    Screen.draw_line(VP_X, VP_Y, VP_X + VP_W, VP_Y, OMNI_BORDER);
    Screen.draw_line(VP_X, VP_Y + VP_H, VP_X + VP_W, VP_Y + VP_H, OMNI_BORDER);
    Screen.draw_line(VP_X + VP_W, VP_Y, VP_X + VP_W, VP_Y + VP_H, OMNI_BORDER);

    // 6. RIGHT SIDE PANEL: PREDEFINED 3D MODELS LIBRARY & STAGE (X: 665 to 960)
    const rPaneX = 665;
    const rPaneW = 295;
    Screen.draw_rectangle(rPaneX, 58, rPaneW, 332, OMNI_PANEL);
    Screen.draw_line(rPaneX, 58, rPaneX, 390, OMNI_BORDER);

    // 6A. TABS: [3D Models (Predefined)] vs [Stage (Prims)]
    Screen.draw_rectangle(rPaneX, 58, rPaneW, 18, OMNI_PANEL_ALT);
    Screen.draw_line(rPaneX, 76, 960, 76, OMNI_BORDER);

    // Tab 1: [3D Models] (Active when sideTab === "models")
    const isModelsActive = (sideTab === "models");
    Screen.draw_rectangle(rPaneX + 4, 59, 90, 16, isModelsActive ? OMNI_PANEL : OMNI_PANEL_ALT);
    if (isModelsActive) Screen.draw_line(rPaneX + 4, 75, rPaneX + 94, 75, OMNI_ORANGE);
    drawText(rPaneX + 10, 72, "3D Models", 11, isModelsActive ? TEXT_BRIGHT : TEXT_MUTED);

    // Tab 2: [Stage]
    const isStageActive = (sideTab === "stage");
    Screen.draw_rectangle(rPaneX + 98, 59, 52, 16, isStageActive ? OMNI_PANEL : OMNI_PANEL_ALT);
    if (isStageActive) Screen.draw_line(rPaneX + 98, 75, rPaneX + 150, 75, OMNI_ORANGE);
    drawText(rPaneX + 106, 72, "Stage", 11, isStageActive ? TEXT_BRIGHT : TEXT_MUTED);

    drawText(rPaneX + 160, 72, "Render Settings", 10, TEXT_DIM);

    // 6B. CONTENT: PREDEFINED 3D MODELS LIBRARY ON SIDE
    if (sideTab === "models") {
        // Search header
        Screen.draw_rectangle(rPaneX + 6, 80, rPaneW - 12, 14, rgba(22, 22, 22, 255));
        drawText(rPaneX + 12, 91, "Predefined 3D Models (" + predefinedModels.length + " Available)", 10, OMNI_ORANGE);

        // Predefined 3D Model Catalog Roster (Compact 4 rows)
        const startMdlIdx = Math.max(0, Math.min(selectedModelIdx - 1, predefinedModels.length - 4));
        for (let i = 0; i < 4; i++) {
            const mIdx = startMdlIdx + i;
            if (mIdx >= predefinedModels.length) break;
            const mdl = predefinedModels[mIdx];
            const itemY = 98 + i * 18;
            const isSel = (mIdx === selectedModelIdx);

            if (isSel) {
                Screen.draw_rectangle(rPaneX + 4, itemY, rPaneW - 8, 17, rgba(45, 65, 95, 255));
                Screen.draw_rectangle(rPaneX + 4, itemY, 3, 17, OMNI_ORANGE);
            }

            drawText(rPaneX + 10, itemY + 13, isSel ? "> " + mdl.name : "  " + mdl.name, 11, isSel ? TEXT_BRIGHT : TEXT_REGULAR);
            drawText(rPaneX + 225, itemY + 13, mdl.type, 10, isSel ? OMNI_CYAN : TEXT_DIM);
        }

        // 6C. DEDICATED 3D MODEL PREVIEW VIEWPORT (TURNTABLE ROTATION)
        const curMdl = predefinedModels[selectedModelIdx];
        const previewY = 172;
        Screen.draw_rectangle(rPaneX + 6, previewY, rPaneW - 12, 126, rgba(20, 20, 20, 255));
        Screen.draw_line(rPaneX + 6, previewY, rPaneX + rPaneW - 6, previewY, OMNI_BORDER);
        Screen.draw_line(rPaneX + 6, previewY + 126, rPaneX + rPaneW - 6, previewY + 126, OMNI_BORDER);
        Screen.draw_line(rPaneX + 6, previewY, rPaneX + 6, previewY + 126, OMNI_BORDER);
        Screen.draw_line(rPaneX + rPaneW - 6, previewY, rPaneX + rPaneW - 6, previewY + 126, OMNI_BORDER);

        // Preview Viewport Header
        drawText(rPaneX + 12, previewY + 14, "3D PREVIEW: " + curMdl.id, 10, OMNI_CYAN);
        drawText(rPaneX + 215, previewY + 14, "Turntable", 9, TEXT_DIM);

        // Render Spinning 3D Model on Side
        renderSideModelPreview(curMdl);

        // 6D. 3D MODEL SPECIFICATIONS & ACTIONS
        const specY = 304;
        Screen.draw_rectangle(rPaneX + 6, specY, rPaneW - 12, 80, OMNI_PANEL_ALT);
        drawText(rPaneX + 12, specY + 14, "Category: " + curMdl.category, 10, TEXT_BRIGHT);
        drawText(rPaneX + 12, specY + 28, "Dimensions: " + curMdl.dims + " | Mass: " + curMdl.mass, 9, TEXT_REGULAR);
        drawText(rPaneX + 12, specY + 42, "Geometry: " + curMdl.vertices + " Vertices, " + curMdl.faces + " Faces", 9, TEXT_MUTED);
        drawText(rPaneX + 12, specY + 56, "Material: " + curMdl.mat, 9, NV_GREEN);

        // Controller instruction pill
        Screen.draw_rectangle(rPaneX + 10, specY + 62, rPaneW - 20, 14, rgba(20, 45, 75, 255));
        drawText(rPaneX + 16, specY + 73, "[X] Spawn into Scene  [SELECT] Stage View", 9, TEXT_BRIGHT);
    } else {
        // Stage View (USD Prim Hierarchy)
        Screen.draw_rectangle(rPaneX + 6, 80, rPaneW - 12, 14, rgba(22, 22, 22, 255));
        drawText(rPaneX + 12, 91, "Stage Prims in World (" + allScenePrims.length + " Loaded)", 10, TEXT_MUTED);

        allScenePrims.forEach((prim, idx) => {
            const itemY = 98 + idx * 16;
            const isSel = (idx === selectedPrimIdx);
            if (isSel) {
                Screen.draw_rectangle(rPaneX + 4, itemY, rPaneW - 8, 15, rgba(45, 65, 95, 255));
                Screen.draw_rectangle(rPaneX + 4, itemY, 2, 15, OMNI_ORANGE);
            }
            drawText(rPaneX + 10, itemY + 12, "o", 10, isSel ? TEXT_BRIGHT : TEXT_MUTED);
            drawText(rPaneX + 24, itemY + 12, prim.id + " (" + prim.name.substring(0, 14) + ")", 11, isSel ? TEXT_BRIGHT : TEXT_REGULAR);
            drawText(rPaneX + 240, itemY + 12, (idx < 5 ? "AMR" : "Prop"), 10, isSel ? OMNI_CYAN : TEXT_DIM);
        });

        // Property Transform Inspector
        const selPrim = allScenePrims[selectedPrimIdx];
        const propY = 222;
        Screen.draw_line(rPaneX, propY, 960, propY, OMNI_BORDER);
        Screen.draw_rectangle(rPaneX, propY, rPaneW, 16, OMNI_PANEL_ALT);
        drawText(rPaneX + 10, propY + 12, "Property: " + selPrim.id, 11, TEXT_BRIGHT);

        drawText(rPaneX + 10, propY + 30, "Prim Path: " + selPrim.primPath, 9, TEXT_DIM);
        drawText(rPaneX + 10, propY + 46, "v Transform", 10, TEXT_BRIGHT);

        // RGB Coordinate Badges
        Screen.draw_rectangle(rPaneX + 70, propY + 37, 44, 12, rgba(60, 25, 25, 255));
        drawText(rPaneX + 74, propY + 46, "X " + selPrim.x.toFixed(1), 9, rgba(240, 80, 80, 255));

        Screen.draw_rectangle(rPaneX + 118, propY + 37, 44, 12, rgba(25, 55, 25, 255));
        drawText(rPaneX + 122, propY + 46, "Y " + selPrim.y.toFixed(1), 9, NV_GREEN);

        Screen.draw_rectangle(rPaneX + 166, propY + 37, 44, 12, rgba(25, 45, 80, 255));
        drawText(rPaneX + 170, propY + 46, "Z " + selPrim.z.toFixed(1), 9, rgba(70, 150, 255, 255));

        drawText(rPaneX + 10, propY + 64, "Rotate Y: " + ((selPrim.rotY * 180 / Math.PI) % 360).toFixed(1) + " deg", 9, TEXT_REGULAR);
        drawText(rPaneX + 10, propY + 80, "Battery: " + selPrim.battery.toFixed(1) + "% | State: " + selPrim.state, 10, NV_GREEN);
        drawText(rPaneX + 10, propY + 98, "Task: " + selPrim.task.substring(0, 32), 9, TEXT_MUTED);

        Screen.draw_rectangle(rPaneX + 10, propY + 106, rPaneW - 20, 14, rgba(20, 45, 75, 255));
        drawText(rPaneX + 16, propY + 117, "[SELECT] 3D Model Library  [X] Assign", 9, TEXT_BRIGHT);
    }

    // 7. BOTTOM DOCK PANEL: CONTENT BROWSER / CONSOLE (Y: 390 to 522)
    Screen.draw_rectangle(0, 390, 960, 132, OMNI_PANEL);
    Screen.draw_line(0, 390, 960, 390, OMNI_BORDER);

    // Tab buttons
    Screen.draw_rectangle(0, 390, 960, 18, OMNI_PANEL_ALT);
    Screen.draw_line(0, 408, 960, 408, OMNI_BORDER);

    const bTabs = [ "Content", "Showcases", "NVIDIA Assets", "Materials", "Console" ];
    let tabX = 10;
    bTabs.forEach(t => {
        const isTabSel = (t === "Console");
        if (isTabSel) {
            Screen.draw_rectangle(tabX, 391, 58, 16, OMNI_PANEL);
            Screen.draw_line(tabX, 407, tabX + 58, 407, OMNI_ORANGE);
            drawText(tabX + 8, 404, t, 11, TEXT_BRIGHT);
        } else {
            drawText(tabX + 8, 404, t, 11, TEXT_MUTED);
        }
        tabX += 70;
    });

    drawText(560, 404, "omniverse://localhost/IsaacWarehouse/Robots/", 10, TEXT_DIM);

    // Left Sub-tree
    Screen.draw_rectangle(0, 408, 160, 114, rgba(30, 30, 30, 255));
    Screen.draw_line(160, 408, 160, 522, OMNI_BORDER);

    drawText(10, 424, "+ Import Assets", 10, NV_GREEN);
    drawText(10, 442, "> 3D Models Folder", 10, TEXT_MUTED);
    drawText(10, 460, "v Omniverse Server", 10, TEXT_BRIGHT);
    drawText(22, 476, "- IsaacWarehouse", 10, OMNI_CYAN);
    drawText(22, 492, "- Predefined_Robots", 10, TEXT_REGULAR);
    drawText(10, 510, "> Local Storage (ux0:)", 10, TEXT_MUTED);

    // Right Area: Live Stage Event Stream
    const logStartX = 170;
    drawText(logStartX, 424, "STAGE EVENT STREAM & TELEMETRY LOG", 10, TEXT_MUTED);
    for (let i = 0; i < Math.min(5, consoleLogs.length); i++) {
        const lineY = 442 + i * 15;
        drawText(logStartX, lineY, consoleLogs[i], 11, (i === 0) ? TEXT_BRIGHT : TEXT_MUTED);
    }

    // 8. BOTTOM CONTROLLER ACTION BAR (Y: 522 to 544)
    Screen.draw_rectangle(0, 522, 960, 22, OMNI_DARKEST);
    Screen.draw_line(0, 522, 960, 522, OMNI_BORDER);

    drawText(14, 538, "[L1/R1] 3D Model", 11, TEXT_BRIGHT);
    drawText(140, 538, "[R-Stick] Orbit 3D", 11, TEXT_BRIGHT);
    drawText(265, 538, "[L-Stick] Pan 3D", 11, TEXT_BRIGHT);
    drawText(375, 538, "[D-Pad] Browse", 11, TEXT_REGULAR);
    drawText(470, 538, "[X] Spawn / Assign", 11, NV_GREEN);
    drawText(595, 538, "[O] Dock", 11, OMNI_CYAN);
    drawText(660, 538, "[] E-Stop", 11, OMNI_RED);
    drawText(735, 538, "[SELECT] Tab", 11, OMNI_ORANGE);
    drawText(845, 538, "Isaac Sim 60Hz", 10, TEXT_DIM);

    Screen.end_drawing();
    Screen.swap_buffers();
}

// -----------------------------------------------------------------------------
// AUTONOMOUS LOCAL SIMULATION LOOP (60 FPS)
// -----------------------------------------------------------------------------
function updateSimulation(dt) {
    simTime += dt;
    previewTurntableAngle += dt * 1.5; // Smooth 3D turntable spin for side model preview

    // Autonomous AMR navigation loop
    robots.forEach((r, idx) => {
        if (r.state === "NAVIGATING" || r.state === "PATROLLING") {
            r.battery = Math.max(5.0, r.battery - dt * 0.05);

            const dx = r.tx - r.x;
            const dz = r.tz - r.z;
            const dist = Math.sqrt(dx * dx + dz * dz);

            if (dist > 1.0) {
                const targetRot = Math.atan2(dx, dz);
                let diffRot = targetRot - r.rotY;
                while (diffRot > Math.PI) diffRot -= 2 * Math.PI;
                while (diffRot < -Math.PI) diffRot += 2 * Math.PI;
                r.rotY += diffRot * dt * 3.0;

                r.x += (dx / dist) * r.speed * dt * 10.0;
                r.z += (dz / dist) * r.speed * dt * 10.0;
            } else {
                const waypoints = [
                    { x: 0, z: -35 }, { x: -35, z: 0 }, { x: 35, z: 0 },
                    { x: 0, z: 35 }, { x: -20, z: 20 }, { x: 20, z: -20 }
                ];
                const wp = waypoints[Math.floor((simTime + idx * 2) % waypoints.length)];
                r.tx = wp.x + (Math.random() - 0.5) * 15.0;
                r.tz = wp.z + (Math.random() - 0.5) * 15.0;
            }
        }
    });
}

// -----------------------------------------------------------------------------
// CONTROLLER INPUT HANDLING
// -----------------------------------------------------------------------------
const prevButtons = new Map();
function justPressed(btn) {
    const isDown = Pads.check(btn);
    const wasDown = prevButtons.get(btn) === true;
    prevButtons.set(btn, isDown);
    return isDown && !wasDown;
}

function handleInput() {
    const pad = Pads.read();

    // 1. Right Stick: Orbit 3D Perspective Camera (Yaw & Pitch)
    if (Math.abs(pad.rx) > 25) {
        orbitYaw += (pad.rx / 128.0) * 0.04;
    }
    if (Math.abs(pad.ry) > 25) {
        orbitPitch = Math.max(0.08, Math.min(1.45, orbitPitch - (pad.ry / 128.0) * 0.04));
    }

    // 2. Left Stick: Pan Camera Target in 3D Space
    if (Math.abs(pad.lx) > 25) {
        const panAmount = (pad.lx / 128.0) * 1.5;
        targetX += Rx * panAmount;
        targetZ += Rz * panAmount;
    }
    if (Math.abs(pad.ly) > 25) {
        const panAmount = (pad.ly / 128.0) * 1.5;
        targetX += Fx * panAmount;
        targetZ += Fz * panAmount;
    }

    // 3. L1 / R1: Cycle Predefined 3D Models on Side (or Prims)
    if (justPressed(Pads.L1)) {
        if (sideTab === "models") {
            selectedModelIdx = (selectedModelIdx - 1 + predefinedModels.length) % predefinedModels.length;
            addLog("[3D Library] Selected: " + predefinedModels[selectedModelIdx].name);
        } else {
            selectedPrimIdx = (selectedPrimIdx - 1 + allScenePrims.length) % allScenePrims.length;
            addLog("[Selection] Prim: " + allScenePrims[selectedPrimIdx].id);
        }
    }
    if (justPressed(Pads.R1)) {
        if (sideTab === "models") {
            selectedModelIdx = (selectedModelIdx + 1) % predefinedModels.length;
            addLog("[3D Library] Selected: " + predefinedModels[selectedModelIdx].name);
        } else {
            selectedPrimIdx = (selectedPrimIdx + 1) % allScenePrims.length;
            addLog("[Selection] Prim: " + allScenePrims[selectedPrimIdx].id);
        }
    }

    // 4. D-Pad UP / DOWN: Browse Catalog or Mission
    if (justPressed(Pads.UP)) {
        if (sideTab === "models") {
            selectedModelIdx = (selectedModelIdx - 1 + predefinedModels.length) % predefinedModels.length;
        } else {
            selectedPrimIdx = (selectedPrimIdx - 1 + allScenePrims.length) % allScenePrims.length;
        }
    }
    if (justPressed(Pads.DOWN)) {
        if (sideTab === "models") {
            selectedModelIdx = (selectedModelIdx + 1) % predefinedModels.length;
        } else {
            selectedPrimIdx = (selectedPrimIdx + 1) % allScenePrims.length;
        }
    }

    // 5. CROSS: Spawn Predefined 3D Model into Scene or Dispatch
    if (justPressed(Pads.CROSS)) {
        if (sideTab === "models") {
            const spawnedModel = predefinedModels[selectedModelIdx];
            addLog("[Spawn] 3D Model instantiated: " + spawnedModel.name);
            // Move camera target towards spawn zone
            targetX = 0; targetY = 8; targetZ = 0;
        } else {
            const bot = robots[selectedPrimIdx % robots.length];
            const mission = availableMissions[selectedMissionIdx];
            bot.state = "NAVIGATING";
            bot.task = mission.title;
            addLog("[Dispatch] " + bot.id + " -> " + mission.title);
        }
    }

    // 6. CIRCLE: Dock active robot
    if (justPressed(Pads.CIRCLE)) {
        const bot = robots[0];
        bot.tx = 0.0;
        bot.tz = -15.0;
        bot.state = "NAVIGATING";
        bot.task = "Autonomous Inductive Docking";
        addLog("[Dock] AMR-01 returning to bay");
    }

    // 7. SQUARE: E-Stop Toggle
    if (justPressed(Pads.SQUARE)) {
        robots.forEach(r => {
            if (r.state !== "E_STOP") {
                r.state = "E_STOP";
                r.speed = 0.0;
            } else {
                r.state = "PATROLLING";
                r.speed = 1.0;
            }
        });
        addLog("[E-STOP] All robotics motion paused.");
    }

    // 8. SELECT: Toggle Side Panel Tab (Predefined 3D Models <-> Stage Prims)
    if (justPressed(Pads.SELECT)) {
        sideTab = (sideTab === "models") ? "stage" : "models";
        addLog("[Side Panel] Switched to " + (sideTab === "models" ? "3D Models Library" : "Stage Tree"));
    }

    // 9. START: Reset Camera to Default Isometric Angle
    if (justPressed(Pads.START)) {
        orbitYaw = 0.55;
        orbitPitch = 0.42;
        camDist = 185.0;
        targetX = 0.0;
        targetY = 8.0;
        targetZ = 0.0;
        addLog("[Camera] Reset to Perspective Default");
    }
}

// -----------------------------------------------------------------------------
// MAIN GAME LOOP (Synchronized with VSync)
// -----------------------------------------------------------------------------
let lastFrameTime = Date.now();

const mainLoop = os.setInterval(() => {
    if (!running) {
        os.clearInterval(mainLoop);
        return;
    }

    const now = Date.now();
    const dt = Math.min(0.05, Math.max(0.001, (now - lastFrameTime) / 1000.0));
    lastFrameTime = now;

    handleInput();
    updateCameraVectors();
    updateSimulation(dt);
    render();
}, 0);
