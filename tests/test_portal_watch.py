"""Offline checks for official portal discovery, trust boundaries and coverage."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from portal_watch import candidate_links, scan, valid_source
from coverage_audit import audit

SRC={"id":"pr-curitiba","name":"Curitiba","state":"PR","kind":"municipal",
     "url":"https://transito.curitiba.pr.gov.br/patio/leilao-eletronico-de-veiculos/52",
     "host":"transito.curitiba.pr.gov.br","status":"discovery_only",
     "review_required":True}
class PortalTests(unittest.TestCase):
    def test_requires_explicit_host_and_status(self):
        self.assertTrue(valid_source(SRC))
        self.assertFalse(valid_source(dict(SRC,host="evil.example")))
        self.assertFalse(valid_source(dict(SRC,review_required=False)))
    def test_discovers_same_host_links_without_guessing_event(self):
        html='<a href="/patio/leilao-123">Edital de Leilão 123</a>' \
             '<a href="https://evil.example/leilao/33">Leilão veículos</a>' \
             '<a href="http://transito.curitiba.pr.gov.br/leilao">Leilão</a>' \
             '<a href="/patio/leilao-123">Edital de Leilão 123</a>'
        rows=candidate_links(SRC,html)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["source_kind"],"official_portal")
        self.assertEqual(rows[0]["state_hint"],"PR")
        self.assertNotIn("auction_date",rows[0])
        self.assertNotIn("event_url",rows[0])
    def test_rejects_page_fragments_print_navigation_and_old_years(self):
        src=dict(SRC,id="mg-patrimonio",url="https://www.mg.gov.br/planejamento/pagina/gestao-governamental/logistica-e-patrimonio/leiloes",host="www.mg.gov.br",state="MG")
        html=('<a href="#main">Ir para o conteúdo principal</a>'
              '<a href="?imprimir=1">Imprimir</a>'
              '<a href="/leiloes/edital-2025.pdf">Edital Leilão 011/2025 - Veículos</a>'
              '<a href="/leiloes/edital-2026.pdf">Edital Leilão 011/2026 - Veículos</a>'
              '<a href="/credenciamento-2026.pdf">Credenciamento de examinadores</a>')
        rows=candidate_links(src,html)
        self.assertEqual(len(rows),1)
        self.assertIn("2026",rows[0]["title"])
        self.assertNotIn("#",rows[0]["source_url"])

    def test_failures_isolated_and_not_published(self):
        bad=dict(SRC,id="broken",url="https://transito.curitiba.pr.gov.br/error")
        def load(src):
            if src["id"]=="broken": raise OSError("HTTP 403")
            return '<a href="/patio/leilao-123">Leilão 123</a>'
        candidates,statuses=scan([bad,SRC],loader=load)
        self.assertEqual(len(candidates),1)
        self.assertEqual(statuses[0]["status"],"failed")
        self.assertEqual(statuses[1]["status"],"ok")
    def test_coverage_uses_distinct_events_not_state_rows(self):
        feed={"events":[
           {"id":"a-go","organizer":"VIP Leilões","event_id":"a",
            "states":["GO","SP"],"source_url":"https://www.vipleiloes.com.br/evento/detalhes/a"},
           {"id":"a-sp","organizer":"VIP Leilões","event_id":"a",
            "states":["GO","SP"],"source_url":"https://www.vipleiloes.com.br/evento/detalhes/a"}]}
        result=audit(feed,[SRC],{"items":[{"title":"unverified"}]},
                     {"candidates_count":5,"source_statuses":[{"status":"ok"}]})
        self.assertEqual(result["unique_events"],1)
        self.assertEqual(result["events_by_state"],{"GO":1,"SP":1})
        self.assertEqual(result["review_queue_items"],1)
        self.assertEqual(result["unverified_portal_leads"],5)

if __name__=="__main__":
    unittest.main()
