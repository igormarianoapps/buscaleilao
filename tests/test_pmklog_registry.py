import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from auction_platform_watch import host_ok
class PMKRegistryTests(unittest.TestCase):
 def test_17_registered_distinct_sources(self):
    sites=json.loads((Path(__file__).resolve().parents[1]/"app/auction-platforms.json").read_text(encoding="utf-8"))
    self.assertEqual(len(sites),17)
    self.assertEqual(len({s["id"] for s in sites}),17)
    pmk=next(s for s in sites if s["id"]=="pmklog")
    self.assertTrue(all(host_ok(pmk,url) for url in [pmk["discovery_url"]]+pmk["additional_discovery_urls"]))
    self.assertFalse(host_ok(pmk,"https://pmklog.com.br.evil.example/leilao/"))
    self.assertEqual(pmk["status"],"candidate_adapter")
    self.assertTrue(pmk["requires_individual_event_link"])
if __name__=="__main__":unittest.main()
