"""
FARSverse Experiment & Analysis Lab
Run comparative simulation scenarios, compute performance metrics, and export data.
"""
from __future__ import annotations
import csv
import io
import json
import time
from typing import Any, Dict, List, Optional
from kernel.farsverse.world import FARSverseWorld
from kernel.farsverse.robot import FARSverseRobot
from kernel.farsverse.task_manager import TaskManager


class ExperimentLab:
    """Automated benchmark scenario runner comparing multi-robot fleet configurations."""

    @staticmethod
    def run_benchmark(robot_count: int = 3,
                      num_tasks: int = 15,
                      environment_type: str = "hospital",
                      seed_id: int = 42) -> Dict[str, Any]:
        """Run a discrete-event benchmark simulation run to evaluate performance metrics."""
        import random
        rng = random.Random(seed_id)

        world = FARSverseWorld(environment_type)
        task_manager = TaskManager()
        events: List[Dict[str, Any]] = []

        # Create robots
        robots: List[FARSverseRobot] = []
        for i in range(1, robot_count + 1):
            r = FARSverseRobot(
                robot_id=f"FARS-{i:02d}",
                name=f"BenchBot-{i:02d}",
                robot_type="hospital_assistant",
                initial_pos=(0.0, -10.0),
                speed=2.2,
                battery=100.0
            )
            robots.append(r)

        # Generate standard test task sequence
        dest_candidates = [f"Room{i}" for i in range(1, 21)] + ["Pharmacy", "EmergencyRoom", "ICU1", "ICU2"]
        task_types = ["assist_patient", "deliver_medicine", "guide_patient", "check_room"]

        test_tasks = []
        for i in range(num_tasks):
            loc = rng.choice(dest_candidates)
            ttype = rng.choice(task_types)
            prio = rng.randint(1, 4)
            test_tasks.append((ttype, loc, prio))

        # Simulation loop variables
        sim_time = 0.0
        dt = 0.2
        max_duration = 300.0  # max 5 sim minutes
        task_idx = 0
        collision_count = 0
        total_idle_time = 0.0

        start_real = time.time()

        while sim_time < max_duration:
            sim_time += dt

            # Spawn next task every 8-15 sim seconds
            if task_idx < len(test_tasks) and (sim_time >= task_idx * 12.0):
                ttype, loc, prio = test_tasks[task_idx]
                task_manager.create_task(ttype, loc, prio, description=f"Benchmark Task #{task_idx+1}")
                task_idx += 1

            # Autonomous task assignment
            task_manager.schedule(robots, world, events)

            # Update robots
            for r in robots:
                if r.state == "IDLE":
                    total_idle_time += dt
                comp = r.update(dt, world, events)
                if comp:
                    task_manager.on_task_completed(comp, events)
                if r.state == "ERROR":
                    collision_count += 1

            # Termination condition: all tasks processed and all robots idle
            if task_idx >= len(test_tasks) and len(task_manager.task_queue) == 0 and len(task_manager.active_tasks) == 0:
                break

        real_elapsed = time.time() - start_real

        # Gather metrics
        completed = len(task_manager.completed_tasks)
        completion_rate = round((completed / num_tasks) * 100.0, 1) if num_tasks > 0 else 0.0
        avg_resp = task_manager.get_metrics()['avg_response_time_seconds']
        total_dist = sum(r.total_distance for r in robots)
        avg_battery_end = sum(r.battery for r in robots) / len(robots) if robots else 0.0
        battery_consumed = round(100.0 - avg_battery_end, 1)

        result = {
            'run_id': f"run_{robot_count}bot_{int(time.time())}",
            'robot_count': robot_count,
            'environment': environment_type,
            'total_tasks': num_tasks,
            'completed_tasks': completed,
            'failed_tasks': len(task_manager.failed_tasks),
            'completion_rate_percent': completion_rate,
            'avg_response_time_seconds': avg_resp,
            'total_distance_meters': round(total_dist, 1),
            'battery_consumed_percent': battery_consumed,
            'simulation_duration_seconds': round(sim_time, 1),
            'real_computation_seconds': round(real_elapsed, 2),
            'collisions_and_reroutes': collision_count,
            'total_idle_time_seconds': round(total_idle_time, 1),
            'timestamp': time.time()
        }
        return result

    @staticmethod
    def export_csv(run_results: List[Dict[str, Any]]) -> str:
        """Export experiment run results to standard CSV string."""
        if not run_results:
            return ""
        output = io.StringIO()
        fieldnames = list(run_results[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for r in run_results:
            writer.writerow(r)
        return output.getvalue()
