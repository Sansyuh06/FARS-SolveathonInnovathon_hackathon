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
const OMNI_DARKEST    = rgba(24, 24, 24, 255);   // Title bar, deep charcoal
const OMNI_BG         = rgba(30, 30, 30, 255);   // Viewport & panel background
const OMNI_PANEL      = rgba(38, 38, 38, 255);   // Docks & sidebars
const OMNI_PANEL_ALT  = rgba(46, 46, 46, 255);   // Secondary header / tab rows
const OMNI_BORDER     = rgba(56, 56, 56, 255);   // Structural dividers
const OMNI_BORDER_HI  = rgba(75, 75, 75, 255);   // Active outlines

const NV_GREEN        = rgba(118, 185, 0, 255);  // NVIDIA Signature Green #76B900
const NV_GREEN_DIM    = rgba(75, 120, 0, 255);
const OMNI_ORANGE     = rgba(243, 156, 18, 255); // Omniverse USD selection glow
const OMNI_ORANGE_DIM = rgba(160, 95, 10, 255);
const OMNI_RED        = rgba(235, 60, 60, 255);
const OMNI_BLUE       = rgba(60, 140, 240, 255);
const OMNI_CYAN       = rgba(0, 210, 240, 255);

const TEXT_BRIGHT     = rgba(240, 240, 240, 255);
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
let httpAvailable = false; // Disabled by default to prevent vs0:sys/external/libhttp.suprx error
let connectionTested = false;

let selectedPrimIdx = 0; // 0..4: AMRs, 5: Industrial Compressor, 6: Rack Facility
let selectedMissionIdx = 0;
let activeBottomTab = "console"; // "content" | "console"
let showWireframe = true;

// 3D Perspective Viewport Geometry (X: 32 to 665, Y: 58 to 390)
const VP_X  = 32;
const VP_Y  = 58;
const VP_W  = 633;
const VP_H  = 332;
const VP_CX = VP_X + Math.floor(VP_W / 2);
const VP_CY = VP_Y + Math.floor(VP_H / 2);
const FOCAL = 310.0;

// 3D Camera Orbit Parameters
let camYaw   = 0.52;  // Orbit angle around vertical Y
let camPitch = 0.38;  // Elevation angle
let camDist  = 165.0; // Distance to focus target
let targetX  = 0.0;
let targetY  = 10.0;
let targetZ  = 0.0;

let camX = 0.0;
let camY = 0.0;
let camZ = 0.0;

// Log History (Omniverse Console)
const consoleLogs = [
    "[USD Composer 2023.2.5] Stage loaded: IsaacWarehouse.usd",
    "[RTX Real-Time] Vulkan pipeline initialized at 960x544",
    "[Physics] PhysX 5.1 robotics solver active (60 Hz)",
    "[Fleet] 5 AMRs synchronized with warehouse stage prims"
];

function addLog(msg) {
    const t = simTime.toFixed(1) + "s";
    consoleLogs.unshift("[" + t + "] " + msg);
    if (consoleLogs.length > 7) consoleLogs.pop();
}

