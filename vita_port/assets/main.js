// =============================================================================
// FARSVERSE POCKET -- NVIDIA OMNIVERSE USD COMPOSER & DRIVE SIM 1:1 REPLICA
// REALISTIC 3D CAD ENGINE: SOLID SHADED MESHES, GIZMOS, SENSOR PIP & DRIVE NET
// =============================================================================

const font = Font.load_font_file("app0:/assets/segoeui.ttf");

// Initialize PS Vita Analog Controller Sampling Mode (Left & Right sticks)
try {
    if (typeof Pads !== "undefined" && typeof Pads.setSamplingMode === "function") {
        Pads.setSamplingMode(Pads.MODE_ANALOG_WIDE !== undefined ? Pads.MODE_ANALOG_WIDE : 2);
    }
} catch (e) {}

// Helper: 32-bit RGBA color for Vita2D hardware
function rgba(r, g, b, a) {
    if (a === undefined) a = 255;
    return (
        ((a & 255) << 24) |
        ((b & 255) << 16) |
        ((g & 255) << 8) |
        (r & 255)
    ) >>> 0;
}

// Helper: Normalize PS Vita / Vita3K analog stick axis with deadzone
// Sony SceCtrlData gives uint8 (0..255) with 128 resting center
function getAxisDelta(rawVal) {
    if (typeof rawVal !== "number") return 0;
    if (rawVal >= 0 && rawVal <= 255) {
        var diff = rawVal - 128;
        if (Math.abs(diff) < 22) return 0; // deadzone
        return Math.max(-1.0, Math.min(1.0, diff / 128.0));
    }
    if (Math.abs(rawVal) < 22) return 0;
    return Math.max(-1.0, Math.min(1.0, rawVal / 128.0));
}

// -----------------------------------------------------------------------------
// NVIDIA OMNIVERSE & DRIVE SIM COLOR PALETTE
// -----------------------------------------------------------------------------
var OMNI_DARKEST    = rgba(18, 18, 18, 255);
var OMNI_BG         = rgba(24, 25, 26, 255);
var OMNI_PANEL      = rgba(32, 33, 35, 255);
var OMNI_PANEL_ALT  = rgba(40, 42, 44, 255);
var OMNI_BORDER     = rgba(50, 52, 54, 255);
var OMNI_BORDER_HI  = rgba(75, 78, 82, 255);

var NV_GREEN        = rgba(118, 185, 0, 255);  // NVIDIA Signature Green #76B900
var NV_GREEN_DIM    = rgba(65, 105, 0, 255);
var OMNI_ORANGE     = rgba(243, 156, 18, 255); // Omniverse USD selection glow
var OMNI_ORANGE_DIM = rgba(160, 95, 10, 255);
var OMNI_RED        = rgba(235, 60, 60, 255);
var OMNI_BLUE       = rgba(60, 140, 240, 255);
var OMNI_CYAN       = rgba(0, 220, 245, 255);  // LiDAR / DriveNet point cloud
var OMNI_VIOLET     = rgba(185, 95, 255, 255);
var OMNI_YELLOW     = rgba(245, 210, 40, 255);

var TEXT_BRIGHT     = rgba(245, 245, 245, 255);
var TEXT_REGULAR    = rgba(200, 200, 200, 255);
var TEXT_MUTED      = rgba(140, 140, 140, 255);
var TEXT_DIM        = rgba(90, 90, 90, 255);

var SHADOW_COLOR    = rgba(8, 8, 8, 150);

// -----------------------------------------------------------------------------
// APPLICATION & SIMULATION STATE
// -----------------------------------------------------------------------------
var running = true;
var simTime = 0.0;
var simFrame = 142;
var simPlaying = true;
var hostIp = "192.168.0.135";
var hostPort = 8080;
var hostOnline = false;

var sideTab = "models"; // "models" | "neural" | "stage"
var selectedModelIdx = 0;
var selectedPrimIdx  = 0;
var selectedMissionIdx = 0;
var showNeuralPerception = true;
var showGizmo = true;
var showSensorPIP = true;

// 3D Perspective Viewport Area (X: 32 to 665, Y: 58 to 390)
var VP_X  = 32;
var VP_Y  = 58;
var VP_W  = 633;
var VP_H  = 332;
var VP_CX = VP_X + (VP_W >> 1); // 348
var VP_CY = VP_Y + (VP_H >> 1); // 224
var FOCAL = 345.0;

// Upright 3D Look-At Camera Parameters (Top-down Isometric View)
var orbitYaw   = 0.65;  // ~37 degrees azimuth
var orbitPitch = 0.45;  // ~26 degrees elevation
var camDist    = 185.0; // Distance to focus target
var targetX    = 0.0;
var targetY    = 10.0;  // Focus on center of warehouse floor
var targetZ    = 0.0;

var camX = 0.0, camY = 0.0, camZ = 0.0;
var Fx = 0.0, Fy = 0.0, Fz = 0.0;
var Rx = 0.0, Ry = 0.0, Rz = 0.0;
var Ux = 0.0, Uy = 0.0, Uz = 0.0;

// Side 3D Model Preview Viewport Area
var PREV_CX    = 812;
var PREV_CY    = 238;
var PREV_FOCAL = 145.0;
var PREV_DIST  = 40.0;
var previewTurntableAngle = 0.0;

// Live Stage Event Stream
var consoleLogs = [
    "[USD Composer 2023.2.5] Stage loaded: IsaacWarehouse.usd",
    "[NVIDIA DRIVE] PhysX 5.1 & TensorRT 8.6 DriveNet solver active (60 Hz)",
    "[Neural Net] Multi-layer perception graph streaming at 3.2ms latency",
    "[Perception] LiDAR 360 point cloud & trajectory prediction ribbon active"
];

function addLog(msg) {
    var t = simTime.toFixed(1) + "s";
    consoleLogs.unshift("[" + t + "] " + msg);
    if (consoleLogs.length > 7) consoleLogs.pop();
}

// Particle System (ambient dust motes)
var NUM_PARTICLES = 22;
var particles = [];
for (var pi = 0; pi < NUM_PARTICLES; pi++) {
    particles.push({
        x: (Math.random() - 0.5) * 140,
        y: Math.random() * 28 + 1,
        z: (Math.random() - 0.5) * 140,
        vx: (Math.random() - 0.5) * 0.25,
        vy: (Math.random() - 0.5) * 0.06,
        vz: (Math.random() - 0.5) * 0.25,
        bright: 40 + Math.floor(Math.random() * 55)
    });
}

// -----------------------------------------------------------------------------
// PREDEFINED 3D MODELS CATALOG (Available on Side Panel)
// -----------------------------------------------------------------------------
var predefinedModels = [
    {
        id: "MDL-CARTER",
        name: "AMR Carter Logistics",
        category: "Robotics / AMRs",
        type: "Mesh",
        vertices: 64, faces: 36,
        dims: "120 x 85 x 45 cm", mass: "145 kg",
        mat: "OmniPBR_IndustrialMetal",
        desc: "Autonomous transport chassis with rotating 360 LiDAR",
        color: NV_GREEN
    },
    {
        id: "MDL-PUMP",
        name: "Vacuum Compressor Pump",
        category: "Machinery / Plant",
        type: "Mesh",
        vertices: 72, faces: 42,
        dims: "180 x 110 x 140 cm", mass: "380 kg",
        mat: "OmniPBR_CastIron_Green",
        desc: "Industrial compressor pump with twin pistons & tank",
        color: rgba(110, 140, 100, 255)
    },
    {
        id: "MDL-UVC",
        name: "Hospital UV-C Sterilizer",
        category: "Medical Robotics",
        type: "Mesh",
        vertices: 48, faces: 28,
        dims: "60 x 60 x 165 cm", mass: "68 kg",
        mat: "OmniPBR_QuartzSanitize",
        desc: "High-intensity ultraviolet disinfection lamp tower",
        color: OMNI_VIOLET
    },
    {
        id: "MDL-CRASH",
        name: "Emergency Crash Cart",
        category: "Hospital Props",
        type: "Mesh",
        vertices: 52, faces: 30,
        dims: "90 x 65 x 110 cm", mass: "42 kg",
        mat: "OmniPBR_MedicalSteel",
        desc: "Resuscitation emergency trolley with defibrillator rack",
        color: OMNI_RED
    },
    {
        id: "MDL-RACK",
        name: "High-Bay Storage Rack",
        category: "Warehouse Logistics",
        type: "Xform / Mesh",
        vertices: 84, faces: 48,
        dims: "300 x 120 x 450 cm", mass: "620 kg",
        mat: "OmniPBR_GalvanizedSteel",
        desc: "Structural steel pallet racking unit with cross-bracing",
        color: rgba(70, 115, 175, 255)
    },
    {
        id: "MDL-CRATE",
        name: "Pallet Cargo Crate",
        category: "Cargo / Freight",
        type: "Mesh",
        vertices: 32, faces: 18,
        dims: "120 x 80 x 85 cm", mass: "210 kg",
        mat: "OmniPBR_WoodCardboard",
        desc: "Heavy wooden shipping pallet with reinforced container",
        color: rgba(170, 130, 80, 255)
    },
    {
        id: "MDL-BOLLARD",
        name: "Safety Hazard Bollard",
        category: "Facility Safety",
        type: "Mesh",
        vertices: 24, faces: 14,
        dims: "30 x 30 x 100 cm", mass: "55 kg",
        mat: "OmniPBR_HazardYellow",
        desc: "Impact-resistant guard post with hazard caution stripes",
        color: OMNI_YELLOW
    }
];

// -----------------------------------------------------------------------------
// ACTIVE USD PRIMS IN WAREHOUSE SCENE
// -----------------------------------------------------------------------------
var robots = [
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
        aiConfidence: "99.4%",
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
        aiConfidence: "98.7%",
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
        aiConfidence: "97.9%",
        color: OMNI_VIOLET
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
        aiConfidence: "98.2%",
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
        aiConfidence: "96.5%",
        color: OMNI_ORANGE
    }
];

var sceneProps = [
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
        aiConfidence: "99.1%",
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
        aiConfidence: "99.8%",
        color: rgba(70, 115, 175, 255)
    }
];

var allScenePrims = robots.concat(sceneProps);

// Mission Roster
var availableMissions = [
    { title: "PATROL CORRIDORS", loc: "Aisle_A", desc: "Routine security inspection", priority: "NORMAL" },
    { title: "DELIVER PHARMACEUTICALS", loc: "Pharmacy", desc: "Transport scheduled meds to ICU", priority: "HIGH" },
    { title: "PATIENT CALL: ROOM 5", loc: "Room_5", desc: "Nurse call button response", priority: "URGENT" },
    { title: "STERILIZE EMERGENCY WARD", loc: "ER_Ward", desc: "Automated UV-C cycle", priority: "NORMAL" },
    { title: "ICU CRITICAL ASSIST", loc: "ICU_1", desc: "Emergency crash cart assist", priority: "CRITICAL" },
    { title: "RETURN TO CHARGING DOCK", loc: "Dock_1", desc: "Autonomous inductive recharge", priority: "LOW" },
    { title: "ISAAC SIM AI PATH DISPATCH", loc: "Hub", desc: "Host LLM (phi3:mini) navigation", priority: "AI" }
];

