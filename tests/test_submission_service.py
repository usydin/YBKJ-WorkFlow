import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app.backup import JSONLBackupService
from app.database import SQLiteDataPool
from app.intake_service import IntakeService
from app.parser_engine import ParserEngine
from app.submission_service import SubmissionService, scoped_key
from app.work_metrics import summarize_pool

TEXT = "2026-11-26 09:00-10:30 合成火灾报警设备检查完成"


class SubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.db = SQLiteDataPool(root / "test.sqlite")
        with patch("app.database.ensure_runtime_directories"):
            self.db.initialize()
        self.backup = JSONLBackupService(root / "backup.jsonl")
        self.backup.raw_inputs_path = root / "raw.jsonl"
        self.intake = IntakeService(self.db, self.backup)
        self.parser = ParserEngine(self.db)
        self.svc = SubmissionService(self.intake, self.parser)
        self.key = str(uuid4())

    def submit(self, actor="SYNTH-E1", key=None, text=TEXT, **kw):
        return self.svc.submit(actor_id=actor, request_id=key or self.key,
                               project="合成项目", text=text, **kw)

    def parse(self, actor="SYNTH-E1", key=None):
        return self.svc.parse(actor_id=actor, request_id=key or self.key)

    def status(self, actor="SYNTH-E1", key=None):
        return self.svc.status(actor_id=actor, request_id=key or self.key)

    def test_commit_then_target_parse(self):
        a=self.submit(); b=self.parse()
        self.assertEqual(a["parse_status"],"SAVED_AWAITING_PARSE")
        self.assertEqual(b["parse_status"],"REVIEW_RECORDS_AVAILABLE")
        self.assertEqual(b["review_counts"],{"pending":1,"confirmed":0,"ignored":0})
        self.assertEqual(summarize_pool(self.db)["task_count"],0)
        self.assertEqual(self.db.get_parsed_record(1)["source_raw_text"],TEXT)

    def test_other_queue_untouched(self):
        a=self.submit(); b=self.submit(key=str(uuid4()))
        self.parse()
        self.assertEqual([r["id"] for r in self.db.get_pending_raw_inputs()],[b["raw_input_id"]])

    def test_actor_isolation_and_same_key(self):
        a=self.submit()
        self.assertIsNone(self.status("SYNTH-E2")); self.assertIsNone(self.parse("SYNTH-E2"))
        b=self.submit("SYNTH-E2")
        self.assertNotEqual(a["raw_input_id"],b["raw_input_id"])
        self.assertEqual(self.parse()["record_count"],1)
        self.assertEqual(self.status("SYNTH-E2")["record_count"],0)

    def test_replay_after_review_uses_current_state(self):
        a=self.submit(); self.parse()
        row=self.db.list_parsed_records()[0]
        self.db.apply_record_review(row["id"],row,{},"SYNTH-REVIEW","confirm")
        b=self.submit(); self.assertTrue(b["replayed"])
        self.assertEqual(b["raw_input_id"],a["raw_input_id"])
        self.assertEqual(b["review_counts"]["confirmed"],1)
        self.assertEqual(self.parse()["record_count"],1)
        self.assertEqual(summarize_pool(self.db)["task_count"],1)

    def test_conflicting_replay_rejected(self):
        self.submit()
        with self.assertRaises(ValueError): self.submit(text=TEXT+" 修订")
        self.assertEqual(len(self.db.get_pending_raw_inputs()),1)

    def test_backup_failure_does_not_lose_submission(self):
        with patch.object(self.backup,"append_raw_input",side_effect=OSError("synthetic")):
            a=self.submit()
        self.assertEqual(a["backup_status"],"PENDING")
        self.assertEqual(a["submission_status"],"COMMITTED")
        self.assertEqual(self.submit()["backup_status"],"SYNCED")

    def test_parse_fault_retry(self):
        self.submit()
        with patch.object(self.db,"_mark_pending_parsed",side_effect=RuntimeError("synthetic")):
            a=self.parse()
        self.assertEqual(a["parse_status"],"PARSE_RETRY_REQUIRED")
        self.assertEqual(a["record_count"],0)
        self.assertEqual(self.parse()["record_count"],1)

    def test_concurrent_submit_and_parse(self):
        with ThreadPoolExecutor(max_workers=2) as pool:
            a,b=list(pool.map(lambda _:self.submit(),range(2)))
            self.assertEqual(a["raw_input_id"],b["raw_input_id"])
            a,b=list(pool.map(lambda _:self.parse(),range(2)))
        self.assertEqual(a["record_count"],1)
        self.assertEqual(b["record_count"],1)
        self.assertEqual(len(self.db.list_parsed_records()),1)

    def test_legacy_partial_held(self):
        a=self.submit()
        self.db.insert_parsed_records(self.parser.parse_text(TEXT,raw_input_id=a["raw_input_id"]))
        self.assertEqual(self.parse()["parse_status"],"RECONCILIATION_REQUIRED")
        self.assertEqual(len(self.db.list_parsed_records()),1)

    def test_invalid_inputs(self):
        for text in [" ", "中"*6000, "x\n"*101, "\x00x"]:
            with self.subTest(text_length=len(text)),self.assertRaises(ValueError): self.submit(text=text)
        with self.assertRaises(ValueError): self.submit(source="screenshot")
        with self.assertRaises(ValueError): self.submit(actor="bad\nid")
        with self.assertRaises(ValueError): self.submit(key="not-a-uuid")
        self.assertEqual(len(self.db.get_pending_raw_inputs()),0)

    def test_post_commit_status_unavailable(self):
        with patch.object(self.db,"read_submission_snapshot",side_effect=OSError("synthetic")):
            a=self.submit()
        self.assertEqual(a["submission_status"],"COMMITTED")
        self.assertEqual(a["parse_status"],"STATUS_UNKNOWN")
        self.assertIsNone(a["record_count"])
        self.assertEqual(self.submit()["raw_input_id"],a["raw_input_id"])

    def test_receipt_no_raw_content(self):
        a=self.submit(); self.parse(); b=self.status()
        for receipt in [a,b]:
            self.assertFalse({"raw_text","operator_name","source_raw_text","request_key"} & receipt.keys())
        self.assertNotEqual(scoped_key("SYNTH-E1",self.key),scoped_key("SYNTH-E2",self.key))


if __name__=="__main__":
    unittest.main()
