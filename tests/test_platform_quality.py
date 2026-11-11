import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from platform_quality import audit
class PlatformQualityTests(unittest.TestCase):
 def test_multistate_event_counted_once(self):
    site={"id":"leilo","name":"Leilo","batch":1,"allowed_hosts":["leilo.com.br"]}
    records=[{"id":"a-go","event_id":"a","organizer":"Leilo","states":["GO","PA"],"source_url":"https://leilo.com.br/leilao/evento/super-terca/","link_verified":True,"destination_verified":True},
             {"id":"a-pa","event_id":"a","organizer":"Leilo","states":["GO","PA"],"source_url":"https://leilo.com.br/leilao/evento/super-terca/","link_verified":True,"destination_verified":True}]
    q=audit([site],{"platforms":{"leilo":{"status":"reachable","candidate_count":40}}},
        {},{"updated_at":"2026-11-11T10:00:00Z","events":records},{},{})
    self.assertEqual(q["per_platform"]["leilo"]["verified_events"],1)
    self.assertEqual(q["per_platform"]["leilo"]["states_with_verified_events"],["GO","PA"])
 def test_does_not_claim_certification_from_reachability(self):
    site={"id":"flex","name":"Flex","batch":1,"allowed_hosts":["www.flexleiloes.com.br"]}
    q=audit([site],{"platforms":{"flex":{"status":"reachable","candidate_count":5}}},
        {},{"events":[]},{},{})
    self.assertEqual(q["per_platform"]["flex"]["integration_status"],"monitoring_no_verified_vehicle_event")
    self.assertEqual(q["per_platform"]["flex"]["verified_events"],0)
 def test_unverified_event_not_counted(self):
    site={"id":"hisa","name":"Hisa","batch":2,"allowed_hosts":["hisaleiloes.com.br"]}
    q=audit([site],{}, {},{"events":[{"id":"h","source_url":"https://hisaleiloes.com.br/leilao/4","link_verified":True}]},{},{})
    self.assertEqual(q["per_platform"]["hisa"]["verified_events"],0)
if __name__=="__main__":unittest.main()
