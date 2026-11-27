from __future__ import annotations

import logging
from typing import Any

from app.database import SQLiteDataPool
from app.intake_service import IntakeService


OCR_STAGING_SOURCE_TYPES = (
    "manual_paste",
    "future_ocr",
    "screenshot",
    "wechat_image",
)
OCR_STAGING_STATUSES = ("draft", "confirmed", "imported", "ignored")


class OCRStagingService:
    def __init__(
        self,
        data_pool: SQLiteDataPool,
        intake_service: IntakeService,
    ) -> None:
        self.data_pool = data_pool
        self.intake_service = intake_service
        self.logger = logging.getLogger("ybkj_workflow.ocr_staging")

    def create_staging_record(
        self,
        raw_text: str,
        source_type: str,
        source_name: str,
        note: str = "",
    ) -> int:
        normalized_text = str(raw_text or "").strip()
        if not normalized_text:
            raise ValueError("暂存文本不能为空。")

        normalized_source_type = self._normalize_source_type(source_type)
        record_id = self.data_pool.create_ocr_staging_record(
            {
                "source_type": normalized_source_type,
                "source_name": str(source_name or "").strip() or "手动粘贴",
                "raw_text": normalized_text,
                "cleaned_text": "",
                "status": "draft",
                "note": str(note or "").strip(),
                "imported_raw_input_id": None,
            }
        )
        self.logger.info(
            "OCR staging record created: id=%s source_type=%s source_name=%s",
            record_id,
            normalized_source_type,
            source_name,
        )
        return record_id

    def list_staging_records(self, status: str | None = None) -> list[dict[str, Any]]:
        normalized_status = self._normalize_status(status) if status else None
        return self.data_pool.list_ocr_staging_records(normalized_status)

    def get_staging_record(self, record_id: int) -> dict[str, Any] | None:
        return self.data_pool.get_ocr_staging_record(record_id)

    def update_staging_record(
        self,
        record_id: int,
        cleaned_text: str,
        note: str,
        status: str,
    ) -> None:
        record = self.data_pool.get_ocr_staging_record(record_id)
        if record is None:
            raise ValueError("暂存记录不存在。")
        if str(record.get("status", "")) == "imported":
            raise ValueError("该暂存记录已导入 raw_inputs，不可重复修改导入状态。")

        normalized_status = self._normalize_status(status)
        if normalized_status == "imported":
            raise ValueError("导入状态仅能由导入操作设置。")
        self.data_pool.update_ocr_staging_record(
            record_id,
            {
                "cleaned_text": str(cleaned_text or "").strip(),
                "note": str(note or "").strip(),
                "status": normalized_status,
            },
        )

    def mark_ignored(self, record_id: int) -> None:
        record = self.data_pool.get_ocr_staging_record(record_id)
        if record is None:
            raise ValueError("暂存记录不存在。")
        if str(record.get("status", "")) == "imported":
            raise ValueError("已导入记录不可忽略。")
        self.data_pool.update_ocr_staging_record(record_id, {"status": "ignored"})

    def import_to_raw_inputs(self, record_id: int) -> dict[str, Any]:
        record = self.data_pool.get_ocr_staging_record(record_id)
        if record is None:
            raise ValueError("暂存记录不存在。")

        current_status = str(record.get("status", "")).strip()
        if current_status == "imported":
            raise ValueError("该暂存记录已导入 raw_inputs，请勿重复导入。")
        if current_status != "confirmed":
            raise ValueError("仅已人工确认的暂存记录可以导入。")

        import_text = (
            str(record.get("cleaned_text", "")).strip()
            or str(record.get("raw_text", "")).strip()
        )
        if not import_text:
            raise ValueError("暂存记录没有可导入的文本内容。")

        source_type = self._map_staging_source_to_raw_input_source(
            str(record.get("source_type", "")).strip()
        )
        source_name = str(record.get("source_name", "")).strip() or "OCR暂存导入"
        note = str(record.get("note", "")).strip()

        result = self.intake_service.submit_raw_input(
            operator_name="OCR暂存导入",
            source_type=source_type,
            source_name=source_name,
            source_path="",
            default_project="其他",
            raw_text=import_text,
            note=note,
        )
        imported_raw_input_id = int(result["id"])
        self.data_pool.update_ocr_staging_record(
            record_id,
            {
                "status": "imported",
                "imported_raw_input_id": imported_raw_input_id,
            },
        )
        self.logger.info(
            "OCR staging imported to raw_inputs: staging_id=%s raw_input_id=%s",
            record_id,
            imported_raw_input_id,
        )
        return {
            "staging_record_id": record_id,
            "imported_raw_input_id": imported_raw_input_id,
            "source_type": source_type,
            "source_name": source_name,
        }

    def get_summary(self) -> dict[str, int]:
        return self.data_pool.count_ocr_staging_records_by_status()

    def _normalize_source_type(self, source_type: str) -> str:
        normalized = str(source_type or "").strip()
        if normalized not in OCR_STAGING_SOURCE_TYPES:
            return "manual_paste"
        return normalized

    def _normalize_status(self, status: str | None) -> str:
        normalized = str(status or "").strip() or "draft"
        if normalized not in OCR_STAGING_STATUSES:
            raise ValueError("OCR 暂存状态无效。")
        return normalized

    def _map_staging_source_to_raw_input_source(self, source_type: str) -> str:
        if source_type == "manual_paste":
            return "paste"
        if source_type in {"future_ocr", "screenshot", "wechat_image"}:
            return "screenshot"
        return "unknown"
