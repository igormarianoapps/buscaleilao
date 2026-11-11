import sys
import unittest
from pathlib import Path
from datetime import date
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from regional_collect import strict_url,candidates,verified_lots,collect_regionals,CONFIG
class RegionalTests(unittest.TestCase):
    def test_vardana_future_first_party_lot_page(self):
        source=('<h3>12/11</h3><h4>Leilão de Veículos</h4>'
                '<p>5ª feira às 10h - transmissão</p>'
                '<a href="veiculos.php?lei=1085">VER RELAÇÃO DE LOTES</a>')
        rows=candidates("vardana",source,date(2026,11,11))
        self.assertEqual(rows[0][0],"https://www.vardanaleiloes.com.br/vardana/veiculos.php?lei=1085")
        self.assertEqual(rows[0][1],"2026-11-12")
        self.assertFalse(strict_url("vardana","https://www.vardanaleiloes.com.br.evil.example/vardana/veiculos.php?lei=1085"))
        self.assertFalse(strict_url("vardana","https://www.vardanaleiloes.com.br/vardana/index"))
        self.assertFalse(strict_url("vardana","https://www.vardanaleiloes.com.br/vardana/veiculos.php?lei=1085&next=evil"))
        detail="<h3>12/11/2026</h3><h4>Leilão de Veículos</h4><h2>Lote 1 GM/ONIX 1.0</h2>"
        self.assertTrue(verified_lots("vardana",detail,"2026-11-12"))
        self.assertFalse(verified_lots("vardana",detail,"2026-11-13"))
        self.assertFalse(verified_lots("vardana","<h3>12/11/2026</h3>Leilão de Veículos Relação em breve","2026-11-12"))
    def test_claudio_requires_real_lots(self):
        html=('<p>Leilão Presencial / Online 17/11/2026 às 10:00 horas Veículos</p>'
              '<a href="/relacao-foto/902">Acessar leilão</a>')
        rows=candidates("claudio",html,date(2026,11,11))
        self.assertEqual(len(rows),1)
        self.assertFalse(verified_lots("claudio","<h2>17/11/2026</h2>Listagem de Veículos Estamos atualizando esse leilão, em breve os lotes estarão disponíveis.","2026-11-17"))
        self.assertTrue(verified_lots("claudio","<h2>17/11/2026</h2>Listagem de Veículos 001 CHEVROLET ONIX","2026-11-17"))
    def test_collector_independently_quarantines_one_site(self):
        home='<h3>12/11</h3><p>Leilão de Veículos às 10h</p><a href="veiculos.php?lei=1085">VER RELAÇÃO DE LOTES</a>'
        detail='<h2>12/11/2026</h2><h3>Leilão de Veículos</h3><h2>Lote 1 FIAT/UNO</h2>'
        def loader(site,url):
            if site=="claudio":raise ValueError("HTTP 403")
            return home if url==CONFIG[site]["home"] else detail
        found,errs=collect_regionals(date(2026,11,11),loader)
        self.assertEqual(len(found),1)
        self.assertTrue(any(e["id"]=="claudio" for e in errs))

if __name__=="__main__":unittest.main()
