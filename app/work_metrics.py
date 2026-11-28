"""Read-side maintenance metrics V1. No storage, authorization or device state writes."""
from collections import Counter
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json
import re


def record_revision(row):
    """Bind an allocation snapshot to the exact reviewed legacy record."""
    return hashlib.sha256(json.dumps(dict(row), sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(",", ":")).encode()).hexdigest()


def _day(value):
    try:
        d = date.fromisoformat(value)
        return d.isoformat() if d.isoformat() == value else None
    except (ValueError, TypeError):
        return None


def _elapsed(value):
    # Legacy zero is a missing-value sentinel. Do not invent an actual zero.
    try:
        h = Decimal(str(value))
        if not h.is_finite() or not 0 < h <= 24:
            return None
        return int((h * 60).quantize(Decimal("1"), rounding=ROUND_HALF_UP)) or None
    except (InvalidOperation, ValueError, TypeError):
        return None


def summarize(rows, *, allocations=None, start=None, end=None):
    """Aggregate caller-scoped records, by work_date (not clock-day allocation).

    allocations maps integer record IDs to {revision, roster_complete, people},
    with people mapping stable employee IDs to integer minutes or None. The
    caller must establish authority/provenance; this module does not do so.
    Explicit allocations are reported task allocations, not attendance or payroll.
    Legacy name-based estimates remain separate and are never added to them.
    """
    if (start is None) != (end is None) or (start is not None and
            (not _day(start) or not _day(end) or start > end)):
        raise ValueError("invalid inclusive work-date range")
    allocations = {} if allocations is None else allocations
    if not isinstance(allocations, dict):
        raise ValueError("invalid allocations")
    seen, selected = set(), []
    undated = 0
    for row in rows:
        if row.get("confirm_status") != "confirmed":
            continue
        rid = row.get("id")
        if type(rid) is not int or rid <= 0 or rid in seen:
            raise ValueError("invalid or duplicate confirmed record ID")
        seen.add(rid)
        day = _day(row.get("work_date"))
        undated += day is None
        if start is None or (day is not None and start <= day <= end):
            selected.append((row, day))
    if any(type(k) is not int for k in allocations) or not allocations.keys() <= {r["id"] for r, _ in selected}:
        raise ValueError("allocation outside selected confirmed records")
    elapsed = missing = completed = known_person = known_slots = complete = estimate = estimate_tasks = 0
    people, systems, work_types, projects, days = {}, Counter(), Counter(), Counter(), Counter()
    for row, day in selected:
        rid = row["id"]
        minutes = _elapsed(row.get("duration_hours"))
        missing += minutes is None
        elapsed += minutes or 0
        completed += row.get("status") == "完成"
        for counter, key in ((systems, "system_category"), (work_types, "work_type"), (projects, "project")):
            counter[str(row.get(key) or "待确认")] += 1
        days[day or "待确认日期"] += 1
        if rid in allocations:
            a = allocations[rid]
            if (not isinstance(a, dict) or set(a) != {"revision", "roster_complete", "people"}
                    or a["revision"] != record_revision(row) or type(a["roster_complete"]) is not bool
                    or not isinstance(a["people"], dict) or not a["people"]):
                raise ValueError("invalid or stale participation snapshot")
            for employee, m in a["people"].items():
                if (not isinstance(employee, str) or not employee.strip() or employee != employee.strip()
                        or len(employee) > 128 or (m is not None and
                        (type(m) is not int or not 0 <= m <= 1440 or (minutes is not None and m > minutes)))):
                    raise ValueError("invalid participant allocation")
                bucket = people.setdefault(employee, {"task_count": 0, "known_minutes": 0, "missing_count": 0})
                bucket["task_count"] += 1
                bucket["missing_count"] += m is None
                bucket["known_minutes"] += m or 0
                known_slots += m is not None
                known_person += m or 0
            complete += a["roster_complete"] and all(m is not None for m in a["people"].values())
        else:
            names = {n for n in re.split(r"[、，,/\s；;]+", str(row.get("worker_names") or "")) if n}
            if minutes is not None and names and row.get("employee_confirm_required") in (0, False):
                estimate += minutes * len(names)
                estimate_tasks += 1
    n = len(selected)
    return {
        "contract": "WORKFLOW_METRICS_V1", "start_date": start, "end_date": end,
        "task_count": n, "reported_completed_count": completed,
        "task_elapsed_known_minutes": elapsed if n != missing or not n else None,
        "task_elapsed_total_minutes": elapsed if not missing else None,
        "task_elapsed_missing_count": missing,
        "reported_person_known_minutes": known_person if known_slots or not n else None,
        "reported_person_total_minutes": known_person if complete == n else None,
        "complete_participation_task_count": complete, "incomplete_participation_task_count": n - complete,
        "legacy_estimated_person_minutes": estimate if estimate_tasks else None,
        "legacy_estimate_task_count": estimate_tasks, "undated_confirmed_in_input": undated,
        "by_employee_id": dict(sorted(people.items())), "by_system": dict(sorted(systems.items())),
        "by_work_type": dict(sorted(work_types.items())), "by_project": dict(sorted(projects.items())),
        "by_work_date": dict(sorted(days.items())),
    }


def summarize_pool(data_pool, *, start=None, end=None, allocations=None):
    """Local desktop adapter only; HTTP callers must supply a scoped row snapshot."""
    return summarize(data_pool.list_confirmed_records_for_report(),
                     start=start, end=end, allocations=allocations)
