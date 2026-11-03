"""MVP release gates: event integrity and safe optional discovery ordering."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from validate_feed import validate_feed

NOW=datetime(2026,11,3,17,0,tzinfo=timezone.utc)
STAMP="2026-11-03T16:59:00+00:00"

def sample():
    row={"id":"one","title":"Leilão de veículos","state":"GO","city":"Goiânia",
         "auction_date":"2026-11-09","auction_time":None,"organizer":"Detran",
         "source_url":"https://goias.gov.br/leilao"}
    return {"updated_at":STAMP,"events":[row]}, {"checked_at":STAMP,
        "verified":1,"unique_events":1}

class GateTests(unittest.TestCase):
    def test_valid_feed_passes(self):
        feed,report=sample()
        self.assertEqual(validate_feed(feed,report,NOW),[])
    def test_empty_feed_never_replaces_last_good_feed(self):
        feed,report=sample()
        feed["events"]=[]
        self.assertTrue(validate_feed(feed,report,NOW))
    def test_bad_link_or_date_or_state_rejected(self):
        for key,value in [("source_url","http://example.org"),
                          ("auction_date","2020-01-01"),
                          ("state","XX")]:
            with self.subTest(field=key):
                feed,report=sample()
                feed["events"][0][key]=value
                self.assertTrue(validate_feed(feed,report,NOW))
    def test_duplicate_event_id_rows_rejected(self):
        feed,report=sample()
        feed["events"].append(dict(feed["events"][0]))
        report["verified"]=2
        self.assertTrue(any("duplicate ID" in e for e in validate_feed(feed,report,NOW)))
    def test_multistate_entries_share_identity(self):
        feed,report=sample()
        feed["events"][0].update({"id":"one-go","event_id":"one",
                                   "states":["GO","DF"]})
        another=dict(feed["events"][0],id="one-df",state="DF")
        feed["events"].append(another)
        report["verified"]=2
        self.assertEqual(validate_feed(feed,report,NOW),[])
    def test_report_mismatch_rejected(self):
        feed,report=sample()
        report["unique_events"]=7
        self.assertTrue(validate_feed(feed,report,NOW))
    def test_workflow_publishes_feed_before_optional_discovery(self):
        yaml=(ROOT/".github/workflows/collect.yml").read_text(encoding="utf-8")
        names=["Validate verified auction feed","Publish verified feed first",
               "Discover new auction leads","Discover official PNCP auction notices",
               "Prioritize unverified discovery leads","Publish optional research diagnostics"]
        offsets=[yaml.index("- name: "+name) for name in names]
        self.assertEqual(offsets,sorted(offsets))
        for name in ("Discover new auction leads",
                     "Discover official PNCP auction notices",
                     "Prioritize unverified discovery leads"):
            self.assertIn("continue-on-error: true",
                yaml.split("- name: "+name,1)[1].split("- name:",1)[0])
        core=yaml.split("- name: Publish verified feed first",1)[1].split("- name:",1)[0]
        self.assertIn("git add app/events.json app/collection-report.json app/source-health.json",core)
        self.assertNotIn("pncp-candidates.json",core)

if __name__=="__main__":
    unittest.main()
