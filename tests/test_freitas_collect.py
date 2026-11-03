"""Offline tests: Freitas detail pages are accepted only with future dated vehicle events."""
import sys
import unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from freitas_collect import parse_detail,official_id

TEXT = """226 LOTES VEÍCULOS - CAMINHÕES - MOTOS - SEMI NOVOS
Fechamento a partir das 10h00 do dia 04/11/2099 (quarta-feira)
Leiloeiro: Sérgio Villa Nova de Freitas
Modalidade: ONLINE E PRESENCIAL
Local do leilão:
AV. JUSCELINO KUBITSCHEK DE OLIVEIRA, 1360 - STA BÁRBARA DOESTE / SP
Condições de Venda Edital/Anúncio
"""
URL="https://www.freitasleiloeiro.com.br/Leiloes/Lotes?leilaoId=8152"

class FreitasTests(unittest.TestCase):
    def test_detail_requires_explicit_date_and_location(self):
        found=parse_detail(TEXT,URL,today=date(2099,11,3))
        self.assertIsNotNone(found)
        self.assertEqual(found["auction_date"],"2099-11-04")
        self.assertEqual(found["auction_time"],"10:00")
        self.assertEqual(found["state"],"SP")
        self.assertEqual(found["source_url"],URL)
        self.assertIsNone(found["vehicle_count"])
    def test_past_date_rejected(self):
        self.assertIsNone(parse_detail(TEXT,URL,today=date(2099,11,5)))
    def test_non_vehicle_rejected(self):
        self.assertIsNone(parse_detail(TEXT.replace("VEÍCULOS - CAMINHÕES - MOTOS - SEMI NOVOS","IMÓVEIS COMERCIAIS"),URL,today=date(2099,11,3)))
    def test_nav_menu_does_not_turn_real_estate_into_vehicle_event(self):
        page = ("VEÍCULOS | IMÓVEIS | MATERIAIS\n" +
                "LEILÃO DE IMÓVEIS COMERCIAIS\n" +
                "Fechamento a partir das 10h00 do dia 04/11/2099\n" +
                "Local do leilão: SÃO PAULO / SP")
        self.assertIsNone(parse_detail(page,URL,today=date(2099,11,3)))

    def test_untrusted_domain_rejected(self):
        self.assertIsNone(official_id("https://evil.example/Leiloes/Lotes?leilaoId=8152"))
        self.assertIsNone(official_id("https://www.freitasleiloeiro.com.br/Leiloes/Lotes?leilaoId=abc"))

if __name__=="__main__": unittest.main()
