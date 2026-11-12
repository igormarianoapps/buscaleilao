import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from pmklog_collect import event_id,parse_edition,collect_pmklog,KNOWN
class PMKTests(unittest.TestCase):
 def test_only_first_party_edition_routes(self):
    self.assertIsNotNone(event_id(KNOWN))
    self.assertIsNone(event_id(KNOWN.replace("pmklog.com.br","pmklog.com.br.evil.test")))
    self.assertIsNone(event_id("https://pmklog.com.br/leilao/"))
    self.assertIsNone(event_id(KNOWN+"&next=https://evil.example"))
 def test_actual_archived_november_edition_rejected(self):
    html=("Finalizado Lote 1 GO Fiat Palio 09/11/2026 Finalizado Lote 2 GO Honda CG 09/11/2026 "
          "Leilão recorrente 3 edições realizadas Próxima edição No momento, não há uma nova edição prevista. "
          "Edições anteriores: 09/11/2026 PÁTIO ANÁPOLIS/GO")
    self.assertIsNone(parse_edition(html,KNOWN,date(2026,11,12)))
 def test_new_date_without_lots_cannot_publish(self):
    html="Leilão recorrente Próxima edição 20/11/2026 às 09h00 PÁTIO ANÁPOLIS/GO"
    self.assertIsNone(parse_edition(html,KNOWN,date(2026,11,12)))
 def test_future_edition_with_lots_and_patio_may_publish(self):
    html=("Lote 1 GO Fiat Palio 20/11/2026 Lote 2 GO Honda CG 20/11/2026 "
          "Leilão recorrente Próxima edição 20/11/2026 às 09h00 PÁTIO ANÁPOLIS/GO")
    r=parse_edition(html,KNOWN,date(2026,11,12))
    self.assertEqual(r["auction_date"],"2026-11-20")
    self.assertEqual(r["state"],"GO")
    self.assertEqual(r["vehicle_count"],None)
 def test_no_future_editions_empty_not_error(self):
    home=f'<a href="{KNOWN}">Leilão Detran</a>'
    result,errors=collect_pmklog(date(2026,11,12),lambda url:home if url=="https://pmklog.com.br/" else
          "Leilão recorrente Próxima edição No momento, não há uma nova edição prevista.")
    self.assertEqual(result,[])
    self.assertEqual(errors,[])

class PMKIndexRecoveryTests(unittest.TestCase):
 def test_secondary_calendar_finds_new_active_edition(self):
    new="https://pmklog.com.br/leilao/evento/leilao-veiculos/?evento=fa724af3-d396-11f1-a2f8-02420a000015"
    seen=[]
    def loader(url):
        seen.append(url)
        if url=="https://pmklog.com.br/":raise OSError("homepage offline")
        if url=="https://pmklog.com.br/leilao/":
            return f'<a href="{new}">Leilão de veículos</a>'
        if url=="https://pmklog.com.br/nossos-leiloes":return ""
        if url==new:
            return ("Lote 1 GO Fiat Palio 20/11/2026 Lote 2 GO Honda CG 20/11/2026 "
                    "Próxima edição 20/11/2026 às 09h00 PÁTIO ANÁPOLIS/GO")
        return "Próxima edição No momento, não há uma nova edição prevista."
    events,errors=collect_pmklog(date(2026,11,12),loader)
    self.assertEqual(len(events),1)
    self.assertEqual(events[0]["source_url"],new)
    self.assertTrue(any(e["id"].startswith("pmklog:index") for e in errors))
    self.assertIn("https://pmklog.com.br/nossos-leiloes",seen)
 def test_only_trusted_edition_links_from_secondary_index(self):
    from pmklog_collect import discover_urls
    links=discover_urls('<a href="https://evil.example/leilao/evento/leilao-carro/?evento=fa724af3-d396-11f1-a2f8-02420a000015">Fraud</a>')
    self.assertEqual(links,[KNOWN])

if __name__=="__main__":unittest.main()
