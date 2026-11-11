import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from auction_platform_watch import host_ok
class SPATests(unittest.TestCase):
 def test_fragment_route_only_for_discovery(self):
    from urllib.parse import urldefrag
    s={"allowed_hosts":["www.mcleilao.com.br"]}
    self.assertTrue(host_ok(s,urldefrag("https://www.mcleilao.com.br/#/home").url))
    self.assertFalse(host_ok(s,"https://www.mcleilao.com.br/#/home"))
if __name__=="__main__":unittest.main()