// Text drawing helper
function drawText(x, y, str, size, color) {
    if (size === undefined) size = 12;
    if (color === undefined) color = TEXT_REGULAR;
    try {
        Font.font_draw_text(font, x | 0, y | 0, color, size, String(str));
    } catch (e) {}
}

// -----------------------------------------------------------------------------
// LOOK-AT CAMERA & PERSPECTIVE PROJECTION
// -----------------------------------------------------------------------------
function updateCameraVectors() {
    var cosP = Math.cos(orbitPitch);
    var sinP = Math.sin(orbitPitch);
    var cosY = Math.cos(orbitYaw);
    var sinY = Math.sin(orbitYaw);

    camX = targetX + camDist * sinY * cosP;
    camY = targetY + camDist * sinP;
    camZ = targetZ + camDist * cosY * cosP;

    var invDist = 1.0 / camDist;
    Fx = (targetX - camX) * invDist;
    Fy = (targetY - camY) * invDist;
    Fz = (targetZ - camZ) * invDist;

    var rLen = Math.sqrt(Fz * Fz + Fx * Fx);
    if (rLen > 0.0001) {
        Rx = -Fz / rLen;
        Ry = 0.0;
        Rz = Fx / rLen;
    } else {
        Rx = 1.0; Ry = 0.0; Rz = 0.0;
    }

    Ux = Ry * Fz - Rz * Fy;
    Uy = Rz * Fx - Rx * Fz;
    Uz = Rx * Fy - Ry * Fx;
}

function project3D(wx, wy, wz) {
    var dx = wx - camX;
    var dy = wy - camY;
    var dz = wz - camZ;

    var camRight = dx * Rx + dy * Ry + dz * Rz;
    var camUp    = dx * Ux + dy * Uy + dz * Uz;
    var camDepth = dx * Fx + dy * Fy + dz * Fz;

    if (camDepth <= 5.0) return null;

    var sx = VP_CX + (camRight / camDepth) * FOCAL;
    var sy = VP_CY - (camUp / camDepth) * FOCAL;

    if (sx < VP_X - 35 || sx > VP_X + VP_W + 35 || sy < VP_Y - 35 || sy > VP_Y + VP_H + 35) {
        return null;
    }

    return { x: sx, y: sy, depth: camDepth };
}

function drawLine3D(x1, y1, z1, x2, y2, z2, color) {
    var p1 = project3D(x1, y1, z1);
    var p2 = project3D(x2, y2, z2);
    if (!p1 || !p2) return;
    Screen.draw_line(p1.x, p1.y, p2.x, p2.y, color);
}

// =============================================================================
// SCANLINE FILLED POLYGON RASTERIZER (FAST HARDWARE-ACCELERATED)
// =============================================================================
function fillQuad(ax, ay, bx, by, cx, cy, dx, dy, color, clX0, clY0, clX1, clY1) {
    var minY = ay, maxY = ay;
    if (by < minY) minY = by; if (by > maxY) maxY = by;
    if (cy < minY) minY = cy; if (cy > maxY) maxY = cy;
    if (dy < minY) dy = dy; if (dy > maxY) maxY = dy;

    var sY = (minY | 0) + 1;
    if (sY < clY0) sY = clY0;
    var eY = maxY | 0;
    if (eY > clY1) eY = clY1;
    if (sY & 1) sY++;
    if (sY > eY) return;

    for (var y = sY; y <= eY; y += 2) {
        var xL = 9999, xR = -9999;
        if ((ay <= y && by > y) || (by <= y && ay > y)) {
            var x = ax + (y - ay) / (by - ay) * (bx - ax);
            if (x < xL) xL = x; if (x > xR) xR = x;
        }
        if ((by <= y && cy > y) || (cy <= y && by > y)) {
            var x = bx + (y - by) / (cy - by) * (cx - bx);
            if (x < xL) xL = x; if (x > xR) xR = x;
        }
        if ((cy <= y && dy > y) || (dy <= y && cy > y)) {
            var x = cx + (y - cy) / (dy - cy) * (dx - cx);
            if (x < xL) xL = x; if (x > xR) xR = x;
        }
        if ((dy <= y && ay > y) || (ay <= y && dy > y)) {
            var x = dx + (y - dy) / (ay - dy) * (ax - dx);
            if (x < xL) xL = x; if (x > xR) xR = x;
        }
        if (xL < xR) {
            var lx = xL | 0;
            if (lx < clX0) lx = clX0;
            var rx = xR | 0;
            if (rx > clX1) rx = clX1;
            if (rx > lx) Screen.draw_rectangle(lx, y, rx - lx, 2, color);
        }
    }
}

// Directional Key Light Vector (from upper-left-front)
var LIGHT_X = 0.35, LIGHT_Y = 0.82, LIGHT_Z = 0.45;
var FOG_NEAR = 110.0, FOG_RANGE_INV = 1.0 / 300.0;
var FOG_R = 24, FOG_G = 25, FOG_B = 26;

// Solid Shaded 3D Box with Directional Lighting, Specular Glints & Edge Outlines
function drawSolidBox3D(cx, cy, cz, sx, sy, sz, rotY, baseColor, selColor) {
    var hx = sx * 0.5, hy = sy * 0.5, hz = sz * 0.5;
    var cosR = Math.cos(rotY), sinR = Math.sin(rotY);
    var bR = baseColor & 255;
    var bG = (baseColor >>> 8) & 255;
    var bB = (baseColor >>> 16) & 255;

    var v0 = project3D(cx - hx*cosR + hz*sinR, cy - hy, cz - hx*sinR - hz*cosR);
    var v1 = project3D(cx + hx*cosR + hz*sinR, cy - hy, cz + hx*sinR - hz*cosR);
    var v2 = project3D(cx + hx*cosR - hz*sinR, cy - hy, cz + hx*sinR + hz*cosR);
    var v3 = project3D(cx - hx*cosR - hz*sinR, cy - hy, cz - hx*sinR + hz*cosR);
    var v4 = project3D(cx - hx*cosR + hz*sinR, cy + hy, cz - hx*sinR - hz*cosR);
    var v5 = project3D(cx + hx*cosR + hz*sinR, cy + hy, cz + hx*sinR - hz*cosR);
    var v6 = project3D(cx + hx*cosR - hz*sinR, cy + hy, cz + hx*sinR + hz*cosR);
    var v7 = project3D(cx - hx*cosR - hz*sinR, cy + hy, cz - hx*sinR + hz*cosR);

    var tcX = camX - cx, tcY = camY - cy, tcZ = camZ - cz;

    var fc = 0;
    var fv = [];

    // Top face
    if (tcY > 0 && v4 && v5 && v6 && v7) {
        var br = 0.35 + Math.max(0, LIGHT_Y) * 0.65;
        var dp = (v4.depth + v5.depth + v6.depth + v7.depth) * 0.25;
        fv[fc++] = {a:v7, b:v6, c:v5, d:v4, br:br, dp:dp};
    }
    // Bottom face
    if (tcY < 0 && v0 && v1 && v2 && v3) {
        var br = 0.2;
        var dp = (v0.depth + v1.depth + v2.depth + v3.depth) * 0.25;
        fv[fc++] = {a:v0, b:v1, c:v2, d:v3, br:br, dp:dp};
    }
    // Front face (+Z)
    var fnDot = sinR * tcX + cosR * tcZ;
    if (fnDot > 0 && v3 && v2 && v6 && v7) {
        var br = 0.25 + Math.max(0, sinR * LIGHT_X + cosR * LIGHT_Z) * 0.65;
        var dp = (v3.depth + v2.depth + v6.depth + v7.depth) * 0.25;
        fv[fc++] = {a:v3, b:v2, c:v6, d:v7, br:br, dp:dp};
    }
    // Back face (-Z)
    if (fnDot < 0 && v0 && v1 && v5 && v4) {
        var br = 0.25 + Math.max(0, -sinR * LIGHT_X - cosR * LIGHT_Z) * 0.65;
        var dp = (v0.depth + v1.depth + v5.depth + v4.depth) * 0.25;
        fv[fc++] = {a:v4, b:v5, c:v1, d:v0, br:br, dp:dp};
    }
    // Right face (+X)
    var rxDot = cosR * tcX - sinR * tcZ;
    if (rxDot > 0 && v1 && v2 && v6 && v5) {
        var br = 0.25 + Math.max(0, cosR * LIGHT_X - sinR * LIGHT_Z) * 0.65;
        var dp = (v1.depth + v2.depth + v6.depth + v5.depth) * 0.25;
        fv[fc++] = {a:v5, b:v6, c:v2, d:v1, br:br, dp:dp};
    }
    // Left face (-X)
    if (rxDot < 0 && v0 && v3 && v7 && v4) {
        var br = 0.25 + Math.max(0, -cosR * LIGHT_X + sinR * LIGHT_Z) * 0.65;
        var dp = (v0.depth + v3.depth + v7.depth + v4.depth) * 0.25;
        fv[fc++] = {a:v0, b:v3, c:v7, d:v4, br:br, dp:dp};
    }

    // Sort back-to-front
    for (var i = 1; i < fc; i++) {
        var key = fv[i];
        var j = i - 1;
        while (j >= 0 && fv[j].dp < key.dp) {
            fv[j + 1] = fv[j];
            j--;
        }
        fv[j + 1] = key;
    }

    // Render faces
    for (var i = 0; i < fc; i++) {
        var f = fv[i];
        var fr = (bR * f.br) | 0;
        var fg = (bG * f.br) | 0;
        var fb = (bB * f.br) | 0;

        // Depth fog attenuation
        var fogT = (f.dp - FOG_NEAR) * FOG_RANGE_INV;
        if (fogT < 0) fogT = 0; if (fogT > 1) fogT = 1;
        if (fogT > 0) {
            fr = (fr + (FOG_R - fr) * fogT) | 0;
            fg = (fg + (FOG_G - fogT * fg) * fogT) | 0;
            fb = (fb + (FOG_B - fb) * fogT) | 0;
        }

        if (fr > 255) fr = 255; if (fg > 255) fg = 255; if (fb > 255) fb = 255;
        if (fr < 0) fr = 0; if (fg < 0) fg = 0; if (fb < 0) fb = 0;

        fillQuad(f.a.x, f.a.y, f.b.x, f.b.y, f.c.x, f.c.y, f.d.x, f.d.y,
                 rgba(fr, fg, fb, 255), VP_X, VP_Y, VP_X + VP_W, VP_Y + VP_H);

        // Chamfered CAD edge highlights
        var edgeCol = rgba(Math.min(255, fr + 26), Math.min(255, fg + 26), Math.min(255, fb + 26), 255);
        Screen.draw_line(f.a.x, f.a.y, f.b.x, f.b.y, edgeCol);
        Screen.draw_line(f.b.x, f.b.y, f.c.x, f.c.y, edgeCol);
        Screen.draw_line(f.c.x, f.c.y, f.d.x, f.d.y, edgeCol);
        Screen.draw_line(f.d.x, f.d.y, f.a.x, f.a.y, edgeCol);
    }

    // Selection outline
    if (selColor) {
        var allV = [v0,v1,v2,v3,v4,v5,v6,v7];
        var edges = [[0,1],[1,2],[2,3],[3,0],[4,5],[5,6],[6,7],[7,4],[0,4],[1,5],[2,6],[3,7]];
        for (var e = 0; e < 12; e++) {
            var ea = allV[edges[e][0]], eb = allV[edges[e][1]];
            if (ea && eb) {
                Screen.draw_line(ea.x, ea.y, eb.x, eb.y, selColor);
                Screen.draw_line(ea.x + 1, ea.y, eb.x + 1, eb.y, selColor);
            }
        }
    }
}

