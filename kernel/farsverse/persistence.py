"""
FARSverse Persistence & Asset Management
SQLite project storage, scenario saves, and secure GLB/glTF asset uploads.
"""
from __future__ import annotations
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

UPLOAD_DIR = Path("assets/uploads").resolve()
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class FARSversePersistence:
    """Manages project configurations, saved scenarios, and model asset storage."""

    def __init__(self, db_conn: sqlite3.Connection):
        self._conn = db_conn
        self._conn.row_factory = sqlite3.Row
        self._init_tables()
        self.seed_default_projects()

    def _init_tables(self) -> None:
        c = self._conn.cursor()
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS farsverse_projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                environment_type TEXT NOT NULL,
                world_data TEXT,
                robot_configs TEXT,
                scenario_config TEXT,
                created_at REAL,
                updated_at REAL
            );

            CREATE TABLE IF NOT EXISTS farsverse_assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_type TEXT NOT NULL,
                file_size INTEGER,
                storage_path TEXT NOT NULL,
                uploaded_at REAL
            );

            CREATE TABLE IF NOT EXISTS farsverse_experiments (
                id TEXT PRIMARY KEY,
                project_id TEXT,
                robot_count INTEGER,
                total_tasks INTEGER,
                completion_rate REAL,
                avg_response_time REAL,
                total_distance REAL,
                battery_consumed REAL,
                result_json TEXT,
                created_at REAL
            );
            """
        )
        self._conn.commit()

    def seed_default_projects(self) -> None:
        c = self._conn.cursor()
        c.execute("SELECT COUNT(*) FROM farsverse_projects")
        if c.fetchone()[0] == 0:
            now = time.time()
            default_robots = [
                {'id': 'FARS-01', 'name': 'CareBot Alpha', 'robot_type': 'hospital_assistant', 'speed': 2.2, 'battery': 100.0, 'battery_capacity': 100.0},
                {'id': 'FARS-02', 'name': 'MedCourier 02', 'robot_type': 'delivery_robot', 'speed': 2.5, 'battery': 95.0, 'battery_capacity': 100.0},
                {'id': 'FARS-03', 'name': 'PatientGuide 03', 'robot_type': 'hospital_assistant', 'speed': 1.8, 'battery': 88.0, 'battery_capacity': 100.0},
                {'id': 'FARS-04', 'name': 'ServiceUnit 04', 'robot_type': 'service_robot', 'speed': 2.0, 'battery': 75.0, 'battery_capacity': 100.0},
                {'id': 'FARS-05', 'name': 'PatrolBot 05', 'robot_type': 'hospital_assistant', 'speed': 2.4, 'battery': 92.0, 'battery_capacity': 100.0},
            ]

            projects = [
                (
                    'proj_hospital_flagship',
                    'FARS General Hospital (Flagship)',
                    'Full-scale healthcare facility digital twin with 20 patient rooms, ICU, ER, and pharmacy.',
                    'hospital',
                    json.dumps({}),
                    json.dumps(default_robots),
                    json.dumps({'human_count': 24, 'auto_requests': True}),
                    now,
                    now
                ),
                (
                    'proj_campus_demo',
                    'Innovation Campus Quad',
                    'Multi-building campus quad with central plaza, academic complex, science library, and dining hall.',
                    'campus',
                    json.dumps({}),
                    json.dumps(default_robots[:3]),
                    json.dumps({'human_count': 16, 'auto_requests': True}),
                    now,
                    now
                ),
                (
                    'proj_warehouse_demo',
                    'Logistics Fulfillment Center',
                    'High-throughput warehouse with storage aisles, automated sorting, and receiving docks.',
                    'warehouse',
                    json.dumps({}),
                    json.dumps(default_robots[:3]),
                    json.dumps({'human_count': 8, 'auto_requests': False}),
                    now,
                    now
                ),
                (
                    'proj_sandbox_empty',
                    'Blank Simulation Studio',
                    'Empty custom sandbox for testing user-defined room geometries and custom obstacles.',
                    'empty',
                    json.dumps({}),
                    json.dumps(default_robots[:2]),
                    json.dumps({'human_count': 0, 'auto_requests': False}),
                    now,
                    now
                )
            ]

            c.executemany(
                """
                INSERT INTO farsverse_projects
                (id, name, description, environment_type, world_data, robot_configs, scenario_config, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                projects
            )
            self._conn.commit()

    def list_projects(self) -> List[Dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT id, name, description, environment_type, robot_configs, created_at, updated_at FROM farsverse_projects ORDER BY updated_at DESC")
        rows = c.fetchall()
        projects = []
        for r in rows:
            robots = json.loads(r['robot_configs'] or '[]')
            projects.append({
                'id': r['id'],
                'name': r['name'],
                'description': r['description'],
                'environment_type': r['environment_type'],
                'robot_count': len(robots),
                'created_at': r['created_at'],
                'updated_at': r['updated_at']
            })
        return projects

    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT * FROM farsverse_projects WHERE id = ?", (project_id,))
        row = c.fetchone()
        if not row:
            return None
        return {
            'id': row['id'],
            'name': row['name'],
            'description': row['description'],
            'environment_type': row['environment_type'],
            'world_data': json.loads(row['world_data'] or '{}'),
            'robot_configs': json.loads(row['robot_configs'] or '[]'),
            'scenario_config': json.loads(row['scenario_config'] or '{}'),
            'created_at': row['created_at'],
            'updated_at': row['updated_at']
        }

    def save_project(self,
                     project_id: str,
                     name: str,
                     description: str,
                     environment_type: str,
                     world_data: Dict[str, Any],
                     robot_configs: List[Dict[str, Any]],
                     scenario_config: Dict[str, Any]) -> Dict[str, Any]:
        now = time.time()
        c = self._conn.cursor()
        c.execute(
            """
            INSERT INTO farsverse_projects
            (id, name, description, environment_type, world_data, robot_configs, scenario_config, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                description=excluded.description,
                environment_type=excluded.environment_type,
                world_data=excluded.world_data,
                robot_configs=excluded.robot_configs,
                scenario_config=excluded.scenario_config,
                updated_at=excluded.updated_at
            """,
            (
                project_id,
                name,
                description,
                environment_type,
                json.dumps(world_data),
                json.dumps(robot_configs),
                json.dumps(scenario_config),
                now,
                now
            )
        )
        self._conn.commit()
        return {'status': 'saved', 'id': project_id, 'updated_at': now}

    def delete_project(self, project_id: str) -> bool:
        c = self._conn.cursor()
        c.execute("DELETE FROM farsverse_projects WHERE id = ?", (project_id,))
        self._conn.commit()
        return c.rowcount > 0

    def register_asset(self, asset_id: str, original_name: str, filename: str, file_type: str, file_size: int, storage_path: str) -> Dict[str, Any]:
        now = time.time()
        c = self._conn.cursor()
        c.execute(
            """
            INSERT INTO farsverse_assets
            (id, name, filename, file_type, file_size, storage_path, uploaded_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (asset_id, original_name, filename, file_type, file_size, storage_path, now)
        )
        self._conn.commit()
        return {
            'id': asset_id,
            'name': original_name,
            'filename': filename,
            'file_type': file_type,
            'file_size': file_size,
            'uploaded_at': now
        }

    def list_assets(self) -> List[Dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT * FROM farsverse_assets ORDER BY uploaded_at DESC")
        return [dict(r) for r in c.fetchall()]

    def record_experiment(self, exp_data: Dict[str, Any]) -> None:
        c = self._conn.cursor()
        c.execute(
            """
            INSERT INTO farsverse_experiments
            (id, project_id, robot_count, total_tasks, completion_rate, avg_response_time, total_distance, battery_consumed, result_json, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exp_data.get('run_id', f"exp_{int(time.time())}"),
                exp_data.get('project_id', 'proj_hospital_flagship'),
                exp_data.get('robot_count', 3),
                exp_data.get('total_tasks', 0),
                exp_data.get('completion_rate_percent', 0.0),
                exp_data.get('avg_response_time_seconds', 0.0),
                exp_data.get('total_distance_meters', 0.0),
                exp_data.get('battery_consumed_percent', 0.0),
                json.dumps(exp_data),
                exp_data.get('timestamp', time.time())
            )
        )
        self._conn.commit()

    def list_experiments(self) -> List[Dict[str, Any]]:
        c = self._conn.cursor()
        c.execute("SELECT result_json FROM farsverse_experiments ORDER BY created_at DESC LIMIT 20")
        rows = c.fetchall()
        return [json.loads(r['result_json']) for r in rows if r['result_json']]
