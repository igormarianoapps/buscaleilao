import sys,unittest
from pathlib import Path
from datetime import datetime,timezone
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from platform_health_alert import assess
class CollectorHealthTests(unittest.TestCase):
 def test_reports_blocked_site_without_failing_verified_events(self):
    now=datetime(2026,11,12,12,0,tzinfo=timezone.utc)
    sources=[{"id":"milan"},{"id":"leilo"}]
    combined={"platforms":{"milan":{"availability":"unavailable"},
                            "leilo":{"availability":"reachable","discovered_links":10}}}
    q={"per_platform":{"milan":{"verified_events":0},"leilo":{"verified_events":3}}}
    feed={"updated_at":now.isoformat(),"events":[{"id":"a","event_id":"a"},{"id":"a-go","event_id":"a"}]}
    report=assess(sources,combined,q,feed,now)
    self.assertEqual(report["sources_reachable"],1)
    self.assertEqual(report["sources_with_events"],1)
    self.assertEqual(report["unique_feed_events"],1)
    self.assertTrue(report["feed_fresh"])
    self.assertTrue(any("milan" in x for x in report["warnings"]))
 def test_marks_stale_feed_as_warning(self):
    now=datetime(2026,11,12,12,0,tzinfo=timezone.utc)
    r=assess([],{"platforms":{}},{},{"events":[],"updated_at":"2026-11-01T00:00:00Z"},now)
    self.assertFalse(r["feed_fresh"])
    self.assertGreaterEqual(r["warning_count"],2)

class OperationalHealthTests(unittest.TestCase):
 def test_reachable_zero_is_not_a_failure(self):
    now=datetime(2026,11,12,12,0,tzinfo=timezone.utc)
    a=assess([{"id":"empty"}],{"platforms":{"empty":{"availability":"reachable","discovered_links":0}}},
        {"per_platform":{"empty":{"verified_events":0}}},
        {"updated_at":now.isoformat(),"events":[{"id":"a"}]},now)
    self.assertEqual(a["sources"]["empty"]["condition"],"reachable_no_verified_events")
    self.assertEqual(a["warning_count"],0)
 def test_alerts_on_disappearing_events(self):
    now=datetime(2026,11,12,12,0,tzinfo=timezone.utc)
    a=assess([{"id":"vip"}],{"platforms":{"vip":{"availability":"reachable"}}},
        {"per_platform":{"vip":{"verified_events":0}}},
        {"updated_at":now.isoformat(),"events":[{"id":"a"}]},now,
        previous={"sources":{"vip":{"verified_events":12}},"unique_feed_events":20})
    self.assertTrue(any("vip: lost all" in w for w in a["warnings"]))
    self.assertTrue(any("dropped sharply" in w for w in a["warnings"]))
 def test_freshness_is_distinct_from_preserving_old_feed(self):
    now=datetime(2026,11,12,12,0,tzinfo=timezone.utc)
    a=assess([],{"platforms":{}},{},
        {"updated_at":"2026-11-10T00:00:00+00:00","events":[{"id":"a"}]},now)
    self.assertEqual(a["feed_status"],"stale_or_unavailable")
    self.assertFalse(a["feed_fresh"])

if __name__=="__main__":unittest.main()