// Flat Ground Contact Shadow
function drawGroundShadow(cx, cz, halfW, halfD) {
    var s0 = project3D(cx - halfW, 0.08, cz - halfD);
    var s1 = project3D(cx + halfW, 0.08, cz - halfD);
    var s2 = project3D(cx + halfW, 0.08, cz + halfD);
    var s3 = project3D(cx - halfW, 0.08, cz + halfD);
    if (s0 && s1 && s2 && s3) {
        fillQuad(s0.x, s0.y, s1.x, s1.y, s2.x, s2.y, s3.x, s3.y,
                 SHADOW_COLOR, VP_X, VP_Y, VP_X + VP_W, VP_Y + VP_H);
    }
}

// -----------------------------------------------------------------------------
// 3D INTERACTIVE TRANSFORM GIZMO (OMNIVERSE USD COMPOSER SIGNATURE)
// -----------------------------------------------------------------------------
function renderTransformGizmo(cx, cy, cz) {
    var origin = project3D(cx, cy, cz);
    if (!origin) return;

    var gLen = 16.0;
    var xHead = project3D(cx + gLen, cy, cz);
    var yHead = project3D(cx, cy + gLen, cz);
    var zHead = project3D(cx, cy, cz + gLen);

    // Center pivot sphere
    Screen.draw_fill_circle(4, origin.x, origin.y, OMNI_ORANGE);
    Screen.draw_fill_circle(2, origin.x, origin.y, TEXT_BRIGHT);

    // X Axis (Red)
    if (xHead) {
        Screen.draw_line(origin.x, origin.y, xHead.x, xHead.y, rgba(240, 60, 60, 255));
        Screen.draw_fill_circle(3, xHead.x, xHead.y, rgba(240, 60, 60, 255));
        drawText(xHead.x + 3, xHead.y - 4, "X", 10, rgba(240, 60, 60, 255));
    }

    // Y Axis (Green)
    if (yHead) {
        Screen.draw_line(origin.x, origin.y, yHead.x, yHead.y, NV_GREEN);
        Screen.draw_fill_circle(3, yHead.x, yHead.y, NV_GREEN);
        drawText(yHead.x + 3, yHead.y - 4, "Y", 10, NV_GREEN);
    }

    // Z Axis (Blue)
    if (zHead) {
        Screen.draw_line(origin.x, origin.y, zHead.x, zHead.y, rgba(50, 140, 255, 255));
        Screen.draw_fill_circle(3, zHead.x, zHead.y, rgba(50, 140, 255, 255));
        drawText(zHead.x + 3, zHead.y - 4, "Z", 10, rgba(50, 140, 255, 255));
    }
}

// -----------------------------------------------------------------------------
// NVIDIA DRIVE SIM MULTI-SENSOR PERCEPTION SUITE
// -----------------------------------------------------------------------------

// 1. AI 3D Bounding Box with CAD Bracket Accents and Confidence Pill
function drawAIPerceptionBox(cx, cy, cz, sx, sy, sz, label, color) {
    var hx = sx * 0.5 + 1.2, hy = sy * 0.5 + 1.2, hz = sz * 0.5 + 1.2;
    var v = [
        project3D(cx - hx, cy - hy, cz - hz),
        project3D(cx + hx, cy - hy, cz - hz),
        project3D(cx + hx, cy - hy, cz + hz),
        project3D(cx - hx, cy - hy, cz + hz),
        project3D(cx - hx, cy + hy, cz - hz),
        project3D(cx + hx, cy + hy, cz - hz),
        project3D(cx + hx, cy + hy, cz + hz),
        project3D(cx - hx, cy + hy, cz + hz)
    ];

    var edges = [
        [0, 1], [1, 2], [2, 3], [3, 0],
        [4, 5], [5, 6], [6, 7], [7, 4],
        [0, 4], [1, 5], [2, 6], [3, 7]
    ];

    for (var i = 0; i < edges.length; i++) {
        var pA = v[edges[i][0]], pB = v[edges[i][1]];
        if (pA && pB) Screen.draw_line(pA.x, pA.y, pB.x, pB.y, color);
    }

    var topPt = project3D(cx, cy + hy + 2.5, cz);
    if (topPt) {
        Screen.draw_rectangle(topPt.x - 42, topPt.y - 12, 84, 12, rgba(16, 22, 18, 230));
        Screen.draw_line(topPt.x - 42, topPt.y, topPt.x + 42, topPt.y, color);
        drawText(topPt.x - 38, topPt.y - 2, label, 9, TEXT_BRIGHT);
    }
}

// 2. Multi-Beam 360° LiDAR Point Cloud with Distance-Intensity Color Coding
function renderLiDARPointCloud(bot) {
    var lidarY = 9.2;
    var sweepA = simTime * 6.5;

    // Ground Range Rings with distance labels
    var rings = [ 12.0, 24.0, 36.0, 48.0 ];
    for (var r = 0; r < rings.length; r++) {
        var rad = rings[r];
        var lastPt = null;
        for (var i = 0; i <= 20; i++) {
            var a = (i / 20) * Math.PI * 2;
            var pt = project3D(bot.x + Math.cos(a) * rad, 0.15, bot.z + Math.sin(a) * rad);
            if (lastPt && pt) {
                Screen.draw_line(lastPt.x, lastPt.y, pt.x, pt.y, rgba(0, 210, 240, 40));
            }
            lastPt = pt;
        }
    }

    // 32 Rotating Laser Beam Returns
    for (var i = 0; i < 32; i++) {
        var angle = sweepA + (i / 32) * Math.PI * 2;
        var dist = 36.0;
        if (Math.abs(Math.sin(angle * 2.0)) > 0.55) dist = 18.0;
        if (Math.abs(Math.cos(angle * 3.0)) > 0.8) dist = 11.0;

        var hitX = bot.x + Math.sin(angle) * dist;
        var hitZ = bot.z + Math.cos(angle) * dist;
        var hitY = (Math.sin(angle * 4.0) > 0.3) ? 5.5 : 0.4;

        // Color coding by return distance (NVIDIA DRIVE Sim intensity gradient)
        var beamColor = (dist < 15.0) ? rgba(235, 60, 60, 70) : ((dist < 25.0) ? rgba(118, 185, 0, 70) : rgba(0, 220, 245, 60));
        var dotColor  = (dist < 15.0) ? OMNI_RED : ((dist < 25.0) ? NV_GREEN : OMNI_CYAN);

        drawLine3D(bot.x, lidarY, bot.z, hitX, hitY, hitZ, beamColor);

        var pPt = project3D(hitX, hitY, hitZ);
        if (pPt) {
            Screen.draw_rectangle(pPt.x - 1, pPt.y - 1, 3, 3, dotColor);
        }
    }
}

// 3. Autonomous Predictive Trajectory Planning Ribbon
function renderTrajectoryRibbon(bot) {
    var steps = 10;
    var prevL = null, prevR = null, prevC = null;

    for (var s = 0; s <= steps; s++) {
        var t = s / steps;
        var wx = bot.x + (bot.tx - bot.x) * t + Math.sin(simTime * 2.0 + t * 4.0) * 1.6;
        var wz = bot.z + (bot.tz - bot.z) * t;

        var pL = project3D(wx - 2.2, 0.25, wz);
        var pR = project3D(wx + 2.2, 0.25, wz);
        var pC = project3D(wx, 0.3, wz);

        if (prevL && prevR && pL && pR) {
            Screen.draw_line(prevL.x, prevL.y, pL.x, pL.y, NV_GREEN);
            Screen.draw_line(prevR.x, prevR.y, pR.x, pR.y, NV_GREEN);
            Screen.draw_line(pL.x, pL.y, pR.x, pR.y, rgba(118, 185, 0, 85));
            if (prevC && pC) Screen.draw_line(prevC.x, prevC.y, pC.x, pC.y, TEXT_BRIGHT);
        }

        // Waypoint timestamp beads
        if (s === 4 || s === 7 || s === 10) {
            if (pC) {
                Screen.draw_fill_circle(3, pC.x, pC.y, OMNI_ORANGE);
                drawText(pC.x + 5, pC.y - 3, "t+" + (t * 2.5).toFixed(1) + "s", 9, TEXT_BRIGHT);
            }
        }

        prevL = pL; prevR = pR; prevC = pC;
    }
}

// 4. Multi-Camera Sensor Viewing Frustum
function renderCameraFrustum(bot) {
    var cosR = Math.cos(bot.rotY), sinR = Math.sin(bot.rotY);
    var camPos = { x: bot.x + sinR * 7.5, y: 5.8, z: bot.z + cosR * 7.5 };
    var pApex = project3D(camPos.x, camPos.y, camPos.z);
    if (!pApex) return;

    var fDist = 24.0;
    var fW = 16.0, fH = 9.0;

    var c1 = project3D(camPos.x + sinR * fDist - cosR * (fW/2), camPos.y + fH/2, camPos.z + cosR * fDist + sinR * (fW/2));
    var c2 = project3D(camPos.x + sinR * fDist + cosR * (fW/2), camPos.y + fH/2, camPos.z + cosR * fDist - sinR * (fW/2));
    var c3 = project3D(camPos.x + sinR * fDist + cosR * (fW/2), camPos.y - fH/2, camPos.z + cosR * fDist - sinR * (fW/2));
    var c4 = project3D(camPos.x + sinR * fDist - cosR * (fW/2), camPos.y - fH/2, camPos.z + cosR * fDist + sinR * (fW/2));

    var fColor = rgba(118, 185, 0, 90);
    if (c1 && c2 && c3 && c4) {
        Screen.draw_line(pApex.x, pApex.y, c1.x, c1.y, fColor);
        Screen.draw_line(pApex.x, pApex.y, c2.x, c2.y, fColor);
        Screen.draw_line(pApex.x, pApex.y, c3.x, c3.y, fColor);
        Screen.draw_line(pApex.x, pApex.y, c4.x, c4.y, fColor);

        Screen.draw_line(c1.x, c1.y, c2.x, c2.y, NV_GREEN);
        Screen.draw_line(c2.x, c2.y, c3.x, c3.y, NV_GREEN);
        Screen.draw_line(c3.x, c3.y, c4.x, c4.y, NV_GREEN);
        Screen.draw_line(c4.x, c4.y, c1.x, c1.y, NV_GREEN);
    }
}

