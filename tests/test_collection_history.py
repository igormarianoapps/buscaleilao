"""P0.2 progress counts verified collection checkpoints, never unit-test runs."""
import sys
import unittest
from datetime import datetime,timezone,timedelta
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from record_collection_history import build_history

BASE=datetime(2026,11,3,20,43,tzinfo=timezone.utc)
def report(stamp, count=48):
    return {"checked_at":stamp.isoformat(timespec="seconds"),"unique_events":count,
            "states_with_events":["GO","SP"],"curated_success":19,"curated_failure":3}

class StabilityLedgerTests(unittest.TestCase):
    def test_three_consecutive_runs_still_require_github_success(self):
        first=build_history({},report(BASE),"100","1",BASE+timedelta(minutes=1))
        second_time=BASE+timedelta(hours=12)
        second=build_history(first,report(second_time),"101","1",second_time+timedelta(minutes=1))
        third_time=second_time+timedelta(hours=12)
        third=build_history(second,report(third_time),"102","1",third_time+timedelta(minutes=1))
        self.assertEqual(third["consecutive_recorded_runs"],3)
        self.assertTrue(third["requires_confirmed_workflow_success"])
        self.assertEqual(len(third["runs"]),3)
    def test_repeat_of_same_attempt_is_idempotent(self):
        first=build_history({},report(BASE),"100","1",BASE+timedelta(minutes=1))
        twice=build_history(first,report(BASE),"100","1",BASE+timedelta(minutes=2))
        self.assertEqual(len(twice["runs"]),1)
        self.assertEqual(twice["consecutive_recorded_runs"],1)
    def test_long_gap_resets_stability_sequence(self):
        first=build_history({},report(BASE),"100","1",BASE+timedelta(minutes=1))
        later=BASE+timedelta(hours=25)
        result=build_history(first,report(later),"101","1",later+timedelta(minutes=1))
        self.assertEqual(result["consecutive_recorded_runs"],1)
    def test_stale_report_cannot_be_recorded(self):
        with self.assertRaises(ValueError):
            build_history({},report(BASE),"100","1",BASE+timedelta(hours=3))
    def test_fake_test_run_identifier_cannot_be_recorded(self):
        with self.assertRaises(ValueError):
            build_history({},report(BASE),"not-a-run","1",BASE+timedelta(minutes=1))
    def test_workflow_records_only_after_feed_and_research(self):
        yaml=(Path(__file__).resolve().parents[1]/".github/workflows/collect.yml").read_text(encoding="utf-8")
        self.assertLess(yaml.index("- name: Publish verified feed first"),
                        yaml.index("- name: Record P0.2 collection history"))
        self.assertLess(yaml.index("- name: Publish optional research diagnostics"),
                        yaml.index("- name: Record P0.2 collection history"))

if __name__=="__main__":unittest.main()
