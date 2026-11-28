"""Project-scoped review adapter for trusted local callers, not an HTTP authorization layer."""
from datetime import date
import re

from app.submission_service import ACTOR
from app.work_metrics import record_revision

EDITABLE = {"work_date", "project", "system_category", "work_type", "status",
            "location", "device_or_part", "problem_description", "solution", "result", "note"}


class ScopedReviewService:
    def __init__(self, pool, *, actor_id: str, projects: tuple[str, ...]):
        if not isinstance(actor_id, str) or not ACTOR.fullmatch(actor_id):
            raise ValueError("invalid trusted reviewer")
        if not isinstance(projects, tuple) or len(projects) > 100 or any(
            not isinstance(p, str) or not p or p != p.strip() or len(p) > 120
            or any(ord(c) < 32 for c in p) for p in projects
        ):
            raise ValueError("invalid trusted project scope")
        self.pool, self.actor_id, self.projects = pool, actor_id, tuple(sorted(set(projects)))

    @staticmethod
    def _present(row):
        scope = row["scope_project"]
        record = {k: v for k, v in row.items() if k != "scope_project"}
        return {"scope_project": scope, "project_mismatch": record["project"] != scope,
                "revision": record_revision(record), "record": record}

    def list(self, *, after_id: int = 0, limit: int = 50):
        if type(after_id) is not int or not 0 <= after_id < 2**63-1 or type(limit) is not int or not 1 <= limit <= 100:
            raise ValueError("invalid review page")
        rows = self.pool.list_scoped_review_rows(self.projects, after_id, limit+1)
        return {"items": [self._present(r) for r in rows[:limit]],
                "next_after_id": rows[limit-1]["id"] if len(rows) > limit else None}

    def get(self, record_id: int):
        if type(record_id) is not int or not 1 <= record_id < 2**63:
            raise ValueError("invalid record ID")
        rows = self.pool.list_scoped_review_rows(self.projects, record_id-1, 1)
        return self._present(rows[0]) if rows and rows[0]["id"] == record_id else None

    def apply(self, record_id: int, *, revision: str, action: str, updates: dict):
        current = self.get(record_id)
        if current is None:
            raise PermissionError("record unavailable")
        if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{64}", revision) or current["revision"] != revision:
            raise ValueError("stale review revision")
        if action not in ("update", "confirm", "ignore", "restore_pending"):
            raise ValueError("invalid review action")
        if not isinstance(updates, dict) or not set(updates) <= EDITABLE or any(
            not isinstance(v, str) or len(v) > 4096 or "\x00" in v for v in updates.values()
        ):
            raise ValueError("invalid or protected review fields")
        if "work_date" in updates or action == "confirm":
            day = updates.get("work_date", current["record"]["work_date"])
            if day or action == "confirm":
                if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
                    raise ValueError("valid work date required")
        result = self.pool.apply_record_review(
            record_id, current["record"], updates, self.actor_id, action,
            scope_project=current["scope_project"],
        )
        return {"event_id": result["event_id"], "record": self._present(
            {**result["after"], "scope_project": current["scope_project"]})}