// 5. On-Board Camera Picture-In-Picture (PIP) View (NVIDIA DRIVE Sim Signature)
function renderSensorPIP(bot) {
    if (!showSensorPIP) return;

    var pipX = VP_X + VP_W - 146;
    var pipY = VP_Y + 12;
    var pipW = 140;
    var pipH = 86;

    // Monitor frame
    Screen.draw_rectangle(pipX, pipY, pipW, pipH, rgba(14, 16, 18, 240));
    Screen.draw_line(pipX, pipY, pipX + pipW, pipY, OMNI_BORDER_HI);
    Screen.draw_line(pipX, pipY + pipH, pipX + pipW, pipY + pipH, OMNI_BORDER_HI);
    Screen.draw_line(pipX, pipY, pipX, pipY + pipH, OMNI_BORDER_HI);
    Screen.draw_line(pipX + pipW, pipY, pipX + pipW, pipY + pipH, OMNI_BORDER_HI);

    // Title bar
    Screen.draw_rectangle(pipX, pipY, pipW, 13, rgba(20, 30, 22, 255));
    Screen.draw_fill_circle(3, pipX + 8, pipY + 6, NV_GREEN);
    drawText(pipX + 16, pipY + 10, "CAM 0: DRIVE-NET", 9, TEXT_BRIGHT);

    // Simulated camera sensor viewport (sky & floor perspective)
    var viewY = pipY + 14;
    var viewH = pipH - 14;
    Screen.draw_rectangle(pipX + 2, viewY, pipW - 4, viewH * 0.45, rgba(28, 32, 38, 255)); // Wall
    Screen.draw_rectangle(pipX + 2, viewY + viewH * 0.45, pipW - 4, viewH * 0.55, rgba(42, 45, 50, 255)); // Floor

    // Aisle perspective lines
    var vpMidX = pipX + (pipW >> 1);
    var vpHozY = viewY + Math.floor(viewH * 0.45);
    Screen.draw_line(vpMidX - 10, vpHozY, pipX + 15, pipY + pipH - 2, rgba(245, 210, 40, 180));
    Screen.draw_line(vpMidX + 10, vpHozY, pipX + pipW - 15, pipY + pipH - 2, rgba(245, 210, 40, 180));

    // Simulated Oncoming Obstacle Box with AI target crosshair
    var objX = vpMidX + Math.sin(simTime * 1.5) * 16;
    var objY = vpHozY + 8;
    Screen.draw_rectangle(objX - 12, objY - 10, 24, 20, rgba(60, 140, 240, 160));
    Screen.draw_line(objX - 6, objY, objX + 6, objY, NV_GREEN);
    Screen.draw_line(objX, objY - 6, objX, objY + 6, NV_GREEN);
    drawText(objX - 10, objY + 16, "AMR_02 [98%]", 8, NV_GREEN);

    drawText(pipX + 6, pipY + pipH - 4, "30 FPS | RAW RGB + SEG", 8, TEXT_DIM);
}

// -----------------------------------------------------------------------------
// DETAILED 3D OBJECT RENDERING (CARTER AMR, UV-C, CRASH CART, MACHINERY)
// -----------------------------------------------------------------------------
function renderCarterAMR(bot, isSelected) {
    var selCol = isSelected ? OMNI_ORANGE : 0;
    var chassisCol = isSelected ? rgba(52, 58, 66, 255) : rgba(38, 42, 48, 255);

    // 1. Lower Chassis Skid Base
    drawSolidBox3D(bot.x, 2.5, bot.z, 11.5, 3.5, 15.0, bot.rotY, chassisCol, selCol);

    // 2. Yellow/Black Hazard Side Skirt Strips
    drawSolidBox3D(bot.x, 1.2, bot.z, 11.8, 1.0, 14.0, bot.rotY, OMNI_YELLOW, 0);

    // 3. Side Drive Wheels (Left & Right)
    var cosR = Math.cos(bot.rotY), sinR = Math.sin(bot.rotY);
    var wL_X = bot.x - cosR * 6.2, wL_Z = bot.z + sinR * 6.2;
    var wR_X = bot.x + cosR * 6.2, wR_Z = bot.z - sinR * 6.2;
    drawSolidBox3D(wL_X, 2.2, wL_Z, 1.6, 4.2, 4.2, bot.rotY, rgba(22, 22, 22, 255), 0);
    drawSolidBox3D(wR_X, 2.2, wR_Z, 1.6, 4.2, 4.2, bot.rotY, rgba(22, 22, 22, 255), 0);

    // 4. Payload Top Deck Plate
    drawSolidBox3D(bot.x, 5.2, bot.z, 9.5, 1.8, 12.5, bot.rotY, bot.color, selCol);

    // 5. Front Stereo Depth Camera Sensor Bar
    var camX_pos = bot.x + sinR * 7.4, camZ_pos = bot.z + cosR * 7.4;
    drawSolidBox3D(camX_pos, 5.0, camZ_pos, 7.0, 1.5, 1.8, bot.rotY, rgba(20, 20, 20, 255), 0);

    // 6. Top Cylindrical LiDAR Pedestal & Rotating Puck Scanner
    drawSolidBox3D(bot.x, 7.5, bot.z, 4.0, 2.5, 4.0, bot.rotY, rgba(30, 32, 35, 255), selCol);
    drawSolidBox3D(bot.x, 9.4, bot.z, 3.2, 1.8, 3.2, simTime * 4.5, rgba(16, 16, 16, 255), selCol);

    // Pulsing Status LED Ring
    var ringPt = project3D(bot.x, 6.4, bot.z);
    if (ringPt) Screen.draw_fill_circle(3, ringPt.x, ringPt.y, NV_GREEN);
}

function renderUVCTower(bot, isSelected) {
    var selCol = isSelected ? OMNI_ORANGE : 0;
    var chassisCol = isSelected ? rgba(52, 58, 66, 255) : rgba(38, 42, 48, 255);

    drawSolidBox3D(bot.x, 2.8, bot.z, 9.5, 4.5, 9.5, bot.rotY, chassisCol, selCol);
    drawSolidBox3D(bot.x, 11.5, bot.z, 4.2, 13.0, 4.2, bot.rotY, OMNI_VIOLET, selCol);
    drawSolidBox3D(bot.x, 18.5, bot.z, 7.5, 2.2, 7.5, bot.rotY, rgba(42, 44, 48, 255), selCol);

    // Violet sterilizing glow core
    var corePt = project3D(bot.x, 11.5, bot.z);
    if (corePt) Screen.draw_fill_circle(4, corePt.x, corePt.y, rgba(185, 95, 255, 200));
}

function renderCrashCart(bot, isSelected) {
    var selCol = isSelected ? OMNI_ORANGE : 0;
    drawSolidBox3D(bot.x, 4.8, bot.z, 8.5, 8.5, 12.0, bot.rotY, OMNI_RED, selCol);
    // Medical tray top & monitor
    drawSolidBox3D(bot.x, 10.2, bot.z, 6.5, 2.8, 9.0, bot.rotY, rgba(235, 235, 235, 255), selCol);
    drawSolidBox3D(bot.x - 2.0, 13.0, bot.z, 1.5, 3.5, 4.5, bot.rotY, rgba(30, 30, 30, 255), selCol);
}

