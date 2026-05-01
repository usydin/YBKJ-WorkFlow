from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from app.config import DATABASE_PATH, ensure_runtime_directories
from app.models import RawInputRecord


class SQLiteDataPool:
    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path
        self.logger = logging.getLogger("ybkj_workflow.database")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

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
                    default_project TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    status TEXT NOT NULL,
                    note TEXT DEFAULT ''
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
                    default_project,
                    raw_text,
                    status,
                    note
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.created_at,
                    record.operator_name,
                    record.source_type,
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

    def get_dashboard_counts(self) -> dict[str, Any]:
        with self._connect() as connection:
            today_record_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM raw_inputs
                WHERE date(created_at) = date('now', 'localtime')
                """
            ).fetchone()["count"]

            pending_confirmation_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM raw_inputs
                WHERE status IN ('pending_parse', 'parsed')
                """
            ).fetchone()["count"]

        return {
            "today_record_count": today_record_count,
            "pending_confirmation_count": pending_confirmation_count,
        }
