import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from app.backup import JSONLBackupService
from app.database import SQLiteDataPool
from app.intake_service import IntakeService
from app.parser_engine import ParserEngine
from app.submission_service import SubmissionService
from app.review_service import ScopedReviewService
from app.work_metrics import summarize_pool


class ScopedReviewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root=Path(self.tmp.name)
        self.db=SQLiteDataPool(root/"test.sqlite")
        with patch("app.database.ensure_runtime_directories"):
            self.db.initialize()
        backup=JSONLBackupService(root/"backup.jsonl")
        backup.raw_inputs_path=root/"raw.jsonl"
        self.svc=SubmissionService(IntakeService(self.db,backup),ParserEngine(self.db))
        self.review=ScopedReviewService(self.db,actor_id="REVIEW-1",projects=("SYNTH-A",))
        self.rid=self.make("SYNTH-A")

    def make(self, project):
        key=str(uuid4())
        self.svc.submit(actor_id="SYNTH-E1",request_id=key,project=project,text="2026-11-26 09:00-10:00 合成火灾报警检查完成")
        self.svc.parse(actor_id="SYNTH-E1",request_id=key)
        return max(r["id"] for r in self.db.list_parsed_records())

    def apply(self, action="confirm", updates=None, revision=None):
        return self.review.apply(self.rid,revision=revision or self.review.get(self.rid)["revision"],
                                 action=action,updates=updates if updates is not None else {"project":"SYNTH-A"})

    def test_confirm_and_audit_and_metrics(self):
        a=self.apply()
        self.assertEqual(a["record"]["record"]["confirm_status"],"confirmed")
        self.assertEqual(summarize_pool(self.db)["task_count"],1)
        with sqlite3.connect(self.db.db_path) as c:
            self.assertEqual(c.execute("SELECT actor,action FROM record_review_events WHERE id=?",(a["event_id"],)).fetchone(),("REVIEW-1","confirm"))

    def test_scope_denies_read_and_write(self):
        other=self.make("SYNTH-B")
        self.assertIsNone(self.review.get(other))
        self.assertEqual([x["record"]["id"] for x in self.review.list()["items"]],[self.rid])
        with self.assertRaises(PermissionError):
            self.review.apply(other,revision="0"*64,action="ignore",updates={})
        self.assertEqual(self.db.get_parsed_record(other)["confirm_status"],"pending")

    def test_no_scope(self):
        empty=ScopedReviewService(self.db,actor_id="REVIEW-2",projects=())
        self.assertEqual(empty.list(),{"items":[],"next_after_id":None})
        self.assertIsNone(empty.get(self.rid))

    def test_inferred_project_not_authority(self):
        self.db.update_parsed_record(self.rid,{"project":"SYNTH-B"})
        self.assertTrue(self.review.get(self.rid)["project_mismatch"])
        self.assertIsNone(ScopedReviewService(self.db,actor_id="REVIEW-2",projects=("SYNTH-B",)).get(self.rid))
        with self.assertRaises(ValueError): self.apply(updates={})
        self.assertFalse(self.apply()["record"]["project_mismatch"])

    def test_transfer_and_protected_fields_rejected(self):
        for updates in ({"project":"SYNTH-B"},{"raw_input_id":2},{"source_raw_text":"changed"},{"worker_names":"forged"}):
            with self.subTest(updates=updates),self.assertRaises(ValueError): self.apply(updates=updates)

    def test_stale_revision_rejected(self):
        rev=self.review.get(self.rid)["revision"]
        self.apply("update",{"note":"first"})
        with self.assertRaises(ValueError): self.apply(revision=rev)
        self.assertEqual(self.db.get_parsed_record(self.rid)["note"],"first")

    def test_terminal_reopen_required(self):
        self.apply()
        with self.assertRaises(ValueError): self.apply("update",{"note":"changed"})
        with self.assertRaises(ValueError): self.apply("restore_pending",{"note":"changed"})
        self.apply("restore_pending",{})
        self.assertEqual(summarize_pool(self.db)["task_count"],0)
        self.apply("ignore",{})
        self.assertEqual(self.db.get_parsed_record(self.rid)["confirm_status"],"ignored")

    def test_scope_rechecked_in_transaction(self):
        original=self.db.apply_record_review
        def race(*args,**kwargs):
            with sqlite3.connect(self.db.db_path) as c:
                c.execute("UPDATE raw_inputs SET default_project='SYNTH-B' WHERE id=(SELECT raw_input_id FROM parsed_records WHERE id=?)",(self.rid,))
            return original(*args,**kwargs)
        with patch.object(self.db,"apply_record_review",side_effect=race),self.assertRaises(PermissionError):
            self.apply()
        self.assertEqual(self.db.get_parsed_record(self.rid)["confirm_status"],"pending")

    def test_date_and_page_validation(self):
        with self.assertRaises(ValueError): self.apply(updates={"work_date":"2026-02-30"})
        with self.assertRaises(ValueError): self.review.list(limit=101)
        with self.assertRaises(ValueError): self.review.get(True)
        second=self.make("SYNTH-A")
        page=self.review.list(limit=1)
        self.assertEqual(page["next_after_id"],self.rid)
        self.assertEqual(self.review.list(after_id=self.rid)["items"][0]["record"]["id"],second)

    def test_audit_failure_rolls_back(self):
        with sqlite3.connect(self.db.db_path) as c:
            c.execute("CREATE TRIGGER synthetic_fail BEFORE INSERT ON record_review_events BEGIN SELECT RAISE(ABORT,'synthetic'); END")
        with self.assertRaises(sqlite3.IntegrityError): self.apply()
        self.assertEqual(self.db.get_parsed_record(self.rid)["confirm_status"],"pending")

    def test_legacy_not_in_scoped_queue(self):
        with sqlite3.connect(self.db.db_path) as c:
            c.execute("UPDATE raw_input_backup_outbox SET request_key=NULL")
        self.assertIsNone(self.review.get(self.rid))


if __name__=="__main__":
    unittest.main()
