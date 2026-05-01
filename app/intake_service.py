from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime

from app.backup import JSONLBackupService
from app.config import RECORD_STATUSES, SOURCE_TYPES
from app.database import SQLiteDataPool
from app.models import RawInputRecord


class IntakeService:
    def __init__(
        self,
        data_pool: SQLiteDataPool,
        backup_service: JSONLBackupService,
    ) -> None:
        self.data_pool = data_pool
        self.backup_service = backup_service
        self.logger = logging.getLogger("ybkj_workflow.intake")

    def submit_raw_input(
        self,
        operator_name: str,
        source_type: str,
        default_project: str,
        raw_text: str,
        note: str = "",
    ) -> dict[str, str | int]:
        normalized_text = raw_text.strip()
        if not normalized_text:
            raise ValueError("raw_text cannot be empty")

        normalized_source_type = source_type if source_type in SOURCE_TYPES else "paste"
        normalized_status = "pending_parse"
        if normalized_status not in RECORD_STATUSES:
            raise ValueError("invalid default record status")

        record = RawInputRecord(
            created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            operator_name=(operator_name or "").strip() or "未填写",
            source_type=normalized_source_type,
            default_project=(default_project or "").strip() or "其他",
            raw_text=normalized_text,
            status=normalized_status,
            note=(note or "").strip(),
        )

        record_id = self.data_pool.insert_raw_input(record)
        self.backup_service.append_raw_input(asdict(record))

        self.logger.info(
            "Raw input submitted: id=%s source_type=%s operator=%s project=%s status=%s",
            record_id,
            record.source_type,
            record.operator_name,
            record.default_project,
            record.status,
        )

        return {
            "id": record_id,
            "created_at": record.created_at,
            "operator_name": record.operator_name,
            "source_type": record.source_type,
            "default_project": record.default_project,
            "status": record.status,
        }
