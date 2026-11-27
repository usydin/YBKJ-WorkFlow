from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import (
    APP_INFO,
    DATABASE_PATH,
    ensure_runtime_directories,
    is_reserved_person_name,
    normalize_worker_names_text,
    split_worker_names_text,
)
from app.models import ParsedRecord, RawInputRecord


class SQLiteDataPool:
    def __init__(self, db_path: Path = DATABASE_PATH) -> None:
        self.db_path = db_path
        self.logger = logging.getLogger("ybkj_workflow.database")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
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
                    updated_at TEXT DEFAULT '',
                    note TEXT DEFAULT '',
                    FOREIGN KEY (raw_input_id) REFERENCES raw_inputs(id)
                )
                """
            )
            self._ensure_columns(
                connection,
                "parsed_records",
                {
                    "updated_at": "TEXT DEFAULT ''",
                    "note": "TEXT DEFAULT ''",
                },
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ocr_staging_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL DEFAULT 'manual_paste',
                    source_name TEXT DEFAULT '',
                    raw_text TEXT NOT NULL,
                    cleaned_text TEXT DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'draft',
                    note TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    imported_raw_input_id INTEGER DEFAULT NULL
                )
                """
            )
            self._ensure_columns(
                connection,
                "ocr_staging_records",
                {
                    "source_name": "TEXT DEFAULT ''",
                    "cleaned_text": "TEXT DEFAULT ''",
                    "status": "TEXT NOT NULL DEFAULT 'draft'",
                    "note": "TEXT DEFAULT ''",
                    "updated_at": "TEXT NOT NULL DEFAULT ''",
                    "imported_raw_input_id": "INTEGER DEFAULT NULL",
                },
            )
            connection.commit()

        self.logger.info("SQLite data pool initialized: %s", self.db_path)
        return self.db_path

    def cleanup_reserved_person_names(self) -> int:
        updated_rows = 0
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reserved_name = APP_INFO.developer

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, worker_names, wechat_nickname
                FROM parsed_records
                WHERE worker_names LIKE ?
                   OR TRIM(wechat_nickname) = ?
                """,
                (f"%{reserved_name}%", reserved_name),
            ).fetchall()

            for row in rows:
                record_id = int(row["id"])
                current_worker_names = str(row["worker_names"] or "").strip()
                current_wechat_nickname = str(row["wechat_nickname"] or "").strip()
                normalized_worker_names = normalize_worker_names_text(current_worker_names)
                sanitized_wechat_nickname = (
                    "" if is_reserved_person_name(current_wechat_nickname) else current_wechat_nickname
                )
                updates: dict[str, Any] = {}

                if normalized_worker_names != current_worker_names:
                    updates["worker_names"] = normalized_worker_names
                    if not normalized_worker_names:
                        updates["employee_confirm_required"] = 1

                if sanitized_wechat_nickname != current_wechat_nickname:
                    updates["wechat_nickname"] = sanitized_wechat_nickname

                if updates:
                    updates["updated_at"] = now
                    columns = ", ".join(f"{column} = ?" for column in updates)
                    params = list(updates.values()) + [record_id]
                    connection.execute(
                        f"UPDATE parsed_records SET {columns} WHERE id = ?",
                        params,
                    )
                    updated_rows += 1

            connection.commit()

        if updated_rows > 0:
            self.logger.info(
                "Reserved person name cleanup applied: reserved_name=%s updated_rows=%s",
                reserved_name,
                updated_rows,
            )
        return updated_rows

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

    def create_ocr_staging_record(self, data: dict[str, Any]) -> int:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO ocr_staging_records (
                    source_type,
                    source_name,
                    raw_text,
                    cleaned_text,
                    status,
                    note,
                    created_at,
                    updated_at,
                    imported_raw_input_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(data.get("source_type", "")).strip() or "manual_paste",
                    str(data.get("source_name", "")).strip(),
                    str(data.get("raw_text", "")).strip(),
                    str(data.get("cleaned_text", "")).strip(),
                    str(data.get("status", "")).strip() or "draft",
                    str(data.get("note", "")).strip(),
                    now,
                    now,
                    data.get("imported_raw_input_id"),
                ),
            )
            connection.commit()
        return int(cursor.lastrowid)

    def list_ocr_staging_records(self, status: str | None = None) -> list[dict[str, Any]]:
        query = ["SELECT * FROM ocr_staging_records WHERE 1=1"]
        params: list[Any] = []
        normalized_status = str(status or "").strip()
        if normalized_status:
            query.append("AND status = ?")
            params.append(normalized_status)
        query.append("ORDER BY id DESC")

        with self._connect() as connection:
            rows = connection.execute(" ".join(query), tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get_ocr_staging_record(self, record_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM ocr_staging_records WHERE id = ?",
                (record_id,),
            ).fetchone()
        return dict(row) if row else None

    def update_ocr_staging_record(self, record_id: int, updates: dict[str, Any]) -> None:
        if not updates:
            return
        updates = dict(updates)
        updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        columns = ", ".join(f"{column} = ?" for column in updates)
        params = list(updates.values()) + [record_id]
        with self._connect() as connection:
            connection.execute(
                f"UPDATE ocr_staging_records SET {columns} WHERE id = ?",
                params,
            )
            connection.commit()

    def count_ocr_staging_records_by_status(self) -> dict[str, int]:
        counts = {
            "total_count": 0,
            "draft_count": 0,
            "confirmed_count": 0,
            "imported_count": 0,
            "ignored_count": 0,
            "pending_import_count": 0,
        }
        with self._connect() as connection:
            total_row = connection.execute(
                "SELECT COUNT(*) AS count FROM ocr_staging_records"
            ).fetchone()
            counts["total_count"] = int(total_row["count"] if total_row else 0)

            rows = connection.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM ocr_staging_records
                GROUP BY status
                """
            ).fetchall()

        for row in rows:
            status_name = str(row["status"] or "").strip()
            count = int(row["count"] or 0)
            if status_name == "draft":
                counts["draft_count"] = count
            elif status_name == "confirmed":
                counts["confirmed_count"] = count
            elif status_name == "imported":
                counts["imported_count"] = count
            elif status_name == "ignored":
                counts["ignored_count"] = count

        counts["pending_import_count"] = (
            counts["draft_count"] + counts["confirmed_count"]
        )
        return counts

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

    def list_parsed_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        filters = filters or {}
        query = ["SELECT * FROM parsed_records WHERE 1=1"]
        params: list[Any] = []

        if confirm_status := filters.get("confirm_status"):
            if confirm_status != "all":
                query.append("AND confirm_status = ?")
                params.append(confirm_status)
        if project := filters.get("project"):
            if project != "全部":
                query.append("AND project = ?")
                params.append(project)
        if system_category := filters.get("system_category"):
            if system_category != "全部":
                query.append("AND system_category = ?")
                params.append(system_category)
        if work_type := filters.get("work_type"):
            if work_type != "全部":
                query.append("AND work_type = ?")
                params.append(work_type)
        if keyword := str(filters.get("keyword", "")).strip():
            query.append(
                """
                AND (
                    source_raw_text LIKE ?
                    OR worker_names LIKE ?
                    OR wechat_nickname LIKE ?
                    OR project LIKE ?
                    OR problem_description LIKE ?
                    OR solution LIKE ?
                    OR result LIKE ?
                )
                """
            )
            keyword_like = f"%{keyword}%"
            params.extend([keyword_like] * 7)

        query.append("ORDER BY id DESC")

        with self._connect() as connection:
            rows = connection.execute(" ".join(query), tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get_parsed_record(self, record_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM parsed_records WHERE id = ?",
                (record_id,),
            ).fetchone()
        return None if row is None else dict(row)

    def get_parsed_record_snapshot(self, record_id: int) -> dict[str, Any] | None:
        return self.get_parsed_record(record_id)

    def update_parsed_record(self, record_id: int, updates: dict[str, Any]) -> None:
        if not updates:
            return

        columns = ", ".join(f"{column} = ?" for column in updates)
        values = list(updates.values()) + [record_id]

        with self._connect() as connection:
            connection.execute(
                f"UPDATE parsed_records SET {columns} WHERE id = ?",
                values,
            )
            connection.commit()

    def update_confirm_status(self, record_id: int, confirm_status: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE parsed_records
                SET confirm_status = ?
                WHERE id = ?
                """,
                (confirm_status, record_id),
            )
            connection.commit()

    def count_parsed_records_by_status(self) -> dict[str, int]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT confirm_status, COUNT(*) AS count
                FROM parsed_records
                GROUP BY confirm_status
                """
            ).fetchall()

        counts = {"pending": 0, "confirmed": 0, "ignored": 0}
        for row in rows:
            counts[str(row["confirm_status"])] = int(row["count"])
        return counts

    def _append_confirmed_record_filters(
        self,
        query: list[str],
        params: list[Any],
        filters: dict[str, Any] | None = None,
        *,
        exact_date: str | None = None,
    ) -> None:
        filters = filters or {}

        normalized_date = (exact_date or "").strip()
        if normalized_date:
            query.append("AND work_date = ?")
            params.append(normalized_date)
        else:
            start_date = str(filters.get("start_date", "")).strip()
            end_date = str(filters.get("end_date", "")).strip()
            if start_date:
                query.append("AND work_date >= ?")
                params.append(start_date)
            if end_date:
                query.append("AND work_date <= ?")
                params.append(end_date)

        if project := str(filters.get("project", "")).strip():
            if project != "全部":
                query.append("AND project = ?")
                params.append(project)
        if system_category := str(filters.get("system_category", "")).strip():
            if system_category != "全部":
                query.append("AND system_category = ?")
                params.append(system_category)

        work_type = str(filters.get("work_type", "")).strip()
        if work_type and work_type != "全部":
            if work_type == "维修":
                query.append("AND work_type IN (?, ?)")
                params.extend(["维修", "维修或维护"])
            elif work_type == "维护":
                query.append("AND work_type IN (?, ?)")
                params.extend(["维护", "维修或维护"])
            elif work_type == "会议":
                query.append("AND work_type IN (?, ?)")
                params.extend(["会议", "安全交底 / 会议类"])
            elif work_type == "安全交底":
                query.append("AND work_type IN (?, ?)")
                params.extend(["安全交底", "安全交底 / 会议类"])
            else:
                query.append("AND work_type = ?")
                params.append(work_type)

        if worker_names := str(filters.get("worker_names", "")).strip():
            query.append("AND worker_names LIKE ?")
            params.append(f"%{worker_names}%")

    def list_confirmed_records_for_report(
        self,
        date: str | None = None,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query = ["SELECT * FROM parsed_records WHERE confirm_status = 'confirmed'"]
        params: list[Any] = []
        self._append_confirmed_record_filters(query, params, filters, exact_date=date)

        query.append(
            """
            ORDER BY
                CASE WHEN work_date = '' THEN 1 ELSE 0 END ASC,
                work_date DESC,
                CASE WHEN start_time = '' THEN 1 ELSE 0 END ASC,
                start_time ASC,
                id ASC
            """
        )

        with self._connect() as connection:
            rows = connection.execute(" ".join(query), tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def count_parsed_records_for_scope(
        self,
        *,
        date: str | None = None,
        filters: dict[str, Any] | None = None,
        confirm_status: str | None = None,
    ) -> int:
        query = ["SELECT COUNT(*) FROM parsed_records WHERE 1=1"]
        params: list[Any] = []

        if confirm_status:
            query.append("AND confirm_status = ?")
            params.append(confirm_status)

        self._append_confirmed_record_filters(query, params, filters, exact_date=date)

        with self._connect() as connection:
            row = connection.execute(" ".join(query), tuple(params)).fetchone()
        return int(row[0] if row else 0)

    def list_confirmed_records_for_analytics(
        self,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        query = [
            """
            SELECT
                id,
                work_date,
                project,
                system_category,
                work_type,
                status,
                start_time,
                end_time,
                duration_hours,
                worker_names,
                location,
                device_or_part,
                problem_description,
                solution,
                result,
                note,
                source_raw_text
            FROM parsed_records
            WHERE confirm_status = 'confirmed'
            """
        ]
        params: list[Any] = []
        self._append_confirmed_record_filters(query, params, filters)
        query.append(
            """
            ORDER BY
                CASE WHEN work_date = '' THEN 1 ELSE 0 END ASC,
                work_date DESC,
                CASE WHEN start_time = '' THEN 1 ELSE 0 END ASC,
                start_time ASC,
                id DESC
            """
        )

        with self._connect() as connection:
            rows = connection.execute(" ".join(query), tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get_available_work_dates(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT DISTINCT work_date
                FROM parsed_records
                WHERE confirm_status = 'confirmed'
                  AND work_date <> ''
                ORDER BY work_date DESC
                """
            ).fetchall()
        return [str(row["work_date"]) for row in rows]

    def get_report_filter_options(self) -> dict[str, list[str]]:
        with self._connect() as connection:
            project_rows = connection.execute(
                """
                SELECT DISTINCT project
                FROM parsed_records
                WHERE confirm_status = 'confirmed'
                  AND project <> ''
                ORDER BY project ASC
                """
            ).fetchall()
            system_rows = connection.execute(
                """
                SELECT DISTINCT system_category
                FROM parsed_records
                WHERE confirm_status = 'confirmed'
                  AND system_category <> ''
                ORDER BY system_category ASC
                """
            ).fetchall()
            work_type_rows = connection.execute(
                """
                SELECT DISTINCT work_type
                FROM parsed_records
                WHERE confirm_status = 'confirmed'
                  AND work_type <> ''
                ORDER BY work_type ASC
                """
            ).fetchall()
            worker_rows = connection.execute(
                """
                SELECT DISTINCT worker_names
                FROM parsed_records
                WHERE confirm_status = 'confirmed'
                  AND worker_names <> ''
                ORDER BY worker_names ASC
                """
            ).fetchall()

        worker_names: set[str] = set()
        for row in worker_rows:
            for normalized_name in split_worker_names_text(str(row["worker_names"])):
                worker_names.add(normalized_name)

        return {
            "projects": [str(row["project"]) for row in project_rows],
            "system_categories": [str(row["system_category"]) for row in system_rows],
            "work_types": [str(row["work_type"]) for row in work_type_rows],
            "worker_names": sorted(worker_names),
        }

    def list_employee_aliases(self, include_inactive: bool = True, keyword: str | None = None) -> list[dict[str, Any]]:
        query = ["SELECT * FROM employee_aliases WHERE 1=1"]
        params = []
        
        if not include_inactive:
            query.append("AND is_active = 1")
            
        if keyword and keyword.strip():
            query.append("AND (real_name LIKE ? OR wechat_nickname LIKE ? OR alias LIKE ? OR team LIKE ? OR note LIKE ?)")
            kw = f"%{keyword.strip()}%"
            params.extend([kw] * 5)
            
        query.append("ORDER BY id DESC")
        
        with self._connect() as connection:
            rows = connection.execute(" ".join(query), tuple(params)).fetchall()
        return [dict(row) for row in rows]

    def get_employee_alias(self, alias_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM employee_aliases WHERE id = ?", (alias_id,)).fetchone()
        return dict(row) if row else None

    def create_employee_alias(self, data: dict[str, Any]) -> int:
        real_name = str(data.get("real_name", "")).strip()
        if not real_name:
            raise ValueError("real_name 不能为空")
            
        wechat_nickname = str(data.get("wechat_nickname", "")).strip()
        alias = str(data.get("alias", "")).strip()
        if not wechat_nickname and not alias:
            raise ValueError("wechat_nickname 和 alias 至少有一个不为空")
            
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO employee_aliases (
                    real_name, wechat_nickname, alias, team, is_active, created_at, updated_at, note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    real_name,
                    wechat_nickname,
                    alias,
                    str(data.get("team", "")).strip(),
                    1 if data.get("is_active", True) else 0,
                    now,
                    now,
                    str(data.get("note", "")).strip()
                )
            )
            connection.commit()
            return int(cursor.lastrowid)

    def update_employee_alias(self, alias_id: int, updates: dict[str, Any]) -> None:
        if not updates:
            return
            
        updates["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        columns = ", ".join(f"{k} = ?" for k in updates.keys())
        params = list(updates.values()) + [alias_id]
        
        with self._connect() as connection:
            connection.execute(f"UPDATE employee_aliases SET {columns} WHERE id = ?", tuple(params))
            connection.commit()

    def set_employee_alias_active(self, alias_id: int, is_active: bool) -> None:
        self.update_employee_alias(alias_id, {"is_active": 1 if is_active else 0})

    def delete_employee_alias(self, alias_id: int, physical: bool = False) -> None:
        with self._connect() as connection:
            if physical:
                connection.execute("DELETE FROM employee_aliases WHERE id = ?", (alias_id,))
            else:
                connection.execute("UPDATE employee_aliases SET is_active = 0 WHERE id = ?", (alias_id,))
            connection.commit()

    def resolve_worker_name(self, raw_name: str) -> tuple[str, bool]:
        """Resolve only a single active row; ambiguous identity requires review."""
        name = raw_name.strip()
        if not name or is_reserved_person_name(name):
            return "", False
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT real_name FROM employee_aliases
                WHERE is_active = 1
                AND (real_name = ? OR wechat_nickname = ? OR alias = ?)
                LIMIT 2
                """,
                (name, name, name),
            ).fetchall()
        if len(rows) == 1:
            resolved = str(rows[0]["real_name"]).strip()
            if resolved and not is_reserved_person_name(resolved):
                return resolved, True
        return name, False

    def resolve_worker_names(self, raw_names_text: str) -> dict[str, Any]:
        if not raw_names_text.strip():
            return {"mapped_names": "", "unresolved_names": [], "employee_confirm_required": True}
            
        raw_list = [n.strip() for n in split_worker_names_text(raw_names_text) if n.strip()]
        if not raw_list:
            return {"mapped_names": "", "unresolved_names": [], "employee_confirm_required": True}

        mapped_list = []
        unresolved = []
        
        for name in raw_list:
            mapped_name, is_mapped = self.resolve_worker_name(name)
            if mapped_name:
                mapped_list.append(mapped_name)
            if not is_mapped:
                unresolved.append(name)
                
        final_mapped = normalize_worker_names_text("、".join(mapped_list))
                
        return {
            "mapped_names": final_mapped,
            "unresolved_names": unresolved,
            "employee_confirm_required": len(unresolved) > 0
        }

    def resolve_employee_alias(self, nickname: str) -> str:
        resolved, is_mapped = self.resolve_worker_name(nickname)
        return resolved if is_mapped else ""

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

            confirmed_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM parsed_records
                WHERE confirm_status = 'confirmed'
                """
            ).fetchone()["count"]

            ignored_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM parsed_records
                WHERE confirm_status = 'ignored'
                """
            ).fetchone()["count"]

        return {
            "today_record_count": today_record_count,
            "pending_confirmation_count": pending_raw_count + pending_parsed_count,
            "confirmed_record_count": confirmed_count,
            "ignored_record_count": ignored_count,
        }
