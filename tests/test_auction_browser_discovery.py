import ast,unittest
from pathlib import Path
class BrowserCollectionTests(unittest.TestCase):
    def test_browser_collector_is_research_only(self):
        source=(Path(__file__).resolve().parents[1]/"scripts/auction_browser_discovery.py").read_text()
        self.assertIn('"publication_allowed":False',source)
        self.assertIn('"published":0',source)
        self.assertNotIn("ignore_https_errors=True",source)
        ast.parse(source)
if __name__=="__main__":unittest.main()