// -----------------------------------------------------------------------------
// USD STAGE PRIMS & ROBOTS
// -----------------------------------------------------------------------------
const robots = [
    {
        id: "AMR-01",
        name: "Heavy Logistics",
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
        name: "Medicine Courier",
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
        name: "UV-C Sterilizer",
        primPath: "/World/Robots/AMR_03_Sterilizer",
        x: 45.0, y: 0.0, z: 25.0,
        tx: 45.0, tz: 25.0,
        rotY: -0.8,
        speed: 0.65,
        battery: 76.2,
        state: "STERILIZING",
        task: "Emergency Ward UV-C Sweep",
        color: rgba(180, 100, 240, 255)
    },
    {
        id: "AMR-04",
        name: "Patient Escort",
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
        name: "Rapid Security",
        primPath: "/World/Robots/AMR_05_Security",
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

// Additional Omniverse Warehouse Prims
const otherPrims = [
    {
        id: "PUMP-01",
        name: "Extracted_Object_Clone_0",
        primPath: "/World/Machinery/Industrial_Compressor_Pump",
        x: 20.0, y: 0.0, z: 0.0,
        tx: 20.0, tz: 0.0,
        rotY: 0.0,
        speed: 0.0,
        battery: 100.0,
        state: "ONLINE",
        task: "Facility Vacuum & Air Pressure Pump",
        color: rgba(130, 145, 110, 255)
    },
    {
        id: "RACK-01",
        name: "RackLarge_A1_A7",
        primPath: "/World/Environment/Racks/RackLarge_A1_A7",
        x: -70.0, y: 0.0, z: 0.0,
        tx: -70.0, tz: 0.0,
        rotY: 0.0,
        speed: 0.0,
        battery: 100.0,
        state: "STATIC",
        task: "High-Bay Pallet Storage Rack",
        color: rgba(70, 110, 160, 255)
    }
];

// All selectable scene prims
const allPrims = [...robots, ...otherPrims];

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

// -----------------------------------------------------------------------------
// TEXT DRAWING HELPER
// -----------------------------------------------------------------------------
function drawText(x, y, str, size = 13, color = TEXT_REGULAR) {
    try {
        Font.font_draw_text(font, Math.floor(x), Math.floor(y), color, size, String(str));
    } catch (e) {
        // Fallback
    }
}

// -----------------------------------------------------------------------------
// NETWORK INTEGRATION (SAFE - NO BLOCKING / NO LIBHTTP LOG SPAM)
// -----------------------------------------------------------------------------
function testHostConnection() {
    connectionTested = true;
    try {
        if (typeof Net === "undefined" || !Net.is_connected || !Net.is_connected()) {
            addLog("[Net] Vita Wi-Fi disconnected. RTX Autonomous Active.");
            httpAvailable = false;
            return false;
        }
        const url = "http://" + hostIp + ":" + hostPort + "/api/farsverse/state";
        const res = Net.get(url);
        if (res && res.status === 200 && res.body) {
            const data = JSON.parse(res.body);
            hostOnline = true;
            httpAvailable = true;
            addLog("[Net] Connected to Host Isaac Sim: " + hostIp);
            if (data.robots && Array.isArray(data.robots)) {
                for (let i = 0; i < Math.min(robots.length, data.robots.length); i++) {
                    robots[i].x = data.robots[i].x || robots[i].x;
                    robots[i].z = data.robots[i].y || data.robots[i].z || robots[i].z;
                    robots[i].battery = data.robots[i].battery || robots[i].battery;
                }
            }
            return true;
        }
    } catch (e) {
        httpAvailable = false;
        hostOnline = false;
        addLog("[Net] Host unreached. 60Hz Autonomous PhysX Active.");
    }
    return false;
}

function dispatchSelectedMission() {
    const prim = allPrims[selectedPrimIdx];
    const mission = availableMissions[selectedMissionIdx];
    addLog("[Dispatch] " + prim.id + " -> " + mission.title);
    if (selectedPrimIdx < robots.length) {
        const bot = robots[selectedPrimIdx];
        bot.state = "NAVIGATING";
        bot.task = mission.title + " (" + mission.loc + ")";
        bot.tx = (Math.random() - 0.5) * 80.0;
        bot.tz = (Math.random() - 0.5) * 80.0;
    }
    // Attempt host dispatch only if connection is confirmed online
    if (hostOnline && httpAvailable) {
        try {
            const payload = JSON.stringify({
                task_type: mission.title.toLowerCase().replace(/ /g, "_"),
                location: mission.loc,
                priority: 2
            });
            Net.post("http://" + hostIp + ":" + hostPort + "/api/farsverse/task", payload, "application/json");
        } catch (e) {
            httpAvailable = false;
        }
    }
}

// -----------------------------------------------------------------------------
// 3D PERSPECTIVE PROJECTION ENGINE
// -----------------------------------------------------------------------------
function updateCamera() {
    // Camera orbital spherical coordinates
    const cosP = Math.cos(camPitch);
    const sinP = Math.sin(camPitch);
    const cosY = Math.cos(camYaw);
    const sinY = Math.sin(camYaw);

    camX = targetX + camDist * sinY * cosP;
    camY = targetY + camDist * sinP;
    camZ = targetZ - camDist * cosY * cosP;
}

function project3D(wx, wy, wz) {
    const dx = wx - camX;
    const dy = wy - camY;
    const dz = wz - camZ;

    // Yaw rotation (around Y axis)
    const cosY = Math.cos(camYaw);
    const sinY = Math.sin(camYaw);
    const x1 = dx * cosY - dz * sinY;
    const z1 = dx * sinY + dz * cosY;

    // Pitch rotation (around X axis)
    const cosP = Math.cos(camPitch);
    const sinP = Math.sin(camPitch);
    const y2 = dy * cosP - z1 * sinP;
    const z2 = dy * sinP + z1 * cosP;

    if (z2 <= 4.0) return null; // Behind camera clipping

    const sx = VP_CX + (x1 / z2) * FOCAL;
    const sy = VP_CY - (y2 / z2) * FOCAL;

    return { x: sx, y: sy, depth: z2 };
}

function drawLine3D(x1, y1, z1, x2, y2, z2, color) {
    const p1 = project3D(x1, y1, z1);
    const p2 = project3D(x2, y2, z2);
    if (!p1 || !p2) return;

    // Vita2D hardware line draw
    Screen.draw_line(p1.x, p1.y, p2.x, p2.y, color);
}

// Draw 3D Oriented Box
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
        [0, 4], [1, 5], [2, 6], [3, 7]  // Vertical posts
    ];

    for (let i = 0; i < edges.length; i++) {
        const pA = v[edges[i][0]];
        const pB = v[edges[i][1]];
        if (pA && pB) {
            Screen.draw_line(pA.x, pA.y, pB.x, pB.y, color);
            if (outlineColor !== 0) {
                // Thicker highlight outline for selected Omniverse prim
                Screen.draw_line(pA.x + 1, pA.y, pB.x + 1, pB.y, outlineColor);
                Screen.draw_line(pA.x, pA.y + 1, pB.x, pB.y + 1, outlineColor);
            }
        }
    }
}

