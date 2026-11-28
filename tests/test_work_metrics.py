import unittest
from app.work_metrics import record_revision, summarize, summarize_pool


def row(i=1, **kw):
    return dict(id=i, confirm_status="confirmed", work_date="2026-11-26",
                duration_hours=2.5, worker_names="合成甲、合成乙", employee_confirm_required=0,
                status="完成", project="合成项目", system_category="火灾报警", work_type="维修", **{}) | kw


def allocation(r, people, complete=True):
    return {r['id']: dict(revision=record_revision(r), roster_complete=complete, people=people)}


class WorkMetricsTests(unittest.TestCase):
    def test_legacy_separation(self):
        x = summarize([row()]); self.assertEqual(x['task_elapsed_total_minutes'], 150)
        self.assertEqual(x['legacy_estimated_person_minutes'], 300)
        self.assertIsNone(x['reported_person_total_minutes'])

    def test_actual_partial_shift(self):
        r = row(); x = summarize([r], allocations=allocation(r, {'E1':150,'E2':60}))
        self.assertEqual(x['reported_person_total_minutes'], 210)
        self.assertIsNone(x['legacy_estimated_person_minutes'])
        self.assertEqual(x['by_employee_id']['E2']['known_minutes'],60)

    def test_partial_roster(self):
        r = row(); x = summarize([r], allocations=allocation(r, {'E1':60}, False))
        self.assertEqual(x['reported_person_known_minutes'],60); self.assertIsNone(x['reported_person_total_minutes'])

    def test_missing_and_explicit_zero(self):
        r = row(duration_hours=0); x = summarize([r], allocations=allocation(r, {'E1':0,'E2':None}))
        self.assertIsNone(x['task_elapsed_total_minutes']); self.assertEqual(x['reported_person_known_minutes'],0)
        self.assertIsNone(x['reported_person_total_minutes'])

    def test_mixed_no_combining(self):
        r = row(); x = summarize([r,row(2)], allocations=allocation(r, {'E1':90}))
        self.assertEqual(x['reported_person_known_minutes'],90); self.assertEqual(x['legacy_estimated_person_minutes'],300)
        self.assertIsNone(x['reported_person_total_minutes'])

    def test_unconfirmed_excluded(self):
        x = summarize([row(),row(2,confirm_status='pending'),row(3,confirm_status='ignored')])
        self.assertEqual(x['task_count'],1); self.assertEqual(x['reported_completed_count'],1)

    def test_unresolved_no_estimate(self):
        self.assertIsNone(summarize([row(employee_confirm_required=1)])['legacy_estimated_person_minutes'])

    def test_stale_rejected(self):
        r = row(); a = allocation(r, {'E1':60})
        with self.assertRaises(ValueError): summarize([r | {'updated_at':'new'}], allocations=a)

    def test_invalid_allocation(self):
        r = row()
        for m in (-1,151,True,1.5):
            with self.subTest(m=m),self.assertRaises(ValueError): summarize([r], allocations=allocation(r, {'E1':m}))

    def test_range_and_groups(self):
        x=summarize([row(),row(2,work_date='2026-11-27'),row(3,work_date='2026-02-30')],start='2026-11-26',end='2026-11-26')
        self.assertEqual(x['task_count'],1); self.assertEqual(x['undated_confirmed_in_input'],1)
        self.assertEqual(x['by_system'],{'火灾报警':1})

    def test_duplicate_and_outside_rejected(self):
        with self.assertRaises(ValueError): summarize([row(),row()])
        r=row(2,confirm_status='pending')
        with self.assertRaises(ValueError): summarize([r],allocations=allocation(r, {'E1':1}))

    def test_invalid_hours(self):
        for h in ('nan','inf',-1,25,True,'oops'):
            with self.subTest(h=h): self.assertIsNone(summarize([row(duration_hours=h)])['task_elapsed_total_minutes'])

    def test_empty_and_period_validation(self):
        x=summarize([]); self.assertEqual(x['task_elapsed_total_minutes'],0); self.assertEqual(x['reported_person_total_minutes'],0)
        with self.assertRaises(ValueError): summarize([],start='2026-02-30',end='2026-03-01')

    def test_local_adapter(self):
        class Pool:
            def list_confirmed_records_for_report(self): return [row()]
        self.assertEqual(summarize_pool(Pool()),summarize([row()]))


if __name__ == '__main__': unittest.main()
