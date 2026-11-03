"""Regression tests for UTC midnight vs Brasília local auction day."""
import sys
import unittest
from datetime import date, datetime, timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from auction_clock import auction_today
from browser_collect import future_date
from validate_feed import validate_feed
from freitas_collect import parse_detail

class AuctionClockTests(unittest.TestCase):
    def test_utc_midnight_still_previous_day_in_brazil(self):
        utc_midnight=datetime(2026,11,4,0,30,tzinfo=timezone.utc)
        self.assertEqual(auction_today(utc_midnight),date(2026,11,3))

    def test_utc_early_morning_after_brazil_midnight(self):
        now=datetime(2026,11,4,3,30,tzinfo=timezone.utc)
        self.assertEqual(auction_today(now),date(2026,11,4))

    def test_naive_datetime_rejected(self):
        with self.assertRaises(ValueError):
            auction_today(datetime(2026,11,3))

    def test_feed_valid_on_brazilian_event_day_at_utc_midnight(self):
        now=datetime(2026,11,4,0,30,tzinfo=timezone.utc)
        stamp="2026-11-04T00:28:00+00:00"
        feed={"updated_at":stamp,"events":[{
            "id":"go-event","title":"Leilão de veículos","state":"GO",
            "auction_date":"2026-11-03","organizer":"Detran",
            "source_url":"https://goias.gov.br/evento"}]}
        report={"checked_at":stamp,"verified":1,"unique_events":1}
        self.assertEqual(validate_feed(feed,report,now),[])

    def test_previous_brazilian_day_is_expired(self):
        now=datetime(2026,11,4,3,30,tzinfo=timezone.utc)
        stamp="2026-11-04T03:28:00+00:00"
        feed={"updated_at":stamp,"events":[{
            "id":"go-event","title":"Leilão de veículos","state":"GO",
            "auction_date":"2026-11-03","organizer":"Detran",
            "source_url":"https://goias.gov.br/evento"}]}
        report={"checked_at":stamp,"verified":1,"unique_events":1}
        self.assertTrue(any("expired date" in error for error in
                            validate_feed(feed,report,now)))

if __name__=="__main__": unittest.main()
