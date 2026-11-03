"""Regression tests for review queue: never publish guessed auction events."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from prioritize_leads import prioritize, explicit_auction_date, merge_review_sources

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
    def test_expired_auction_with_explicit_date_removed(self):
        items=[{"title":"Detran realiza leilão de veículos em 28/10/2026",
                "published":"Mon, 19 Oct 2026 07:00:00 GMT",
                "url":"https://news.google.com/old","source_priority":"official"}]
        self.assertEqual(prioritize(items,NOW),[])

    def test_próximo_dia_28_published_in_october_is_past(self):
        items=[{"title":"Detran-PR promove leilão de veículos no próximo dia 28",
                "published":"Mon, 19 Oct 2026 07:00:00 GMT",
                "url":"https://news.google.com/oct","source_priority":"official"}]
        self.assertEqual(prioritize(items,NOW),[])

    def test_future_date_is_hint_not_verified_event(self):
        items=[{"title":"Prefeitura promoverá leilão de veículos em 12 de novembro de 2026",
                "published":"Thu, 22 Oct 2026 07:00:00 GMT",
                "url":"https://news.google.com/future","source_priority":"official"}]
        result=prioritize(items,NOW)
        self.assertEqual(len(result),1)
        self.assertEqual(result[0]["date_hint"],"2026-11-12")
        self.assertEqual(result[0]["date_hint_status"],"headline_only_unverified")
        self.assertNotIn("auction_date",result[0])

    def test_ambiguous_date_stays_unverified(self):
        from email.utils import parsedate_to_datetime
        published=parsedate_to_datetime("Thu, 22 Oct 2026 07:00:00 GMT")
        self.assertIsNone(explicit_auction_date("Leilão veículos dia 5",published))

    def test_pncp_and_rss_review_merged_without_publishing(self):
        pncp=[{"title":"Leilão de veículos","state":"AC","city":"Rio Branco",
               "date_hint":"2026-11-18","date_hint_status":"pncp_deadline_unverified",
               "pncp_control":"123-1-1/2026",
               "source_url":"https://pncp.gov.br/app/editais/123/2026/1"}]
        rss=[{"title":"Notícia veículos","news_url":"https://news.google.com/item",
              "priority":2,"review_status":"needs_official_event_page"}]
        merged=merge_review_sources(rss,pncp)
        self.assertEqual(len(merged),2)
        self.assertEqual(merged[0]["source_kind"],"pncp")
        self.assertEqual(merged[0]["state_hint"],"AC")
        self.assertNotIn("auction_date",merged[0])
        self.assertEqual(merged[1]["source_kind"],"news_rss")

    def test_already_curated_pncp_notice_excluded_from_queue(self):
        source_url="https://pncp.gov.br/app/editais/123/2026/1"
        item={"title":"Leilão veículos","source_url":source_url,
              "date_hint":None}
        self.assertEqual(merge_review_sources([],[item],
                         [{"source_url":source_url}]),[])

    def test_non_vehicle_rejected(self):
        self.assertEqual(prioritize([{"title":"Leilão de imóveis","published":"Thu, 22 Oct 2026 07:00:00 GMT","url":"https://news.google.com/a"}],NOW),[])

if __name__=="__main__":
    unittest.main()
