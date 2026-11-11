import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from auction_platform_watch import candidates,host_ok,monitor
SITE={"id":"parque","state_hint":"DF","allowed_hosts":["parquedosleiloes.com.br","www.parquedosleiloes.com.br"],
"discovery_url":"https://www.parquedosleiloes.com.br/leiloes"}
class AuctionPlatformWatchTests(unittest.TestCase):
    def test_rejects_phishing_and_insecure_hosts(self):
        for link in ("http://www.parquedosleiloes.com.br/leilao/123",
                     "https://parquedosleiloes.com.br.evil.example/leilao/123",
                     "https://www.parquedosleiloes.com.br@evil.example/leilao/123",
                     "https://www.parquedosleiloes.com.br:444/leilao/123"):
            self.assertFalse(host_ok(SITE,link),link)
    def test_only_candidate_links_never_publish_auction(self):
        html=('<a href="/leilao/1521/detalhes">LEILÃO BANCOS E FINANCEIRAS VEÍCULOS</a>'
              '<a href="https://evil.example/leilao/55">Leilão de veículos</a>'
              '<a href="/login">Entrar</a>'
              '<a href="/leilao/1553/detalhes">Apartamento centro</a>')
        rows=candidates(SITE,html)
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]["status"],"unverified_candidate")
        self.assertNotIn("auction_date",rows[0])
        self.assertNotIn("link_verified",rows[0])
    def test_failure_isolated(self):
        bad=dict(SITE,id="bad")
        def loader(s):
            if s["id"]=="bad": raise OSError("HTTP 403")
            return '<a href="/leilao/1521/detalhes">Leilão de veículos</a>'
        output=monitor([bad,SITE],loader)
        self.assertEqual(output["bad"]["status"],"unreachable")
        self.assertEqual(output["parque"]["candidate_count"],1)

if __name__=="__main__":unittest.main()