// Draw 3D Transform Gizmo at Prim Location (Matching Omniverse USD Composer)
function drawTransformGizmo(gx, gy, gz) {
    const origin = project3D(gx, gy, gz);
    if (!origin) return;

    const len = 20.0;

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

    // Center pivot square
    Screen.draw_rectangle(origin.x - 3, origin.y - 3, 6, 6, rgba(255, 255, 255, 255));
}

// -----------------------------------------------------------------------------
// 3D SCENE RENDERING (GROUND GRID, RACKS, ROBOTS, MACHINERY)
// -----------------------------------------------------------------------------
function render3DScene() {
    // 1. Perspective Ground Grid (Omniverse style)
    const gridColor     = rgba(45, 45, 45, 255);
    const subGridColor  = rgba(38, 38, 38, 255);
    const axisColorX    = rgba(180, 50, 50, 200);  // Red X-axis
    const axisColorZ    = rgba(50, 100, 190, 200); // Blue Z-axis

    const extent = 100.0;
    const step   = 20.0;

    for (let c = -extent; c <= extent; c += step) {
        // Lines parallel to Z
        const colZ = (c === 0) ? axisColorZ : ((Math.abs(c) % 40 === 0) ? gridColor : subGridColor);
        drawLine3D(c, 0, -extent, c, 0, extent, colZ);

        // Lines parallel to X
        const colX = (c === 0) ? axisColorX : ((Math.abs(c) % 40 === 0) ? gridColor : subGridColor);
        drawLine3D(-extent, 0, c, extent, 0, c, colX);
    }

    // 2. High-Bay Warehouse Racks (Left and Right aisles)
    const rackCols = [ -70.0, 70.0 ];
    for (let r = 0; r < rackCols.length; r++) {
        const rx = rackCols[r];
        const isRackSelected = (selectedPrimIdx === 6 && r === 0);
        const rackBeamCol = isRackSelected ? OMNI_ORANGE : rgba(50, 85, 130, 255);
        const shelfBeams  = rgba(210, 130, 30, 255);

        // 4 Vertical Steel Columns
        const uprights = [
            { x: rx - 8, z: -50 }, { x: rx + 8, z: -50 },
            { x: rx - 8, z:   0 }, { x: rx + 8, z:   0 },
            { x: rx - 8, z:  50 }, { x: rx + 8, z:  50 }
        ];

        for (let u = 0; u < uprights.length; u++) {
            drawLine3D(uprights[u].x, 0, uprights[u].z, uprights[u].x, 36, uprights[u].z, rackBeamCol);
        }

        // Horizontal Shelf Levels (Y = 12, 24, 36)
        for (let lvl = 12; lvl <= 36; lvl += 12) {
            drawLine3D(rx - 8, lvl, -50, rx + 8, lvl, -50, shelfBeams);
            drawLine3D(rx - 8, lvl,   0, rx + 8, lvl,   0, shelfBeams);
            drawLine3D(rx - 8, lvl,  50, rx + 8, lvl,  50, shelfBeams);

            drawLine3D(rx - 8, lvl, -50, rx - 8, lvl, 50, shelfBeams);
            drawLine3D(rx + 8, lvl, -50, rx + 8, lvl, 50, shelfBeams);

            // Diagonal cross-bracing
            drawLine3D(rx - 8, lvl - 12, -50, rx - 8, lvl, 0, rgba(60, 60, 60, 255));
            drawLine3D(rx + 8, lvl - 12,   0, rx + 8, lvl, 50, rgba(60, 60, 60, 255));

            // Pallets and Cargo Crates on shelves
            drawBox3D(rx, lvl + 4, -25, 12, 7, 18, 0, rgba(140, 105, 65, 255), isRackSelected ? OMNI_ORANGE : 0);
            drawBox3D(rx, lvl + 4,  25, 12, 7, 18, 0, rgba(110, 130, 90, 255), isRackSelected ? OMNI_ORANGE : 0);
        }

        // Safety bollard at rack corners (Hazard yellow/black)
        drawBox3D(rx + (r === 0 ? 12 : -12), 4, -55, 3, 8, 3, 0, rgba(230, 190, 20, 255));
        drawBox3D(rx + (r === 0 ? 12 : -12), 4,  55, 3, 8, 3, 0, rgba(230, 190, 20, 255));
    }

    // 3. Industrial Compressor / Vacuum Pump Unit (Isaac Warehouse Machinery)
    const pump = otherPrims[0];
    const isPumpSelected = (selectedPrimIdx === 5);
    const pumpOutline = isPumpSelected ? OMNI_ORANGE : 0;
    const pumpBodyCol = rgba(90, 115, 85, 255); // Industrial sage green

    // Horizontal Tank Cylinder (Approximated as cuboid + end caps)
    drawBox3D(pump.x, 7, pump.z, 22, 12, 12, 0, pumpBodyCol, pumpOutline);
    // Motor pump compressor head on top
    drawBox3D(pump.x - 4, 16, pump.z, 9, 7, 9, 0, rgba(70, 80, 75, 255), pumpOutline);
    drawBox3D(pump.x + 5, 17, pump.z, 7, 9, 7, 0, rgba(60, 70, 65, 255), pumpOutline);
    // Vertical Support Legs
    drawLine3D(pump.x - 9, 0, pump.z - 5, pump.x - 9, 4, pump.z - 5, rgba(40, 40, 40, 255));
    drawLine3D(pump.x + 9, 0, pump.z - 5, pump.x + 9, 4, pump.z - 5, rgba(40, 40, 40, 255));
    drawLine3D(pump.x - 9, 0, pump.z + 5, pump.x - 9, 4, pump.z + 5, rgba(40, 40, 40, 255));
    drawLine3D(pump.x + 9, 0, pump.z + 5, pump.x + 9, 4, pump.z + 5, rgba(40, 40, 40, 255));

    if (isPumpSelected) {
        drawTransformGizmo(pump.x, 0, pump.z);
    }

    // 4. Autonomous Mobile Robots (AMRs)
    robots.forEach((bot, idx) => {
        const isBotSelected = (selectedPrimIdx === idx);
        const botOutline = isBotSelected ? OMNI_ORANGE : 0;
        const chassisCol = isBotSelected ? rgba(40, 45, 50, 255) : rgba(32, 36, 42, 255);

        // Lower Chassis Box (Width: 10, Height: 4.5, Length: 14)
        drawBox3D(bot.x, 3.0, bot.z, 10, 4.5, 14, bot.rotY, chassisCol, botOutline);

        // Top Upper Shell with Accent Stripe
        drawBox3D(bot.x, 6.0, bot.z, 8, 2.0, 11, bot.rotY, bot.color, botOutline);

        // Rotating LiDAR Scanner on Top
        const lidarY = 8.5;
        drawBox3D(bot.x, lidarY, bot.z, 3.5, 2.5, 3.5, simTime * 4.0, rgba(20, 20, 20, 255), botOutline);

        // Simulated LiDAR 3D Laser Beams
        const lBeam1 = Math.cos(simTime * 4.0) * 16.0;
        const lBeam2 = Math.sin(simTime * 4.0) * 16.0;
        drawLine3D(bot.x, lidarY, bot.z, bot.x + lBeam1, lidarY, bot.z + lBeam2, rgba(240, 50, 50, 160));

        // Front Status LED Glow
        const fwdX = Math.sin(bot.rotY) * 7.5;
        const fwdZ = Math.cos(bot.rotY) * 7.5;
        const ledPos = project3D(bot.x + fwdX, 3.5, bot.z + fwdZ);
        if (ledPos) {
            Screen.draw_rectangle(ledPos.x - 2, ledPos.y - 2, 4, 4, bot.color);
        }

        // Draw Transform Gizmo if this AMR is selected
        if (isBotSelected) {
            drawTransformGizmo(bot.x, 0.0, bot.z);
        }
    });

    // 5. Mini 3D Axis Orientation Tripod in Bottom-Left Corner
    const tripodCX = VP_X + 26;
    const tripodCY = VP_Y + VP_H - 26;
    const tLen = 14.0;
    const cosY = Math.cos(camYaw);
    const sinY = Math.sin(camYaw);
    const cosP = Math.cos(camPitch);
    const sinP = Math.sin(camPitch);

    // Tripod X (Red)
    const tx_x = (cosY) * tLen;
    const tx_y = (-sinY * sinP) * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX + tx_x, tripodCY - tx_y, rgba(240, 60, 60, 255));
    drawText(tripodCX + tx_x + 2, tripodCY - tx_y - 4, "X", 10, rgba(240, 60, 60, 255));

    // Tripod Y (Green, Up)
    const ty_y = (cosP) * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX, tripodCY - ty_y, NV_GREEN);
    drawText(tripodCX + 2, tripodCY - ty_y - 4, "Y", 10, NV_GREEN);

    // Tripod Z (Blue)
    const tz_x = (-sinY) * tLen;
    const tz_y = (-cosY * sinP) * tLen;
    Screen.draw_line(tripodCX, tripodCY, tripodCX + tz_x, tripodCY - tz_y, rgba(50, 140, 255, 255));
    drawText(tripodCX + tz_x + 2, tripodCY - tz_y - 4, "Z", 10, rgba(50, 140, 255, 255));

    drawText(tripodCX - 12, tripodCY + 14, "cm [grid]", 9, TEXT_DIM);
}

