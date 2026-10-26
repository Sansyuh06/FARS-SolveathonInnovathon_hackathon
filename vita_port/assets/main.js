// =============================================================================
// FARSVERSE POCKET -- PlayStation Vita Robotics Digital Twin & Command Deck
// =============================================================================

const font = Font.load_font_file("app0:/assets/segoeui.ttf");

// Color Palette (32-bit RGBA integer for Vita2D)
function rgba(r, g, b, a = 255) {
    return (
        ((a & 255) << 24) |
        ((b & 255) << 16) |
        ((g & 255) << 8) |
        (r & 255)
    ) >>> 0;
}

const BG_COLOR      = rgba(12, 16, 22, 255);
const PANEL_BG      = rgba(20, 26, 36, 255);
const PANEL_ALT     = rgba(26, 34, 46, 255);
const BORDER_COLOR  = rgba(45, 58, 76, 255);
const BORDER_ACTIVE = rgba(0, 229, 255, 255);

const TEXT_WHITE    = 0xffffffff;
const TEXT_MUTED    = rgba(148, 163, 184, 255);
const TEXT_DIM      = rgba(100, 116, 139, 255);

const ACCENT_CYAN   = rgba(0, 229, 255, 255);
const ACCENT_GREEN  = rgba(34, 197, 94, 255);
const ACCENT_AMBER  = rgba(245, 158, 11, 255);
const ACCENT_RED    = rgba(239, 68, 68, 255);
const ACCENT_BLUE   = rgba(59, 130, 246, 255);
const ACCENT_PURPLE = rgba(168, 85, 247, 255);

// Application State
let running = true;
let hostIp = "192.168.0.135";
let hostPort = 8080;
let hostOnline = false;
let lastHostPoll = 0;
let hostPollInterval = 1800; // ms
let currentView = "overview"; // 'overview' | 'map_focus' | 'telemetry_focus' | 'net_config'

let selectedRobotIdx = 0;
let selectedMissionIdx = 0;

// Host State
let simTime = 0.0;
let tasksResolved = 0;
let statusMessage = "System Ready. Host Link: " + hostIp + ":" + hostPort;
let logHistory = [
    "FARSverse Pocket initialized.",
    "Dual-core ARM Cortex-A9 host bridge ready.",
    "Listening on local telemetry port."
];

function addLog(msg) {
    const timeStr = (simTime).toFixed(1) + "s";
    logHistory.unshift("[" + timeStr + "] " + msg);
    if (logHistory.length > 8) logHistory.pop();
}

// 5 Autonomous AMRs
const robots = [
    { id: "AMR-01", name: "Heavy Logistics", x: 0, y: -10, targetX: 0, targetY: -10, battery: 94.5, state: "IDLE", mission: "Docked at Charging Bay", speed: 0.0, node: "ChargingDock", color: ACCENT_CYAN },
    { id: "AMR-02", name: "Medicine Courier", x: -30, y: 0, targetX: -30, targetY: 0, battery: 88.0, state: "NAVIGATING", mission: "Pharmacy -> ICU 2", speed: 1.15, node: "Pharmacy", color: ACCENT_GREEN },
    { id: "AMR-03", name: "Sterilization Bot", x: 30, y: 15, targetX: 30, targetY: 15, battery: 76.2, state: "PATROLLING", mission: "Emergency Dept UV-C Sweep", speed: 0.75, node: "EmergencyRoom", color: ACCENT_PURPLE },
    { id: "AMR-04", name: "Patient Escort", x: 0, y: -20, targetX: 0, targetY: -20, battery: 64.8, state: "DELIVERING", mission: "Escort to Room 12", speed: 0.90, node: "Reception", color: ACCENT_BLUE },
    { id: "AMR-05", name: "Rapid Security", x: 0, y: 0, targetX: 0, targetY: 0, battery: 52.1, state: "PATROLLING", mission: "Main Atrium Perimeter", speed: 1.40, node: "MainHall", color: ACCENT_AMBER }
];

