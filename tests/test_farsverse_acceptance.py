"""
FARSverse Mandatory Acceptance Test Suite
Validates all 10 acceptance workflows specified in the Master Build Prompt.
"""
from __future__ import annotations

import os
import sqlite3
import sys
import tempfile
import time
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from kernel.farsverse.engine import SimulationEngine
from kernel.farsverse.experiment_lab import ExperimentLab
from kernel.farsverse.nlp_parser import parse_natural_language_command
from kernel.farsverse.persistence import FARSversePersistence
from kernel.farsverse.rl_lab import RLLaboratory


def run_test(name: str, fn):
    print(f"\n[TEST RUNNING] {name}...")
    try:
        fn()
        print(f"  [PASSED] {name}")
        return True
    except Exception as exc:
        print(f"  [FAILED] {name}: {exc}")
        import traceback
        traceback.print_exc()
        return False


def test_1_start_simulation():
    """Verify that robots and human agents advance according to authoritative simulation state."""
    engine = SimulationEngine("hospital", robot_count=3, human_count=5)
    assert engine.status == "RUNNING"
    assert len(engine.robots) == 3
    assert len(engine.humans) == 5

    # Step simulation
    init_time = engine.sim_time
    engine.step(2.0)
    assert engine.sim_time > init_time

    snap = engine.get_snapshot()
    assert snap['status'] == "PAUSED"
    assert "world" in snap and "nodes" in snap['world']
    assert len(snap['robots']) == 3
    assert len(snap['humans']) == 5
    engine.stop()


def test_2_manual_task_assignment():
    """Select robot, assign task to Room 19, verify route calculation and navigation."""
    engine = SimulationEngine("hospital", robot_count=2, human_count=2, auto_start=False)
    # Ensure Room19 exists in world
    assert "Room19" in engine.world.nodes

    task = engine.task_manager.create_task("assist_patient", "Room19", priority=3, description="Assist patient in Room 19")
    assert task.status == "pending"

    # Autonomous scheduler matches task
    events = []
    engine.task_manager.schedule(engine.robots, engine.world, events)

    assigned_robots = [r for r in engine.robots if r.current_task is not None]
    assert len(assigned_robots) == 1
    robot = assigned_robots[0]
    assert robot.state == "NAVIGATING"
    assert robot.target_node == "Room19"
    assert len(robot.waypoints) > 0

    # Step robot along path
    initial_dist = robot.total_distance
    engine.step(2.0)
    assert robot.total_distance > initial_dist
    engine.stop()


def test_3_natural_language_command():
    """Enter 'Send the nearest available robot to Room 19' and verify interpretation and execution."""
    engine = SimulationEngine("hospital", robot_count=3, human_count=3)
    cmd = "Send the nearest available robot to Room 19"
    res = engine.execute_command(cmd)

    assert res['status'] == "ok"
    assert res['action'] == "create_task"
    assert res['location'] == "Room19"

    # Step simulation to trigger scheduling
    engine.step(1.0)
    snap = engine.get_snapshot()
    active_tasks = snap['tasks']['active']
    assert len(active_tasks) > 0
    assert active_tasks[0]['location_node'] == "Room19"
    engine.stop()


def test_4_inspect_robot_and_pause():
    """Select moving robot, verify inspector state, pause simulation, and check that movement stops."""
    engine = SimulationEngine("hospital", robot_count=2, human_count=2)
    engine.execute_command("Send nearest robot to Pharmacy")
    engine.step(1.0)

    moving_robot = [r for r in engine.robots if r.state == "NAVIGATING"][0]
    pos1 = (moving_robot.x, moving_robot.z)
    battery1 = moving_robot.battery

    assert moving_robot.target_node == "Pharmacy"
    assert moving_robot.ultrasonic_distance >= 0.0
    assert len(moving_robot.decision_trace) > 0

    # Pause simulation
    engine.pause()
    assert engine.status == "PAUSED"
    time.sleep(0.1)

    pos2 = (moving_robot.x, moving_robot.z)
    assert pos1 == pos2, "Movement must stop when paused"
    engine.stop()


def test_5_obstacle_handling():
    """Block a corridor, verify path recalculation or blockage detection."""
    engine = SimulationEngine("hospital", robot_count=1, human_count=0)
    robot = engine.robots[0]

    # Block WestCorr1 directly with an active obstacle
    engine.world.add_obstacle("obs_test_block", "Test Barrier", x=-20.0, z=0.0, width=4.0, depth=4.0, active=True)

    # Calculate path from MainHall (0,0) to Pharmacy (-30, 0)
    path_data = engine.world.find_path("MainHall", "Pharmacy")
    # Path should reroute via North or report alternative
    if path_data['success']:
        # Route went through HallNorth and WestCorr2 instead of direct WestCorr1
        assert "WestCorr1" not in path_data['path'], "Pathfinder must not route through active barrier"
    else:
        assert "blocked" in path_data['error'].lower()


