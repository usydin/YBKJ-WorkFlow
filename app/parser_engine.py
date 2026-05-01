from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any

from app.database import SQLiteDataPool
from app.models import ParsedRecord


class ParserEngine:
    DATE_PATTERN = re.compile(r"(20\d{2})-(\d{1,2})-(\d{1,2})")
    TIME_RANGE_PATTERN = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")
    SENDER_PATTERN = re.compile(r"^([\u4e00-\u9fffA-Za-z0-9_()（）\-·]{2,20})[:：]")

    def __init__(self, data_pool: SQLiteDataPool) -> None:
        self.data_pool = data_pool
        self.logger = logging.getLogger("ybkj_workflow.parser")

    def parse_text(
        self,
        input_text: str,
        *,
        raw_input_id: int = 0,
        operator_name: str = "",
        default_project: str = "",
    ) -> list[ParsedRecord]:
        normalized_text = input_text.strip()
        if not normalized_text:
            return []

        segments = self._split_text(normalized_text)
        if not segments:
            segments = [normalized_text]

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            self._parse_segment(
                segment,
                raw_input_id=raw_input_id,
                created_at=created_at,
                operator_name=operator_name,
                default_project=default_project,
            )
            for segment in segments
        ]

    def classify_record(self, record: ParsedRecord) -> dict[str, Any]:
        return {
            "project": record.project,
            "system_category": record.system_category,
            "work_type": record.work_type,
            "status": record.status,
        }

    def merge_similar_records(self, records: list[ParsedRecord]) -> list[ParsedRecord]:
        return records

    def process_pending_records(self) -> dict[str, int]:
        pending_inputs = self.data_pool.get_pending_raw_inputs()
        generated_count = 0
        pending_confirm_count = 0
        parsed_raw_inputs = 0

        for raw_input in pending_inputs:
            try:
                parsed_records = self.parse_text(
                    raw_input.get("raw_text", ""),
                    raw_input_id=int(raw_input["id"]),
                    operator_name=str(raw_input.get("operator_name", "")),
                    default_project=str(raw_input.get("default_project", "")),
                )
                if not parsed_records:
                    parsed_records = [
                        self._create_fallback_record(
                            raw_input_id=int(raw_input["id"]),
                            raw_text=str(raw_input.get("raw_text", "")),
                            operator_name=str(raw_input.get("operator_name", "")),
                            default_project=str(raw_input.get("default_project", "")),
                        )
                    ]

                generated_count += self.data_pool.insert_parsed_records(parsed_records)
                pending_confirm_count += sum(
                    1 for record in parsed_records if record.confirm_status == "pending"
                )
                self.data_pool.update_raw_input_status(int(raw_input["id"]), "parsed")
                parsed_raw_inputs += 1
            except Exception:
                self.logger.exception(
                    "Failed to parse raw_input id=%s", raw_input.get("id", "unknown")
                )

        self.logger.info(
            "Parser run completed: raw_inputs=%s parsed_records=%s pending_confirm=%s",
            parsed_raw_inputs,
            generated_count,
            pending_confirm_count,
        )
        return {
            "raw_inputs_parsed": parsed_raw_inputs,
            "parsed_records_generated": generated_count,
            "pending_confirm_records": pending_confirm_count,
        }

    def _split_text(self, text: str) -> list[str]:
        lines = [line.strip() for line in text.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            return []

        segments: list[str] = []
        buffer: list[str] = []

        for line in lines:
            starts_new_segment = bool(
                self.DATE_PATTERN.search(line)
                or self.TIME_RANGE_PATTERN.search(line)
                or re.match(r"^\d+[\.、\)]", line)
                or re.match(r"^[一二三四五六七八九十]+[、\.]", line)
            )

            if starts_new_segment and buffer:
                segments.append("\n".join(buffer))
                buffer = [line]
            else:
                buffer.append(line)

        if buffer:
            segments.append("\n".join(buffer))

        return segments or [text]

    def _parse_segment(
        self,
        segment: str,
        *,
        raw_input_id: int,
        created_at: str,
        operator_name: str,
        default_project: str,
    ) -> ParsedRecord:
        work_date = self._extract_date(segment)
        start_time, end_time, duration_hours = self._extract_time_range(segment)
        parsed_status = self._extract_status(segment)
        work_type = self._extract_work_type(segment)
        system_category = self._extract_system_category(segment)
        project = self._extract_project(segment, default_project)
        wechat_nickname = self._extract_sender(segment) or operator_name.strip()
        real_name = self.data_pool.resolve_employee_alias(wechat_nickname)
        worker_names = real_name or wechat_nickname or operator_name.strip()
        employee_confirm_required = not bool(real_name)

        return ParsedRecord(
            raw_input_id=raw_input_id,
            created_at=created_at,
            work_date=work_date,
            project=project,
            system_category=system_category,
            work_type=work_type,
            status=parsed_status,
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            wechat_nickname=wechat_nickname,
            worker_names=worker_names,
            employee_confirm_required=employee_confirm_required,
            problem_description=self._extract_problem_description(segment),
            solution=self._extract_solution(segment),
            result=parsed_status,
            source_raw_text=segment,
            confirm_status="pending",
            note="V0.1 自动解析结果，待人工确认",
        )

    def _create_fallback_record(
        self,
        *,
        raw_input_id: int,
        raw_text: str,
        operator_name: str,
        default_project: str,
    ) -> ParsedRecord:
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return ParsedRecord(
            raw_input_id=raw_input_id,
            created_at=created_at,
            project=default_project or "其他",
            wechat_nickname=operator_name,
            worker_names=operator_name or "待确认",
            employee_confirm_required=True,
            source_raw_text=raw_text,
            note="拆分失败，已按整段原文生成待确认记录",
        )

    def _extract_date(self, text: str) -> str:
        match = self.DATE_PATTERN.search(text)
        if not match:
            return ""
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"

    def _extract_time_range(self, text: str) -> tuple[str, str, float]:
        match = self.TIME_RANGE_PATTERN.search(text)
        if not match:
            return "", "", 0.0

        start_time, end_time = match.groups()
        try:
            start_dt = datetime.strptime(start_time, "%H:%M")
            end_dt = datetime.strptime(end_time, "%H:%M")
            duration = max((end_dt - start_dt).total_seconds() / 3600, 0.0)
        except ValueError:
            duration = 0.0

        return start_time, end_time, round(duration, 2)

    def _extract_status(self, text: str) -> str:
        if any(keyword in text for keyword in ("未完成", "待处理", "继续处理", "未恢复")):
            return "未完成"
        if any(keyword in text for keyword in ("已完成", "完成", "恢复正常")):
            return "完成"
        return "待确认"

    def _extract_work_type(self, text: str) -> str:
        if any(keyword in text for keyword in ("班前会", "安全交底")):
            return "安全交底 / 会议类"
        if "培训" in text:
            return "培训"
        if "巡检" in text:
            return "巡检"
        if any(keyword in text for keyword in ("联动测试", "声光测试", "测试")):
            return "测试"
        if any(keyword in text for keyword in ("清理", "更换", "维修", "处理", "恢复")):
            return "维修或维护"
        return "其他"

    def _extract_system_category(self, text: str) -> str:
        fire_keywords = (
            "火灾报警",
            "烟感",
            "温感",
            "手报",
            "模块",
            "声光",
            "FAR",
            "FCR",
            "报警主机",
        )
        video_keywords = (
            "摄像头",
            "监控",
            "录像机",
            "硬盘",
            "NVR",
            "DVR",
            "交换机",
            "视频",
        )
        if any(keyword in text for keyword in fire_keywords):
            return "火灾报警"
        if any(keyword in text for keyword in video_keywords):
            return "视频监控"
        return "其他装置及设备"

    def _extract_project(self, text: str, default_project: str) -> str:
        project_keywords = (
            "石炼化",
            "康石",
            "沧炼",
            "人才公寓",
            "信息中心",
            "行政",
            "幼儿园",
        )
        for keyword in project_keywords:
            if keyword in text:
                return keyword
        return default_project or "其他"

    def _extract_sender(self, text: str) -> str:
        first_line = text.splitlines()[0].strip() if text.splitlines() else text.strip()
        match = self.SENDER_PATTERN.match(first_line)
        return "" if match is None else match.group(1)

    def _extract_problem_description(self, text: str) -> str:
        for keyword in ("故障", "报警", "异常", "损坏", "不亮", "不通"):
            if keyword in text:
                return text[:160]
        return ""

    def _extract_solution(self, text: str) -> str:
        if any(keyword in text for keyword in ("更换", "维修", "处理", "恢复", "清理")):
            return text[:160]
        return ""