// -----------------------------------------------------------------------------
// COMPLETE OMNIVERSE USD COMPOSER UI RENDERING
// -----------------------------------------------------------------------------
function render() {
    Screen.clear(24, 24, 24, 255);
    Screen.start_drawing();

    // 1. TOP WINDOW TITLE BAR (Y: 0 to 22)
    Screen.draw_rectangle(0, 0, 960, 22, OMNI_DARKEST);
    Screen.draw_line(0, 22, 960, 22, OMNI_BORDER);

    // Green Omniverse Hexagon Icon
    Screen.draw_rectangle(8, 5, 12, 12, NV_GREEN);
    Screen.draw_rectangle(11, 8, 6, 6, OMNI_DARKEST);

    // Title Bar Text
    const stageName = "USD Composer 2023.2.5 | omniverse://localhost/IsaacWarehouse/IsaacWarehouse.usd (read-only)*";
    drawText(26, 16, stageName, 11, TEXT_MUTED);

    // Right Badges
    const badgeX = 760;
    // [LIVE]
    Screen.draw_rectangle(badgeX, 4, 46, 14, rgba(30, 65, 15, 255));
    Screen.draw_rectangle(badgeX, 4, 46, 14, NV_GREEN_DIM);
    Screen.draw_rectangle(badgeX + 5, 8, 5, 5, NV_GREEN);
    drawText(badgeX + 15, 15, "LIVE", 10, TEXT_BRIGHT);

    // [CACHE: OFF]
    Screen.draw_rectangle(badgeX + 52, 4, 76, 14, rgba(65, 20, 20, 255));
    drawText(badgeX + 58, 15, "CACHE: OFF", 10, OMNI_RED);

    // Window controls mock
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

    // Camera Dropdown
    Screen.draw_rectangle(154, 43, 75, 13, rgba(20, 20, 20, 255));
    drawText(160, 53, "Camera  v", 10, TEXT_REGULAR);

    // Stage Lights Dropdown
    Screen.draw_rectangle(235, 43, 90, 13, rgba(20, 20, 20, 255));
    drawText(242, 53, "Stage Lights v", 10, TEXT_REGULAR);

    // Telemetry stats on right of sub-bar
    drawText(710, 53, "60.0 FPS | Vulkan 1.3 | VRAM: 142MB", 10, TEXT_DIM);

    // 4. LEFT VERTICAL TOOL PALETTE (X: 0 to 32, Y: 58 to 390)
    Screen.draw_rectangle(0, 58, 32, 332, OMNI_PANEL);
    Screen.draw_line(32, 58, 32, 390, OMNI_BORDER);

    const tools = [
        { icon: "^", active: true },  // Selection pointer (Orange active)
        { icon: "+", active: false }, // Move gizmo
        { icon: "O", active: false }, // Rotate gizmo
        { icon: "#", active: false }, // Scale gizmo
        { icon: "U", active: false }, // Snap to grid
        { icon: ">", active: false }, // Play PhysX
        { icon: "||", active: false } // Pause
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

    // 5. CENTER 3D VIEWPORT (X: 32 to 665, Y: 58 to 390)
    Screen.draw_rectangle(VP_X, VP_Y, VP_W, VP_H, rgba(22, 22, 22, 255));

    // Enable hardware clipping so 3D objects don't spill outside viewport
    Screen.set_clip_rectangle(VP_X, VP_Y, VP_X + VP_W, VP_Y + VP_H);
    render3DScene();
    Screen.disable_clipping();

    // Viewport Border Outline
    Screen.draw_line(VP_X, VP_Y, VP_X + VP_W, VP_Y, OMNI_BORDER);
    Screen.draw_line(VP_X, VP_Y + VP_H, VP_X + VP_W, VP_Y + VP_H, OMNI_BORDER);
    Screen.draw_line(VP_X + VP_W, VP_Y, VP_X + VP_W, VP_Y + VP_H, OMNI_BORDER);

    // 6. RIGHT SIDE PANEL: STAGE (TOP) & PROPERTIES (BOTTOM) (X: 665 to 960)
    const rPaneX = 665;
    const rPaneW = 295;
    Screen.draw_rectangle(rPaneX, 58, rPaneW, 332, OMNI_PANEL);
    Screen.draw_line(rPaneX, 58, rPaneX, 390, OMNI_BORDER);

    // 6A. STAGE TABS (Y: 58 to 76)
    Screen.draw_rectangle(rPaneX, 58, rPaneW, 18, OMNI_PANEL_ALT);
    Screen.draw_line(rPaneX, 76, 960, 76, OMNI_BORDER);

    // [Stage] Tab (Active)
    Screen.draw_rectangle(rPaneX + 4, 59, 50, 16, OMNI_PANEL);
    Screen.draw_line(rPaneX + 4, 75, rPaneX + 54, 75, OMNI_ORANGE);
    drawText(rPaneX + 12, 72, "Stage", 11, TEXT_BRIGHT);

    drawText(rPaneX + 64, 72, "Layer", 11, TEXT_MUTED);
    drawText(rPaneX + 110, 72, "Render Settings", 11, TEXT_MUTED);

    // Stage Search Bar
    Screen.draw_rectangle(rPaneX + 6, 80, rPaneW - 12, 14, rgba(22, 22, 22, 255));
    drawText(rPaneX + 12, 91, "Search (Name: Old to New)", 10, TEXT_DIM);

    // Tree Column Headers
    drawText(rPaneX + 10, 105, "Name", 10, TEXT_MUTED);
    drawText(rPaneX + 240, 105, "Type", 10, TEXT_MUTED);
    Screen.draw_line(rPaneX + 6, 108, 954, 108, OMNI_BORDER);

    // USD Prims Hierarchy List (Y: 110 to 226)
    allPrims.forEach((prim, idx) => {
        const itemY = 111 + idx * 16;
        const isSelected = (idx === selectedPrimIdx);

        if (isSelected) {
            Screen.draw_rectangle(rPaneX + 4, itemY, rPaneW - 8, 15, rgba(45, 65, 95, 255));
            Screen.draw_rectangle(rPaneX + 4, itemY, 2, 15, OMNI_ORANGE);
        }

        const eyeIcon = "o"; // Visibility eye indicator
        drawText(rPaneX + 8, itemY + 12, eyeIcon, 10, isSelected ? TEXT_BRIGHT : TEXT_MUTED);

        const primType = (idx < robots.length) ? "Xform" : (idx === 5 ? "Mesh" : "Xform");
        const displayName = (idx < robots.length) ? prim.id + " (" + prim.name.split(" ")[0] + ")" : prim.name.substring(0, 16);
        drawText(rPaneX + 22, itemY + 12, displayName, 11, isSelected ? TEXT_BRIGHT : TEXT_REGULAR);
        drawText(rPaneX + 240, itemY + 12, primType, 10, isSelected ? OMNI_CYAN : TEXT_DIM);
    });

    // 6B. PROPERTY PANEL (Y: 228 to 390)
    Screen.draw_line(rPaneX, 228, 960, 228, OMNI_BORDER);
    Screen.draw_rectangle(rPaneX, 228, rPaneW, 16, OMNI_PANEL_ALT);
    drawText(rPaneX + 10, 240, "Property: " + allPrims[selectedPrimIdx].id, 11, TEXT_BRIGHT);

    const selPrim = allPrims[selectedPrimIdx];
    drawText(rPaneX + 10, 256, "Prim Path: " + selPrim.primPath, 9, TEXT_DIM);

    // Transform Rollout
    drawText(rPaneX + 10, 272, "v Transform", 10, TEXT_BRIGHT);

    // Translate [X, Y, Z] with RGB colored badges
    drawText(rPaneX + 14, 287, "Translate", 10, TEXT_MUTED);

    Screen.draw_rectangle(rPaneX + 70, 277, 44, 12, rgba(60, 25, 25, 255));
    drawText(rPaneX + 74, 286, "X " + selPrim.x.toFixed(1), 9, rgba(240, 80, 80, 255));

    Screen.draw_rectangle(rPaneX + 118, 277, 44, 12, rgba(25, 55, 25, 255));
    drawText(rPaneX + 122, 286, "Y " + selPrim.y.toFixed(1), 9, NV_GREEN);

    Screen.draw_rectangle(rPaneX + 166, 277, 44, 12, rgba(25, 45, 80, 255));
    drawText(rPaneX + 170, 286, "Z " + selPrim.z.toFixed(1), 9, rgba(70, 150, 255, 255));

    // Rotate Rollout
    drawText(rPaneX + 14, 303, "Rotate", 10, TEXT_MUTED);
    drawText(rPaneX + 70, 303, "Y: " + ((selPrim.rotY * 180 / Math.PI) % 360).toFixed(1) + " deg", 9, TEXT_REGULAR);

    // Robotics / Telemetry Sub-panel
    drawText(rPaneX + 10, 320, "v Robotics & Telemetry", 10, TEXT_BRIGHT);
    drawText(rPaneX + 14, 334, "State: " + selPrim.state, 10, NV_GREEN);
    drawText(rPaneX + 14, 348, "Battery: " + selPrim.battery.toFixed(1) + "%", 10, TEXT_REGULAR);

    // Battery bar
    const barW = 80;
    const barFill = Math.floor((selPrim.battery / 100.0) * barW);
    Screen.draw_rectangle(rPaneX + 100, 340, barW, 8, rgba(20, 20, 20, 255));
    Screen.draw_rectangle(rPaneX + 100, 340, barFill, 8, selPrim.battery > 30 ? NV_GREEN : OMNI_RED);

    drawText(rPaneX + 14, 363, "Active: " + selPrim.task.substring(0, 28), 9, TEXT_MUTED);

    // Mission dispatch hint
    const mission = availableMissions[selectedMissionIdx];
    drawText(rPaneX + 14, 379, "Queue: [" + mission.priority + "] " + mission.title.substring(0, 20), 9, OMNI_ORANGE);

    // 7. BOTTOM DOCK PANEL: CONTENT BROWSER / CONSOLE (Y: 390 to 522)
    Screen.draw_rectangle(0, 390, 960, 132, OMNI_PANEL);
    Screen.draw_line(0, 390, 960, 390, OMNI_BORDER);

    // Bottom Tabs Row (Y: 390 to 408)
    Screen.draw_rectangle(0, 390, 960, 18, OMNI_PANEL_ALT);
    Screen.draw_line(0, 408, 960, 408, OMNI_BORDER);

    // Tab buttons
    const bTabs = [ "Content", "Showcases", "NVIDIA Assets", "Materials", "Console" ];
    let tabX = 10;
    bTabs.forEach(t => {
        const isTabSel = (activeBottomTab === t.toLowerCase()) || (activeBottomTab === "console" && t === "Console");
        if (isTabSel) {
            Screen.draw_rectangle(tabX, 391, 58, 16, OMNI_PANEL);
            Screen.draw_line(tabX, 407, tabX + 58, 407, OMNI_ORANGE);
            drawText(tabX + 8, 404, t, 11, TEXT_BRIGHT);
        } else {
            drawText(tabX + 8, 404, t, 11, TEXT_MUTED);
        }
        tabX += 70;
    });

    // Content Browser Sub-bar (omniverse path)
    drawText(560, 404, "omniverse://localhost/IsaacWarehouse/Robots/", 10, TEXT_DIM);

    // Left Sub-tree (Bookmarks / Omniverse / Local)
    Screen.draw_rectangle(0, 408, 160, 114, rgba(32, 32, 32, 255));
    Screen.draw_line(160, 408, 160, 522, OMNI_BORDER);

    drawText(10, 424, "+ Import Assets", 10, NV_GREEN);
    drawText(10, 442, "> Bookmarks", 10, TEXT_MUTED);
    drawText(10, 460, "v Omniverse Server", 10, TEXT_BRIGHT);
    drawText(22, 476, "- IsaacWarehouse", 10, OMNI_CYAN);
    drawText(22, 492, "- FARSverse_Fleet", 10, TEXT_REGULAR);
    drawText(10, 510, "> Local Storage (ux0:)", 10, TEXT_MUTED);

    // Right Area: Console Event Logs & Telemetry Stream
    const logStartX = 170;
    drawText(logStartX, 424, "STAGE EVENT STREAM & TELEMETRY LOG", 10, TEXT_MUTED);
    for (let i = 0; i < Math.min(5, consoleLogs.length); i++) {
        const lineY = 442 + i * 15;
        drawText(logStartX, lineY, consoleLogs[i], 11, (i === 0) ? TEXT_BRIGHT : TEXT_MUTED);
    }

    // 8. BOTTOM CONTROLLER ACTION BAR (Y: 522 to 544)
    Screen.draw_rectangle(0, 522, 960, 22, OMNI_DARKEST);
    Screen.draw_line(0, 522, 960, 522, OMNI_BORDER);

    drawText(14, 538, "[L1/R1] Select Prim", 11, TEXT_BRIGHT);
    drawText(145, 538, "[R-Stick] Orbit 3D", 11, TEXT_BRIGHT);
    drawText(275, 538, "[L-Stick] Pan 3D", 11, TEXT_BRIGHT);
    drawText(390, 538, "[D-Pad] Mission", 11, TEXT_REGULAR);
    drawText(500, 538, "[X] Assign", 11, NV_GREEN);
    drawText(580, 538, "[O] Dock", 11, OMNI_CYAN);
    drawText(650, 538, "[] E-Stop", 11, OMNI_RED);
    drawText(730, 538, "[START] Host Link", 11, OMNI_ORANGE);

    drawText(850, 538, "NVIDIA Isaac Sim", 10, TEXT_DIM);

    Screen.end_drawing();
    Screen.swap_buffers();
}

// -----------------------------------------------------------------------------
// AUTONOMOUS LOCAL SIMULATION LOOP (60 FPS)
// -----------------------------------------------------------------------------
function updateSimulation(dt) {
    simTime += dt;

    // Autonomous AMR navigation & patrol loop
    robots.forEach((r, idx) => {
        if (r.state === "NAVIGATING" || r.state === "PATROLLING") {
            r.battery = Math.max(5.0, r.battery - dt * 0.05);

            const dx = r.tx - r.x;
            const dz = r.tz - r.z;
            const dist = Math.sqrt(dx * dx + dz * dz);

            if (dist > 1.0) {
                // Steer rotation towards target
                const targetRot = Math.atan2(dx, dz);
                let diffRot = targetRot - r.rotY;
                while (diffRot > Math.PI) diffRot -= 2 * Math.PI;
                while (diffRot < -Math.PI) diffRot += 2 * Math.PI;
                r.rotY += diffRot * dt * 3.0;

                // Move forward
                r.x += (dx / dist) * r.speed * dt * 10.0;
                r.z += (dz / dist) * r.speed * dt * 10.0;
            } else {
                // Pick next random waypoint in warehouse aisles
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

    // 1. Right Analog Stick: Orbit 3D Camera (Yaw / Pitch)
    if (Math.abs(pad.rx) > 25) {
        camYaw += (pad.rx / 128.0) * 0.04;
    }
    if (Math.abs(pad.ry) > 25) {
        camPitch = Math.max(0.08, Math.min(1.45, camPitch - (pad.ry / 128.0) * 0.04));
    }

    // 2. Left Analog Stick: Pan Camera Target (X / Z)
    if (Math.abs(pad.lx) > 25) {
        const panX = (pad.lx / 128.0) * 1.5;
        targetX += Math.cos(camYaw) * panX;
        targetZ += Math.sin(camYaw) * panX;
    }
    if (Math.abs(pad.ly) > 25) {
        const panZ = (pad.ly / 128.0) * 1.5;
        targetX += -Math.sin(camYaw) * panZ;
        targetZ += Math.cos(camYaw) * panZ;
    }

    // 3. L1 / R1: Cycle Active USD Prim / Robot
    if (justPressed(Pads.L1)) {
        selectedPrimIdx = (selectedPrimIdx - 1 + allPrims.length) % allPrims.length;
        addLog("[Selection] Prim: " + allPrims[selectedPrimIdx].id);
    }
    if (justPressed(Pads.R1)) {
        selectedPrimIdx = (selectedPrimIdx + 1) % allPrims.length;
        addLog("[Selection] Prim: " + allPrims[selectedPrimIdx].id);
    }

    // 4. D-Pad UP / DOWN: Select Mission
    if (justPressed(Pads.UP)) {
        selectedMissionIdx = (selectedMissionIdx - 1 + availableMissions.length) % availableMissions.length;
    }
    if (justPressed(Pads.DOWN)) {
        selectedMissionIdx = (selectedMissionIdx + 1) % availableMissions.length;
    }

    // 5. CROSS: Assign / Dispatch Mission
    if (justPressed(Pads.CROSS)) {
        dispatchSelectedMission();
    }

    // 6. CIRCLE: Dock Robot
    if (justPressed(Pads.CIRCLE)) {
        if (selectedPrimIdx < robots.length) {
            const bot = robots[selectedPrimIdx];
            bot.tx = 0.0;
            bot.tz = -15.0;
            bot.state = "NAVIGATING";
            bot.task = "Autonomous Inductive Docking";
            addLog("[Dock] " + bot.id + " returning to bay");
        }
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

    // 8. START: Attempt Host Link Sync (Explicitly requested by user)
    if (justPressed(Pads.START)) {
        addLog("[Host] Initiating manual link sync...");
        testHostConnection();
    }

    // 9. SELECT: Reset Camera View to Default Isometric
    if (justPressed(Pads.SELECT)) {
        camYaw = 0.52;
        camPitch = 0.38;
        camDist = 165.0;
        targetX = 0.0;
        targetY = 10.0;
        targetZ = 0.0;
        addLog("[Camera] Reset to Perspective Default");
    }
}

// -----------------------------------------------------------------------------
// MAIN GAME LOOP (60 FPS)
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
    updateCamera();
    updateSimulation(dt);
    render();
}, 16);
