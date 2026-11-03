"""Offline tests for browser auction adapters."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from browser_collect import parse_copart_rows, parse_copart_linked_rows, copart_detail_url, parse_vip_text

class Tests(unittest.TestCase):
    def test_copart_two_dates_one_yard(self):
        rows=[["Curitiba - PR","03.11.2099","04.11.2099","55"],
              ["Goiânia - GO","04.11.2099","04.11.2099","89"]]
        result=parse_copart_rows(rows)
        self.assertEqual(len(result),3)
        self.assertEqual({r["state"] for r in result},{"PR","GO"})
        self.assertTrue(all(r["vehicle_count"] is None for r in result))
    def test_copart_rejects_missing_date(self):
        self.assertEqual(parse_copart_rows([["Betim - MG","","","48"]]),[])
    def test_copart_separate_sales_same_yard_and_day(self):
        row={"cells":["Goiânia - GO","04.11.2099","04.11.2099","56"],
             "links":[
                {"text":"04.11.2099","href":"https://www.copart.com.br/saleListResult/10569/2099-11-04?yardNum=56"},
                {"text":"04.11.2099","href":"https://www.copart.com.br/saleListResult/10570/2099-11-04?yardNum=56"}]}
        events=parse_copart_linked_rows([row])
        self.assertEqual(len(events),2)
        self.assertEqual({e["id"] for e in events},{"copart-10569-2099-11-04","copart-10570-2099-11-04"})
        self.assertTrue(all(e["source_link_type"]=="event" for e in events))

    def test_copart_live_now_uses_verified_official_url_date(self):
        row={"cells":["Goiânia - GO","LIVE NOW","","56"],
             "links":[{"text":"LIVE NOW","href":"https://www.copart.com.br/saleListResult/10569/2099-11-04"}]}
        # Date extraction is intentionally restricted to future events.
        events=parse_copart_linked_rows([row])
        self.assertEqual(len(events),1)
        self.assertEqual(events[0]["auction_date"],"2099-11-04")
        self.assertEqual(events[0]["source_link_type"],"event")

    def test_copart_unlinked_day_uses_calendar_not_guessed_url(self):
        row={"cells":["Osasco - SP","04.11.2099","05.11.2099","42"],
             "links":[{"text":"04.11.2099","href":"https://www.copart.com.br/saleListResult/8888/2099-11-04"}]}
        events=parse_copart_linked_rows([row])
        self.assertEqual(len(events),2)
        fallback=[e for e in events if e["auction_date"]=="2099-11-05"][0]
        self.assertEqual(fallback["source_link_type"],"calendar")
        self.assertEqual(fallback["source_url"],"https://www.copart.com.br/salesListResult/")

    def test_copart_rejects_mismatched_or_untrusted_link(self):
        self.assertIsNone(copart_detail_url("https://other.example/saleListResult/1/2099-11-04","2099-11-04"))
        self.assertIsNone(copart_detail_url("https://www.copart.com.br/saleListResult/1/2099-11-05","2099-11-04"))
        self.assertIsNone(copart_detail_url("https://www.copart.com.br/auctionCalendar","2099-11-04"))

    def test_vip_multi_state(self):
        sample="\nSeguradoras\nInício: 03/11/2099 10:00\nLotes 83\nEstados BA-GO-MT\nTipo Leilão Online"
        result=parse_vip_text(sample)
        self.assertEqual({r["state"] for r in result},{"BA","GO","MT"})
        self.assertTrue(all(r["vehicle_count"] is None for r in result))
    def test_vip_rejects_unspecified_uf(self):
        self.assertEqual(parse_vip_text("Seguradoras\nInício: 03/11/2099 10:00\nEstados Não Informado"),[])
    def test_past_events_excluded(self):
        self.assertEqual(parse_copart_rows([["Goiânia - GO","01.01.2020","","70"]]),[])
if __name__=="__main__": unittest.main()
