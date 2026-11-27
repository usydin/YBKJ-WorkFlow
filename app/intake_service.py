from __future__ import annotations

import logging
from datetime import datetime

from app.backup import JSONLBackupService
from app.config import RECORD_STATUSES, SOURCE_TYPES, to_relative_source_path
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
        source_name: str,
        source_path: str,
        default_project: str,
        raw_text: str,
        note: str = "",
        *,
        request_key: str | None = None,
    ) -> dict[str, str | int | bool]:
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
            source_name=(source_name or "").strip() or self._default_source_name(normalized_source_type),
            source_path=to_relative_source_path(source_path),
            default_project=(default_project or "").strip() or "其他",
            raw_text=normalized_text,
            status=normalized_status,
            note=(note or "").strip(),
        )

        record_id, payload, replayed = self.data_pool.submit_raw_input_with_outbox(record, request_key)
        backup_status = self._deliver_backup(record_id)

        self.logger.info(
            "Raw input submitted: id=%s source_type=%s source_name=%s source_path=%s operator=%s project=%s status=%s",
            record_id,
            record.source_type,
            record.source_name,
            record.source_path,
            record.operator_name,
            record.default_project,
            record.status,
        )

        return {
            "id": record_id,
            "created_at": payload["created_at"],
            "operator_name": payload["operator_name"],
            "source_type": payload["source_type"],
            "source_name": payload["source_name"],
            "source_path": payload["source_path"],
            "default_project": payload["default_project"],
            "status": payload["status"],
            "submission_status": "COMMITTED",
            "backup_status": backup_status,
            "replayed": replayed,
        }

    def _deliver_backup(self, raw_id: int) -> str:
        try:
            self.data_pool.deliver_raw_input_backup(raw_id, self.backup_service.append_raw_input)
            return "SYNCED"
        except Exception:
            # The SQLite transaction has already committed; do not tell the caller
            # to resubmit. The durable outbox remains pending for explicit retry.
            self.logger.warning("Raw input backup pending: id=%s", raw_id)
            return "PENDING"

    def retry_pending_backups(self, limit: int = 100) -> dict[str, int]:
        ids = self.data_pool.pending_raw_input_backups(limit)
        synced = sum(self._deliver_backup(raw_id) == "SYNCED" for raw_id in ids)
        return {"attempted": len(ids), "synced": synced, "pending": len(ids) - synced}

    def _default_source_name(self, source_type: str) -> str:
        source_names = {
            "paste": "粘贴输入",
            "txt": "TXT 导入",
            "manual": "手动录入",
            "screenshot": "截图 OCR 预留",
            "batch_txt": "批量 TXT 导入预留",
            "unknown": "未知来源",
        }
        return source_names.get(source_type, "未知来源")