// -----------------------------------------------------------------------------
// MAIN 3D PERSPECTIVE VIEWPORT RENDERING
// -----------------------------------------------------------------------------
function renderMain3DScene() {
    // 1. Perspective CAD Floor Grid & Concrete Aisle Markings
    var gridColor    = rgba(46, 48, 52, 255);
    var subGridColor = rgba(30, 32, 35, 255);
    var axisColorX   = rgba(215, 55, 55, 220);  // Red X-axis
    var axisColorZ   = rgba(55, 135, 225, 220); // Blue Z-axis

    var extent = 90.0;
    var step   = 15.0;

    for (var c = -extent; c <= extent; c += step) {
        var colZ = (c === 0) ? axisColorZ : ((Math.abs(c) % 30 === 0) ? gridColor : subGridColor);
        drawLine3D(c, 0, -extent, c, 0, extent, colZ);

        var colX = (c === 0) ? axisColorX : ((Math.abs(c) % 30 === 0) ? gridColor : subGridColor);
        drawLine3D(-extent, 0, c, extent, 0, c, colX);
    }

    // Floor Detail: High-Contrast Hazard Caution Corridors (#F5D228)
    var laneL = -18.0, laneR = 18.0;
    for (var lz = -75.0; lz <= 75.0; lz += 10.0) {
        drawLine3D(laneL, 0.1, lz, laneL, 0.1, lz + 6.0, OMNI_YELLOW);
        drawLine3D(laneR, 0.1, lz, laneR, 0.1, lz + 6.0, OMNI_YELLOW);
    }

    // Pedestrian Crosswalk Hatching
    for (var px = -16.0; px <= 16.0; px += 4.0) {
        drawLine3D(px, 0.1, -2.5, px, 0.1, 2.5, rgba(230, 230, 230, 180));
    }

    // Docking Bay Stalls & Charging Stations
    drawLine3D(-10.0, 0.1, -12.0, 10.0, 0.1, -12.0, rgba(230, 230, 230, 160));
    drawLine3D(-10.0, 0.1, -24.0, 10.0, 0.1, -24.0, rgba(230, 230, 230, 160));
    drawLine3D(-10.0, 0.1, -12.0, -10.0, 0.1, -24.0, rgba(230, 230, 230, 160));
    drawLine3D(10.0, 0.1, -12.0, 10.0, 0.1, -24.0, rgba(230, 230, 230, 160));

    var dockLabelPt = project3D(0, 0.2, -18.0);
    if (dockLabelPt) drawText(dockLabelPt.x - 22, dockLabelPt.y - 4, "BAY 01 [DOCK]", 9, OMNI_CYAN);

    // 2. Ground Contact Shadows
    drawGroundShadow(sceneProps[0].x, sceneProps[0].z, 14.0, 8.0);
    drawGroundShadow(-60.0, 0.0, 9.0, 48.0);
    drawGroundShadow(60.0, 0.0, 9.0, 48.0);

    for (var bi = 0; bi < robots.length; bi++) {
        drawGroundShadow(robots[bi].x, robots[bi].z, 7.5, 9.5);
    }

    // 3. High-Bay Storage Racks with Pallets & Cargo Crates
    var rackCols = [ -60.0, 60.0 ];
    for (var r = 0; r < rackCols.length; r++) {
        var rx = rackCols[r];
        var isRackSelected = (selectedPrimIdx === 6 && r === 0);
        var rackBeamCol = isRackSelected ? OMNI_ORANGE : rgba(52, 98, 150, 255);
        var shelfBeams  = rgba(230, 120, 25, 255); // Omniverse Orange load beams

        // 6 Vertical Structural Columns
        var uprights = [
            { x: rx - 7, z: -45 }, { x: rx + 7, z: -45 },
            { x: rx - 7, z:   0 }, { x: rx + 7, z:   0 },
            { x: rx - 7, z:  45 }, { x: rx + 7, z:  45 }
        ];

        for (var u = 0; u < uprights.length; u++) {
            drawLine3D(uprights[u].x, 0, uprights[u].z, uprights[u].x, 34, uprights[u].z, rackBeamCol);
        }

        // Diagonal Cross-Bracing Wires ('X' bracing between columns)
        drawLine3D(rx - 7, 0, -45, rx - 7, 34, 0, rgba(80, 120, 165, 140));
        drawLine3D(rx - 7, 34, -45, rx - 7, 0, 0, rgba(80, 120, 165, 140));
        drawLine3D(rx - 7, 0, 0, rx - 7, 34, 45, rgba(80, 120, 165, 140));
        drawLine3D(rx - 7, 34, 0, rx - 7, 0, 45, rgba(80, 120, 165, 140));

        // Horizontal Levels & Solid Shaded Cargo Crates
        for (var lvl = 11; lvl <= 33; lvl += 11) {
            drawLine3D(rx - 7, lvl, -45, rx + 7, lvl, -45, shelfBeams);
            drawLine3D(rx - 7, lvl,   0, rx + 7, lvl,   0, shelfBeams);
            drawLine3D(rx - 7, lvl,  45, rx + 7, lvl,  45, shelfBeams);

            drawLine3D(rx - 7, lvl, -45, rx - 7, lvl, 45, shelfBeams);
            drawLine3D(rx + 7, lvl, -45, rx + 7, lvl, 45, shelfBeams);

            // Solid Pallet Crates with Straps
            drawSolidBox3D(rx, lvl + 4, -22, 11, 7, 16, 0, rgba(165, 125, 78, 255), isRackSelected ? OMNI_ORANGE : 0);
            drawSolidBox3D(rx, lvl + 4,  22, 11, 7, 16, 0, rgba(135, 148, 110, 255), isRackSelected ? OMNI_ORANGE : 0);
        }

        // Safety Hazard Bollards
        drawSolidBox3D(rx + (r === 0 ? 11 : -11), 4, -50, 3, 8, 3, 0, OMNI_YELLOW, 0);
        drawSolidBox3D(rx + (r === 0 ? 11 : -11), 4,  50, 3, 8, 3, 0, OMNI_YELLOW, 0);
    }

    // 4. Industrial Compressor Pump Unit (Solid Shaded)
    var pump = sceneProps[0];
    var isPumpSelected = (selectedPrimIdx === 5);
    var pumpSel = isPumpSelected ? OMNI_ORANGE : 0;
    drawSolidBox3D(pump.x, 7.0, pump.z, 22, 11, 11, 0, rgba(105, 140, 98, 255), pumpSel);
    drawSolidBox3D(pump.x - 4, 15.0, pump.z, 8, 6, 8, 0, rgba(72, 82, 78, 255), pumpSel);
    drawSolidBox3D(pump.x + 5, 16.0, pump.z, 6, 8, 6, 0, rgba(62, 72, 68, 255), pumpSel);

    if (showNeuralPerception) {
        drawAIPerceptionBox(pump.x, 9.0, pump.z, 24, 18, 14, "PUMP-01 [99.1%]", rgba(110, 160, 100, 220));
    }

    // 5. Predefined 3D Autonomous Mobile Robots (AMRs)
    robots.forEach(function(bot, idx) {
        var isBotSelected = (selectedPrimIdx === idx);

        if (bot.modelId === "MDL-CARTER") {
            renderCarterAMR(bot, isBotSelected);
        } else if (bot.modelId === "MDL-UVC") {
            renderUVCTower(bot, isBotSelected);
        } else if (bot.modelId === "MDL-CRASH") {
            renderCrashCart(bot, isBotSelected);
        }

        // Active AMR Neural Perception Overlays (NVIDIA DRIVE Sim)
        if (showNeuralPerception) {
            drawAIPerceptionBox(bot.x, 6.0, bot.z, 12, 10, 16, bot.id + " [" + bot.aiConfidence + "]", bot.color);

            if (isBotSelected || idx === 0) {
                renderLiDARPointCloud(bot);
                renderCameraFrustum(bot);
                renderTrajectoryRibbon(bot);
            }
        }

        // 3D Interactive Transform Gizmo on Selected Robot
        if (isBotSelected && showGizmo) {
            renderTransformGizmo(bot.x, 10.5, bot.z);
        }
    });

    // 6. Floating Atmosphere Dust Particles
    for (var pi = 0; pi < particles.length; pi++) {
        var p = particles[pi];
        var ppt = project3D(p.x, p.y, p.z);
        if (ppt) {
            Screen.draw_rectangle(ppt.x, ppt.y, 2, 2, rgba(200, 215, 235, p.bright));
        }
    }

    // 7. Mini 3D Axis Orientation Tripod in Bottom-Left Corner
    var tripodCX = VP_X + 26;
    var tripodCY = VP_Y + VP_H - 26;
    var tLen = 14.0;
    var cosY = Math.cos(orbitYaw), sinY = Math.sin(orbitYaw);
    var cosP = Math.cos(orbitPitch), sinP = Math.sin(orbitPitch);

    var tx_x = -cosY * tLen, tx_y = (-sinY * sinP) * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX + tx_x, tripodCY - tx_y, rgba(240, 60, 60, 255));
    drawText(tripodCX + tx_x + 2, tripodCY - tx_y - 4, "X", 10, rgba(240, 60, 60, 255));

    var ty_y = cosP * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX, tripodCY - ty_y, NV_GREEN);
    drawText(tripodCX + 2, tripodCY - ty_y - 4, "Y", 10, NV_GREEN);

    var tz_x = sinY * tLen, tz_y = (cosY * sinP) * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX + tz_x, tripodCY - tz_y, rgba(50, 140, 255, 255));
    drawText(tripodCX + tz_x + 2, tripodCY - tz_y - 4, "Z", 10, rgba(50, 140, 255, 255));

    drawText(tripodCX - 12, tripodCY + 14, "cm [grid]", 9, TEXT_DIM);

    // 8. On-Board Sensor Picture-In-Picture (PIP) View
    if (showNeuralPerception) {
        renderSensorPIP(robots[selectedPrimIdx % robots.length]);
    }

    // 9. Viewport Camera HUD Overlay
    var camDeg = ((orbitYaw * 180 / Math.PI) % 360);
    if (camDeg < 0) camDeg += 360;
    var pitchDeg = (orbitPitch * 180 / Math.PI).toFixed(0);
    drawText(VP_X + 8, VP_Y + 12, "Cam: Orbit " + camDeg.toFixed(0) + "° | Pitch " + pitchDeg + "° | Pos (" + camX.toFixed(0) + ", " + camY.toFixed(0) + ", " + camZ.toFixed(0) + ")", 9, TEXT_MUTED);
    drawText(VP_X + 8, VP_Y + 23, "Controls: [R-Stick/IJKL] Orbit | [L-Stick/WASD] Pan Target | [Touch] Orbit", 9, rgba(118, 185, 0, 200));
}

// -----------------------------------------------------------------------------
// DEDICATED PREDEFINED 3D MODEL PREVIEWER (SOLID SHADED TURNTABLE)
// -----------------------------------------------------------------------------
function projectTurntable(lx, ly, lz, angle) {
    var cosA = Math.cos(angle), sinA = Math.sin(angle);
    var rx = lx * cosA - lz * sinA;
    var rz = lx * sinA + lz * cosA;
    var cosP = 0.9394, sinP = 0.3429;
    var ry = ly * cosP - rz * sinP;
    var depth = ly * sinP + rz * cosP + PREV_DIST;
    if (depth <= 2.0) return null;
    return { x: PREV_CX + (rx / depth) * PREV_FOCAL, y: PREV_CY - (ry / depth) * PREV_FOCAL, depth: depth };
}

function drawSolidPreviewBox(cx, cy, cz, sx, sy, sz, angle, baseColor) {
    var hx = sx * 0.5, hy = sy * 0.5, hz = sz * 0.5;
    var bR = baseColor & 255, bG = (baseColor >>> 8) & 255, bB = (baseColor >>> 16) & 255;
    var cosA = Math.cos(angle), sinA = Math.sin(angle);

    var v0 = projectTurntable(cx-hx, cy-hy, cz-hz, angle);
    var v1 = projectTurntable(cx+hx, cy-hy, cz-hz, angle);
    var v2 = projectTurntable(cx+hx, cy-hy, cz+hz, angle);
    var v3 = projectTurntable(cx-hx, cy-hy, cz+hz, angle);
    var v4 = projectTurntable(cx-hx, cy+hy, cz-hz, angle);
    var v5 = projectTurntable(cx+hx, cy+hy, cz-hz, angle);
    var v6 = projectTurntable(cx+hx, cy+hy, cz+hz, angle);
    var v7 = projectTurntable(cx-hx, cy+hy, cz+hz, angle);

    var tcY = 0.3429, tcZ = 0.9394;
    var fc = 0;
    var fv = [];

    if (v4 && v5 && v6 && v7) {
        var br = 0.35 + 0.85 * 0.65;
        var dp = (v4.depth + v5.depth + v6.depth + v7.depth) * 0.25;
        fv[fc++] = {a:v7,b:v6,c:v5,d:v4,br:br,dp:dp};
    }
    if (cosA * tcZ > 0 && v3 && v2 && v6 && v7) {
        var br = 0.25 + Math.max(0, sinA * LIGHT_X + cosA * LIGHT_Z) * 0.65;
        var dp = (v3.depth + v2.depth + v6.depth + v7.depth) * 0.25;
        fv[fc++] = {a:v3,b:v2,c:v6,d:v7,br:br,dp:dp};
    }
    if (-cosA * tcZ > 0 && v0 && v1 && v5 && v4) {
        var br = 0.25 + Math.max(0, -sinA * LIGHT_X - cosA * LIGHT_Z) * 0.65;
        var dp = (v0.depth + v1.depth + v5.depth + v4.depth) * 0.25;
        fv[fc++] = {a:v4,b:v5,c:v1,d:v0,br:br,dp:dp};
    }
    if (-sinA * tcZ > 0 && v1 && v2 && v6 && v5) {
        var br = 0.25 + Math.max(0, cosA * LIGHT_X - sinA * LIGHT_Z) * 0.65;
        var dp = (v1.depth + v2.depth + v6.depth + v5.depth) * 0.25;
        fv[fc++] = {a:v5,b:v6,c:v2,d:v1,br:br,dp:dp};
    }
    if (sinA * tcZ > 0 && v0 && v3 && v7 && v4) {
        var br = 0.25 + Math.max(0, -cosA * LIGHT_X + sinA * LIGHT_Z) * 0.65;
        var dp = (v0.depth + v3.depth + v7.depth + v4.depth) * 0.25;
        fv[fc++] = {a:v0,b:v3,c:v7,d:v4,br:br,dp:dp};
    }

    for (var i = 1; i < fc; i++) {
        var key = fv[i]; var j = i - 1;
        while (j >= 0 && fv[j].dp < key.dp) { fv[j+1] = fv[j]; j--; }
        fv[j+1] = key;
    }

    var pcX0 = 672, pcY0 = 172, pcX1 = 952, pcY1 = 298;

    for (var i = 0; i < fc; i++) {
        var f = fv[i];
        var fr = Math.min(255, (bR * f.br) | 0);
        var fg = Math.min(255, (bG * f.br) | 0);
        var fb = Math.min(255, (bB * f.br) | 0);
        fillQuad(f.a.x, f.a.y, f.b.x, f.b.y, f.c.x, f.c.y, f.d.x, f.d.y,
                 rgba(fr, fg, fb, 255), pcX0, pcY0, pcX1, pcY1);
        var eCol = rgba(Math.min(255,fr+30), Math.min(255,fg+30), Math.min(255,fb+30), 255);
        Screen.draw_line(f.a.x, f.a.y, f.b.x, f.b.y, eCol);
        Screen.draw_line(f.b.x, f.b.y, f.c.x, f.c.y, eCol);
        Screen.draw_line(f.c.x, f.c.y, f.d.x, f.d.y, eCol);
        Screen.draw_line(f.d.x, f.d.y, f.a.x, f.a.y, eCol);
    }
}

