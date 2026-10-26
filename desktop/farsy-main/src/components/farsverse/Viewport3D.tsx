"use client";

import React, { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { FARSverseSnapshot } from "@/lib/farsverse-api";

interface Viewport3DProps {
  snapshot: FARSverseSnapshot | null;
  selectedEntity: { type: string; id: string } | null;
  onSelectEntity: (type: string, id: string) => void;
  cameraMode: "angled" | "topdown" | "follow";
  showPaths: boolean;
  showGrid: boolean;
  showLabels: boolean;
}

interface RobotMeshEntry {
  group: THREE.Group;
  currentPos: THREE.Vector3;
  targetPos: THREE.Vector3;
  currentRotY: number;
  targetRotY: number;
  lidarPuck: THREE.Mesh;
  laserFan: THREE.Mesh;
  haloRingMat: THREE.MeshBasicMaterial;
  chassisMesh: THREE.Mesh;
  selBracket: THREE.Group;
  labelSprite: THREE.Sprite;
  labelCanvas: HTMLCanvasElement;
  labelCtx: CanvasRenderingContext2D;
  labelTex: THREE.CanvasTexture;
  lastBattery: number;
  lastState: string;
  pathLine: THREE.Line;
  pin: THREE.Mesh;
}

interface HumanMeshEntry {
  group: THREE.Group;
  currentPos: THREE.Vector3;
  targetPos: THREE.Vector3;
  avatarBody: THREE.Mesh;
  beacon: THREE.Mesh;
  bodyMat: THREE.MeshStandardMaterial;
  lastNeedsHelp: boolean;
  phaseOffset: number;
}

export function Viewport3D({
  snapshot,
  selectedEntity,
  onSelectEntity,
  cameraMode,
  showPaths,
  showGrid,
  showLabels,
}: Viewport3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);

  // Groups
  const architecturalGroupRef = useRef<THREE.Group>(new THREE.Group());
  const corridorsGroupRef = useRef<THREE.Group>(new THREE.Group());
  const obstaclesGroupRef = useRef<THREE.Group>(new THREE.Group());
  const robotsGroupRef = useRef<THREE.Group>(new THREE.Group());
  const humansGroupRef = useRef<THREE.Group>(new THREE.Group());
  const pathsGroupRef = useRef<THREE.Group>(new THREE.Group());
  const gridHelperRef = useRef<THREE.GridHelper | null>(null);

  // Persistent Object Pools for Liquid-Smooth 60 FPS
  const robotMeshMap = useRef<Map<string, RobotMeshEntry>>(new Map());
  const humanMeshMap = useRef<Map<string, HumanMeshEntry>>(new Map());

  // Dynamic state refs for continuous render loop
  const snapshotRef = useRef(snapshot);
  snapshotRef.current = snapshot;
  const selectedEntityRef = useRef(selectedEntity);
  selectedEntityRef.current = selectedEntity;
  const cameraModeRef = useRef(cameraMode);
  cameraModeRef.current = cameraMode;
  const showPathsRef = useRef(showPaths);
  showPathsRef.current = showPaths;
  const showLabelsRef = useRef(showLabels);
  showLabelsRef.current = showLabels;
  const onSelectEntityRef = useRef(onSelectEntity);
  onSelectEntityRef.current = onSelectEntity;
  const lastCamModeRef = useRef<string>(cameraMode);

  // Viewport Telemetry State
  const [fps, setFps] = useState(60);
  const [navMode, setNavMode] = useState<"orbit" | "pan">("orbit");

  // Sync Navigation Mode (Rotate vs Pan)
  useEffect(() => {
    if (!controlsRef.current) return;
    if (navMode === "pan") {
      controlsRef.current.mouseButtons.LEFT = THREE.MOUSE.PAN;
      if (rendererRef.current) rendererRef.current.domElement.style.cursor = "grab";
    } else {
      controlsRef.current.mouseButtons.LEFT = THREE.MOUSE.ROTATE;
    }
  }, [navMode]);

  const handleZoom = (direction: "in" | "out") => {
    if (!cameraRef.current || !controlsRef.current) return;
    const factor = direction === "in" ? 0.8 : 1.25;
    const offset = cameraRef.current.position.clone().sub(controlsRef.current.target);
    offset.multiplyScalar(factor);
    cameraRef.current.position.copy(controlsRef.current.target).add(offset);
  };

  const handlePan = (dx: number, dz: number) => {
    if (!cameraRef.current || !controlsRef.current) return;
    controlsRef.current.target.x += dx;
    controlsRef.current.target.z += dz;
    cameraRef.current.position.x += dx;
    cameraRef.current.position.z += dz;
  };

  const handleResetView = () => {
    if (!cameraRef.current || !controlsRef.current) return;
    controlsRef.current.target.set(0, 0, 0);
    if (cameraMode === "topdown") {
      cameraRef.current.position.set(0, 75, 0.01);
    } else {
      cameraRef.current.position.set(0, 56, 48);
    }
  };

  // ------------------------------------------------------------------
  // 1. Initialize NVIDIA Omniverse Three.js Studio Scene
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!containerRef.current) return;
    const container = containerRef.current;
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0e1117); // Omniverse titanium slate
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(42, width / height, 0.5, 400);
    camera.position.set(0, 56, 48);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      powerPreference: "high-performance",
    });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.15;
    renderer.domElement.style.touchAction = "none";
    renderer.domElement.style.outline = "none";
    renderer.domElement.style.cursor = "grab";
    container.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = true; // Crucial for natural, fluid 2D/3D panning
    controls.enableZoom = true;
    controls.zoomSpeed = 1.2;
    controls.enableRotate = true;
    controls.rotateSpeed = 0.85;
    controls.enablePan = true;
    controls.panSpeed = 1.1;
    controls.minDistance = 4;
    controls.maxDistance = 250;
    controls.maxPolarAngle = Math.PI / 2.02;
    controls.target.set(0, 0, 0);
    // Left: Rotate, Right: Pan, Middle: Pan
    controls.mouseButtons = {
      LEFT: THREE.MOUSE.ROTATE,
      MIDDLE: THREE.MOUSE.PAN,
      RIGHT: THREE.MOUSE.PAN,
    };
    controlsRef.current = controls;

    // Omniverse Studio Lighting Setup: Clean, sharp PBR lighting
    const ambientLight = new THREE.AmbientLight(0xffffff, 1.4);
    scene.add(ambientLight);

    // Primary High Key Light
    const keyLight = new THREE.DirectionalLight(0xf8fafc, 1.3);
    keyLight.position.set(45, 75, 30);
    scene.add(keyLight);

    // Secondary Cyan Industrial Fill Light
    const fillLight = new THREE.DirectionalLight(0x93c5fd, 0.7);
    fillLight.position.set(-45, 50, -35);
    scene.add(fillLight);

    // Subtle Omniverse Ground Bounce Light
    const groundBounce = new THREE.HemisphereLight(0x1e293b, 0x0f172a, 0.6);
    scene.add(groundBounce);

    // Monolithic Industrial Epoxy Floor
    const floorGeo = new THREE.PlaneGeometry(180, 180);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x11151e,
      roughness: 0.35,
      metalness: 0.25,
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    scene.add(floor);

    // High-Tech Industrial Grid
    const grid = new THREE.GridHelper(160, 80, 0x334155, 0x1e293b);
    grid.position.y = 0.015;
    scene.add(grid);
    gridHelperRef.current = grid;

    // Add Scene Layers
    scene.add(architecturalGroupRef.current);
    scene.add(corridorsGroupRef.current);
    scene.add(obstaclesGroupRef.current);
    scene.add(pathsGroupRef.current);
    scene.add(robotsGroupRef.current);
    scene.add(humansGroupRef.current);

    // Raycaster for entity selection (executed ONLY on distinct clicks, never on drags!)
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let downPos = { x: 0, y: 0, time: 0 };

    const handlePointerDown = (event: MouseEvent) => {
      downPos = { x: event.clientX, y: event.clientY, time: performance.now() };
      renderer.domElement.style.cursor = "grabbing";
    };

    const handlePointerUp = (event: MouseEvent) => {
      renderer.domElement.style.cursor = "grab";
      const dx = event.clientX - downPos.x;
      const dy = event.clientY - downPos.y;
      const dist = Math.hypot(dx, dy);
      const dt = performance.now() - downPos.time;

      // Only perform entity selection if user CLICKED without dragging (> 4px is a pan/orbit)
      if (dist >= 5 || dt > 450 || event.button !== 0) return;

      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);

      // 1. Check robots
      const robotHits = raycaster.intersectObjects(robotsGroupRef.current.children, true);
      if (robotHits.length > 0) {
        let cur: THREE.Object3D | null = robotHits[0].object;
        while (cur && !cur.userData?.robotId) cur = cur.parent;
        if (cur?.userData?.robotId) {
          onSelectEntityRef.current("robot", cur.userData.robotId);
          return;
        }
      }

      // 2. Check humans
      const humanHits = raycaster.intersectObjects(humansGroupRef.current.children, true);
      if (humanHits.length > 0) {
        let cur: THREE.Object3D | null = humanHits[0].object;
        while (cur && !cur.userData?.humanId) cur = cur.parent;
        if (cur?.userData?.humanId) {
          onSelectEntityRef.current("human", cur.userData.humanId);
          return;
        }
      }

      // 3. Check obstacles
      const obsHits = raycaster.intersectObjects(obstaclesGroupRef.current.children, true);
      if (obsHits.length > 0) {
        let cur: THREE.Object3D | null = obsHits[0].object;
        while (cur && !cur.userData?.obstacleId) cur = cur.parent;
        if (cur?.userData?.obstacleId) {
          onSelectEntityRef.current("obstacle", cur.userData.obstacleId);
          return;
        }
      }

      // 4. Check rooms
      const roomHits = raycaster.intersectObjects(architecturalGroupRef.current.children, true);
      if (roomHits.length > 0) {
        let cur: THREE.Object3D | null = roomHits[0].object;
        while (cur && !cur.userData?.roomId) cur = cur.parent;
        if (cur?.userData?.roomId) {
          onSelectEntityRef.current("room", cur.userData.roomId);
          return;
        }
      }
    };

    renderer.domElement.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("pointerup", handlePointerUp);

    // Resize Handler
    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width: w, height: h } = entry.contentRect;
        if (w > 0 && h > 0) {
          camera.aspect = w / h;
          camera.updateProjectionMatrix();
          renderer.setSize(w, h);
        }
      }
    });
    resizeObserver.observe(container);

    // ------------------------------------------------------------------
    // Continuous 60 FPS Animation & Motion Interpolation Loop
    // ------------------------------------------------------------------
    let animId: number;
    let lastTime = performance.now();
    let frameCount = 0;
    let lastFpsUpdate = performance.now();

    const animate = () => {
      animId = requestAnimationFrame(animate);
      const now = performance.now();
      const time = now * 0.001;

      // FPS counter
      frameCount++;
      if (now - lastFpsUpdate >= 1000) {
        setFps(frameCount);
        frameCount = 0;
        lastFpsUpdate = now;
      }

      // 1. Butter-Smooth Robot Position & Orientation Interpolation
      const posLerp = 0.20;
      const rotLerp = 0.22;
      for (const entry of robotMeshMap.current.values()) {
        entry.group.position.lerp(entry.targetPos, posLerp);

        // Shortest-angle spherical rotation lerp
        let dRot = entry.targetRotY - entry.group.rotation.y;
        while (dRot < -Math.PI) dRot += Math.PI * 2;
        while (dRot > Math.PI) dRot -= Math.PI * 2;
        entry.group.rotation.y += dRot * rotLerp;

        // Spin real 3D LiDAR puck at 600 RPM
        if (entry.lidarPuck) {
          entry.lidarPuck.rotation.y += 0.14;
        }
        if (entry.laserFan) {
          entry.laserFan.rotation.y += 0.14;
        }
      }

      // 2. Smooth Human Walking & Idle Animation
      for (const entry of humanMeshMap.current.values()) {
        entry.group.position.lerp(entry.targetPos, 0.16);

        // Subtle biological idle breathing
        if (entry.avatarBody) {
          entry.avatarBody.position.y = 0.65 + Math.sin(time * 2.5 + entry.phaseOffset) * 0.015;
        }
      }

      // 3. Camera Follow Mode Tracking
      if (cameraModeRef.current === "follow" && selectedEntityRef.current?.type === "robot") {
        const selId = selectedEntityRef.current.id;
        const targetRobot = snapshotRef.current?.robots.find((r) => r.id === selId);
        if (targetRobot) {
          const targetPos = new THREE.Vector3(targetRobot.x, 0, targetRobot.z);
          controls.target.lerp(targetPos, 0.08);
          const desiredCamPos = new THREE.Vector3(targetRobot.x + 9, 11, targetRobot.z + 9);
          camera.position.lerp(desiredCamPos, 0.05);
        }
      }

      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(animId);
      resizeObserver.disconnect();
      renderer.domElement.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("pointerup", handlePointerUp);
      renderer.dispose();
      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []); // Initialize scene EXACTLY ONCE: never remount or reset camera on re-renders

  // ------------------------------------------------------------------
  // 2. Camera Presets (ONLY trigger if cameraMode actually changed)
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!cameraRef.current || !controlsRef.current) return;
    if (lastCamModeRef.current === cameraMode) return;
    lastCamModeRef.current = cameraMode;

    const camera = cameraRef.current;
    const controls = controlsRef.current;

    if (cameraMode === "angled") {
      camera.position.set(0, 56, 48);
      controls.target.set(0, 0, 0);
    } else if (cameraMode === "topdown") {
      camera.position.set(0, 75, 0.01);
      controls.target.set(0, 0, 0);
    }
  }, [cameraMode]);

  // 3. Grid Toggle
  useEffect(() => {
    if (gridHelperRef.current) {
      gridHelperRef.current.visible = showGrid;
    }
  }, [showGrid]);

  // ------------------------------------------------------------------
  // 4. Build Unified Omniverse Architectural Floorplan (Once)
  // ------------------------------------------------------------------
  const builtWorldRef = useRef<string>("");
  useEffect(() => {
    if (!snapshot?.world || !sceneRef.current) return;
    const worldKey = `${snapshot.world.name}_${snapshot.world.rooms.length}`;
    if (builtWorldRef.current === worldKey) return;
    builtWorldRef.current = worldKey;

    const archGroup = architecturalGroupRef.current;
    const corrGroup = corridorsGroupRef.current;

    while (archGroup.children.length > 0) archGroup.remove(archGroup.children[0]);
    while (corrGroup.children.length > 0) corrGroup.remove(corrGroup.children[0]);

    // Architectural Materials
    const wallHeight = 1.6;
    const wallMat = new THREE.MeshStandardMaterial({
      color: 0x1f2532,
      roughness: 0.35,
      metalness: 0.3,
    });
    const aluminumCapMat = new THREE.MeshStandardMaterial({
      color: 0x64748b,
      roughness: 0.2,
      metalness: 0.7,
    });
    const glassMat = new THREE.MeshStandardMaterial({
      color: 0x38bdf8,
      roughness: 0.1,
      metalness: 0.1,
      transparent: true,
      opacity: 0.28,
    });

    // Central Hallway Painted Navigation Guidelines
    const hallwayPadMat = new THREE.MeshStandardMaterial({
      color: 0x161b26,
      roughness: 0.4,
      metalness: 0.2,
    });
    // Main spine corridor
    const spine = new THREE.Mesh(new THREE.BoxGeometry(7, 0.02, 60), hallwayPadMat);
    spine.position.set(0, 0.018, 0);
    corrGroup.add(spine);

    // Cross corridor
    const cross = new THREE.Mesh(new THREE.BoxGeometry(65, 0.02, 6), hallwayPadMat);
    cross.position.set(0, 0.018, 0);
    corrGroup.add(cross);

    // Painted Center Line (Subtle white runway dashes)
    const dashMat = new THREE.MeshBasicMaterial({ color: 0x475569 });
    for (let z = -28; z <= 28; z += 3) {
      const dash = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.025, 1.4), dashMat);
      dash.position.set(0, 0.02, z);
      corrGroup.add(dash);
    }

    // Build Interconnected Rooms
    snapshot.world.rooms.forEach((room) => {
      const roomGroup = new THREE.Group();
      roomGroup.userData = { roomId: room.id, roomName: room.name };

      // Room Floor Pad with Chamfered Border
      let floorColor = 0x181e2b; // Slate for patient rooms
      if (room.type === "icu") floorColor = 0x132328; // Medical Teal
      else if (room.type === "pharmacy") floorColor = 0x14271f; // Clean Emerald
      else if (room.type === "emergency") floorColor = 0x2b181b; // High-alert Crimson
      else if (room.type === "dock") floorColor = 0x291d12; // Amber Dock

      const padGeo = new THREE.BoxGeometry(room.width, 0.06, room.depth);
      const padMat = new THREE.MeshStandardMaterial({
        color: floorColor,
        roughness: 0.45,
        metalness: 0.2,
      });
      const pad = new THREE.Mesh(padGeo, padMat);
      pad.position.set(room.x, 0.03, room.z);
      roomGroup.add(pad);

      // Hazard Stripes for Charging Dock
      if (room.type === "dock") {
        const hazardMat = new THREE.MeshBasicMaterial({ color: 0xf59e0b });
        for (let i = -room.width / 2 + 1; i < room.width / 2; i += 2) {
          const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.35, 0.07, room.depth * 0.9), hazardMat);
          stripe.rotation.y = Math.PI / 4;
          stripe.position.set(room.x + i, 0.04, room.z);
          roomGroup.add(stripe);
        }

        // 5 Industrial Inductive Charging Pads
        for (let p = -2; p <= 2; p++) {
          const dockPad = new THREE.Mesh(
            new THREE.CylinderGeometry(0.9, 0.9, 0.04, 16),
            new THREE.MeshStandardMaterial({
              color: 0x0284c7,
              emissive: 0x0369a1,
              roughness: 0.3,
            })
          );
          dockPad.position.set(room.x + p * 1.8, 0.05, room.z);
          roomGroup.add(dockPad);
        }
      }

      // Walls with Precision Aluminum Caps
      const createArchitecturalWall = (w: number, h: number, d: number, x: number, y: number, z: number) => {
        const wall = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), wallMat);
        wall.position.set(x, y, z);
        roomGroup.add(wall);

        // Aluminum Cap Rail
        const cap = new THREE.Mesh(new THREE.BoxGeometry(w + 0.04, 0.05, d + 0.04), aluminumCapMat);
        cap.position.set(x, y + h / 2 + 0.025, z);
        roomGroup.add(cap);
      };

      // North Wall
      createArchitecturalWall(room.width, wallHeight, 0.22, room.x, wallHeight / 2, room.z + room.depth / 2);

      // South Wall with Entryway
      const doorwayWidth = 2.4;
      const sideWallWidth = (room.width - doorwayWidth) / 2;
      createArchitecturalWall(sideWallWidth, wallHeight, 0.22, room.x - room.width / 2 + sideWallWidth / 2, wallHeight / 2, room.z - room.depth / 2);
      createArchitecturalWall(sideWallWidth, wallHeight, 0.22, room.x + room.width / 2 - sideWallWidth / 2, wallHeight / 2, room.z - room.depth / 2);

      // East & West Walls
      createArchitecturalWall(0.22, wallHeight, room.depth, room.x + room.width / 2, wallHeight / 2, room.z);
      createArchitecturalWall(0.22, wallHeight, room.depth, room.x - room.width / 2, wallHeight / 2, room.z);

      // Glass Vision Partition
      if (room.type === "icu" || room.type === "pharmacy" || room.type === "reception") {
        const glass = new THREE.Mesh(new THREE.BoxGeometry(doorwayWidth - 0.2, wallHeight * 0.7, 0.05), glassMat);
        glass.position.set(room.x, wallHeight * 0.45, room.z - room.depth / 2);
        roomGroup.add(glass);
      }

      // Patient Room Bed & Vital Monitor Screen
      if (room.type === "patient_room") {
        const bedFrame = new THREE.Mesh(
          new THREE.BoxGeometry(1.4, 0.45, 2.3),
          new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.5, roughness: 0.3 })
        );
        bedFrame.position.set(room.x + 0.5, 0.22, room.z);
        roomGroup.add(bedFrame);

        const mattress = new THREE.Mesh(
          new THREE.BoxGeometry(1.3, 0.2, 2.2),
          new THREE.MeshStandardMaterial({ color: 0x0284c7, roughness: 0.4 })
        );
        mattress.position.set(room.x + 0.5, 0.45, room.z);
        roomGroup.add(mattress);

        const pillow = new THREE.Mesh(
          new THREE.BoxGeometry(1.0, 0.12, 0.55),
          new THREE.MeshStandardMaterial({ color: 0xf8fafc, roughness: 0.8 })
        );
        pillow.position.set(room.x + 0.5, 0.6, room.z + 0.8);
        roomGroup.add(pillow);

        // Medical vital screen
        const monitor = new THREE.Mesh(
          new THREE.BoxGeometry(0.35, 0.25, 0.05),
          new THREE.MeshStandardMaterial({ color: 0x10b981, emissive: 0x064e3b })
        );
        monitor.position.set(room.x - 0.5, 1.1, room.z + 0.9);
        roomGroup.add(monitor);
      }

      // Omniverse Architectural Room Label Signage
      const label = createOmniverseRoomSign(room.name || room.id);
      label.position.set(room.x, 2.4, room.z);
      label.scale.set(4.0, 1.6, 1);
      roomGroup.add(label);

      archGroup.add(roomGroup);
    });
  }, [snapshot?.world]);

  // ------------------------------------------------------------------
  // 5. Dynamic Obstacles
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!snapshot?.world?.obstacles) return;
    const group = obstaclesGroupRef.current;
    while (group.children.length > 0) group.remove(group.children[0]);

    snapshot.world.obstacles.forEach((obs) => {
      const obsGroup = new THREE.Group();
      obsGroup.userData = { obstacleId: obs.id, name: obs.name };

      const isBlocked = obs.active;
      // High-tech industrial trolley / barrier
      const mesh = new THREE.Mesh(
        new THREE.BoxGeometry(obs.width, 0.85, obs.depth),
        new THREE.MeshStandardMaterial({
          color: isBlocked ? 0xd97706 : 0x334155,
          metalness: 0.6,
          roughness: 0.3,
        })
      );
      mesh.position.set(obs.x, 0.42, obs.z);
      obsGroup.add(mesh);

      // Warning Strobe
      if (isBlocked) {
        const strobe = new THREE.Mesh(
          new THREE.CylinderGeometry(0.2, 0.2, 0.3, 12),
          new THREE.MeshBasicMaterial({ color: 0xf59e0b })
        );
        strobe.position.set(obs.x, 1.0, obs.z);
        obsGroup.add(strobe);
      }

      group.add(obsGroup);
    });
  }, [snapshot?.world?.obstacles]);

  // ------------------------------------------------------------------
  // 6. NVIDIA Isaac AMR / Nova Carter Robot Pool (Persistent 60 FPS)
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!snapshot?.robots) return;
    const robotsGroup = robotsGroupRef.current;
    const pathsGroup = pathsGroupRef.current;
    const map = robotMeshMap.current;
    const currentRobotIds = new Set(snapshot.robots.map((r) => r.id));

    // Remove deleted robots
    for (const [id, entry] of map.entries()) {
      if (!currentRobotIds.has(id)) {
        robotsGroup.remove(entry.group);
        pathsGroup.remove(entry.pathLine);
        pathsGroup.remove(entry.pin);
        map.delete(id);
      }
    }

    snapshot.robots.forEach((robot) => {
      let entry = map.get(robot.id);
      const isSelected = selectedEntity?.type === "robot" && selectedEntity?.id === robot.id;

      // Status Colors
      let haloColorHex = 0x76b900; // NVIDIA Isaac Green
      if (robot.state === "NAVIGATING") haloColorHex = 0x06b6d4; // Cyan
      else if (robot.state === "CHARGING") haloColorHex = 0xf59e0b; // Amber
      else if (robot.state === "ERROR" || robot.battery < 15) haloColorHex = 0xef4444; // Red
      else if (robot.state === "ASSISTING" || robot.state === "DELIVERING") haloColorHex = 0xa855f7; // Purple

      // Build Nova Carter Robot Mesh Once
      if (!entry) {
        const rGroup = new THREE.Group();
        rGroup.userData = { robotId: robot.id, name: robot.name };

        // 1. Lower Drive Base Bumper (Chamfered stealth black)
        const chassisMat = new THREE.MeshStandardMaterial({
          color: 0x181a20,
          metalness: 0.65,
          roughness: 0.28,
        });
        const chassisMesh = new THREE.Mesh(
          new THREE.CylinderGeometry(0.72, 0.78, 0.38, 24),
          chassisMat
        );
        chassisMesh.position.y = 0.22;
        rGroup.add(chassisMesh);

        // 2. Rubber Drive Wheels & Metallic Hubs (Left & Right)
        const wheelGeo = new THREE.CylinderGeometry(0.24, 0.24, 0.12, 16);
        const wheelMat = new THREE.MeshStandardMaterial({ color: 0x0d0f12, roughness: 0.8 });
        const hubMat = new THREE.MeshStandardMaterial({ color: 0x71717a, metalness: 0.8, roughness: 0.2 });

        [-0.72, 0.72].forEach((xSide) => {
          const wheel = new THREE.Mesh(wheelGeo, wheelMat);
          wheel.rotation.z = Math.PI / 2;
          wheel.position.set(xSide, 0.24, 0);
          rGroup.add(wheel);

          const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.12, 0.13, 12), hubMat);
          hub.rotation.z = Math.PI / 2;
          hub.position.set(xSide, 0.24, 0);
          rGroup.add(hub);
        });

        // 3. Perimeter Glowing LED Status Halo Ring
        const haloRingMat = new THREE.MeshBasicMaterial({ color: haloColorHex });
        const halo = new THREE.Mesh(new THREE.TorusGeometry(0.74, 0.04, 8, 28), haloRingMat);
        halo.rotation.x = Math.PI / 2;
        halo.position.y = 0.36;
        rGroup.add(halo);

        // 4. Upper Payload Deck Plate (Titanium Brushed Finish)
        const deck = new THREE.Mesh(
          new THREE.CylinderGeometry(0.66, 0.66, 0.12, 24),
          new THREE.MeshStandardMaterial({ color: 0x272b36, metalness: 0.7, roughness: 0.25 })
        );
        deck.position.y = 0.44;
        rGroup.add(deck);

        // 5. Elevated Sensor Tower
        const pylon = new THREE.Mesh(
          new THREE.BoxGeometry(0.18, 0.45, 0.18),
          new THREE.MeshStandardMaterial({ color: 0x090a0f, roughness: 0.3 })
        );
        pylon.position.set(0, 0.65, -0.22);
        rGroup.add(pylon);

        // 6. Spinning 3D LiDAR Scanner Dome (Velodyne style)
        const lidarPuck = new THREE.Mesh(
          new THREE.CylinderGeometry(0.16, 0.16, 0.22, 16),
          new THREE.MeshStandardMaterial({ color: 0x111827, metalness: 0.8, roughness: 0.2 })
        );
        lidarPuck.position.set(0, 0.94, -0.22);
        rGroup.add(lidarPuck);

        // 7. LiDAR Active Laser Scanner Fan Projection
        const laserFanGeo = new THREE.ConeGeometry(2.4, 0.02, 16, 1, false, -Math.PI / 4, Math.PI / 2);
        const laserFanMat = new THREE.MeshBasicMaterial({
          color: 0x76b900,
          transparent: true,
          opacity: 0.16,
          side: THREE.DoubleSide,
        });
        const laserFan = new THREE.Mesh(laserFanGeo, laserFanMat);
        laserFan.rotation.x = Math.PI / 2;
        laserFan.position.set(0, 0.12, 1.2);
        rGroup.add(laserFan);

        // 8. Front Stereo Depth Camera Bar (Intel RealSense / Nova)
        const cameraBar = new THREE.Mesh(
          new THREE.BoxGeometry(0.35, 0.08, 0.08),
          new THREE.MeshStandardMaterial({ color: 0x05070a, metalness: 0.8 })
        );
        cameraBar.position.set(0, 0.42, 0.66);
        rGroup.add(cameraBar);

        // 9. Emergency Stop Button (Rear Deck)
        const estop = new THREE.Mesh(
          new THREE.CylinderGeometry(0.06, 0.06, 0.05, 8),
          new THREE.MeshStandardMaterial({ color: 0xef4444, roughness: 0.3 })
        );
        estop.position.set(0.35, 0.52, -0.35);
        rGroup.add(estop);

        // 10. Omniverse Selection Bounding Cage / Target Bracket
        const selBracket = new THREE.Group();
        const selRing = new THREE.Mesh(
          new THREE.RingGeometry(1.05, 1.2, 32),
          new THREE.MeshBasicMaterial({ color: 0x76b900, side: THREE.DoubleSide })
        );
        selRing.rotation.x = -Math.PI / 2;
        selRing.position.y = 0.04;
        selBracket.add(selRing);
        selBracket.visible = false;
        rGroup.add(selBracket);

        // 11. Omniverse Holographic Floating HUD Label
        const labelCanvas = document.createElement("canvas");
        labelCanvas.width = 256;
        labelCanvas.height = 96;
        const labelCtx = labelCanvas.getContext("2d")!;
        const labelTex = new THREE.CanvasTexture(labelCanvas);
        const labelSprite = new THREE.Sprite(
          new THREE.SpriteMaterial({ map: labelTex, transparent: true })
        );
        labelSprite.position.set(0, 2.1, 0);
        labelSprite.scale.set(3.2, 1.2, 1);
        rGroup.add(labelSprite);

        // 12. Floor A* Navigation Route Line
        const pathLineMat = new THREE.LineBasicMaterial({
          color: haloColorHex,
          linewidth: 2,
          transparent: true,
          opacity: 0.85,
        });
        const pathLineGeo = new THREE.BufferGeometry();
        pathLineGeo.setFromPoints([new THREE.Vector3(0, 0, 0), new THREE.Vector3(0, 0, 0)]);
        const pathLine = new THREE.Line(pathLineGeo, pathLineMat);
        pathLine.visible = false;
        pathsGroup.add(pathLine);

        // Destination Pin
        const pin = new THREE.Mesh(
          new THREE.ConeGeometry(0.35, 0.7, 8),
          new THREE.MeshBasicMaterial({ color: haloColorHex })
        );
        pin.rotation.x = Math.PI;
        pin.visible = false;
        pathsGroup.add(pin);

        robotsGroup.add(rGroup);

        entry = {
          group: rGroup,
          currentPos: new THREE.Vector3(robot.x, 0, robot.z),
          targetPos: new THREE.Vector3(robot.x, 0, robot.z),
          currentRotY: THREE.MathUtils.degToRad(robot.rotation_y),
          targetRotY: THREE.MathUtils.degToRad(robot.rotation_y),
          lidarPuck,
          laserFan,
          haloRingMat,
          chassisMesh,
          selBracket,
          labelSprite,
          labelCanvas,
          labelCtx,
          labelTex,
          lastBattery: -1,
          lastState: "",
          pathLine,
          pin,
        };
        map.set(robot.id, entry);
      }

      // Smooth Target Updates (Interpolation happens at 60 FPS in animate loop)
      entry.targetPos.set(robot.x, 0, robot.z);
      entry.targetRotY = THREE.MathUtils.degToRad(robot.rotation_y);

      // Selection state
      entry.selBracket.visible = isSelected;

      // Color updates on state change
      if (entry.lastState !== robot.state) {
        entry.haloRingMat.color.setHex(haloColorHex);
        (entry.pathLine.material as THREE.LineBasicMaterial).color.setHex(haloColorHex);
        (entry.pin.material as THREE.MeshBasicMaterial).color.setHex(haloColorHex);
        entry.lastState = robot.state;
      }

      // Redraw label canvas only when battery value updates
      entry.labelSprite.visible = showLabels;
      const bat = Math.round(robot.battery);
      if (showLabels && (entry.lastBattery !== bat || entry.lastBattery === -1)) {
        renderOmniverseLabelCanvas(entry.labelCanvas, entry.labelCtx, robot.id, bat, robot.state);
        entry.labelTex.needsUpdate = true;
        entry.lastBattery = bat;
      }

      // Live Navigation Path Line
      if (showPaths && robot.waypoints && robot.waypoints.length > 0) {
        const points = [new THREE.Vector3(robot.x, 0.05, robot.z)];
        for (let i = robot.waypoint_index; i < robot.waypoints.length; i++) {
          points.push(new THREE.Vector3(robot.waypoints[i][0], 0.05, robot.waypoints[i][1]));
        }

        if (points.length >= 2) {
          entry.pathLine.geometry.setFromPoints(points);
          entry.pathLine.visible = true;

          const lastPt = points[points.length - 1];
          entry.pin.position.set(lastPt.x, 0.9, lastPt.z);
          entry.pin.visible = true;
        } else {
          entry.pathLine.visible = false;
          entry.pin.visible = false;
        }
      } else {
        entry.pathLine.visible = false;
        entry.pin.visible = false;
      }
    });
  }, [snapshot?.robots, selectedEntity, showPaths, showLabels]);

  // ------------------------------------------------------------------
  // 7. Omniverse Digital Twin Holographic Human Avatars
  // ------------------------------------------------------------------
  useEffect(() => {
    if (!snapshot?.humans) return;
    const humansGroup = humansGroupRef.current;
    const map = humanMeshMap.current;
    const currentHumanIds = new Set(snapshot.humans.map((h) => h.id));

    // Remove deleted humans
    for (const [id, entry] of map.entries()) {
      if (!currentHumanIds.has(id)) {
        humansGroup.remove(entry.group);
        map.delete(id);
      }
    }

    snapshot.humans.forEach((human, idx) => {
      let entry = map.get(human.id);
      const isSelected = selectedEntity?.type === "human" && selectedEntity?.id === human.id;

      if (!entry) {
        const hGroup = new THREE.Group();
        hGroup.userData = { humanId: human.id, name: human.name };

        // Role Color Accent
        let roleColor = 0x38bdf8; // Patient Blue
        if (human.agent_type === "nurse") roleColor = 0x0d9488; // Medical Teal
        else if (human.agent_type === "doctor") roleColor = 0xf8fafc; // Clinical White
        else if (human.agent_type === "visitor") roleColor = 0xa855f7; // Violet

        // Ground Locator Hologram Ring
        const groundRing = new THREE.Mesh(
          new THREE.RingGeometry(0.35, 0.42, 16),
          new THREE.MeshBasicMaterial({ color: roleColor, side: THREE.DoubleSide })
        );
        groundRing.rotation.x = -Math.PI / 2;
        groundRing.position.y = 0.02;
        hGroup.add(groundRing);

        // Holographic Mannequin Torso
        const bodyMat = new THREE.MeshStandardMaterial({
          color: roleColor,
          roughness: 0.35,
          metalness: 0.1,
          transparent: true,
          opacity: 0.85,
        });
        const avatarBody = new THREE.Mesh(new THREE.CapsuleGeometry(0.28, 0.72, 8, 16), bodyMat);
        avatarBody.position.y = 0.65;
        hGroup.add(avatarBody);

        // Head
        const head = new THREE.Mesh(
          new THREE.SphereGeometry(0.18, 12, 12),
          new THREE.MeshStandardMaterial({ color: 0xf1f5f9, roughness: 0.4 })
        );
        head.position.y = 1.32;
        hGroup.add(head);

        // Emergency Assistance Beacon
        const beacon = new THREE.Mesh(
          new THREE.SphereGeometry(0.2, 8, 8),
          new THREE.MeshBasicMaterial({ color: 0xef4444 })
        );
        beacon.position.y = 1.8;
        beacon.visible = false;
        hGroup.add(beacon);

        humansGroup.add(hGroup);

        entry = {
          group: hGroup,
          currentPos: new THREE.Vector3(human.x, 0, human.z),
          targetPos: new THREE.Vector3(human.x, 0, human.z),
          avatarBody,
          beacon,
          bodyMat,
          lastNeedsHelp: false,
          phaseOffset: idx * 0.7,
        };
        map.set(human.id, entry);
      }

      // Smooth target interpolation
      entry.targetPos.set(human.x, 0, human.z);

      // Selection Highlight
      if (isSelected) {
        entry.bodyMat.color.setHex(0x76b900); // NVIDIA Green for selection
      } else {
        let baseColor = 0x38bdf8;
        if (human.agent_type === "nurse") baseColor = 0x0d9488;
        else if (human.agent_type === "doctor") baseColor = 0xf8fafc;
        else if (human.agent_type === "visitor") baseColor = 0xa855f7;
        entry.bodyMat.color.setHex(baseColor);
      }

      if (entry.lastNeedsHelp !== human.needs_help) {
        entry.beacon.visible = human.needs_help;
        entry.lastNeedsHelp = human.needs_help;
      }
    });
  }, [snapshot?.humans, selectedEntity]);

  return (
    <div className="relative w-full h-full bg-[#0e1117] overflow-hidden select-none font-mono" ref={containerRef}>
      {/* ------------------------------------------------------------- */}
      {/* Top Left: Omniverse Camera & Stage HUD                        */}
      {/* ------------------------------------------------------------- */}
      <div className="absolute top-3 left-3 z-10 pointer-events-none flex flex-col gap-1.5">
        <div className="bg-[#141720]/85 backdrop-blur-md border border-white/10 px-3.5 py-1.5 rounded text-xs text-white flex items-center gap-2.5 shadow-xl">
          <div className="w-2.5 h-2.5 rounded-full bg-[#76b900] shadow-[0_0_8px_#76b900]" />
          <span className="font-bold tracking-wider text-[#76b900]">NVIDIA ISAAC SIM</span>
          <span className="text-white/20">|</span>
          <span className="text-white/80 uppercase">CAMERA: {cameraMode}</span>
          <span className="text-white/20">|</span>
          <span className="text-white/60">{snapshot?.world?.name || "Initializing..."}</span>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Top Right: Omniverse RTX Real-Time & 3D Orientation Gizmo     */}
      {/* ------------------------------------------------------------- */}
      <div className="absolute top-3 right-3 z-10 pointer-events-none flex flex-col items-end gap-1.5">
        <div className="bg-[#141720]/85 backdrop-blur-md border border-white/10 px-3 py-1.5 rounded text-[11px] text-white/70 flex items-center gap-2 shadow-xl">
          <span className="text-[#76b900] font-bold">RTX: REAL-TIME</span>
          <span className="text-white/20">|</span>
          <span>{fps} FPS</span>
          <span className="text-white/20">|</span>
          <span className="text-white/50">USD: /World</span>
        </div>

        {/* 3D Coordinate Axis Compass */}
        <div className="bg-[#141720]/80 backdrop-blur-sm border border-white/10 p-2 rounded flex items-center gap-2 text-[10px] text-white/60">
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-rose-500" />X</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-[#76b900]" />Y</span>
          <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-cyan-500" />Z</span>
        </div>
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Bottom Center: Omniverse Navigation Hotkey Helper             */}
      {/* ------------------------------------------------------------- */}
      <div className="absolute bottom-3 left-1/2 -translate-x-1/2 z-10 pointer-events-none text-[11px] text-white/40 bg-[#141720]/80 backdrop-blur-sm px-3.5 py-1 rounded-full border border-white/10 shadow-lg">
        Left-Drag: {navMode === "pan" ? "Pan" : "Orbit"} | Right-Drag: Pan | Scroll: Zoom | Click: USD Entity Inspect
      </div>

      {/* ------------------------------------------------------------- */}
      {/* Right Floating: On-Screen Navigation & Pan/Zoom Controls      */}
      {/* ------------------------------------------------------------- */}
      <div className="absolute right-4 bottom-12 z-20 flex flex-col items-center gap-1.5 bg-[#141720]/90 backdrop-blur-md border border-white/10 p-2 rounded-lg shadow-2xl">
        {/* Navigation Mode Switcher */}
        <div className="flex flex-col gap-1 w-full pb-1.5 border-b border-white/10">
          <button
            onClick={() => setNavMode("orbit")}
            title="Orbit (Rotate 3D View)"
            className={`px-2 py-1 rounded text-[10px] font-bold flex items-center justify-center gap-1 transition-all ${
              navMode === "orbit"
                ? "bg-[#76b900] text-black shadow-md shadow-[#76b900]/30"
                : "text-white/60 hover:text-white hover:bg-white/10"
            }`}
          >
            <span>🔄 Rotate</span>
          </button>
          <button
            onClick={() => setNavMode("pan")}
            title="Pan (Move Across Floor with Left-Click Drag)"
            className={`px-2 py-1 rounded text-[10px] font-bold flex items-center justify-center gap-1 transition-all ${
              navMode === "pan"
                ? "bg-[#76b900] text-black shadow-md shadow-[#76b900]/30"
                : "text-white/60 hover:text-white hover:bg-white/10"
            }`}
          >
            <span>✋ Pan</span>
          </button>
        </div>

        {/* Pan Directional Pad */}
        <div className="grid grid-cols-3 gap-1 py-1">
          <div />
          <button
            onClick={() => handlePan(0, -6)}
            title="Pan North (Forward)"
            className="w-7 h-7 bg-white/5 hover:bg-[#76b900]/20 hover:text-[#76b900] rounded flex items-center justify-center text-xs text-white/70 border border-white/10 transition-all active:scale-95"
          >
            ▲
          </button>
          <div />
          <button
            onClick={() => handlePan(-6, 0)}
            title="Pan West (Left)"
            className="w-7 h-7 bg-white/5 hover:bg-[#76b900]/20 hover:text-[#76b900] rounded flex items-center justify-center text-xs text-white/70 border border-white/10 transition-all active:scale-95"
          >
            ◀
          </button>
          <button
            onClick={handleResetView}
            title="Fit / Center View"
            className="w-7 h-7 bg-[#76b900]/15 hover:bg-[#76b900]/30 text-[#76b900] font-bold rounded flex items-center justify-center text-[10px] border border-[#76b900]/30 transition-all active:scale-95"
          >
            ⛶
          </button>
          <button
            onClick={() => handlePan(6, 0)}
            title="Pan East (Right)"
            className="w-7 h-7 bg-white/5 hover:bg-[#76b900]/20 hover:text-[#76b900] rounded flex items-center justify-center text-xs text-white/70 border border-white/10 transition-all active:scale-95"
          >
            ▶
          </button>
          <div />
          <button
            onClick={() => handlePan(0, 6)}
            title="Pan South (Backward)"
            className="w-7 h-7 bg-white/5 hover:bg-[#76b900]/20 hover:text-[#76b900] rounded flex items-center justify-center text-xs text-white/70 border border-white/10 transition-all active:scale-95"
          >
            ▼
          </button>
          <div />
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1 pt-1.5 border-t border-white/10 w-full justify-center">
          <button
            onClick={() => handleZoom("in")}
            title="Zoom In (+)"
            className="w-8 h-7 bg-white/5 hover:bg-[#76b900]/20 hover:text-[#76b900] rounded flex items-center justify-center text-sm font-bold text-white/80 border border-white/10 transition-all active:scale-95"
          >
            +
          </button>
          <button
            onClick={() => handleZoom("out")}
            title="Zoom Out (-)"
            className="w-8 h-7 bg-white/5 hover:bg-[#76b900]/20 hover:text-[#76b900] rounded flex items-center justify-center text-sm font-bold text-white/80 border border-white/10 transition-all active:scale-95"
          >
            -
          </button>
        </div>
      </div>
    </div>
  );
}

