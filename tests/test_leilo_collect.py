import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from leilo_collect import event_slug,events_from_event_page,collect_leilo
URL="https://leilo.com.br/leilao/evento/leilao-de-pesados/"
HTML='''<h1>Leilão de Pesados</h1><p>118 Lotes</p>
<div>LOTE 1 GO IVECO/TECTOR 2022 Leilão:13/11/2026 Sex 13/11 Sex• 09:30 Dar lance</div>
<div>LOTE 2 PA VOLKSWAGEN 17.280 Leilão:13/11/2026 Sex 13/11 Sex• 09:30 Dar lance</div>
<div>LOTE 3 GO DAF/XF 480 Leilão:13/11/2026 Sex 13/11 Sex• 09:30 Dar lance</div>
Leilão recorrente 6 edições realizadas Próxima edição 13 nov sexta às 09h30'''
class LeiloTests(unittest.TestCase):
 def test_trusted_route(self):
    self.assertEqual(event_slug(URL),"leilao-de-pesados")
    self.assertIsNone(event_slug("https://leilo.com.br.evil.example/leilao/evento/leilao-de-pesados/"))
    self.assertIsNone(event_slug("https://leilo.com.br/leilao/evento/leilao-de-pesados/?evento=old"))
    self.assertIsNone(event_slug("https://leilo.com.br/lote/abc"))
 def test_events_are_grouped_by_exact_lot_date_and_state(self):
    x=events_from_event_page(HTML,URL,date(2026,11,11))
    self.assertEqual(len(x),2)
    self.assertEqual(set(y["state"] for y in x),{"GO","PA"})
    self.assertEqual(len(set(y["event_id"] for y in x)),1)
    self.assertEqual(x[0]["auction_date"],"2026-11-13")
    self.assertEqual(x[0]["auction_time"],"09:30")
    self.assertEqual(x[0]["city"],"Local informado no lote")
 def test_old_or_missing_lots_rejected(self):
    self.assertEqual(events_from_event_page(HTML,URL,date(2026,11,14)),[])
    self.assertEqual(events_from_event_page("<h1>Leilão de Pesados</h1>Próxima edição 13/11/2026",URL,date(2026,11,11)),[])
 def test_individual_lot_rejected_even_with_valid_date(self):
    self.assertEqual(events_from_event_page(HTML,"https://leilo.com.br/lote/abc",date(2026,11,11)),[])
 def test_one_site_failure_does_not_stop_others(self):
    found,errors=collect_leilo(date(2026,11,11),
      homepage_loader=lambda _: "<a href='/leilao/evento/leilao-de-pesados/'>Leilão de Pesados</a>",
      event_loader=lambda u: HTML if "pesados/" in u else "")
    self.assertEqual(len(found),2)
if __name__=="__main__":unittest.main()