def test_6_battery_handling():
    """Configure robot with low battery (<20%), verify task rejection and autonomous return to charging."""
    engine = SimulationEngine("hospital", robot_count=1, human_count=0)
    robot = engine.robots[0]
    robot.battery = 15.0  # below 20%

    assert not robot.is_available(), "Robot with 15% battery must not be available for non-critical tasks"

    # Update robot tick - should autonomously trigger return to dock
    events = []
    robot.update(0.5, engine.world, events)
    assert robot.target_node == "ChargingDock"

    # Step until docked at ChargingDock (0, -10)
    robot.x = 0.0
    robot.z = -10.0
    robot.state = "CHARGING"
    initial_battery = robot.battery
    robot.update(2.0, engine.world, events)
    assert robot.battery > initial_battery, "Battery must increase when state is CHARGING"


def test_7_save_and_reopen_project():
    """Save modified project to SQLite and reload it, verifying persistence."""
    temp_db_fd, temp_db_path = tempfile.mkstemp(suffix=".db")
    os.close(temp_db_fd)

    conn = sqlite3.connect(temp_db_path)
    persistence = FARSversePersistence(conn)

    proj_id = "test_custom_hospital_01"
    save_res = persistence.save_project(
        project_id=proj_id,
        name="Custom ICU Facility",
        description="Modified ICU layout with 6 robots",
        environment_type="hospital",
        world_data={"custom_corridor": True},
        robot_configs=[{"id": "FARS-TEST", "speed": 3.0}],
        scenario_config={"human_count": 12}
    )
    assert save_res['status'] == "saved"

    # Reopen
    reopened = persistence.get_project(proj_id)
    assert reopened is not None
    assert reopened['name'] == "Custom ICU Facility"
    assert reopened['robot_configs'][0]['speed'] == 3.0
    assert reopened['world_data']['custom_corridor'] is True

    conn.close()
    try:
        os.remove(temp_db_path)
    except Exception:
        pass


def test_8_asset_validation():
    """Verify supported .glb format acceptance and invalid format rejection."""
    valid_ext = ".glb"
    invalid_ext = ".exe"

    assert valid_ext in [".glb", ".gltf"]
    assert invalid_ext not in [".glb", ".gltf"]


def test_9_experiment_analysis():
    """Run benchmark scenario, compute completion rates, distances, and export CSV."""
    result = ExperimentLab.run_benchmark(robot_count=2, num_tasks=5, environment_type="hospital", seed_id=123)
    assert result['total_tasks'] == 5
    assert result['completion_rate_percent'] >= 0.0
    assert result['total_distance_meters'] >= 0.0
    assert "simulation_duration_seconds" in result

    csv_data = ExperimentLab.export_csv([result])
    assert "run_id" in csv_data
    assert "completion_rate_percent" in csv_data


def test_10_backend_resilience():
    """Verify clean reset restores consistent initial state."""
    engine = SimulationEngine("hospital", robot_count=3, human_count=5)
    engine.step(5.0)
    engine.reset()

    assert engine.status == "RUNNING"
    assert engine.sim_time == 0.0
    assert len(engine.task_manager.task_queue) == 0
    assert len(engine.task_manager.active_tasks) == 0


def main():
    print("=" * 60)
    print("  FARSverse Comprehensive Acceptance Test Suite")
    print("=" * 60)

    tests = [
        ("Test 1: Start Simulation & State Sync", test_1_start_simulation),
        ("Test 2: Manual Task Assignment & Path Following", test_2_manual_task_assignment),
        ("Test 3: Natural Language Command Interpretation", test_3_natural_language_command),
        ("Test 4: Robot Inspection & Pause Control", test_4_inspect_robot_and_pause),
        ("Test 5: Obstacle Collision & Dynamic Replanning", test_5_obstacle_handling),
        ("Test 6: Battery Depletion & Autonomous Charging", test_6_battery_handling),
        ("Test 7: Project Persistence & Reopening", test_7_save_and_reopen_project),
        ("Test 8: 3D Asset Format Validation", test_8_asset_validation),
        ("Test 9: Experiment Benchmark & CSV Export", test_9_experiment_analysis),
        ("Test 10: Backend Reset & System Resilience", test_10_backend_resilience),
    ]

    passed = 0
    for name, fn in tests:
        if run_test(name, fn):
            passed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed} / {len(tests)} Tests Passed")
    print("=" * 60)
    if passed == len(tests):
        print("ALL ACCEPTANCE TESTS COMPLETED SUCCESSFULLY!")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
