import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from platform_coverage_gate import assess, BLOCKERS

def site(key):
    return {"id": key, "name": key}

class CoverageGateTests(unittest.TestCase):
    def test_all_17_sources_have_explicit_diagnosis(self):
        keys = ["leilo", "mcleilao", "flex", "parque", "sodre",
                "copart", "loop", "freitas", "milan", "vip",
                "hisa", "bolsa", "vardana", "claudio",
                "palacio", "rogerio", "pmklog"]
        q = {"per_platform": {k: {"verified_events": (1 if k=="vip" else 0)}
                              for k in keys}}
        combined = {"platforms": {k: {"availability":
                    ("unavailable" if k in ("loop","milan") else "reachable"),
                    "discovered_links": (3 if k=="flex" else 0)} for k in keys}}
        result = assess([site(k) for k in keys], q, {"events":[]}, combined)
        self.assertEqual(result["sites_total"],17)
        self.assertEqual(result["sites_diagnosed"],17)
        self.assertEqual(result["sites_with_verified_events"],1)
        self.assertFalse(result["full_integration_complete"])
        statuses = {x["id"]:x["state"] for x in result["sources"]}
        self.assertEqual(statuses["loop"],"access_limited")
        self.assertEqual(statuses["flex"],"candidates_not_verified")
        self.assertEqual(statuses["rogerio"],"no_verified_event")
        self.assertEqual(statuses["vip"],"events_verified")

    def test_missing_diagnostics_not_mistaken_for_empty_calendar(self):
        result=assess([site("mcleilao")],{},{"events":[]},{})
        self.assertEqual(result["sites_diagnosed"],0)
        self.assertEqual(result["sources"][0]["state"],"not_checked")

    def test_zero_events_never_misrepresented_as_success(self):
        result=assess([site("pmklog")],
            {"per_platform":{"pmklog":{"verified_events":0}}},
            {"events":[]},
            {"platforms":{"pmklog":{"availability":"reachable",
                                    "discovered_links":1}}})
        self.assertFalse(result["full_integration_complete"])
        self.assertFalse(result["sources"][0]["approved_for_publication"])
        self.assertIn("edition",result["sources"][0]["blocker"])

if __name__=="__main__":
    unittest.main()
