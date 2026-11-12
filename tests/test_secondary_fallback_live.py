"""Live revalidation of discovered auction URLs; cached discovery is never proof."""
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from secondary_collect import collect_secondary, SITES

URL = "https://www.flexleiloes.com.br/lotes/2991/"

class SecondaryLiveFallbackTests(unittest.TestCase):
    def test_rechecks_fallback_when_homepage_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "discovery.json"
            path.write_text(json.dumps({"platforms": {"flex": {"candidate_events": [
                {"source_url": URL, "title":
                 "Brasília/DF Leilão de Veículos DATA: 24/11/2026 - 10h00"}
            ]}}}), encoding="utf-8")
            visited = []
            def loader(site, url):
                visited.append((site, url))
                if url in (row[1] for row in SITES.values()):
                    raise OSError("index unavailable")
                if url == URL:
                    return "042 RENAULT SANDERO 091 FIAT UNO 095 FORD RANGER"
                raise OSError("unsupported")
            result, errors = collect_secondary(date(2026, 11, 11), loader, path)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["organizer"], "Flex Leilões")
            self.assertIn(("flex", URL), visited)
            self.assertTrue(any(e["id"] == "flex:index" for e in errors))

    def test_expired_cached_event_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "discovery.json"
            path.write_text(json.dumps({"platforms": {"flex": {"candidate_events": [
                {"source_url": URL, "title":
                 "Brasília/DF Leilão de Veículos DATA: 10/11/2026 - 10h00"}
            ]}}}), encoding="utf-8")
            def loader(site, url):
                if url == URL:
                    return "042 RENAULT SANDERO 091 FIAT UNO 095 FORD RANGER"
                return ""
            result, errors = collect_secondary(date(2026, 11, 11), loader, path)
            self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()
