import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from build_sources_page import render,approved_count
class TestSources(unittest.TestCase):
    def test_all_batches_and_disclaimer(self):
        sites=[{"id":str(i),"name":f"Fonte {i}","batch":i,
                "discovery_url":f"https://f{i}.example/","allowed_hosts":[f"f{i}.example"]} for i in range(1,5)]
        page=render(sites)
        self.assertEqual(page.count('class="source"'),4)
        self.assertIn("Uma fonte monitorada não significa um leilão validado",page)
    def test_unverified_not_counted(self):
        site={"allowed_hosts":["www.exemplo.com"]}
        events=[{"id":"x","source_url":"https://www.exemplo.com/leilao/10","link_verified":True,"destination_verified":True},
                {"id":"y","source_url":"https://www.exemplo.com/leilao/11","link_verified":True}]
        self.assertEqual(approved_count(site,events),1)
    def test_markup_escaped(self):
        site={"id":"x","name":"<script>","batch":1,"discovery_url":"https://safe.example/",
              "allowed_hosts":["safe.example"]}
        self.assertNotIn("<script>",render([site]))
if __name__=="__main__":unittest.main()


class BrowserDiscoverySourceStatusTests(unittest.TestCase):
 def test_source_count_does_not_imply_verified_auction(self):
    sample={"id":"palacio","name":"Palácio","batch":3,"discovery_url":"https://www.palaciodosleiloes.com.br/site/index.php","allowed_hosts":["www.palaciodosleiloes.com.br"]}
    page=render([sample],{"platforms":{"palacio":{"status":"unreachable"}}},[],
      {"platforms":{"palacio":{"availability":"reachable","discovered_links":13}}})
    self.assertIn("13 links em análise",page)
    self.assertIn("Monitorado, sem eventos confirmados",page)
    self.assertNotIn("13 leilão(ões)",page)
