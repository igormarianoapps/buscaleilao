"""Regression tests for review queue: never publish guessed auction events."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from prioritize_leads import prioritize

NOW=datetime(2026,11,3,tzinfo=timezone.utc)

class ReviewTests(unittest.TestCase):
    def test_recent_official_lead_prioritized(self):
        items=[
          {"title":"Prefeitura realizará leilão de veículos em novembro","published":"Thu, 22 Oct 2026 07:00:00 GMT","url":"https://news.google.com/a","publisher_url":"https://example.gov.br","source_priority":"official"},
          {"title":"Leilão de veículos antigos","published":"Wed, 01 Jan 2020 07:00:00 GMT","url":"https://news.google.com/b","publisher_url":"https://example.com","source_priority":"other"}
        ]
        result=prioritize(items, NOW)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["review_status"],"needs_official_event_page")
        self.assertNotIn("auction_date",result[0])
    def test_non_vehicle_rejected(self):
        self.assertEqual(prioritize([{"title":"Leilão de imóveis","published":"Thu, 22 Oct 2026 07:00:00 GMT","url":"https://news.google.com/a"}],NOW),[])

if __name__=="__main__":
    unittest.main()
