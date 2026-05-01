from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import DATASET_DIR


class CorrectionsLogService:
    def __init__(self, log_path: Path | None = None) -> None:
        self.log_path = log_path or (DATASET_DIR / "corrections.log")
        self.logger = logging.getLogger("ybkj_workflow.corrections")

    def ensure_file(self) -> Path:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_path.touch(exist_ok=True)
        return self.log_path

    def append(
        self,
        *,
        operator_name: str,
        action_type: str,
        record_id: int,
        raw_input_id: int,
        before: dict[str, Any],
        after: dict[str, Any],
        source_raw_text: str,
        note: str = "",
    ) -> Path:
        self.ensure_file()
        payload = {
            "correction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "operator_name": operator_name.strip() or "未指定操作员",
            "action_type": action_type,
            "record_id": record_id,
            "raw_input_id": raw_input_id,
            "before": before,
            "after": after,
            "source_raw_text": source_raw_text,
            "note": note,
        }
        with self.log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(json.dumps(payload, ensure_ascii=False) + "\n")

        self.logger.info(
            "Correction logged: action=%s record_id=%s raw_input_id=%s",
            action_type,
            record_id,
            raw_input_id,
        )
        return self.log_path
