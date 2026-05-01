from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time


@dataclass(slots=True)
class MaintenanceRecord:
    project_or_service_object: str = ""
    system_category: str = ""
    work_type: str = ""
    status: str = ""
    record_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    duration_hours: float = 0.0
    personnel: list[str] = field(default_factory=list)
    raw_text: str = ""
    requires_confirmation: bool = False


@dataclass(slots=True)
class RawInputRecord:
    created_at: str
    operator_name: str
    source_type: str
    source_name: str
    source_path: str
    default_project: str
    raw_text: str
    status: str = "pending_parse"
    note: str = ""


@dataclass(slots=True)
class ParsedRecord:
    raw_input_id: int
    created_at: str
    work_date: str = ""
    project: str = ""
    system_category: str = "其他装置及设备"
    work_type: str = "其他"
    status: str = "待确认"
    start_time: str = ""
    end_time: str = ""
    duration_hours: float = 0.0
    wechat_nickname: str = ""
    worker_names: str = ""
    employee_confirm_required: bool = True
    location: str = ""
    device_or_part: str = ""
    problem_description: str = ""
    solution: str = ""
    result: str = ""
    source_raw_text: str = ""
    confirm_status: str = "pending"
    note: str = ""
