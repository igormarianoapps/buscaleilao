"""Offline PNCP discovery tests: national reach without auto-publishing auctions."""
import sys
import unittest
from datetime import date,datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from discover_pncp import candidate,official_record_url,discover,build_url

def row(**overrides):
    base={"numeroControlePNCP":"44892693000140-1-000244/2026",
          "objetoCompra":"Leilão de veículos automotores apreendidos",
          "dataEncerramentoProposta":"2026-11-19T10:00:00",
          "situacaoCompraNome":"Divulgada no PNCP",
          "unidadeOrgao":{"ufSigla":"SP","municipioNome":"Carapicuíba"},
          "orgaoEntidade":{"razaoSocial":"MUNICIPIO DE CARAPICUIBA"}}
    base.update(overrides)
    return base

class PNCPTests(unittest.TestCase):
    def test_valid_future_auction_is_research_candidate_only(self):
        item=candidate(row(),date(2026,11,3))
        self.assertEqual(item["state"],"SP")
        self.assertEqual(item["date_hint"],"2026-11-19")
        self.assertEqual(item["review_status"],"needs_edital_confirmation")
        self.assertNotIn("auction_date",item)
        self.assertEqual(item["source_url"],
            "https://pncp.gov.br/app/editais/44892693000140/2026/244")

    def test_nonvehicle_cancellation_past_and_unknown_date_rejected(self):
        now=date(2026,11,3)
        self.assertIsNone(candidate(row(objetoCompra="Alienação de imóveis"),now))
        self.assertIsNone(candidate(row(situacaoCompraNome="Cancelada"),now))
        self.assertIsNone(candidate(row(dataEncerramentoProposta="2026-10-19T10:00:00"),now))
        self.assertIsNone(candidate(row(dataEncerramentoProposta=None),now))

    def test_malformed_pncp_control_and_missing_uf_rejected(self):
        self.assertIsNone(official_record_url({"numeroControlePNCP":"123-invalid"}))
        self.assertIsNone(candidate(row(unidadeOrgao={}),date(2026,11,3)))

    def test_official_api_queries_both_leilao_modalities(self):
        urls=[]
        def fake_fetch(url):
            urls.append(url)
            if "codigoModalidadeContratacao=1&" in url:
                return {"data":[row()],"totalPaginas":1}
            return {"data":[row(numeroControlePNCP="44892693000140-1-000245/2026")],
                    "totalPaginas":1}
        items,errors,count=discover(
            datetime(2026,11,3,tzinfo=timezone.utc),fetch=fake_fetch)
        self.assertEqual(errors,[])
        self.assertEqual(count,2)
        self.assertEqual(len(items),2)
        self.assertTrue(any("codigoModalidadeContratacao=1" in u for u in urls))
        self.assertTrue(any("codigoModalidadeContratacao=13" in u for u in urls))

    def test_api_failure_is_reported_without_publishing(self):
        def unavailable(_): raise OSError("HTTP 429")
        items,errors,_=discover(
            datetime(2026,11,3,tzinfo=timezone.utc),fetch=unavailable)
        self.assertEqual(items,[])
        self.assertEqual(len(errors),2)

if __name__=="__main__":unittest.main()
