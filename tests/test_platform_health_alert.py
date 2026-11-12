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
if __name__=="__main__":unittest.main()
