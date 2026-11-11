import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from platform_triage import classify,summarize
SITE={"id":"parque","name":"Parque","batch":1,
      "allowed_hosts":["www.parquedosleiloes.com.br"]}
class TriageTests(unittest.TestCase):
 def test_future_vehicle_event_remains_unverified(self):
    row={"title":"LEILÃO DE VEÍCULOS EM BRASÍLIA/DF 24/11/2026 às 10:00",
         "source_url":"https://www.parquedosleiloes.com.br/leilao/1523/detalhes"}
    x=classify(row,SITE,today=date(2026,11,11))
    self.assertEqual(x["category_hint"],"vehicle")
    self.assertEqual(x["date_hint"],"2026-11-24")
    self.assertEqual(x["state_hint_verified_from_event"],"DF")
    self.assertFalse(x["published"])
 def test_lot_is_not_event_and_geography_not_assumed_from_hq(self):
    site={"id":"leilo","allowed_hosts":["leilo.com.br"]}
    row={"title":"LOTE 5 MOTO HONDA CG 160 Goiânia/GO",
         "source_url":"https://leilo.com.br/lote/0b82e2b4-0efd-424b-9843-043d011a39ce/",
         "candidate_kind":"individual_lot"}
    x=classify(row,site,today=date(2026,11,11))
    self.assertEqual(x["url_kind"],"individual_lot_not_auction")
    self.assertIsNone(x["date_hint"])
 def test_nonvehicle_in_hisa_is_excluded(self):
    site={"id":"hisa","allowed_hosts":["hisaleiloes.com.br"]}
    row={"title":"MÓVEIS E ELETRODOMÉSTICOS 19/11/2026 às 17:00",
         "source_url":"https://hisaleiloes.com.br/leilao/2539"}
    x=classify(row,site,today=date(2026,11,11))
    self.assertEqual(x["category_hint"],"non_vehicle")
 def test_known_phishing_domain_rejected(self):
    self.assertIsNone(classify({"title":"Veículos 24/11/2026","source_url":"https://www.parquedosleiloes.com.br.evil.example/leilao/1523/detalhes"},SITE,date(2026,11,11)))
 def test_report_reports_each_platform_even_with_zero(self):
    data=summarize([SITE],{"platforms":{"parque":{"status":"reachable","candidate_events":[]}}})
    self.assertEqual(data["platforms_total"],1)
    self.assertEqual(data["platforms"]["parque"]["candidates_total"],0)
if __name__=="__main__":unittest.main()
