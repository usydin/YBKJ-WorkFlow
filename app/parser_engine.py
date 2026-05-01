from __future__ import annotations

import logging
from typing import Any

from app.models import MaintenanceRecord


class ParserEngine:
    def __init__(self) -> None:
        self.logger = logging.getLogger("ybkj_workflow.parser")

    def parse_text(self, input_text: str) -> list[MaintenanceRecord]:
        self.logger.info("parse_text placeholder invoked")
        if not input_text.strip():
            return []
        return [MaintenanceRecord(raw_text=input_text, requires_confirmation=True)]

    def classify_record(self, record: MaintenanceRecord) -> dict[str, Any]:
        self.logger.info("classify_record placeholder invoked")
        return {
            "system_category": record.system_category or "待分类",
            "work_type": record.work_type or "待判定",
            "status": record.status or "待确认",
        }

    def merge_similar_records(
        self, records: list[MaintenanceRecord]
    ) -> list[MaintenanceRecord]:
        self.logger.info("merge_similar_records placeholder invoked")
        return records
