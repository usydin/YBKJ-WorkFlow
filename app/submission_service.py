"""Scoped text submission use cases. Trusted caller only; no HTTP or auth implementation."""
from __future__ import annotations

import hashlib
import json
import logging
import re
from uuid import UUID

from app.intake_service import IntakeService
from app.parser_engine import ParserEngine

LOG = logging.getLogger("ybkj_workflow.submission")
MAX_TEXT_BYTES = 16384
MAX_LINES = 100
ACTOR = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:@-]{0,127}")


def scoped_key(actor_id: str, request_id: str) -> str:
    if not isinstance(actor_id, str) or not ACTOR.fullmatch(actor_id):
        raise ValueError("invalid trusted actor ID")
    if not isinstance(request_id, str) or len(request_id) != 36:
        raise ValueError("canonical UUID request ID required")
    if str(UUID(request_id)) != request_id:
        raise ValueError("canonical UUID request ID required")
    return "wf1:" + hashlib.sha256(json.dumps(
        [actor_id, request_id], separators=(",", ":")
    ).encode("utf-8")).hexdigest()


class SubmissionService:
    """Single database namespace. Actor/project authorization belongs to the adapter."""
    def __init__(self, intake: IntakeService, parser: ParserEngine):
        if intake.data_pool is not parser.data_pool:
            raise ValueError("submission and parser must share one pool")
        self.intake, self.parser, self.pool = intake, parser, intake.data_pool

    def _snapshot(self, actor_id, request_id):
        return self.pool.read_submission_snapshot(scoped_key(actor_id, request_id), actor_id)

    @staticmethod
    def _receipt(snapshot):
        if snapshot is None:
            return None
        raw, counts = snapshot["raw"], snapshot["review_counts"]
        total = sum(counts.values())
        if raw["status"] == "pending_parse":
            phase = "RECONCILIATION_REQUIRED" if total else "SAVED_AWAITING_PARSE"
        elif raw["status"] == "parsed" and total and set(counts) <= {"pending", "confirmed", "ignored"}:
            phase = "REVIEW_RECORDS_AVAILABLE"
        else:
            phase = "RECONCILIATION_REQUIRED"
        return {
            "submission_status": "COMMITTED",
            "raw_input_id": raw["id"],
            "parse_status": phase,
            "backup_status": "SYNCED" if raw["backup_delivered_at"] is not None else "PENDING",
            "record_count": total,
            "review_counts": {s: counts.get(s, 0) for s in ("pending", "confirmed", "ignored")},
        }

    def status(self, *, actor_id: str, request_id: str):
        return self._receipt(self._snapshot(actor_id, request_id))

    def submit(self, *, actor_id: str, request_id: str, project: str, text: str, source: str = "paste"):
        key = scoped_key(actor_id, request_id)
        if not isinstance(text, str) or not text.strip() or len(text.encode("utf-8")) > MAX_TEXT_BYTES or len(text.splitlines()) > MAX_LINES or "\x00" in text:
            raise ValueError("invalid or oversized submission text")
        if not isinstance(project, str) or not project.strip() or len(project) > 120 or any(ord(c)<32 for c in project):
            raise ValueError("invalid authorized project label")
        if source not in ("paste", "manual"):
            raise ValueError("unsupported text source")
        saved = self.intake.submit_raw_input(
            operator_name=actor_id, source_type=source, source_name="业务文本录入",
            source_path="", default_project=project, raw_text=text, request_key=key,
        )
        # Intake has already committed. A later status-read failure must not imply rollback.
        try:
            receipt = self.status(actor_id=actor_id, request_id=request_id)
            if receipt is None:
                raise RuntimeError("committed submission missing")
        except Exception:
            LOG.warning("Submission status unavailable after commit")
            receipt = {"submission_status": "COMMITTED", "raw_input_id": saved["id"],
                       "parse_status": "STATUS_UNKNOWN", "backup_status": saved["backup_status"],
                       "record_count": None, "review_counts": None}
        return {**receipt, "replayed": saved["replayed"]}

    def parse(self, *, actor_id: str, request_id: str):
        """Only process the named submission. Never scan the global pending queue."""
        snap = self._snapshot(actor_id, request_id)
        receipt = self._receipt(snap)
        if receipt is None or receipt["parse_status"] != "SAVED_AWAITING_PARSE":
            return receipt
        raw = snap["raw"]
        failed = False
        try:
            records = self.parser.parse_text(
                raw["raw_text"], raw_input_id=raw["id"], operator_name=raw["operator_name"],
                default_project=raw["default_project"],
            )
            self.pool.commit_pending_parse(raw["id"], records)
        except Exception:
            failed = True
            LOG.warning("Scoped parse did not complete; raw_id=%s", raw["id"])
        try:
            latest = self.status(actor_id=actor_id, request_id=request_id)
            if latest is None:
                raise RuntimeError("committed submission missing")
        except Exception:
            return {**receipt, "parse_status": "STATUS_UNKNOWN",
                    "record_count": None, "review_counts": None}
        if failed and latest["parse_status"] == "SAVED_AWAITING_PARSE":
            latest["parse_status"] = "PARSE_RETRY_REQUIRED"
        return latest
