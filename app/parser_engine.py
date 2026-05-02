from __future__ import annotations

import logging
import re
from collections import Counter
from datetime import datetime
from typing import Any

from app.config import extract_wechat_sender, is_reserved_person_name
from app.database import SQLiteDataPool
from app.models import ParsedRecord


class ParserEngine:
    DATE_PATTERN = re.compile(r"(20\d{2})-(\d{1,2})-(\d{1,2})")
    TIME_RANGE_PATTERN = re.compile(r"(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})")
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
        parsed_records = [
            self._parse_segment(
                segment,
                raw_input_id=raw_input_id,
                created_at=created_at,
                operator_name=operator_name,
                default_project=default_project,
            )
            for segment in segments
        ]
        self._mark_duplicate_hints(parsed_records)
        return parsed_records

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
        parse_warning_count = 0
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
                parse_warning_count += sum(
                    1 for record in parsed_records if "解析提示" in str(record.note or "")
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
            "parse_warning_records": parse_warning_count,
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
        _ = operator_name
        work_date = self._extract_date(segment)
        start_time, end_time, duration_hours = self._extract_time_range(segment)
        parsed_status = self._extract_status(segment)
        work_type = self._extract_work_type(segment)
        system_category = self._extract_system_category(segment)
        project = self._extract_project(segment, default_project)
        location = self._extract_location(segment)
        wechat_nickname = self._sanitize_wechat_nickname(self._extract_sender(segment))
        mapping_result = self.data_pool.resolve_worker_names(wechat_nickname)
        worker_names = mapping_result["mapped_names"]
        employee_confirm_required = mapping_result["employee_confirm_required"]
        parse_note = self._build_parse_note(
            segment=segment,
            work_date=work_date,
            system_category=system_category,
            work_type=work_type,
            location=location,
            wechat_nickname=wechat_nickname,
            worker_names=worker_names,
            employee_confirm_required=employee_confirm_required,
        )

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
            location=location,
            problem_description=self._extract_problem_description(segment),
            solution=self._extract_solution(segment),
            result=parsed_status,
            source_raw_text=segment,
            confirm_status="pending",
            note=parse_note,
        )

    def _create_fallback_record(
        self,
        *,
        raw_input_id: int,
        raw_text: str,
        operator_name: str,
        default_project: str,
    ) -> ParsedRecord:
        _ = operator_name
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        wechat_nickname = self._sanitize_wechat_nickname(self._extract_sender(raw_text))
        mapping_result = self.data_pool.resolve_worker_names(wechat_nickname)
        worker_names = mapping_result["mapped_names"]
        employee_confirm_required = mapping_result["employee_confirm_required"]

        return ParsedRecord(
            raw_input_id=raw_input_id,
            created_at=created_at,
            project=default_project or "其他",
            wechat_nickname=wechat_nickname,
            worker_names=worker_names,
            employee_confirm_required=employee_confirm_required,
            source_raw_text=raw_text,
            note=self._build_parse_note(
                segment=raw_text,
                work_date="",
                system_category="",
                work_type="",
                location="",
                wechat_nickname=wechat_nickname,
                worker_names=worker_names,
                employee_confirm_required=employee_confirm_required,
                base_message="拆分失败，已按整段原文生成待确认记录",
            ),
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
        return ""

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
        return ""

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
        return extract_wechat_sender(text)

    def _sanitize_wechat_nickname(self, nickname: str) -> str:
        normalized_nickname = str(nickname or "").strip()
        if not normalized_nickname or is_reserved_person_name(normalized_nickname):
            return ""
        return normalized_nickname

    def _extract_location(self, text: str) -> str:
        patterns = (
            r"([\u4e00-\u9fffA-Za-z0-9]+机柜间[A-Za-z0-9]*)",
            r"([\u4e00-\u9fffA-Za-z0-9]+地下车库[\u4e00-\u9fffA-Za-z0-9]*)",
            r"([\u4e00-\u9fffA-Za-z0-9]+办公楼\d*层)",
            r"([\u4e00-\u9fffA-Za-z0-9]+值班室)",
            r"([\u4e00-\u9fffA-Za-z0-9]+岗亭)",
            r"([\u4e00-\u9fffA-Za-z0-9]+门岗)",
            r"([\u4e00-\u9fffA-Za-z0-9]+泵房)",
            r"([\u4e00-\u9fffA-Za-z0-9]+走廊)",
            r"([\u4e00-\u9fffA-Za-z0-9]+操场[\u4e00-\u9fffA-Za-z0-9]*)",
            r"(装置[A-Za-z0-9]+)",
        )
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_problem_description(self, text: str) -> str:
        for keyword in ("故障", "报警", "异常", "损坏", "不亮", "不通"):
            if keyword in text:
                return text[:160]
        return ""

    def _extract_solution(self, text: str) -> str:
        if any(keyword in text for keyword in ("更换", "维修", "处理", "恢复", "清理")):
            return text[:160]
        return ""

    def _build_parse_note(
        self,
        *,
        segment: str,
        work_date: str,
        system_category: str,
        work_type: str,
        location: str,
        wechat_nickname: str,
        worker_names: str,
        employee_confirm_required: bool,
        base_message: str = "V0.4 自动解析结果，待人工确认",
    ) -> str:
        warnings: list[str] = []
        normalized_segment = str(segment or "").strip()
        raw_sender = self._extract_sender(normalized_segment)

        if not work_date:
            warnings.append("缺少日期")
        if not worker_names:
            warnings.append("缺少维修人员")
        elif employee_confirm_required:
            warnings.append("人员需映射确认")
        if not location:
            warnings.append("缺少地点")
        if not system_category:
            warnings.append("缺少系统类别")
        if not work_type:
            warnings.append("缺少工作类型")
        if len(re.sub(r"\s+", "", normalized_segment)) < 24:
            warnings.append("原始文本过短")
        if re.search(r"(一起|两个人|多人|协助|跟着处理|共同处理|一块处理)", normalized_segment):
            warnings.append("多人参与但主维修人员不明确")
        if raw_sender and is_reserved_person_name(raw_sender):
            warnings.append("出现保留名 ybkj-pL")
        if raw_sender and not wechat_nickname and is_reserved_person_name(raw_sender):
            warnings.append("发送人被保留名规则拦截")

        if warnings:
            return f"{base_message}；解析提示：" + "；".join(dict.fromkeys(warnings))
        return base_message

    def _mark_duplicate_hints(self, records: list[ParsedRecord]) -> None:
        if not records:
            return

        recent_records = self.data_pool.get_recent_parsed_records(limit=200)
        batch_counter = Counter(self._build_duplicate_signature(record) for record in records)
        existing_signatures = {
            self._build_duplicate_signature_from_row(row)
            for row in recent_records
            if int(row.get("raw_input_id", 0)) != 0
        }

        for record in records:
            signature = self._build_duplicate_signature(record)
            if not signature:
                continue
            is_duplicate = batch_counter[signature] > 1 or signature in existing_signatures
            if is_duplicate:
                record.note = self._append_warning(record.note, "疑似重复记录")

    def _build_duplicate_signature(self, record: ParsedRecord) -> str:
        summary = (
            record.problem_description.strip()
            or record.solution.strip()
            or record.source_raw_text.strip()
        )
        normalized_summary = re.sub(r"[\W_]+", "", summary.casefold())
        if len(normalized_summary) < 8:
            return ""
        return "|".join(
            [
                record.work_date.strip(),
                record.project.strip(),
                record.location.strip(),
                normalized_summary[:48],
            ]
        )

    def _build_duplicate_signature_from_row(self, row: dict[str, Any]) -> str:
        summary = (
            str(row.get("problem_description", "")).strip()
            or str(row.get("solution", "")).strip()
            or str(row.get("source_raw_text", "")).strip()
        )
        normalized_summary = re.sub(r"[\W_]+", "", summary.casefold())
        if len(normalized_summary) < 8:
            return ""
        return "|".join(
            [
                str(row.get("work_date", "")).strip(),
                str(row.get("project", "")).strip(),
                str(row.get("location", "")).strip(),
                normalized_summary[:48],
            ]
        )

    def _append_warning(self, note: str, warning: str) -> str:
        normalized_note = str(note or "").strip()
        if not normalized_note:
            return f"解析提示：{warning}"
        if warning in normalized_note:
            return normalized_note
        if "解析提示：" in normalized_note:
            return f"{normalized_note}；{warning}"
        return f"{normalized_note}；解析提示：{warning}"
