import sys
import unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from bolsa_collect import detail_id,parse_details,collect_bolsa
DETAIL="https://www.bolsadeleiloes.com.br/leilao/920"
CONTENT="<h3>ABERTO PARA LANCES</h3><h3>Grande Leilão de Veículos Banco SANTANDER</h3><div>Data 18/11/2026 às 13:00:00</div><p>LOCAL: BELO HORIZONTE-MG</p><h3>LOTE 1</h3><h3>FIAT UNO</h3><h3>LOTE 2</h3><h3>HONDA CG 160</h3>"
class BolsaTests(unittest.TestCase):
    def test_exact_host_and_event_specific_route(self):
        self.assertEqual(detail_id(DETAIL),"920")
        self.assertIsNone(detail_id("https://www.bolsadeleiloes.com.br.evil.example/leilao/920"))
        self.assertIsNone(detail_id("https://www.bolsadeleiloes.com.br/leilao/920?next=evil"))
        self.assertIsNone(detail_id("https://www.bolsadeleiloes.com.br/"))
    def test_actual_vehicle_event_in_location_state(self):
        e=parse_details(CONTENT,DETAIL,date(2026,11,11))
        self.assertEqual(e["state"],"MG")
        self.assertEqual(e["auction_date"],"2026-11-18")
        self.assertEqual(e["city"],"Belo Horizonte")
        self.assertNotIn("link_verified",e)
        self.assertIsNone(parse_details(CONTENT,DETAIL,date(2026,11,20)))
        self.assertIsNone(parse_details(CONTENT.replace("LOTE 2","Sem lotes"),DETAIL,date(2026,11,11)))
    def test_skips_appliances_and_isolates_failures(self):
        main=('<a href="/leilao/910">Leilão de eletrodomésticos</a>'
              '<a href="/leilao/920">Grande Leilão de Veículos Banco Santander</a>')
        events,errors=collect_bolsa(today=date(2026,11,11),
              index_loader=lambda _:main,detail_loader=lambda _:CONTENT)
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["id"],"bolsa-920-2026-11-18")
        self.assertEqual(errors,[])

if __name__=="__main__":unittest.main()
