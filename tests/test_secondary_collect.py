import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from secondary_collect import event_date,trusted_url,parse_event,collect_secondary,SITES
class SecondaryTests(unittest.TestCase):
 def test_event_dates(self):
    self.assertEqual(event_date("Data 13 de nov de 2026 às 10:00",date(2026,11,11)),("2026-11-13","10:00"))
    self.assertEqual(event_date("DATA: 24/11/2026 - 10h00",date(2026,11,11)),("2026-11-24","10:00"))
    self.assertIsNone(event_date("DATA: 10/11/2026 - 10h00",date(2026,11,11)))
 def test_hosts_strict(self):
    self.assertFalse(trusted_url("parque","https://www.parquedosleiloes.com.br.evil.example/leilao/1523/detalhes"))
    self.assertFalse(trusted_url("flex","https://www.flexleiloes.com.br/lotes/2991?next=evil"))
    self.assertTrue(trusted_url("flex","https://www.flexleiloes.com.br/lotes/2991/"))
 def test_parque_rejects_equipment_and_past_vehicle_events(self):
    url="https://www.parquedosleiloes.com.br/leilao/1522/detalhes"
    html="<h1>LEILÃO DE BENS E EQUIPAMENTOS</h1>Data 13 de nov de 2026 às 10:00 Categoria BENS E EQUIPAMENTOS 1lote FORD"
    self.assertIsNone(parse_event("parque","Detalhes",html,url,date(2026,11,11)))
    html="<h1>BANCOS E FINANCEIRAS VEICULOS</h1>Data 10 de nov de 2026 às 13:00 Categoria VEICULOS 1lote FORD BRASÍLIA/DF"
    self.assertIsNone(parse_event("parque","Detalhes",html,url,date(2026,11,11)))
 def test_parque_court_title_without_vehicles_word(self):
    url="https://www.parquedosleiloes.com.br/leilao/1524/detalhes"
    detail=("<h1>2ª VARA DE BRASÍLIA - 2ª PRAÇA</h1> "
            "Data 12 de nov de 2026 às 14:00 Categoria VEICULOS "
            "Local do Bem: Asa Norte/DF 1lote FIAT PALIO EDX")
    item=parse_event("parque","Detalhes",detail,url,date(2026,11,12))
    self.assertIsNotNone(item)
    self.assertEqual(item["state"],"DF")
    self.assertIsNone(parse_event("parque","Detalhes",
        detail.replace("Categoria VEICULOS","Categoria BENS E EQUIPAMENTOS"),
        url,date(2026,11,12)))
 def test_flex_requires_explicit_location(self):
    url="https://www.flexleiloes.com.br/lotes/2991/"
    label="Leilão de Veículos 04 Veículos DATA: 24/11/2026 - 10h00"
    body="042 RENAULT SANDERO 091 FIAT UNO 095 FORD RANGER"
    self.assertIsNone(parse_event("flex",label,body,url,date(2026,11,11)))
    label="Brasília/DF Leilão de Veículos 04 Veículos DATA: 24/11/2026 - 10h00"
    self.assertIsNotNone(parse_event("flex",label,body,url,date(2026,11,11)))
 def test_hisa_excludes_appliances(self):
    url="https://hisaleiloes.com.br/leilao/2539"
    self.assertIsNone(parse_event("hisa","MÓVEIS E ELETRODOMÉSTICOS Data 19/11/2026 às 17:00",
        "Lote 1 FIAT UNO Data 19/11/2026",url,date(2026,11,11)))
 def test_failure_isolated(self):
    def loader(site,url):
        if site=="hisa":raise OSError("blocked")
        return "" if url==SITES[site][1] else ""
    data,errors=collect_secondary(date(2026,11,11),loader)
    self.assertEqual(data,[])
    self.assertTrue(any(x["id"]=="hisa" for x in errors))

class RejectionReasonsTests(unittest.TestCase):
 def test_future_flex_without_verified_lot_location(self):
    from secondary_collect import rejection_reason
    label="Leilão de Veículos 04 Veículos DATA: 24/11/2026 - 10h00"
    detail="<p>042 RENAULT SANDERO 091 FIAT UNO 095 FORD RANGER</p>"
    reason=rejection_reason("flex",label,detail,"https://www.flexleiloes.com.br/lotes/2991",date(2026,11,12))
    self.assertEqual(reason,"event_or_lot_location_unverified")
 def test_parque_nonvehicle_auction(self):
    from secondary_collect import rejection_reason
    reason=rejection_reason("parque","Detalhes",
      "<h1>LEILÃO DE EQUIPAMENTOS</h1>Data 13 de nov de 2026 às 10:00 Categoria BENS E EQUIPAMENTOS",
      "https://www.parquedosleiloes.com.br/leilao/1522/detalhes",date(2026,11,12))
    self.assertEqual(reason,"not_vehicle_category")
 def test_hisa_unpublished_lots(self):
    from secondary_collect import rejection_reason
    label="CARROS E MOTOS Data: 26/11/2026 às 15:00 SAO CAETANO DO SUL, SP"
    html="<h2>LOTES EM BREVE</h2> Data 26/11/2026"
    url="https://hisaleiloes.com.br/leilao/2538"
    self.assertEqual(rejection_reason("hisa",label,html,url,date(2026,11,12)),"lots_not_published")
    self.assertIsNone(parse_event("hisa",label,html,url,date(2026,11,12)))

if __name__=="__main__":unittest.main()

class FlexCanonicalRedirectTests(unittest.TestCase):
 def test_only_exact_lot_url_is_approved(self):
    from secondary_collect import trusted_url
    self.assertTrue(trusted_url("flex","https://www.flexleiloes.com.br/lotes/2991/"))
    self.assertFalse(trusted_url("flex","https://www.flexleiloes.com.br/lotes/2992/redirect"))

class FlexLotLocationTests(unittest.TestCase):
 def test_visitor_lot_site_explicitly_provides_state_not_company_hq(self):
    from secondary_collect import verified_lot_location
    self.assertEqual(verified_lot_location(
        "Leilão de veículos Visitação: Pátio Sobradinho/DF. Lote 001 Fiat Uno"),("Sobradinho","DF"))
    self.assertIsNone(verified_lot_location("Leilão de veículos Empresa sediada em Brasília/DF"))

class SecondaryFallbackTests(unittest.TestCase):
 def test_research_urls_are_corroboration_candidates_not_published(self):
    from secondary_collect import fallback_candidates
    payload={"platforms":{"flex":{"candidate_events":[
        {"title":"Leilão de Veículos 04 DATA: 24/11/2026 - 10h00",
         "source_url":"https://www.flexleiloes.com.br/lotes/2991"},
        {"title":"Fraud","source_url":"https://www.flexleiloes.com.br.evil.test/lotes/2991"},
        {"title":"Category only","source_url":"https://www.flexleiloes.com.br/veiculos-leves/"}]}}}
    rows=fallback_candidates("flex",payload)
    self.assertEqual(len(rows),1)
    self.assertTrue(next(iter(rows)).endswith("/lotes/2991"))
    self.assertEqual(fallback_candidates("hisa",payload),{})
