import sys,unittest
from datetime import date
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from palacio_collect import auction_id,extract_event
URL="https://www.palaciodosleiloes.com.br/site/index.php?leilao_pesquisa=8905"
HTML=("Leilão 8905 Veículos recuperados de financiamento "
      "Data da realização: 20/11/2026 às 10:00 Pátio: Juatuba/MG "
      "Sequência: 10 Lote: 1 Fiat Uno "
      "Sequência: 11 Lote: 2 Volkswagen Gol")
class PalacioTests(unittest.TestCase):
 def test_specific_numeric_event_only(self):
    self.assertEqual(auction_id(URL),"8905")
    self.assertIsNone(auction_id(URL.replace("palaciodosleiloes.com.br","palaciodosleiloes.com.br.evil.org")))
    self.assertIsNone(auction_id(URL.replace("8905","8905&next=evil")))
 def test_event_requires_full_date_vehicle_lots_and_location(self):
    row=extract_event(HTML,URL,date(2026,11,12))
    self.assertIsNotNone(row)
    self.assertEqual(row["state"],"MG")
    self.assertEqual(row["auction_date"],"2026-11-20")
    self.assertEqual(row["vehicle_count"],None)
 def test_numbered_lots_without_colon_are_supported(self):
    row=extract_event(HTML.replace("Lote: 1","Lote 1").replace("Lote: 2","Lote nº 2"),URL,date(2026,11,12))
    self.assertIsNotNone(row)
 def test_ambiguous_no_state_and_past_event_rejected(self):
    self.assertIsNone(extract_event(HTML.replace("Juatuba/MG","Juatuba"),URL,date(2026,11,12)))
    self.assertIsNone(extract_event(HTML,URL,date(2026,11,21)))
    self.assertIsNone(extract_event(HTML.replace("Lote: 2","Lote: 1"),URL,date(2026,11,12)))
    self.assertIsNone(extract_event(HTML.replace("Veículos recuperados de financiamento","Eletrodomésticos"),URL,date(2026,11,12)))
if __name__=="__main__":unittest.main()
