from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

from app.config import DATABASE_PATH, ensure_runtime_directories


class SQLiteDataPool:
    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path
        self.logger = logging.getLogger("ybkj_workflow.database")

    def initialize(self) -> Path:
        ensure_runtime_directories()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as connection:
            connection.execute("PRAGMA journal_mode=WAL;")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS app_meta (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.commit()

        self.logger.info("SQLite data pool initialized: %s", self.db_path)
        return self.db_path
