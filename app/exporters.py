from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable

from app.config import OUTPUTS_DIR, REPORTS_DIR, ensure_runtime_directories
from app.models import MaintenanceRecord


class ExportService:
    def __init__(self) -> None:
        self.logger = logging.getLogger("ybkj_workflow.export")

    def export_excel(self, records: Iterable[MaintenanceRecord]) -> Path:
        ensure_runtime_directories()
        target_path = OUTPUTS_DIR / "excel" / "maintenance_records_placeholder.xlsx"
        record_count = sum(1 for _ in records)
        self.logger.info("export_excel placeholder invoked, records=%s", record_count)
        raise NotImplementedError(f"Excel export placeholder not implemented yet: {target_path}")

    def export_text_report(self, records: Iterable[MaintenanceRecord]) -> Path:
        ensure_runtime_directories()
        target_path = REPORTS_DIR / "daily" / "daily_report_placeholder.txt"
        record_count = sum(1 for _ in records)
        self.logger.info(
            "export_text_report placeholder invoked, records=%s", record_count
        )
        raise NotImplementedError(
            f"Text report export placeholder not implemented yet: {target_path}"
        )
