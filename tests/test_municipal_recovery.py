"""Contract checks for newly confirmed municipal notices.

Fixtures reproduce short notice passages visible on the official municipal
calendar and official auctioneer event detail, not guessed event data.
"""
import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from source_collector import validate

CURITIBA="""Leilão - 25 de novembro de 2026
Edital de Leilão Eletrônico SMDT Nº 18/2026
Itens nº 1 ao nº 42: Veículos em circulação
Data e horário: 25/11/2026, às 9h
Itens nº 43: Sucata aproveitável
Leilão - 11 de novembro de 2026
Edital de Leilão Eletrônico SMDT Nº 17/2026
Itens nº 1 ao nº 33: Veículos em circulação
Data e horário: 11/11/2026, às 9h
Edital de Leilão Eletrônico SMDT Nº 16/2026
Lote Único
Itens nº 1 ao nº 68: Sucata Inservível
Data e horário: 11/11/2026, às 9h"""
ARACAJU="""LEILÃO DE VEÍCULOS E BENS DA PREFEITURA MUNICIPAL DE ARACAJU - N° 003/2026
Em Andamento
Data do Leilão: 12/11/2026
Encerramento do primeiro lote a partir das: 09:30
Comitente: PREFEITURA MUNICIPAL DE ARACAJU
LEILÃO DE BENS MÓVEIS:
CADEIRAS E MOBÍLIAS ESCOLARES; VEICULO.
O Presente Leilão tem por objetivo a venda de veículos usados e materiais inservíveis."""

class MunicipalRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources={x["id"]:x for x in json.loads(
            (ROOT/"app/sources.json").read_text(encoding="utf-8"))}
    def test_curitiba_three_edital_sessions_have_individual_evidence(self):
        items=[self.sources[k] for k in (
            "curitiba-smdt-16-2026","curitiba-smdt-17-2026",
            "curitiba-smdt-18-2026")]
        self.assertEqual(len({x["source_url"] for x in items}),1)
        self.assertTrue(all(x["source_url"].startswith(
            "https://transito.curitiba.pr.gov.br/") for x in items))
        self.assertTrue(all(validate(CURITIBA,x) for x in items))
        self.assertEqual({x["auction_date"] for x in items},
                         {"2026-11-11","2026-11-25"})
        self.assertTrue(all(x["vehicle_count"] is None for x in items))
    def test_aracaju_uses_real_auctioneer_detail_with_verified_clock(self):
        src=self.sources["aracaju-3-leilao-2026-11-12"]
        self.assertEqual(src["auction_time"],"09:30")
        self.assertTrue(src["source_url"].startswith(
            "https://rjleiloes.com.br/leilao/4845/"))
        self.assertTrue(validate(ARACAJU,src))
        self.assertIsNone(src["vehicle_count"])
    def test_unrelated_content_cannot_confirm_aracaju(self):
        with self.assertRaises(ValueError):
            validate(CURITIBA,self.sources["aracaju-3-leilao-2026-11-12"])

if __name__=="__main__":unittest.main()
