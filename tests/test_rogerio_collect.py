import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from rogerio_collect import detail_id,parse_event,collect_rogerio
URL="https://rogeriomenezes.com.br/leilao/1650"
HTML=("<h1>LEILÃO ONLINE E PRESENCIAL FINANCEIRAS</h1>"
      "<p>3 lotes Sexta-feira, 20/11/2026 às 13:00h Online e presencial "
      "No dia do leilão, das 08 às 13 horas, na Av. Brasil, Campo Grande/ RJ</p>"
      "<div>LOTE 1 FIAT UNO 2018/2019</div><div>LOTE 2 HONDA CG 2020/2021</div>")
class RogerioTests(unittest.TestCase):
 def test_individual_url_host_and_path_only(self):
    self.assertEqual(detail_id(URL),"1650")
    self.assertIsNone(detail_id(URL.replace("rogeriomenezes.com.br","rogeriomenezes.com.br.evil.example")))
    self.assertIsNone(detail_id(URL+"?next=evil"))
    self.assertIsNone(detail_id("https://rogeriomenezes.com.br/leiloes"))
 def test_future_real_lots_admitted(self):
    row=parse_event(HTML,URL,date(2026,11,12))
    self.assertIsNotNone(row)
    self.assertEqual(row["state"],"RJ")
    self.assertEqual(row["auction_date"],"2026-11-20")
 def test_rejects_archived_empty_or_undated(self):
    self.assertIsNone(parse_event(HTML,URL,date(2026,11,21)))
    self.assertIsNone(parse_event(HTML.replace("3 lotes","0 lotes"),URL,date(2026,11,12)))
    self.assertIsNone(parse_event(HTML.replace("LOTE 2","VEICULO 2"),URL,date(2026,11,12)))
    self.assertIsNone(parse_event(HTML.replace("Campo Grande/ RJ","Campo Grande"),URL,date(2026,11,12)))
    self.assertIsNone(parse_event("Rascunho "+HTML,URL,date(2026,11,12)))
 def test_index_empty_is_legitimate(self):
    feed,errors=collect_rogerio(date(2026,11,12),
        lambda url:"<h2>Nenhum leilão disponível no momento</h2>")
    self.assertEqual(feed,[])
    self.assertEqual(errors,[])
 def test_index_isolated_failure_and_active_event(self):
    def loader(url):
        if "leiloes-judiciais" in url:raise OSError("unavailable")
        if "/leilao/1650" in url:return HTML
        return '<a href="/leilao/1650">Leilão financeiro</a>'
    events,errors=collect_rogerio(date(2026,11,12),loader)
    self.assertEqual(len(events),1)
    self.assertTrue(any(e["id"].startswith("rogerio:index") for e in errors))
 def test_existing_security_approval(self):
    from auction_links import destination_status
    from auction_security import valid_destination
    row=parse_event(HTML,URL,date(2026,11,12))
    self.assertTrue(destination_status(row)[0])
    self.assertTrue(valid_destination(row))
if __name__=="__main__":unittest.main()
