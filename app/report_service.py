from __future__ import annotations

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from app.config import (
    APP_INFO,
    REPORTS_DIR,
    ensure_runtime_directories,
    normalize_worker_names_text,
    split_worker_names_text,
)
from app.database import SQLiteDataPool


SYSTEM_CATEGORY_ORDER = ["火灾报警", "视频监控", "其他装置及设备"]
WORK_TYPE_ORDER = [
    "维修",
    "维护",
    "维修或维护",
    "巡检",
    "测试",
    "会议",
    "安全交底",
    "安全交底 / 会议类",
    "培训",
    "施工配合",
    "其他",
]


class DailyReportService:
    def __init__(
        self,
        data_pool: SQLiteDataPool,
        output_dir: Path | None = None,
    ) -> None:
        self.data_pool = data_pool
        self.output_dir = output_dir or (REPORTS_DIR / "daily")
        self.logger = logging.getLogger("ybkj_workflow.report")

    def build_daily_report(
        self,
        date: str,
        filters: dict[str, Any] | None = None,
    ) -> tuple[str, dict[str, Any]]:
        filters = filters or {}
        try:
            records = self.data_pool.list_confirmed_records_for_report(date, filters)
            summary = self.build_summary(records)
            summary["date"] = (date or "").strip()
            summary["filters"] = dict(filters)

            report_text = self._compose_report_text(date, filters, records, summary)
            self.logger.info(
                "Daily report built: date=%s filters=%s confirmed_records=%s total_hours=%.2f",
                date,
                filters,
                summary["record_count"],
                summary["total_duration_hours"],
            )
            return report_text, summary
        except Exception:
            self.logger.exception("Failed to build daily report: date=%s filters=%s", date, filters)
            raise

    def export_daily_report_text(
        self,
        report_text: str,
        date: str,
        suffix: str = "txt",
        record_count: int = 0,
    ) -> Path:
        try:
            ensure_runtime_directories()
            self.output_dir.mkdir(parents=True, exist_ok=True)
            file_suffix = "md" if suffix.lower() == "md" else "txt"
            safe_date = self._sanitize_date_for_filename(date)
            target_path = self.output_dir / f"daily_report_{safe_date}.{file_suffix}"
            export_text = (
                self._to_markdown(report_text)
                if file_suffix == "md"
                else report_text
            )
            with target_path.open("w", encoding="utf-8") as report_file:
                report_file.write(export_text)

            self.logger.info(
                "Daily report exported: path=%s records=%s suffix=%s",
                target_path.as_posix(),
                record_count,
                file_suffix,
            )
            return target_path
        except Exception:
            self.logger.exception(
                "Failed to export daily report: date=%s suffix=%s records=%s",
                date,
                suffix,
                record_count,
            )
            raise

    def build_summary(self, records: list[dict[str, Any]]) -> dict[str, Any]:
        system_counts = {key: 0 for key in SYSTEM_CATEGORY_ORDER}
        work_type_counts: dict[str, int] = {}
        worker_set: set[str] = set()
        total_duration_hours = 0.0
        missing_worker_count = 0
        missing_duration_count = 0

        for record in records:
            system_category = str(record.get("system_category", "") or "其他装置及设备")
            if system_category not in system_counts:
                system_counts[system_category] = 0
            system_counts[system_category] += 1

            work_type = str(record.get("work_type", "") or "其他")
            work_type_counts[work_type] = work_type_counts.get(work_type, 0) + 1

            names = self._split_worker_names(str(record.get("worker_names", "")))
            if names:
                worker_set.update(names)
            else:
                missing_worker_count += 1

            try:
                duration_value = float(record.get("duration_hours", 0) or 0)
            except (TypeError, ValueError):
                duration_value = 0.0
            if duration_value > 0:
                total_duration_hours += duration_value
            else:
                missing_duration_count += 1

        ordered_work_type_counts: dict[str, int] = {}
        for key in WORK_TYPE_ORDER:
            if key in work_type_counts:
                ordered_work_type_counts[key] = work_type_counts[key]
        for key in sorted(work_type_counts):
            if key not in ordered_work_type_counts:
                ordered_work_type_counts[key] = work_type_counts[key]

        return {
            "record_count": len(records),
            "system_category_counts": system_counts,
            "work_type_counts": ordered_work_type_counts,
            "workers": sorted(worker_set),
            "worker_count": len(worker_set),
            "total_duration_hours": round(total_duration_hours, 2),
            "missing_worker_count": missing_worker_count,
            "missing_duration_count": missing_duration_count,
        }

    def _compose_report_text(
        self,
        date: str,
        filters: dict[str, Any],
        records: list[dict[str, Any]],
        summary: dict[str, Any],
    ) -> str:
        generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
        project_text = str(filters.get("project", "全部") or "全部")
        workers_text = "、".join(summary["workers"]) if summary["workers"] else "无"

        lines = [
            "【维保日报通】",
            f"日期：{date or '全部日期'}",
            f"项目：{project_text}",
            f"生成时间：{generated_at}",
            "数据来源：已确认记录",
            "",
            "一、今日工作概览",
            f"今日共确认工作记录 {summary['record_count']} 条。",
            "其中：",
            f"- 火灾报警：{summary['system_category_counts'].get('火灾报警', 0)} 条",
            f"- 视频监控：{summary['system_category_counts'].get('视频监控', 0)} 条",
            f"- 其他装置及设备：{summary['system_category_counts'].get('其他装置及设备', 0)} 条",
            f"- 总工时：{summary['total_duration_hours']} H",
            f"- 参与人员：{workers_text}",
            "",
            "二、分类明细",
        ]

        grouped_records = self._group_by_system_category(records)
        displayed_group = False
        for category in SYSTEM_CATEGORY_ORDER:
            category_records = grouped_records.get(category, [])
            if not category_records:
                continue
            displayed_group = True
            lines.append("")
            lines.append(f"【{category}】")
            for index, record in enumerate(category_records, start=1):
                lines.append(f"{index}. {self._format_record_line(record)}")

        if not displayed_group:
            lines.append("")
            lines.append("当前筛选条件下没有已确认记录，请先到人工确认页确认记录。")

        lines.extend(
            [
                "",
                "三、待关注事项",
                f"- 未填写人员记录：{summary['missing_worker_count']} 条",
                f"- 未填写工时记录：{summary['missing_duration_count']} 条",
                "- 建议人工复核后再对外发送。",
                "",
                "四、备注",
                f"本日报由 {APP_INFO.project_name_en} / {APP_INFO.tool_name} 本地生成。",
                f"Developer: {APP_INFO.developer}",
                f"Version: {APP_INFO.version}",
            ]
        )

        return "\n".join(lines)

    def _group_by_system_category(
        self,
        records: list[dict[str, Any]],
    ) -> dict[str, list[dict[str, Any]]]:
        grouped: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            category = str(record.get("system_category", "") or "其他装置及设备")
            grouped.setdefault(category, []).append(record)
        return grouped

    def _format_record_line(self, record: dict[str, Any]) -> str:
        time_text = self._format_time_text(
            str(record.get("start_time", "")),
            str(record.get("end_time", "")),
        )
        worker_text = str(record.get("worker_names", "")).strip() or "人员待确认"
        worker_text = normalize_worker_names_text(worker_text) or "人员待确认"
        project_text = str(record.get("project", "")).strip() or "项目待确认"
        work_type_text = str(record.get("work_type", "")).strip() or "其他"
        result_text = self._display_result(record)
        description_text = self._display_description(record)
        return (
            f"{time_text}｜{worker_text}｜{project_text}｜{work_type_text}｜"
            f"{description_text}，结果：{result_text}"
        )

    def _format_time_text(self, start_time: str, end_time: str) -> str:
        start_time = start_time.strip()
        end_time = end_time.strip()
        if start_time and end_time:
            return f"{start_time}-{end_time}"
        if start_time:
            return f"{start_time}-时间待确认"
        if end_time:
            return f"时间待确认-{end_time}"
        return "时间待确认"

    def _display_result(self, record: dict[str, Any]) -> str:
        result_text = str(record.get("result", "")).strip()
        if result_text:
            return result_text
        status_text = str(record.get("status", "")).strip()
        return status_text or "待确认"

    def _display_description(self, record: dict[str, Any]) -> str:
        for field_name in (
            "problem_description",
            "solution",
            "device_or_part",
            "location",
            "source_raw_text",
        ):
            value = str(record.get(field_name, "")).strip()
            if value:
                return value.replace("\n", " ")[:120]
        return "内容待补充"

    def _split_worker_names(self, worker_names: str) -> list[str]:
        return split_worker_names_text(worker_names)

    def _sanitize_date_for_filename(self, date: str) -> str:
        normalized_date = (date or "").strip() or datetime.now().strftime("%Y-%m-%d")
        sanitized = re.sub(r"[^0-9\-]", "-", normalized_date)
        return sanitized or datetime.now().strftime("%Y-%m-%d")

    def _to_markdown(self, report_text: str) -> str:
        lines = report_text.splitlines()
        markdown_lines: list[str] = []
        for line in lines:
            if line == "【维保日报通】":
                markdown_lines.append("# 维保日报通")
            elif line.startswith("一、"):
                markdown_lines.append(f"## {line}")
            elif line.startswith("二、") or line.startswith("三、") or line.startswith("四、"):
                markdown_lines.append(f"## {line}")
            elif line.startswith("【") and line.endswith("】"):
                markdown_lines.append(f"### {line[1:-1]}")
            else:
                markdown_lines.append(line)
        return "\n".join(markdown_lines)