function renderSideModelPreview(model) {
    // 3D Turntable ring at base
    var numPoints = 16;
    var rad = 14.0;
    var prevPt = null;
    for (var i = 0; i <= numPoints; i++) {
        var a = (i / numPoints) * Math.PI * 2;
        var pt = projectTurntable(Math.cos(a) * rad, -10.0, Math.sin(a) * rad, previewTurntableAngle);
        if (prevPt && pt) Screen.draw_line(prevPt.x, prevPt.y, pt.x, pt.y, rgba(70, 72, 76, 255));
        prevPt = pt;
    }

    var angle = previewTurntableAngle;
    var mdlColor = model.color;

    if (model.id === "MDL-CARTER") {
        drawSolidPreviewBox(0, -6, 0, 16, 6, 22, angle, mdlColor);
        drawSolidPreviewBox(0, -1, 0, 13, 4, 17, angle, rgba(220, 220, 220, 255));
        drawSolidPreviewBox(0, 4, 0, 6, 4, 6, angle, rgba(30, 30, 30, 255));
    } else if (model.id === "MDL-PUMP") {
        drawSolidPreviewBox(0, -4, 0, 24, 11, 11, angle, mdlColor);
        drawSolidPreviewBox(-4, 5, 0, 8, 7, 8, angle, rgba(70, 80, 75, 255));
        drawSolidPreviewBox(5, 6, 0, 6, 9, 6, angle, rgba(60, 70, 65, 255));
    } else if (model.id === "MDL-UVC") {
        drawSolidPreviewBox(0, -8, 0, 12, 5, 12, angle, rgba(50, 50, 50, 255));
        drawSolidPreviewBox(0, 2, 0, 5, 16, 5, angle, mdlColor);
        drawSolidPreviewBox(0, 11, 0, 9, 3, 9, angle, rgba(40, 40, 40, 255));
    } else if (model.id === "MDL-CRASH") {
        drawSolidPreviewBox(0, -3, 0, 12, 12, 16, angle, mdlColor);
        drawSolidPreviewBox(0, 5, 0, 9, 4, 12, angle, rgba(240, 240, 240, 255));
    } else if (model.id === "MDL-RACK") {
        drawSolidPreviewBox(0, 0, 0, 14, 24, 28, angle, mdlColor);
        drawSolidPreviewBox(0, -4, 0, 10, 4, 18, angle, rgba(160, 120, 70, 255));
        drawSolidPreviewBox(0, 4, 0, 10, 4, 18, angle, rgba(130, 145, 95, 255));
    } else if (model.id === "MDL-CRATE") {
        drawSolidPreviewBox(0, -8, 0, 18, 3, 18, angle, rgba(140, 100, 60, 255));
        drawSolidPreviewBox(0, 0, 0, 14, 13, 14, angle, mdlColor);
    } else if (model.id === "MDL-BOLLARD") {
        drawSolidPreviewBox(0, -8, 0, 8, 2, 8, angle, rgba(50, 50, 50, 255));
        drawSolidPreviewBox(0, 1, 0, 5, 16, 5, angle, mdlColor);
    }
}

// -----------------------------------------------------------------------------
// INTERACTIVE NEURAL NETWORK ARCHITECTURE HUD (DRIVENET DEEP LEARNING)
// -----------------------------------------------------------------------------
function renderNeuralNetworkHUD(rPaneX, rPaneW) {
    var netY = 82;
    Screen.draw_rectangle(rPaneX + 6, netY, rPaneW - 12, 218, rgba(18, 19, 21, 255));
    Screen.draw_line(rPaneX + 6, netY, rPaneX + rPaneW - 6, netY, OMNI_BORDER);
    Screen.draw_line(rPaneX + 6, netY + 218, rPaneX + rPaneW - 6, netY + 218, OMNI_BORDER);
    Screen.draw_line(rPaneX + 6, netY, rPaneX + 6, netY + 218, OMNI_BORDER);
    Screen.draw_line(rPaneX + rPaneW - 6, netY, rPaneX + rPaneW - 6, netY + 218, OMNI_BORDER);

    drawText(rPaneX + 12, netY + 14, "NVIDIA DRIVE NET (PERCEPTION & ACTION)", 10, NV_GREEN);
    drawText(rPaneX + 225, netY + 14, "TensorRT INT8", 9, TEXT_DIM);

    // 4 Neural Layers
    var layers = [
        { name: "Input",  x: rPaneX + 24, count: 4, labels: ["LIDAR", "CAM", "IMU", "ODO"] },
        { name: "Conv",   x: rPaneX + 88, count: 5, labels: ["F1", "F2", "F3", "F4", "F5"] },
        { name: "Policy", x: rPaneX + 160, count: 5, labels: ["A1", "A2", "A3", "A4", "A5"] },
        { name: "Action", x: rPaneX + 232, count: 3, labels: ["v_spd", "w_steer", "P_conf"] }
    ];

    // Synaptic Weight Connections & Pulsing Signals
    for (var l = 0; l < layers.length - 1; l++) {
        var lA = layers[l];
        var lB = layers[l + 1];
        for (var i = 0; i < lA.count; i++) {
            var yA = netY + 45 + i * 30;
            for (var j = 0; j < lB.count; j++) {
                var yB = netY + 36 + j * 28;
                Screen.draw_line(lA.x, yA, lB.x, yB, rgba(46, 54, 48, 255));

                var pulseT = ((simTime * 2.5 + (i * 3 + j) * 0.2) % 1.0);
                var px = lA.x + (lB.x - lA.x) * pulseT;
                var py = yA + (yB - yA) * pulseT;
                Screen.draw_rectangle(px - 1, py - 1, 2, 2, NV_GREEN);
            }
        }
    }

    // Layer Nodes with dynamic activation sizes
    layers.forEach(function(l, lIdx) {
        drawText(l.x - 10, netY + 28, l.name, 9, TEXT_MUTED);
        for (var n = 0; n < l.count; n++) {
            var ny = (l.count === 5 ? netY + 36 + n * 28 : (l.count === 4 ? netY + 45 + n * 30 : netY + 60 + n * 36));
            var actPulse = Math.sin(simTime * 4.0 + n * 1.2 + lIdx * 2.0);
            var nRadius = (actPulse > 0.3) ? 5 : 4;
            var nodeCol = (lIdx === 0) ? OMNI_CYAN : (lIdx === 3 ? OMNI_ORANGE : NV_GREEN);

            Screen.draw_rectangle(l.x - nRadius, ny - nRadius, nRadius * 2, nRadius * 2, nodeCol);
            drawText(l.x + 8, ny + 3, l.labels[n], 9, TEXT_REGULAR);
        }
    });

    // Deep Learning Diagnostics Bar
    var diagY = 304;
    Screen.draw_rectangle(rPaneX + 6, diagY, rPaneW - 12, 80, OMNI_PANEL_ALT);
    drawText(rPaneX + 12, diagY + 14, "Model: PhysX-DriveNet-v4.2 (8.4M Params)", 9, TEXT_BRIGHT);
    drawText(rPaneX + 12, diagY + 28, "Inference Latency: 3.2ms | Jitter: 0.1ms", 9, NV_GREEN);
    drawText(rPaneX + 12, diagY + 42, "Perception: LiDAR (360), Depth Cam, IMU 6-Axis", 9, TEXT_MUTED);
    drawText(rPaneX + 12, diagY + 56, "Policy Action: v=1.15 m/s, w=+14.2 deg, P=99.4%", 9, OMNI_ORANGE);

    Screen.draw_rectangle(rPaneX + 10, diagY + 62, rPaneW - 20, 14, rgba(20, 45, 75, 255));
    drawText(rPaneX + 14, diagY + 73, "[TRIANGLE] Toggle Overlays  [SELECT] Tab", 9, TEXT_BRIGHT);
}

