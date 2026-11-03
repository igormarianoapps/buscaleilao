"""Offline regression tests for independent collection, caching and trust boundaries."""
import sys
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from source_collector import collect_curated, validate

def source(id,url,evidence=None):
    return {"id":id,"source_url":url,"title":"Leilão",
            "auction_date":"2099-11-04","auction_time":"10:00",
            "state":"GO","city":"Goiânia","organizer":"Prefeitura",
            "source_type":"municipal","vehicle_count":None,
            "evidence":evidence or ["04/11/2099","leilão"]}

class SourceCollectorTests(unittest.TestCase):
    def test_one_fetch_for_shared_url_and_individual_validation(self):
        page="Leilão 04/11/2099 com 20 lotes"
        items=[source("good","https://example.org/a"),
               source("bad","https://example.org/a",["outro edital"])]
        with patch("source_collector.fetch_text",return_value=page) as mocked:
            events,failed,health=collect_curated(items,checked="2099-01-01T00:00:00Z")
        self.assertEqual(mocked.call_count,1)
        self.assertEqual([e["id"] for e in events],["good"])
        self.assertEqual([e["id"] for e in failed],["bad"])
        self.assertEqual(health["successful_sources"],1)
        self.assertEqual(health["failed_sources"],1)

    def test_shared_page_preserves_static_and_browser_evidence(self):
        items=[
            source("static","https://example.org/shared",["notice A"]),
            source("dynamic","https://example.org/shared",["notice B"])
        ]
        with patch("source_collector.fetch_text",return_value="notice A"):
            events,failed,_=collect_curated(
                items,browser_loader=lambda urls:{urls[0]:("notice B",None)})
        self.assertEqual({e["id"] for e in events},{"static","dynamic"})
        self.assertEqual(failed,[])

    def test_one_failure_does_not_stop_other_sources(self):
        def fetching(url):
            if url.endswith("/blocked"):
                raise OSError("connection timeout")
            return "Leilão 04/11/2099 confirmado"
        with patch("source_collector.fetch_text",side_effect=fetching):
            events,failed,health=collect_curated(
                [source("blocked","https://example.org/blocked"),
                 source("good","https://example.org/ok")])
        self.assertEqual([x["id"] for x in events],["good"])
        self.assertEqual([x["id"] for x in failed],["blocked"])

    def test_browser_retry_for_missing_evidence(self):
        with patch("source_collector.fetch_text",return_value="Carregando..."):
            events,failed,health=collect_curated(
                [source("dynamic","https://example.org/dynamic")],
                browser_loader=lambda urls:{urls[0]:("Leilão 04/11/2099",None)})
        self.assertEqual(len(events),1)
        self.assertEqual(failed,[])

    def test_does_not_retry_explicit_access_denial(self):
        with patch("source_collector.fetch_text",side_effect=OSError("HTTP 403 Forbidden")):
            def forbidden(_):
                self.fail("Must not retry access restrictions")
            events,failed,_=collect_curated(
                [source("blocked","https://example.org/private")],
                browser_loader=forbidden)
        self.assertEqual(events,[])
        self.assertEqual(len(failed),1)

    def test_rate_limit_respected_without_browser_retry(self):
        with patch("source_collector.fetch_text",side_effect=OSError("HTTP Error 429: Too Many Requests")):
            def blocked(_):
                self.fail("HTTP 429 must wait for another scheduled collection")
            records,failed,_=collect_curated(
                [source("rate-limit","https://example.org/429")],
                browser_loader=blocked)
        self.assertEqual(records,[])
        self.assertEqual(failed[0]["id"],"rate-limit")

    def test_previous_health_tracks_failures(self):
        with patch("source_collector.fetch_text",side_effect=OSError("timeout")):
            _,_,health=collect_curated(
                [source("one","https://example.org/a")],
                previous_health={"sources":{"one":{"consecutive_failures":3,"last_success_at":"2099-01-01"}}})
        self.assertEqual(health["sources"]["one"]["consecutive_failures"],4)
        self.assertEqual(health["sources"]["one"]["last_success_at"],"2099-01-01")

    def test_cancellation_rejected(self):
        with self.assertRaises(ValueError):
            validate("Leilão 04/11/2099. Leilão cancelado.", source("a","https://example.org/a"))

if __name__=="__main__":
    unittest.main()
