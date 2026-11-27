from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Iterable, Mapping, Any

from app.config import (
    JSONL_BACKUP_PATH,
    RAW_INPUTS_JSONL_PATH,
    ensure_runtime_directories,
)


class JSONLBackupService:
    def __init__(self, backup_path: Path = JSONL_BACKUP_PATH) -> None:
        self.backup_path = backup_path
        self.raw_inputs_path = RAW_INPUTS_JSONL_PATH
        self.logger = logging.getLogger("ybkj_workflow.backup")

    def initialize_backup_file(self) -> Path:
        ensure_runtime_directories()
        self.backup_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_path.touch(exist_ok=True)
        self.raw_inputs_path.parent.mkdir(parents=True, exist_ok=True)
        self.raw_inputs_path.touch(exist_ok=True)
        self.logger.info("JSONL backup placeholder ready: %s", self.backup_path)
        self.logger.info("Raw input JSONL ready: %s", self.raw_inputs_path)
        return self.backup_path

    def backup_records(
        self, records: Iterable[Mapping[str, Any]], output_path: Path | None = None
    ) -> Path:
        target_path = output_path or self.backup_path
        target_path.parent.mkdir(parents=True, exist_ok=True)

        with target_path.open("a", encoding="utf-8") as backup_file:
            for record in records:
                backup_file.write(
                    json.dumps(dict(record), ensure_ascii=False) + "\n"
                )

        self.logger.info("JSONL backup completed: %s", target_path)
        return target_path

    def append_raw_input(self, record: Mapping[str, Any]) -> Path:
        if "_workflow_event_id" not in record:
            return self.backup_records([record], output_path=self.raw_inputs_path)
        # Outbox delivery owns a SQLite write lock. Use a single database per
        # JSONL destination. Preserve legacy lines; a corrupt projection is
        # left untouched and remains pending rather than being silently truncated.
        target = self.raw_inputs_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink():
            raise OSError("backup destination must not be a symlink")
        payload = dict(record)
        old = target.read_bytes() if target.exists() else b""
        event = payload["_workflow_event_id"]
        matches = []
        for line in old.splitlines():
            if line.strip():
                existing = json.loads(line)
                if not isinstance(existing, dict):
                    raise ValueError("invalid JSONL backup row")
                if existing.get("_workflow_event_id") == event:
                    matches.append(existing)
        if matches:
            if len(matches) != 1 or matches[0] != payload:
                raise ValueError("conflicting backup event")
            return target
        suffix = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8") + b"\n"
        if old and not old.endswith(b"\n"):
            suffix = b"\n" + suffix
        fd, name = tempfile.mkstemp(prefix=".raw-input-", suffix=".tmp", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(old)
                stream.write(suffix)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, target)
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return target