// -----------------------------------------------------------------------------
// COMPLETE OMNIVERSE USD COMPOSER UI RENDERING
// -----------------------------------------------------------------------------
function render() {
    Screen.start_drawing();
    Screen.clear(22, 23, 24, 255);

    // 1. TOP WINDOW TITLE BAR (Y: 0 to 22)
    Screen.draw_rectangle(0, 0, 960, 22, OMNI_DARKEST);
    Screen.draw_line(0, 22, 960, 22, OMNI_BORDER);

    // NVIDIA Omniverse Signature Green Hexagon Logo
    Screen.draw_rectangle(8, 5, 12, 12, NV_GREEN);
    Screen.draw_rectangle(11, 8, 6, 6, OMNI_DARKEST);

    drawText(26, 16, "USD Composer 2023.2.5 | omniverse://localhost/IsaacWarehouse/IsaacWarehouse.usd (read-only)*", 11, TEXT_MUTED);

    var badgeX = 760;
    Screen.draw_rectangle(badgeX, 4, 46, 14, rgba(30, 65, 15, 255));
    Screen.draw_rectangle(badgeX + 5, 8, 5, 5, NV_GREEN);
    drawText(badgeX + 15, 15, "LIVE", 10, TEXT_BRIGHT);

    Screen.draw_rectangle(badgeX + 52, 4, 76, 14, rgba(65, 20, 20, 255));
    drawText(badgeX + 58, 15, "CACHE: OFF", 10, OMNI_RED);

    drawText(904, 15, "_   [ ]   X", 11, TEXT_MUTED);

    // 2. MAIN MENU BAR (Y: 22 to 40)
    Screen.draw_rectangle(0, 22, 960, 18, OMNI_PANEL);
    Screen.draw_line(0, 40, 960, 40, OMNI_BORDER);

    var menus = [ "File", "Edit", "Create", "Component", "Window", "Render", "Tools", "Layout", "Help" ];
    var menuX = 12;
    menus.forEach(function(m) {
        drawText(menuX, 35, m, 11, TEXT_REGULAR);
        menuX += (m.length > 6 ? 58 : 42);
    });

    // 3. VIEWPORT SUB-TOOLBAR (Y: 40 to 58)
    Screen.draw_rectangle(0, 40, 960, 18, OMNI_PANEL_ALT);
    Screen.draw_line(0, 58, 960, 58, OMNI_BORDER);

    // RTX Real-Time Pill
    Screen.draw_rectangle(38, 43, 110, 13, rgba(18, 18, 18, 255));
    Screen.draw_rectangle(43, 47, 5, 5, NV_GREEN);
    drawText(53, 53, "RTX - Real-Time", 10, TEXT_BRIGHT);

    // AI Neural Net Perception Badge
    Screen.draw_rectangle(154, 43, 105, 13, showNeuralPerception ? rgba(25, 50, 15, 255) : rgba(20, 20, 20, 255));
    Screen.draw_rectangle(159, 47, 5, 5, showNeuralPerception ? NV_GREEN : TEXT_MUTED);
    drawText(168, 53, "DRIVE Net: " + (showNeuralPerception ? "ON" : "OFF"), 10, showNeuralPerception ? NV_GREEN : TEXT_MUTED);

    // Camera & Lights Dropdowns
    Screen.draw_rectangle(265, 43, 75, 13, rgba(18, 18, 18, 255));
    drawText(272, 53, "Camera  v", 10, TEXT_REGULAR);

    Screen.draw_rectangle(346, 43, 90, 13, rgba(18, 18, 18, 255));
    drawText(353, 53, "Stage Lights v", 10, TEXT_REGULAR);

    drawText(690, 53, "60.0 FPS | Vulkan 1.3 | Solid PBR | PhysX 5.1", 10, TEXT_DIM);

    // 4. LEFT VERTICAL TOOL PALETTE (X: 0 to 32, Y: 58 to 390)
    Screen.draw_rectangle(0, 58, 32, 332, OMNI_PANEL);
    Screen.draw_line(32, 58, 32, 390, OMNI_BORDER);

    var tools = [
        { icon: "^", active: true },
        { icon: "+", active: false },
        { icon: "O", active: false },
        { icon: "#", active: false },
        { icon: "U", active: false },
        { icon: ">", active: false },
        { icon: "||", active: false }
    ];

    tools.forEach(function(tl, i) {
        var ty = 64 + i * 28;
        if (tl.active) {
            Screen.draw_rectangle(4, ty, 24, 22, rgba(243, 156, 18, 50));
            Screen.draw_rectangle(4, ty, 2, 22, OMNI_ORANGE);
            drawText(12, ty + 16, tl.icon, 13, OMNI_ORANGE);
        } else {
            drawText(12, ty + 16, tl.icon, 12, TEXT_MUTED);
        }
    });

    // 5. MAIN 3D PERSPECTIVE VIEWPORT (X: 32 to 665, Y: 58 to 390)
    Screen.draw_rectangle(VP_X, VP_Y, VP_W, VP_H, rgba(16, 17, 18, 255));
    renderMain3DScene();

    Screen.draw_line(VP_X, VP_Y, VP_X + VP_W, VP_Y, OMNI_BORDER);
    Screen.draw_line(VP_X, VP_Y + VP_H, VP_X + VP_W, VP_Y + VP_H, OMNI_BORDER);
    Screen.draw_line(VP_X + VP_W, VP_Y, VP_X + VP_W, VP_Y + VP_H, OMNI_BORDER);

    // 6. RIGHT SIDE PANEL (X: 665 to 960)
    var rPaneX = 665;
    var rPaneW = 295;
    Screen.draw_rectangle(rPaneX, 58, rPaneW, 332, OMNI_PANEL);
    Screen.draw_line(rPaneX, 58, rPaneX, 390, OMNI_BORDER);

    // TABS: [3D Models] | [Neural Net] | [Stage]
    Screen.draw_rectangle(rPaneX, 58, rPaneW, 18, OMNI_PANEL_ALT);
    Screen.draw_line(rPaneX, 76, 960, 76, OMNI_BORDER);

    var isModels = (sideTab === "models");
    Screen.draw_rectangle(rPaneX + 4, 59, 82, 16, isModels ? OMNI_PANEL : OMNI_PANEL_ALT);
    if (isModels) Screen.draw_line(rPaneX + 4, 75, rPaneX + 86, 75, OMNI_ORANGE);
    drawText(rPaneX + 8, 72, "3D Models", 10, isModels ? TEXT_BRIGHT : TEXT_MUTED);

    var isNeural = (sideTab === "neural");
    Screen.draw_rectangle(rPaneX + 88, 59, 82, 16, isNeural ? OMNI_PANEL : OMNI_PANEL_ALT);
    if (isNeural) Screen.draw_line(rPaneX + 88, 75, rPaneX + 170, 75, NV_GREEN);
    drawText(rPaneX + 92, 72, "Neural Net", 10, isNeural ? NV_GREEN : TEXT_MUTED);

    var isStage = (sideTab === "stage");
    Screen.draw_rectangle(rPaneX + 172, 59, 52, 16, isStage ? OMNI_PANEL : OMNI_PANEL_ALT);
    if (isStage) Screen.draw_line(rPaneX + 172, 75, rPaneX + 224, 75, OMNI_CYAN);
    drawText(rPaneX + 178, 72, "Stage", 10, isStage ? TEXT_BRIGHT : TEXT_MUTED);

    // CONTENT BASED ON ACTIVE SIDE TAB
    if (sideTab === "neural") {
        renderNeuralNetworkHUD(rPaneX, rPaneW);
    } else if (sideTab === "models") {
        Screen.draw_rectangle(rPaneX + 6, 80, rPaneW - 12, 14, rgba(20, 21, 22, 255));
        drawText(rPaneX + 12, 91, "Predefined 3D Models (" + predefinedModels.length + " Available)", 10, OMNI_ORANGE);

        var startMdlIdx = Math.max(0, Math.min(selectedModelIdx - 1, predefinedModels.length - 4));
        for (var i = 0; i < 4; i++) {
            var mIdx = startMdlIdx + i;
            if (mIdx >= predefinedModels.length) break;
            var mdl = predefinedModels[mIdx];
            var itemY = 98 + i * 18;
            var isSel = (mIdx === selectedModelIdx);

            if (isSel) {
                Screen.draw_rectangle(rPaneX + 4, itemY, rPaneW - 8, 17, rgba(45, 65, 95, 255));
                Screen.draw_rectangle(rPaneX + 4, itemY, 3, 17, OMNI_ORANGE);
            }

            drawText(rPaneX + 10, itemY + 13, isSel ? "> " + mdl.name : "  " + mdl.name, 11, isSel ? TEXT_BRIGHT : TEXT_REGULAR);
            drawText(rPaneX + 225, itemY + 13, mdl.type, 10, isSel ? OMNI_CYAN : TEXT_DIM);
        }

        var curMdl = predefinedModels[selectedModelIdx];
        var previewY = 172;
        Screen.draw_rectangle(rPaneX + 6, previewY, rPaneW - 12, 126, rgba(18, 19, 20, 255));
        Screen.draw_line(rPaneX + 6, previewY, rPaneX + rPaneW - 6, previewY, OMNI_BORDER);
        Screen.draw_line(rPaneX + 6, previewY + 126, rPaneX + rPaneW - 6, previewY + 126, OMNI_BORDER);
        Screen.draw_line(rPaneX + 6, previewY, rPaneX + 6, previewY + 126, OMNI_BORDER);
        Screen.draw_line(rPaneX + rPaneW - 6, previewY, rPaneX + rPaneW - 6, previewY + 126, OMNI_BORDER);

        drawText(rPaneX + 12, previewY + 14, "3D PREVIEW: " + curMdl.id, 10, OMNI_CYAN);
        drawText(rPaneX + 215, previewY + 14, "Turntable", 9, TEXT_DIM);

        renderSideModelPreview(curMdl);

        var specY = 304;
        Screen.draw_rectangle(rPaneX + 6, specY, rPaneW - 12, 80, OMNI_PANEL_ALT);
        drawText(rPaneX + 12, specY + 14, "Category: " + curMdl.category, 10, TEXT_BRIGHT);
        drawText(rPaneX + 12, specY + 28, "Dimensions: " + curMdl.dims + " | Mass: " + curMdl.mass, 9, TEXT_REGULAR);
        drawText(rPaneX + 12, specY + 42, "Geometry: " + curMdl.vertices + " Vertices, " + curMdl.faces + " Faces", 9, TEXT_MUTED);
        drawText(rPaneX + 12, specY + 56, "Material: " + curMdl.mat, 9, NV_GREEN);

        Screen.draw_rectangle(rPaneX + 10, specY + 62, rPaneW - 20, 14, rgba(20, 45, 75, 255));
        drawText(rPaneX + 16, specY + 73, "[X] Spawn into Scene  [SELECT] Tab", 9, TEXT_BRIGHT);
    } else {
        // Stage View
        Screen.draw_rectangle(rPaneX + 6, 80, rPaneW - 12, 14, rgba(20, 21, 22, 255));
        drawText(rPaneX + 12, 91, "Stage Prims in World (" + allScenePrims.length + " Loaded)", 10, TEXT_MUTED);

        allScenePrims.forEach(function(prim, idx) {
            var itemY = 98 + idx * 16;
            var isSel = (idx === selectedPrimIdx);
            if (isSel) {
                Screen.draw_rectangle(rPaneX + 4, itemY, rPaneW - 8, 15, rgba(45, 65, 95, 255));
                Screen.draw_rectangle(rPaneX + 4, itemY, 2, 15, OMNI_ORANGE);
            }
            drawText(rPaneX + 10, itemY + 12, "o", 10, isSel ? TEXT_BRIGHT : TEXT_MUTED);
            drawText(rPaneX + 24, itemY + 12, prim.id + " (" + prim.name.substring(0, 14) + ")", 11, isSel ? TEXT_BRIGHT : TEXT_REGULAR);
            drawText(rPaneX + 240, itemY + 12, (idx < 5 ? "AMR" : "Prop"), 10, isSel ? OMNI_CYAN : TEXT_DIM);
        });

        var selPrim = allScenePrims[selectedPrimIdx];
        var propY = 222;
        Screen.draw_line(rPaneX, propY, 960, propY, OMNI_BORDER);
        Screen.draw_rectangle(rPaneX, propY, rPaneW, 16, OMNI_PANEL_ALT);
        drawText(rPaneX + 10, propY + 12, "Property: " + selPrim.id, 11, TEXT_BRIGHT);

        drawText(rPaneX + 10, propY + 30, "Prim Path: " + selPrim.primPath, 9, TEXT_DIM);
        drawText(rPaneX + 10, propY + 46, "v Transform", 10, TEXT_BRIGHT);

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
        drawText(rPaneX + 16, propY + 117, "[SELECT] Tab  [X] Assign Mission", 9, TEXT_BRIGHT);
    }

    // 7. BOTTOM DOCK PANEL: CONTENT BROWSER & TIMELINE (Y: 390 to 522)
    Screen.draw_rectangle(0, 390, 960, 132, OMNI_PANEL);
    Screen.draw_line(0, 390, 960, 390, OMNI_BORDER);

    Screen.draw_rectangle(0, 390, 960, 18, OMNI_PANEL_ALT);
    Screen.draw_line(0, 408, 960, 408, OMNI_BORDER);

    var bTabs = [ "Content", "Showcases", "NVIDIA Assets", "Materials", "Console", "Timeline" ];
    var tabX = 10;
    bTabs.forEach(function(t) {
        var isTabSel = (t === "Console");
        if (isTabSel) {
            Screen.draw_rectangle(tabX, 391, 58, 16, OMNI_PANEL);
            Screen.draw_line(tabX, 407, tabX + 58, 407, OMNI_ORANGE);
            drawText(tabX + 8, 404, t, 11, TEXT_BRIGHT);
        } else {
            drawText(tabX + 8, 404, t, 11, TEXT_MUTED);
        }
        tabX += 66;
    });

    drawText(560, 404, "omniverse://localhost/IsaacWarehouse/Robots/", 10, TEXT_DIM);

    // Left Sub-tree
    Screen.draw_rectangle(0, 408, 160, 114, rgba(28, 29, 31, 255));
    Screen.draw_line(160, 408, 160, 522, OMNI_BORDER);

    drawText(10, 424, "+ Import Assets", 10, NV_GREEN);
    drawText(10, 442, "> 3D Models Folder", 10, TEXT_MUTED);
    drawText(10, 460, "v Omniverse Server", 10, TEXT_BRIGHT);
    drawText(22, 476, "- IsaacWarehouse", 10, OMNI_CYAN);
    drawText(22, 492, "- Predefined_Robots", 10, TEXT_REGULAR);
    drawText(10, 510, "> Local Storage (ux0:)", 10, TEXT_MUTED);

    // Right Area: Live Stage Event Stream
    var logStartX = 170;
    drawText(logStartX, 424, "STAGE EVENT STREAM & TELEMETRY LOG", 10, TEXT_MUTED);
    for (var i = 0; i < Math.min(5, consoleLogs.length); i++) {
        var lineY = 442 + i * 15;
        drawText(logStartX, lineY, consoleLogs[i], 11, (i === 0) ? TEXT_BRIGHT : TEXT_MUTED);
    }

    // 8. BOTTOM CONTROLLER ACTION BAR & PLAYBACK (Y: 522 to 544)
    Screen.draw_rectangle(0, 522, 960, 22, OMNI_DARKEST);
    Screen.draw_line(0, 522, 960, 522, OMNI_BORDER);

    // Timeline Scrubber
    drawText(12, 538, "[>] 00142 / 00240", 10, NV_GREEN);
    Screen.draw_line(125, 524, 125, 542, OMNI_BORDER);

    drawText(135, 538, "[L1/R1] Cycle", 11, TEXT_BRIGHT);
    drawText(235, 538, "[R-Stick] Orbit", 11, TEXT_BRIGHT);
    drawText(330, 538, "[L-Stick] Pan", 11, TEXT_BRIGHT);
    drawText(420, 538, "[X] Spawn/Dispatch", 11, NV_GREEN);
    drawText(540, 538, "[/\\ ] Overlays", 11, OMNI_CYAN);
    drawText(630, 538, "[O] Dock", 11, OMNI_ORANGE);
    drawText(695, 538, "[] E-Stop", 11, OMNI_RED);
    drawText(765, 538, "[SELECT] Tab", 11, TEXT_BRIGHT);
    drawText(865, 538, "DRIVE 60Hz", 10, TEXT_DIM);

    Screen.end_drawing();
    Screen.swap_buffers();
}

