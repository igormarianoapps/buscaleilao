"""Regression tests for official MG portal and individual lot confirmation."""
import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from mg_detran_collect import listing_candidates,detail_confirms,detail_identity,collect_mg,HOME

def card(status="Publicado",closing="16/11/2026",link="/lotes/lista-lotes/3669/2026"):
    return (f"<div>Edital de Leilão 1945/2026 governador valadares "
            f"1945 - DEPOSITO DO LESTE LTDA {status} "
            f"Encerramento: {closing} 18:00 "
            f'<a href="{link}">Detalhes</a></div>')
class MGTests(unittest.TestCase):
    def test_parse_official_list_with_closing_not_opening_date(self):
        rows=listing_candidates(card(),today=date(2026,11,11))
        self.assertEqual(len(rows),1)
        e=rows[0]
        self.assertEqual(e["auction_date"],"2026-11-16")
        self.assertEqual(e["date_kind"],"closing")
        self.assertEqual(e["state"],"MG")
        self.assertEqual(e["auction_number"],"1945/2026")
        self.assertEqual(e["source_url"],
            "https://leilao.transito.mg.gov.br/lotes/lista-lotes/3669/2026")
    def test_reject_completed_invalid_early_and_external(self):
        self.assertEqual(listing_candidates(card(status="Finalizado"),today=date(2026,11,11)),[])
        self.assertEqual(listing_candidates(card(closing="09/11/2026"),today=date(2026,11,11)),[])
        self.assertEqual(listing_candidates(card(link="https://evil.example/lotes/lista-lotes/3669/2026"),today=date(2026,11,11)),[])
        self.assertIsNone(detail_identity("https://leilao.transito.mg.gov.br.evil.example/lotes/lista-lotes/3669/2026"))
        self.assertIsNone(detail_identity("https://leilao.transito.mg.gov.br/lotes/lista-lotes/3669/2026?redirect=evil"))
    def test_detail_requires_real_lots_and_same_auction_number(self):
        self.assertTrue(detail_confirms("<h4>Leilão 1945 - GOVERNADOR VALADARES</h4><div>Lote 1 - CONSERVADO</div>","1945/2026"))
        self.assertFalse(detail_confirms("<div>Leilão 1944 - GOVERNADOR VALADARES. Lote 1</div>","1945/2026"))
        self.assertFalse(detail_confirms("<div>Leilão 1945 - GOVERNADOR VALADARES</div>","1945/2026"))
    def test_collector_quarantines_unverifiable_detail(self):
        def loader(url):
            if url==HOME: return card()
            return "<h4>Leilão 1945</h4>no lots"
        events,errors=collect_mg(today=date(2026,11,11),loader=loader)
        self.assertEqual(events,[])
        self.assertEqual(len(errors),1)
    def test_collector_accepts_verified_official_detail(self):
        def loader(url):
            if url==HOME: return card()
            return "<h4>Leilão 1945 - GOVERNADOR VALADARES</h4>Lote 1 - CONSERVADO"
        events,errors=collect_mg(today=date(2026,11,11),loader=loader)
        self.assertEqual(len(events),1)
        self.assertEqual(errors,[])

if __name__=="__main__":unittest.main()
