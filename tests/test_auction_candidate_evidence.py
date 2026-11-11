import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from auction_candidate_evidence import trusted,extract,dates_from_text
SITE={"id":"parque","allowed_hosts":["www.parquedosleiloes.com.br"]}
class EvidenceTests(unittest.TestCase):
 def test_dates_not_published_even_with_vehicle_and_lots(self):
    row=extract(SITE,"https://www.parquedosleiloes.com.br/leilao/1500/detalhes",
        "Leilão de veículos 21/11/2026 Lote 1 Honda Civic Lote 2 Fiat Uno",date(2026,11,11))
    self.assertEqual(row["date_mentions"],["2026-11-21"])
    self.assertTrue(row["vehicle_text_found"])
    self.assertFalse(row["approved_for_publication"])
 def test_hostname_spoof_and_http_disallowed(self):
    self.assertFalse(trusted(SITE,"https://www.parquedosleiloes.com.br.evil.org/leilao"))
    self.assertFalse(trusted(SITE,"http://www.parquedosleiloes.com.br/leilao"))
 def test_invalid_past_date_filtered(self):
    self.assertEqual(dates_from_text("01/11/2026 50/11/2026",date(2026,11,11)),[])
if __name__=="__main__":unittest.main()