// -----------------------------------------------------------------------------
// AUTONOMOUS SIMULATION LOOP
// -----------------------------------------------------------------------------
function updateSimulation(dt) {
    simTime += dt;
    simFrame = (simFrame + 1) % 240;
    previewTurntableAngle += dt * 1.5;

    // Update Dust Particles
    for (var pi = 0; pi < particles.length; pi++) {
        var p = particles[pi];
        p.x += p.vx;
        p.y += p.vy;
        p.z += p.vz;
        if (p.x < -70) p.x = 70; if (p.x > 70) p.x = -70;
        if (p.z < -70) p.z = 70; if (p.z > 70) p.z = -70;
        if (p.y < 0.5) p.y = 28; if (p.y > 28) p.y = 0.5;
    }

    robots.forEach(function(r, idx) {
        if (r.state === "NAVIGATING" || r.state === "PATROLLING") {
            r.battery = Math.max(5.0, r.battery - dt * 0.05);

            var dx = r.tx - r.x;
            var dz = r.tz - r.z;
            var dist = Math.sqrt(dx * dx + dz * dz);

            if (dist > 1.0) {
                var targetRot = Math.atan2(dx, dz);
                var diffRot = targetRot - r.rotY;
                while (diffRot > Math.PI) diffRot -= 2 * Math.PI;
                while (diffRot < -Math.PI) diffRot += 2 * Math.PI;
                r.rotY += diffRot * dt * 3.0;

                r.x += (dx / dist) * r.speed * dt * 10.0;
                r.z += (dz / dist) * r.speed * dt * 10.0;
            } else {
                var waypoints = [
                    { x: 0, z: -35 }, { x: -35, z: 0 }, { x: 35, z: 0 },
                    { x: 0, z: 35 }, { x: -20, z: 20 }, { x: 20, z: -20 }
                ];
                var wp = waypoints[Math.floor((simTime + idx * 2) % waypoints.length)];
                r.tx = wp.x + (Math.random() - 0.5) * 15.0;
                r.tz = wp.z + (Math.random() - 0.5) * 15.0;
            }
        }
    });
}

// -----------------------------------------------------------------------------
// CONTROLLER INPUT HANDLING
// -----------------------------------------------------------------------------
var prevButtons = new Map();
function justPressed(btn) {
    var isDown = Pads.check(btn);
    var wasDown = prevButtons.get(btn) === true;
    prevButtons.set(btn, isDown);
    return isDown && !wasDown;
}

var lastTouchX = -1, lastTouchY = -1;
var isTouching = false;

function handleTouch() {
    try {
        if (typeof Touch === "undefined" || typeof Touch.peek !== "function") return;
        var tData = Touch.peek(0);
        if (tData && tData.count > 0 && tData.touches && tData.touches.length > 0) {
            var t0 = tData.touches[0];
            var tx = (t0.x > 960) ? Math.floor(t0.x * 960 / 1920) : t0.x;
            var ty = (t0.y > 544) ? Math.floor(t0.y * 544 / 1088) : t0.y;

            if (tx >= VP_X && tx <= VP_X + VP_W && ty >= VP_Y && ty <= VP_Y + VP_H) {
                if (isTouching && lastTouchX >= 0) {
                    var dX = tx - lastTouchX;
                    var dY = ty - lastTouchY;
                    orbitYaw += dX * 0.008;
                    orbitPitch = Math.max(0.08, Math.min(1.48, orbitPitch - dY * 0.008));
                }
                lastTouchX = tx;
                lastTouchY = ty;
                isTouching = true;
                return;
            }
        }
    } catch (e) {}
    isTouching = false;
    lastTouchX = -1;
    lastTouchY = -1;
}

function handleInput() {
    handleTouch();
    var pad = Pads.read();

    // 1. Right Stick (or Vita3K I/J/K/L): Orbit 3D Camera (Yaw & Pitch)
    var rxNorm = getAxisDelta(pad.rx);
    var ryNorm = getAxisDelta(pad.ry);

    if (rxNorm !== 0) {
        orbitYaw += rxNorm * 0.045;
    }
    if (ryNorm !== 0) {
        orbitPitch = Math.max(0.08, Math.min(1.48, orbitPitch - ryNorm * 0.035));
    }

    // 2. Left Stick (or Vita3K W/A/S/D): Pan Camera Target in 3D Space
    var lxNorm = getAxisDelta(pad.lx);
    var lyNorm = getAxisDelta(pad.ly);

    var fLen = Math.sqrt(Fx * Fx + Fz * Fz);
    var fwdX = (fLen > 0.001) ? (Fx / fLen) : 0;
    var fwdZ = (fLen > 0.001) ? (Fz / fLen) : 1;

    if (lxNorm !== 0 || lyNorm !== 0) {
        var panSpeed = 2.4;
        targetX += (Rx * lxNorm - fwdX * lyNorm) * panSpeed;
        targetZ += (Rz * lxNorm - fwdZ * lyNorm) * panSpeed;
    }

    // Camera Zoom In / Out via L2 / R2 triggers (or keys U / O)
    if (Pads.check(Pads.L2)) camDist = Math.max(45.0, camDist - 2.5);
    if (Pads.check(Pads.R2)) camDist = Math.min(420.0, camDist + 2.5);

    // 3. L1 / R1: Cycle Catalog Models or Stage Prims
    if (justPressed(Pads.L1)) {
        if (sideTab === "models") {
            selectedModelIdx = (selectedModelIdx - 1 + predefinedModels.length) % predefinedModels.length;
            addLog("[3D Library] " + predefinedModels[selectedModelIdx].name);
        } else {
            selectedPrimIdx = (selectedPrimIdx - 1 + allScenePrims.length) % allScenePrims.length;
            addLog("[Selection] Prim: " + allScenePrims[selectedPrimIdx].id);
        }
    }
    if (justPressed(Pads.R1)) {
        if (sideTab === "models") {
            selectedModelIdx = (selectedModelIdx + 1) % predefinedModels.length;
            addLog("[3D Library] " + predefinedModels[selectedModelIdx].name);
        } else {
            selectedPrimIdx = (selectedPrimIdx + 1) % allScenePrims.length;
            addLog("[Selection] Prim: " + allScenePrims[selectedPrimIdx].id);
        }
    }

    // 4. D-Pad UP / DOWN: Browse Roster
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
            var spawnedModel = predefinedModels[selectedModelIdx];
            addLog("[Spawn] Instantiated: " + spawnedModel.name);
            targetX = 0; targetY = 10; targetZ = 0;
        } else {
            var bot = robots[selectedPrimIdx % robots.length];
            var mission = availableMissions[selectedMissionIdx];
            bot.state = "NAVIGATING";
            bot.task = mission.title;
            addLog("[Dispatch] " + bot.id + " -> " + mission.title);
        }
    }

    // 6. TRIANGLE: Toggle AI Neural Perception Overlays (LiDAR, Frustum, Trajectory, Boxes)
    if (justPressed(Pads.TRIANGLE)) {
        showNeuralPerception = !showNeuralPerception;
        addLog("[Perception] Neural overlays " + (showNeuralPerception ? "ENABLED" : "DISABLED"));
    }

    // 7. CIRCLE: Dock Robot
    if (justPressed(Pads.CIRCLE)) {
        var bot = robots[0];
        bot.tx = 0.0;
        bot.tz = -15.0;
        bot.state = "NAVIGATING";
        bot.task = "Autonomous Inductive Docking";
        addLog("[Dock] AMR-01 returning to bay");
    }

    // 8. SQUARE: E-Stop Toggle
    if (justPressed(Pads.SQUARE)) {
        robots.forEach(function(r) {
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

    // 9. SELECT: Cycle Side Panel (3D Models -> Neural Net -> Stage)
    if (justPressed(Pads.SELECT)) {
        if (sideTab === "models") sideTab = "neural";
        else if (sideTab === "neural") sideTab = "stage";
        else sideTab = "models";
        addLog("[Side Panel] Tab: " + sideTab.toUpperCase());
    }

    // 10. START: Reset Camera to Default Isometric View
    if (justPressed(Pads.START)) {
        orbitYaw = 0.65;
        orbitPitch = 0.45;
        camDist = 185.0;
        targetX = 0.0;
        targetY = 10.0;
        targetZ = 0.0;
        addLog("[Camera] Reset to Default View");
    }
}

// -----------------------------------------------------------------------------
// MAIN GAME LOOP (VSYNC 60 FPS)
// -----------------------------------------------------------------------------
var lastFrameTime = Date.now();

var mainLoop = os.setInterval(function() {
    if (!running) {
        os.clearInterval(mainLoop);
        return;
    }

    var now = Date.now();
    var dt = Math.min(0.05, Math.max(0.001, (now - lastFrameTime) / 1000.0));
    lastFrameTime = now;

    handleInput();
    updateCameraVectors();
    updateSimulation(dt);
    render();
}, 0);
