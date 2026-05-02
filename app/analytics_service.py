from __future__ import annotations

import logging
from typing import Any

from app.config import split_worker_names_text
from app.database import SQLiteDataPool


SYSTEM_CATEGORY_KEYS = ("火灾报警", "视频监控", "其他装置及设备")


class AnalyticsService:
    def __init__(self, data_pool: SQLiteDataPool) -> None:
        self.data_pool = data_pool
        self.logger = logging.getLogger("ybkj_workflow.analytics")

    def get_overview(self, filters: dict[str, Any] | None = None) -> dict[str, Any]:
        records = self.get_detail_records(filters)
        worker_set: set[str] = set()
        total_duration_hours = 0.0
        missing_worker_count = 0
        missing_duration_count = 0
        system_counts = {key: 0 for key in SYSTEM_CATEGORY_KEYS}

        for record in records:
            category = self._normalize_system_category(record.get("system_category", ""))
            system_counts[category] = system_counts.get(category, 0) + 1

            worker_names = self._split_worker_names(str(record.get("worker_names", "")))
            if worker_names:
                worker_set.update(worker_names)
            else:
                missing_worker_count += 1

            duration_value = self._to_duration(record.get("duration_hours", 0))
            if duration_value > 0:
                total_duration_hours += duration_value
            else:
                missing_duration_count += 1

        overview = {
            "total_records": len(records),
            "total_duration_hours": round(total_duration_hours, 2),
            "unique_workers": len(worker_set),
            "missing_worker_count": missing_worker_count,
            "missing_duration_count": missing_duration_count,
            "fire_alarm_count": system_counts.get("火灾报警", 0),
            "video_count": system_counts.get("视频监控", 0),
            "other_count": system_counts.get("其他装置及设备", 0),
        }
        return overview

    def get_by_worker(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        records = self.get_detail_records(filters)
        buckets: dict[str, dict[str, Any]] = {}

        for record in records:
            worker_names = self._split_worker_names(str(record.get("worker_names", "")))
            if not worker_names:
                worker_names = ["人员待确认"]

            duration_value = self._to_duration(record.get("duration_hours", 0))
            category = self._normalize_system_category(record.get("system_category", ""))

            for worker_name in worker_names:
                bucket = buckets.setdefault(
                    worker_name,
                    {
                        "worker_name": worker_name,
                        "record_count": 0,
                        "total_duration_hours": 0.0,
                        "fire_alarm_count": 0,
                        "video_count": 0,
                        "other_count": 0,
                        "missing_duration_count": 0,
                    },
                )
                bucket["record_count"] += 1
                if duration_value > 0:
                    bucket["total_duration_hours"] += duration_value
                else:
                    bucket["missing_duration_count"] += 1

                if category == "火灾报警":
                    bucket["fire_alarm_count"] += 1
                elif category == "视频监控":
                    bucket["video_count"] += 1
                else:
                    bucket["other_count"] += 1

        return self._sort_rows(
            [
                {
                    **row,
                    "total_duration_hours": round(float(row["total_duration_hours"]), 2),
                }
                for row in buckets.values()
            ],
            name_key="worker_name",
        )

    def get_by_project(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self._aggregate_simple(filters, "project", "其他")

    def get_by_system_category(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        rows = self._aggregate_simple(filters, "system_category", "其他装置及设备")
        return self._sort_rows(rows, name_key="system_category")

    def get_by_work_type(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self._aggregate_simple(filters, "work_type", "其他")

    def get_detail_records(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        return self.data_pool.list_confirmed_records_for_analytics(filters)

    def _aggregate_simple(
        self,
        filters: dict[str, Any] | None,
        key: str,
        default_label: str,
    ) -> list[dict[str, Any]]:
        records = self.get_detail_records(filters)
        buckets: dict[str, dict[str, Any]] = {}

        for record in records:
            raw_value = str(record.get(key, "")).strip()
            if key == "system_category":
                label = self._normalize_system_category(raw_value)
            else:
                label = raw_value or default_label

            bucket = buckets.setdefault(
                label,
                {
                    key: label,
                    "record_count": 0,
                    "total_duration_hours": 0.0,
                },
            )
            bucket["record_count"] += 1
            bucket["total_duration_hours"] += self._to_duration(record.get("duration_hours", 0))

        return self._sort_rows(
            [
                {
                    **row,
                    "total_duration_hours": round(float(row["total_duration_hours"]), 2),
                }
                for row in buckets.values()
            ],
            name_key=key,
        )

    def _sort_rows(self, rows: list[dict[str, Any]], name_key: str) -> list[dict[str, Any]]:
        return sorted(
            rows,
            key=lambda item: (
                -int(item.get("record_count", 0)),
                -float(item.get("total_duration_hours", 0) or 0),
                str(item.get(name_key, "")),
            ),
        )

    def _split_worker_names(self, worker_names: str) -> list[str]:
        return split_worker_names_text(worker_names)

    def _normalize_system_category(self, value: Any) -> str:
        normalized = str(value or "").strip()
        if normalized in SYSTEM_CATEGORY_KEYS:
            return normalized
        return "其他装置及设备"

    def _to_duration(self, value: Any) -> float:
        try:
            duration_value = float(value or 0)
        except (TypeError, ValueError):
            duration_value = 0.0
        return max(duration_value, 0.0)