// Mission Roster
const availableMissions = [
    { title: "PATROL CORRIDORS", loc: "MainHall", desc: "Routine security & path obstacle inspection", priority: "NORMAL" },
    { title: "DELIVER PHARMACEUTICALS", loc: "Pharmacy", desc: "Transport scheduled medication to ICU 2", priority: "HIGH" },
    { title: "PATIENT CALL: ROOM 5", loc: "Room5", desc: "Respond to nurse call button alert", priority: "URGENT" },
    { title: "STERILIZE EMERGENCY WARD", loc: "EmergencyRoom", desc: "Execute automated UV-C sanitation cycle", priority: "NORMAL" },
    { title: "ICU CRITICAL ASSIST", loc: "ICU1", desc: "Deliver emergency crash cart telemetry", priority: "CRITICAL" },
    { title: "RETURN TO CHARGING DOCK", loc: "ChargingDock", desc: "Autonomous inductive recharge protocol", priority: "LOW" },
    { title: "AI OLLAMA TASK DISPATCH", loc: "Reception", desc: "Query host LLM (phi3:mini) for optimal route", priority: "AI" }
];

// Hospital Rooms for 2D Map (Normalized coordinates)
const hospitalRooms = [
    { id: "Entrance", name: "Entrance", x: -10, y: -30, w: 20, h: 8, color: rgba(50, 60, 80) },
    { id: "Reception", name: "Reception", x: -12, y: -22, w: 24, h: 10, color: rgba(45, 55, 75) },
    { id: "ChargingDock", name: "Charging Bay", x: -10, y: -12, w: 20, h: 8, color: rgba(60, 50, 30) },
    { id: "MainHall", name: "Main Atrium", x: -16, y: -4, w: 32, h: 12, color: rgba(30, 40, 55) },
    { id: "Pharmacy", name: "Pharmacy", x: -38, y: -6, w: 18, h: 12, color: rgba(20, 60, 45) },
    { id: "StaffOffice", name: "Staff Office", x: -38, y: 10, w: 18, h: 12, color: rgba(35, 45, 65) },
    { id: "WaitingHall", name: "Waiting Hall", x: 20, y: -6, w: 18, h: 12, color: rgba(45, 35, 60) },
    { id: "EmergencyRoom", name: "Emergency Ward", x: 20, y: 10, w: 18, h: 14, color: rgba(65, 30, 30) },
    { id: "ICU_Ward", name: "ICU Complex", x: -18, y: 22, w: 36, h: 14, color: rgba(70, 25, 25) },
    { id: "WestWing", name: "Rooms 1-10", x: -38, y: -28, w: 18, h: 20, color: rgba(25, 35, 50) },
    { id: "EastWing", name: "Rooms 11-20", x: 20, y: -28, w: 18, h: 20, color: rgba(25, 35, 50) }
];

// Button Debouncing Map
const prevButtons = new Map();
function justPressed(btn) {
    const isDown = Pads.check(btn);
    const wasDown = prevButtons.get(btn) === true;
    prevButtons.set(btn, isDown);
    return isDown && !wasDown;
}

// Draw Text Helper
function drawText(x, y, str, size = 18, color = TEXT_WHITE) {
    try {
        Font.font_draw_text(font, Math.floor(x), Math.floor(y), color, size, String(str));
    } catch (e) {
        // Fallback
    }
}

// -----------------------------------------------------------------------------
// HOST NETWORK SYNC
// -----------------------------------------------------------------------------
function syncWithHost() {
    try {
        const url = "http://" + hostIp + ":" + hostPort + "/api/farsverse/state";
        const res = Net.get(url);
        if (res && res.status === 200 && res.body) {
            const data = JSON.parse(res.body);
            hostOnline = true;
            if (data.sim_time) simTime = data.sim_time;
            if (data.robots && Array.isArray(data.robots)) {
                for (let i = 0; i < Math.min(robots.length, data.robots.length); i++) {
                    const rData = data.robots[i];
                    robots[i].x = rData.x || robots[i].x;
                    robots[i].y = rData.y || rData.z || robots[i].y;
                    robots[i].battery = rData.battery || robots[i].battery;
                    robots[i].state = rData.state ? rData.state.toUpperCase() : robots[i].state;
                    robots[i].node = rData.current_node || robots[i].node;
                }
            }
            if (data.metrics && data.metrics.completed_tasks !== undefined) {
                tasksResolved = data.metrics.completed_tasks;
            }
            statusMessage = "Host Synced: " + hostIp + ":" + hostPort;
            return true;
        }
    } catch (e) {
        hostOnline = false;
        statusMessage = "Host Offline. Local Autonomous Mode Active.";
    }
    return false;
}

