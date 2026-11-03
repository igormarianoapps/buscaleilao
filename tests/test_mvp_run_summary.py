"""Regression tests for the per-execution MVP status summary."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from tempfile import TemporaryDirectory
from datetime import datetime, timezone

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
import mvp_run_summary as status

class SummaryTests(unittest.TestCase):
    def test_missing_optional_results_are_not_claimed_complete(self):
        report={"checked_at":"2026-11-03T20:07:57+00:00",
                "unique_events":39,"states_with_events":["GO","SP"],
                "curated_success":13,"curated_failure":7}
        summary=status.summarize(report)
        self.assertIn("39",summary)
        self.assertIn("não produzido nesta coleta",summary)
        self.assertIn("três execuções completas consecutivas",summary)

    def test_pncp_and_vip_results_distinguished(self):
        report={"checked_at":"2026-11-03T20:07:57+00:00"}
        summary=status.summarize(report,
            pncp={"count":4,"errors":[{"error":"HTTP 429"}]},
            review={"unverified_count":9,"pncp_leads":4},
            vip={"status":"partial_cards_fallback","candidate_cards":2})
        self.assertIn("4 candidatos; 1 erros",summary)
        self.assertIn("partial_cards_fallback; 2 cartões",summary)

    def test_stale_file_not_reused_as_new_evidence(self):
        with TemporaryDirectory() as tmp:
            with patch.object(status,"ROOT",Path(tmp)):
                (Path(tmp)/"pncp-candidates.json").write_text(
                    '{"checked_at":"2026-11-02T12:00:00+00:00","count":50}',
                    encoding="utf-8")
                self.assertIsNone(status.read_current(
                    "pncp-candidates.json","2026-11-03T20:07:57+00:00"))
                (Path(tmp)/"pncp-candidates.json").write_text(
                    '{"checked_at":"2026-11-03T20:08:01+00:00","count":5}',
                    encoding="utf-8")
                self.assertEqual(status.read_current(
                    "pncp-candidates.json","2026-11-03T20:07:57+00:00")["count"],5)

if __name__=="__main__":
    unittest.main()
