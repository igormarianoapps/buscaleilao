"""Trust boundary regression tests: host impersonation, link shapes and notices."""
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from auction_links import destination_status, certify_links

class LinkSafetyTests(unittest.TestCase):
    def base(self, url="https://www.vipleiloes.com.br/evento/detalhes/141126cttupe"):
        return {"id":"vip","organizer":"VIP Leilões","source_type":"private",
                "source_link_type":"event","auction_date":"2026-11-14","source_url":url}

    def test_known_direct_event_allowed(self):
        ok, _ = destination_status(self.base())
        self.assertTrue(ok)
    def test_https_is_not_proof(self):
        for url in (
            "https://vipleiloes.com.br.evil.example/evento/detalhes/123",
            "https://www.vipleiloes.com.br/agenda",
            "http://www.vipleiloes.com.br/evento/detalhes/123",
            "https://www.vipleiloes.com.br@evil.example/evento/detalhes/123",
            "https://www.vipleiloes.com.br/noticias/leilao",
            "https://www.vipleiloes.com.br:8443/evento/detalhes/123",
        ):
            with self.subTest(url=url):
                self.assertFalse(destination_status(self.base(url))[0])
    def test_copart_date_and_identity(self):
        row={"organizer":"Copart","source_link_type":"event",
             "auction_date":"2026-11-14",
             "source_url":"https://www.copart.com.br/saleListResult/10592/2026-11-14"}
        self.assertTrue(destination_status(row)[0])
        row["auction_date"]="2026-11-15"
        self.assertFalse(destination_status(row)[0])
    def test_government_article_not_event(self):
        row={"organizer":"Prefeitura de Cuiabá — Semob",
             "source_type":"municipal",
             "source_url":"https://www.cuiaba.mt.gov.br/noticias/semob-leilao"}
        self.assertFalse(destination_status(row)[0])
        row["event_url"]="https://www.focoleiloes.com.br/leilao/497/lotes"
        self.assertTrue(destination_status(row)[0])
    def test_quarantine(self):
        rows=[self.base(),self.base("https://fake-auction.example/leilao/3")]
        certify_links(rows)
        self.assertTrue(rows[0]["link_verified"])
        self.assertFalse(rows[1]["link_verified"])
        self.assertEqual(rows[1]["link_review"],"quarantine")

if __name__ == "__main__":
    unittest.main()