function assignMissionToHost(robotId, mission) {
    addLog("Dispatching " + robotId + " -> " + mission.loc);
    if (hostOnline) {
        try {
            const payload = JSON.stringify({
                task_type: mission.title.toLowerCase().replace(/ /g, "_"),
                location: mission.loc,
                priority: 2,
                description: mission.desc
            });
            Net.post("http://" + hostIp + ":" + hostPort + "/api/farsverse/task", payload, "application/json");
            addLog("Host task confirmed: " + mission.loc);
        } catch (e) {
            addLog("Host dispatch err, running locally.");
        }
    }
    // Update local robot state
    const bot = robots[selectedRobotIdx];
    bot.state = "NAVIGATING";
    bot.mission = mission.title + " (" + mission.loc + ")";
    tasksResolved++;
}

// -----------------------------------------------------------------------------
// LOCAL AUTONOMOUS SIMULATION (Runs at 60 FPS on Vita)
// -----------------------------------------------------------------------------
let mapPanX = 0;
let mapPanY = 0;
let mapZoom = 1.0;

function updateLocalSimulation(dt) {
    simTime += dt;

    // Smooth movement of AMRs towards target
    robots.forEach((r, idx) => {
        // Battery drain simulation
        if (r.state === "NAVIGATING" || r.state === "PATROLLING") {
            r.battery = Math.max(5.0, r.battery - dt * 0.08);
            // Simulated movement
            const dx = r.targetX - r.x;
            const dy = r.targetY - r.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist > 0.5) {
                r.x += (dx / dist) * r.speed * dt * 4.0;
                r.y += (dy / dist) * r.speed * dt * 4.0;
            } else {
                // Pick next patrol target
                const room = hospitalRooms[Math.floor((simTime + idx * 3) % hospitalRooms.length)];
                r.targetX = room.x + (room.w / 2);
                r.targetY = room.y + (room.h / 2);
                r.node = room.id;
            }
        } else if (r.state === "CHARGING") {
            r.battery = Math.min(100.0, r.battery + dt * 0.5);
        }
    });

    // Background host sync
    const now = Date.now();
    if (now - lastHostPoll > hostPollInterval) {
        lastHostPoll = now;
        syncWithHost();
    }
}

// -----------------------------------------------------------------------------
// INPUT HANDLING
// -----------------------------------------------------------------------------
function handleInput() {
    const pad = Pads.read();

    // Analog Stick Map Panning
    if (Math.abs(pad.lx) > 30) mapPanX += (pad.lx / 128) * 3;
    if (Math.abs(pad.ly) > 30) mapPanY += (pad.ly / 128) * 3;

    // L1 / R1: Cycle Selected AMR
    if (justPressed(Pads.L1)) {
        selectedRobotIdx = (selectedRobotIdx - 1 + robots.length) % robots.length;
        addLog("Selected " + robots[selectedRobotIdx].id);
    }
    if (justPressed(Pads.R1)) {
        selectedRobotIdx = (selectedRobotIdx + 1) % robots.length;
        addLog("Selected " + robots[selectedRobotIdx].id);
    }

    // D-Pad UP / DOWN: Navigate Missions
    if (justPressed(Pads.UP)) {
        selectedMissionIdx = (selectedMissionIdx - 1 + availableMissions.length) % availableMissions.length;
    }
    if (justPressed(Pads.DOWN)) {
        selectedMissionIdx = (selectedMissionIdx + 1) % availableMissions.length;
    }

    // CROSS: Assign Selected Mission
    if (justPressed(Pads.CROSS)) {
        const mission = availableMissions[selectedMissionIdx];
        assignMissionToHost(robots[selectedRobotIdx].id, mission);
    }

    // CIRCLE: Return Robot to Dock
    if (justPressed(Pads.CIRCLE)) {
        const bot = robots[selectedRobotIdx];
        bot.targetX = 0;
        bot.targetY = -10;
        bot.state = "NAVIGATING";
        bot.mission = "Return to Charging Dock";
        addLog(bot.id + " returning to dock.");
    }

    // SQUARE: Emergency Stop (E-Stop)
    if (justPressed(Pads.SQUARE)) {
        robots.forEach(r => {
            r.state = "IDLE";
            r.mission = "E-STOP HALT";
        });
        addLog("EMERGENCY STOP TRIGGERED");
        statusMessage = "EMERGENCY STOP ACTIVE";
    }

    // TRIANGLE: Toggle Host Network Connection
    if (justPressed(Pads.TRIANGLE)) {
        addLog("Pinging host at " + hostIp + "...");
        syncWithHost();
    }

    // START: Force API Sync
    if (justPressed(Pads.START)) {
        syncWithHost();
        addLog("Manual Host State Poll Triggered");
    }

    // SELECT: Toggle View Mode
    if (justPressed(Pads.SELECT)) {
        currentView = (currentView === "overview") ? "map_focus" : "overview";
    }
}

