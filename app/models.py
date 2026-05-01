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