// ------------------------------------------------------------------
// Canvas Graphics Renderers for Omniverse Signage & Billboards
// ------------------------------------------------------------------
function renderOmniverseLabelCanvas(
  canvas: HTMLCanvasElement,
  ctx: CanvasRenderingContext2D,
  robotId: string,
  battery: number,
  state: string
) {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Omniverse Dark Titanium Badge
  ctx.fillStyle = "rgba(18, 22, 31, 0.92)";
  ctx.beginPath();
  ctx.roundRect(10, 6, 236, 84, 6);
  ctx.fill();
  ctx.strokeStyle = "rgba(118, 185, 0, 0.4)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  // Robot ID text
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 22px monospace";
  ctx.textAlign = "left";
  ctx.fillText(robotId, 22, 36);

  // Battery percentage
  ctx.fillStyle = battery > 20 ? "#76b900" : "#ef4444";
  ctx.font = "bold 19px monospace";
  ctx.textAlign = "right";
  ctx.fillText(`${battery}%`, 232, 36);

  // Battery bar background
  ctx.fillStyle = "rgba(255, 255, 255, 0.12)";
  ctx.fillRect(22, 48, 210, 12);

  // Battery bar fill
  ctx.fillStyle = battery > 20 ? "#76b900" : "#ef4444";
  ctx.fillRect(22, 48, Math.max(4, (battery / 100) * 210), 12);

  // State text
  ctx.fillStyle = "rgba(255, 255, 255, 0.55)";
  ctx.font = "14px monospace";
  ctx.textAlign = "left";
  ctx.fillText(state, 22, 78);
}

function createOmniverseRoomSign(name: string): THREE.Sprite {
  const canvas = document.createElement("canvas");
  canvas.width = 256;
  canvas.height = 100;
  const ctx = canvas.getContext("2d")!;

  ctx.fillStyle = "rgba(15, 20, 28, 0.88)";
  ctx.beginPath();
  ctx.roundRect(12, 10, 232, 80, 6);
  ctx.fill();
  ctx.strokeStyle = "rgba(255, 255, 255, 0.18)";
  ctx.lineWidth = 1.5;
  ctx.stroke();

  ctx.fillStyle = "#e2e8f0";
  ctx.font = "bold 20px monospace";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.fillText(name.toUpperCase(), 128, 50);

  const texture = new THREE.CanvasTexture(canvas);
  const spriteMat = new THREE.SpriteMaterial({ map: texture, transparent: true });
  return new THREE.Sprite(spriteMat);
}