// -----------------------------------------------------------------------------
// RENDERING (960 x 544 Native PS Vita OLED)
// -----------------------------------------------------------------------------
function render() {
    Screen.start_drawing();
    Screen.clear(12, 16, 22, 255);

    // 1. TOP HEADER (Height: 38px)
    Screen.draw_rectangle(0, 0, 960, 38, PANEL_BG);
    Screen.draw_line(0, 38, 960, 38, BORDER_COLOR);

    drawText(16, 26, "FARSVERSE POCKET", 20, ACCENT_CYAN);
    drawText(200, 26, "v2.5", 14, TEXT_MUTED);

    // Host status indicator
    const hostStatusCol = hostOnline ? ACCENT_GREEN : ACCENT_AMBER;
    const hostStatusText = hostOnline ? "[ONLINE] " + hostIp + ":" + hostPort : "[OFFLINE] LOCAL DIGITAL TWIN";
    Screen.draw_fill_circle(4, 380, 20, hostStatusCol);
    drawText(392, 25, hostStatusText, 14, hostStatusCol);

    drawText(750, 25, "SOLVED: " + tasksResolved, 14, ACCENT_GREEN);
    drawText(850, 25, "T+" + simTime.toFixed(0) + "s", 14, TEXT_WHITE);

    // 2. LEFT PANE: 2D HOSPITAL DIGITAL TWIN MAP (X: 10 to 480, Y: 46 to 495)
    const mapW = 475;
    const mapH = 450;
    const mapOriginX = 245 + mapPanX;
    const mapOriginY = 270 + mapPanY;
    const mapScale = 4.2 * mapZoom;

    Screen.draw_rectangle(10, 46, mapW, mapH, PANEL_BG);
    Screen.draw_line(10, 46, 10 + mapW, 46, BORDER_COLOR);
    Screen.draw_line(10, 46 + mapH, 10 + mapW, 46 + mapH, BORDER_COLOR);
    Screen.draw_line(10, 46, 10, 46 + mapH, BORDER_COLOR);
    Screen.draw_line(10 + mapW, 46, 10 + mapW, 46 + mapH, BORDER_COLOR);

    // Map Header label
    drawText(20, 66, "HOSPITAL DIGITAL TWIN [960x544 CAD]", 13, ACCENT_CYAN);

    // Draw hallway connector corridors
    hospitalRooms.forEach(rm => {
        const rx = mapOriginX + rm.x * mapScale;
        const ry = mapOriginY - (rm.y + rm.h / 2) * mapScale;
        Screen.draw_line(mapOriginX, mapOriginY, rx, ry, rgba(30, 42, 58, 255));
    });

    // Draw hospital rooms
    hospitalRooms.forEach(rm => {
        const rx = mapOriginX + rm.x * mapScale;
        const ry = mapOriginY - (rm.y + rm.h) * mapScale;
        const rw = rm.w * mapScale;
        const rh = rm.h * mapScale;

        // Clip to map pane
        if (rx + rw > 12 && rx < 10 + mapW && ry + rh > 48 && ry < 46 + mapH) {
            Screen.draw_rectangle(rx, ry, rw, rh, rm.color);
            // Room outline
            Screen.draw_line(rx, ry, rx + rw, ry, BORDER_COLOR);
            Screen.draw_line(rx + rw, ry, rx + rw, ry + rh, BORDER_COLOR);
            Screen.draw_line(rx + rw, ry + rh, rx, ry + rh, BORDER_COLOR);
            Screen.draw_line(rx, ry + rh, rx, ry, BORDER_COLOR);

            if (rw > 30) {
                drawText(rx + 4, ry + 14, rm.name, 10, TEXT_MUTED);
            }
        }
    });

    // Draw Robot AMRs on Map
    robots.forEach((r, idx) => {
        const bx = mapOriginX + r.x * mapScale;
        const by = mapOriginY - r.y * mapScale;

        if (bx > 12 && bx < 10 + mapW && by > 48 && by < 46 + mapH) {
            const isSelected = idx === selectedRobotIdx;
            // Pulsing selection halo
            if (isSelected) {
                Screen.draw_fill_circle(10, bx, by, rgba(0, 229, 255, 60));
                Screen.draw_fill_circle(7, bx, by, rgba(0, 229, 255, 120));
            }
            // Robot chassis
            Screen.draw_fill_circle(5, bx, by, r.color);
            drawText(bx + 7, by + 4, r.id, 10, isSelected ? ACCENT_CYAN : TEXT_WHITE);
        }
    });

    // 3. RIGHT PANE: TELEMETRY & ROBOT INSPECTOR (X: 495 to 950)
    const curBot = robots[selectedRobotIdx];
    const paneX = 495;
    const paneW = 455;

    // 3A. Selected Robot Telemetry Card (Y: 46 to 195)
    Screen.draw_rectangle(paneX, 46, paneW, 150, PANEL_BG);
    Screen.draw_line(paneX, 46, paneX + paneW, 46, BORDER_ACTIVE);
    Screen.draw_line(paneX, 196, paneX + paneW, 196, BORDER_COLOR);
    Screen.draw_line(paneX, 46, paneX, 196, BORDER_COLOR);
    Screen.draw_line(paneX + paneW, 46, paneX + paneW, 196, BORDER_COLOR);

    drawText(paneX + 14, 70, curBot.id + " -- " + curBot.name, 18, TEXT_WHITE);
    // State badge
    const stateCol = (curBot.state === "NAVIGATING" || curBot.state === "DELIVERING") ? ACCENT_GREEN : (curBot.state === "PATROLLING" ? ACCENT_CYAN : ACCENT_AMBER);
    drawText(paneX + 330, 70, "[" + curBot.state + "]", 14, stateCol);

    // Battery bar
    drawText(paneX + 14, 96, "BATTERY:", 12, TEXT_MUTED);
    const batW = 200;
    const batFill = Math.floor((curBot.battery / 100.0) * batW);
    Screen.draw_rectangle(paneX + 75, 86, batW, 12, rgba(30, 40, 50, 255));
    Screen.draw_rectangle(paneX + 75, 86, batFill, 12, curBot.battery > 30 ? ACCENT_GREEN : ACCENT_RED);
    drawText(paneX + 285, 96, curBot.battery.toFixed(1) + "%", 12, TEXT_WHITE);

    // Position & Velocity Telemetry
    drawText(paneX + 14, 122, "COORDINATES:", 12, TEXT_MUTED);
    drawText(paneX + 110, 122, "X: " + curBot.x.toFixed(1) + "m   Y: " + curBot.y.toFixed(1) + "m", 12, TEXT_WHITE);

    drawText(paneX + 14, 144, "SPEED / NODE:", 12, TEXT_MUTED);
    drawText(paneX + 110, 144, curBot.speed.toFixed(2) + " m/s  |  " + curBot.node, 12, ACCENT_CYAN);

    drawText(paneX + 14, 166, "ACTIVE TASK:", 12, TEXT_MUTED);
    drawText(paneX + 110, 166, curBot.mission, 12, TEXT_WHITE);

    // Quick AMR selector tabs (L1 / R1)
    robots.forEach((r, idx) => {
        const tabX = paneX + 14 + idx * 85;
        const isSel = idx === selectedRobotIdx;
        Screen.draw_rectangle(tabX, 175, 78, 16, isSel ? rgba(0, 229, 255, 60) : PANEL_ALT);
        drawText(tabX + 12, 187, r.id, 11, isSel ? ACCENT_CYAN : TEXT_MUTED);
    });

    // 3B. Mission Assignment Menu (Y: 204 to 380)
    Screen.draw_rectangle(paneX, 204, paneW, 176, PANEL_BG);
    Screen.draw_line(paneX, 204, paneX + paneW, 204, BORDER_COLOR);
    Screen.draw_line(paneX, 380, paneX + paneW, 380, BORDER_COLOR);
    Screen.draw_line(paneX, 204, paneX, 380, BORDER_COLOR);
    Screen.draw_line(paneX + paneW, 204, paneX + paneW, 380, BORDER_COLOR);

    drawText(paneX + 14, 224, "MISSION ASSIGNMENT [D-PAD UP/DOWN, CROSS]", 13, ACCENT_CYAN);

    // Show up to 5 missions around selected
    const startIdx = Math.max(0, Math.min(selectedMissionIdx - 2, availableMissions.length - 5));
    for (let i = 0; i < 5; i++) {
        const mIdx = startIdx + i;
        if (mIdx >= availableMissions.length) break;
        const m = availableMissions[mIdx];
        const itemY = 236 + i * 27;
        const isHighlight = mIdx === selectedMissionIdx;

        if (isHighlight) {
            Screen.draw_rectangle(paneX + 8, itemY, paneW - 16, 24, rgba(0, 229, 255, 30));
            Screen.draw_rectangle(paneX + 8, itemY, 3, 24, ACCENT_CYAN);
        }

        const prioCol = (m.priority === "CRITICAL" || m.priority === "URGENT") ? ACCENT_RED : (m.priority === "HIGH" ? ACCENT_AMBER : (m.priority === "AI" ? ACCENT_PURPLE : ACCENT_GREEN));
        drawText(paneX + 16, itemY + 17, isHighlight ? "> " + m.title : "  " + m.title, 12, isHighlight ? TEXT_WHITE : TEXT_MUTED);
        drawText(paneX + 370, itemY + 17, "[" + m.priority + "]", 10, prioCol);
    }

    // 3C. Task History & Event Log (Y: 388 to 495)
    Screen.draw_rectangle(paneX, 388, paneW, 108, PANEL_BG);
    Screen.draw_line(paneX, 388, paneX + paneW, 388, BORDER_COLOR);
    Screen.draw_line(paneX, 496, paneX + paneW, 496, BORDER_COLOR);
    Screen.draw_line(paneX, 388, paneX, 496, BORDER_COLOR);
    Screen.draw_line(paneX + paneW, 388, paneX + paneW, 496, BORDER_COLOR);

    drawText(paneX + 14, 406, "EVENT LOG & TELEMETRY STREAM", 12, ACCENT_CYAN);
    for (let i = 0; i < Math.min(4, logHistory.length); i++) {
        drawText(paneX + 14, 426 + i * 16, logHistory[i], 11, i === 0 ? TEXT_WHITE : TEXT_DIM);
    }

    // 4. BOTTOM CONTROLLER ACTION BAR (Y: 504 to 544)
    Screen.draw_rectangle(0, 504, 960, 40, rgba(14, 18, 26, 255));
    Screen.draw_line(0, 504, 960, 504, BORDER_COLOR);

    drawText(20, 528, "[L1/R1] Robot", 13, TEXT_WHITE);
    drawText(150, 528, "[D-Pad] Mission", 13, TEXT_WHITE);
    drawText(290, 528, "[X] Assign", 13, ACCENT_GREEN);
    drawText(390, 528, "[O] Dock", 13, ACCENT_CYAN);
    drawText(490, 528, "[] E-Stop", 13, ACCENT_RED);
    drawText(590, 528, "[/\] Host Link", 13, ACCENT_AMBER);
    drawText(720, 528, "[START] Sync", 13, TEXT_WHITE);
    drawText(840, 528, "[SELECT] Map", 13, TEXT_WHITE);

    Screen.end_drawing();
    Screen.swap_buffers();
}

// -----------------------------------------------------------------------------
// MAIN GAME LOOP (Runs at 60 FPS)
// -----------------------------------------------------------------------------
let lastFrame = Date.now();

const mainLoop = os.setInterval(() => {
    if (!running) {
        os.clearInterval(mainLoop);
        return;
    }

    const now = Date.now();
    const dt = Math.min(0.05, Math.max(0.001, (now - lastFrame) / 1000));
    lastFrame = now;

    handleInput();
    updateLocalSimulation(dt);
    render();
}, 16);
