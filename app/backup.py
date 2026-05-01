from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable, Mapping, Any

from app.config import JSONL_BACKUP_PATH, ensure_runtime_directories


class JSONLBackupService:
    def __init__(self, backup_path: Path = JSONL_BACKUP_PATH) -> None:
        self.backup_path = backup_path
        self.logger = logging.getLogger("ybkj_workflow.backup")

    def initialize_backup_file(self) -> Path:
        ensure_runtime_directories()
        self.backup_path.parent.mkdir(parents=True, exist_ok=True)
        self.backup_path.touch(exist_ok=True)
        self.logger.info("JSONL backup placeholder ready: %s", self.backup_path)
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
