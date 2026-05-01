from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from app.config import DATABASE_PATH, ensure_runtime_directories
from app.models import ParsedRecord, RawInputRecord


class SQLiteDataPool:
    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path
        self.logger = logging.getLogger("ybkj_workflow.database")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _table_columns(self, connection: sqlite3.Connection, table_name: str) -> set[str]:
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        return {row["name"] for row in rows}

    def _ensure_columns(
        self,
        connection: sqlite3.Connection,
        table_name: str,
        columns: dict[str, str],
    ) -> None:
        existing_columns = self._table_columns(connection, table_name)
        for column_name, column_definition in columns.items():
            if column_name not in existing_columns:
                connection.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"
                )

    def initialize(self) -> Path:
        ensure_runtime_directories()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL;")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS raw_inputs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    operator_name TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    source_name TEXT DEFAULT '',
                    source_path TEXT DEFAULT '',
                    default_project TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    note TEXT DEFAULT ''
                )
                """
            )
            self._ensure_columns(
                connection,
                "raw_inputs",
                {
                    "source_name": "TEXT DEFAULT ''",
                    "source_path": "TEXT DEFAULT ''",
                    "note": "TEXT DEFAULT ''",
                },
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS employee_aliases (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    real_name TEXT NOT NULL,
                    wechat_nickname TEXT DEFAULT '',
                    alias TEXT DEFAULT '',
                    team TEXT DEFAULT '',
                    is_active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    note TEXT DEFAULT ''
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS parsed_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    raw_input_id INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    work_date TEXT DEFAULT '',
                    project TEXT DEFAULT '',
                    system_category TEXT DEFAULT '',
                    work_type TEXT DEFAULT '',
                    status TEXT DEFAULT '',
                    start_time TEXT DEFAULT '',
                    end_time TEXT DEFAULT '',
                    duration_hours REAL DEFAULT 0,
                    wechat_nickname TEXT DEFAULT '',
                    worker_names TEXT DEFAULT '',
                    employee_confirm_required INTEGER NOT NULL DEFAULT 1,
                    location TEXT DEFAULT '',
                    device_or_part TEXT DEFAULT '',
                    problem_description TEXT DEFAULT '',
                    solution TEXT DEFAULT '',
                    result TEXT DEFAULT '',
                    source_raw_text TEXT NOT NULL,
                    confirm_status TEXT NOT NULL DEFAULT 'pending',
                    note TEXT DEFAULT '',
                    FOREIGN KEY (raw_input_id) REFERENCES raw_inputs(id)
                )
                """
            )
            connection.commit()

        self.logger.info("SQLite data pool initialized: %s", self.db_path)
        return self.db_path

    def insert_raw_input(self, record: RawInputRecord) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO raw_inputs (
                    created_at,
                    operator_name,
                    source_type,
                    source_name,
                    source_path,
                    default_project,
                    raw_text,
                    status,
                    note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.created_at,
                    record.operator_name,
                    record.source_type,
                    record.source_name,
                    record.source_path,
                    record.default_project,
                    record.raw_text,
                    record.status,
                    record.note,
                ),
            )
            connection.commit()

        record_id = int(cursor.lastrowid)
        self.logger.info("Raw input inserted into SQLite: id=%s", record_id)
        return record_id

    def count_pending_raw_inputs(self) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT COUNT(*) AS count FROM raw_inputs WHERE status = 'pending_parse'"
            ).fetchone()
        return int(row["count"])

    def get_pending_raw_inputs(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM raw_inputs
                WHERE status = 'pending_parse'
                ORDER BY id ASC
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def update_raw_input_status(self, raw_input_id: int, status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                "UPDATE raw_inputs SET status = ? WHERE id = ?",
                (status, raw_input_id),
            )
            connection.commit()

    def insert_parsed_records(self, records: list[ParsedRecord]) -> int:
        if not records:
            return 0

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO parsed_records (
                    raw_input_id,
                    created_at,
                    work_date,
                    project,
                    system_category,
                    work_type,
                    status,
                    start_time,
                    end_time,
                    duration_hours,
                    wechat_nickname,
                    worker_names,
                    employee_confirm_required,
                    location,
                    device_or_part,
                    problem_description,
                    solution,
                    result,
                    source_raw_text,
                    confirm_status,
                    note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.raw_input_id,
                        record.created_at,
                        record.work_date,
                        record.project,
                        record.system_category,
                        record.work_type,
                        record.status,
                        record.start_time,
                        record.end_time,
                        record.duration_hours,
                        record.wechat_nickname,
                        record.worker_names,
                        1 if record.employee_confirm_required else 0,
                        record.location,
                        record.device_or_part,
                        record.problem_description,
                        record.solution,
                        record.result,
                        record.source_raw_text,
                        record.confirm_status,
                        record.note,
                    )
                    for record in records
                ],
            )
            connection.commit()
        return len(records)

    def get_recent_parsed_records(self, limit: int = 100) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM parsed_records
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [dict(row) for row in rows]

    def resolve_employee_alias(self, nickname: str) -> str:
        if not nickname.strip():
            return ""

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT real_name
                FROM employee_aliases
                WHERE is_active = 1
                  AND (
                    wechat_nickname = ?
                    OR alias = ?
                    OR real_name = ?
                  )
                ORDER BY id ASC
                LIMIT 1
                """,
                (nickname, nickname, nickname),
            ).fetchone()
        return "" if row is None else str(row["real_name"])

    def get_dashboard_counts(self) -> dict[str, Any]:
        with self._connect() as connection:
            today_record_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM raw_inputs
                WHERE date(created_at) = date('now', 'localtime')
                """
            ).fetchone()["count"]

            pending_raw_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM raw_inputs
                WHERE status = 'pending_parse'
                """
            ).fetchone()["count"]

            pending_parsed_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM parsed_records
                WHERE confirm_status = 'pending'
                """
            ).fetchone()["count"]

        return {
            "today_record_count": today_record_count,
            "pending_confirmation_count": pending_raw_count + pending_parsed_count,
        }
