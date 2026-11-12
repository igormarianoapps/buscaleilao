import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from loop_collect import AGENDA,event_id,agenda_urls,parse_event,collect_loop
URL="https://loopleiloes.com.br/eventos/leilao-2026-11"
PAGE="Leilão de veículos Data do leilão: 24/11/2026 às 10:00 Pátio: Mogi das Cruzes/SP Lote 1 Chevrolet Onix Lote 2 Honda Civic"
class LoopTests(unittest.TestCase):
 def test_official_domain_not_corporate_or_revenda(self):
    self.assertEqual(event_id(URL),"leilao-2026-11")
    self.assertIsNone(event_id("https://loopbrasil.com/leilao/123"))
    self.assertIsNone(event_id("https://looprevenda.com.br/eventos/123"))
    self.assertIsNone(event_id("https://loopleiloes.com.br.eventos.evil.org/eventos/123"))
 def test_no_scheduled_events_is_valid_result(self):
    self.assertEqual(agenda_urls("<h1>Agenda de eventos</h1>Não há eventos agendados no momento."),[])
    events,errors=collect_loop(date(2026,11,12),lambda _: "<h1>Agenda de eventos</h1>Não há eventos agendados no momento.")
    self.assertEqual(events,[])
    self.assertEqual(errors,[])
 def test_event_gate_needs_all_independent_fields(self):
    x=parse_event(PAGE,URL,date(2026,11,12))
    self.assertIsNotNone(x)
    self.assertEqual(x["state"],"SP")
    self.assertIsNone(parse_event(PAGE.replace("Mogi das Cruzes/SP","Mogi das Cruzes"),URL,date(2026,11,12)))
    self.assertIsNone(parse_event(PAGE.replace("Lote 2","Lote 1"),URL,date(2026,11,12)))
    self.assertIsNone(parse_event(PAGE,URL,date(2026,11,25)))
if __name__=="__main__":unittest.main()
