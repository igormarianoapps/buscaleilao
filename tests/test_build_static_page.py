"""Regression checks that generated public HTML exactly matches verified feed data."""
import json
import re
import unittest
from pathlib import Path

from scripts.build_static_page import build_page, CODE_MARKER, FEED_MARKER

ROOT=Path(__file__).resolve().parents[1]
APP=ROOT/"app"

class StandalonePageTests(unittest.TestCase):
    def test_checked_in_html_matches_feed_and_template(self):
        html=build_page(
            (APP/"index.template.html").read_text(encoding="utf-8"),
            (APP/"agenda.mjs").read_text(encoding="utf-8"),
            json.loads((APP/"events.json").read_text(encoding="utf-8")),
        )
        self.assertEqual((APP/"index.html").read_text(encoding="utf-8"),html)
        self.assertNotIn(CODE_MARKER,html)
        self.assertNotIn(FEED_MARKER,html)

    def test_embedded_feed_is_valid_and_current(self):
        page=(APP/"index.html").read_text(encoding="utf-8")
        payload=re.search(r'<script id="embedded-feed" type="application/json">([\s\S]*?)</script>',page)
        self.assertIsNotNone(payload)
        embedded=json.loads(payload.group(1))
        feed=json.loads((APP/"events.json").read_text(encoding="utf-8"))
        self.assertEqual(embedded,feed)
        self.assertGreater(len(feed["events"]),0)

    def test_generator_refuses_empty_feed_and_escapes_script_termination(self):
        template='<script id="embedded-feed">__EMBEDDED_FEED__</script><script>/* __AGENDA_CODE__ */</script>'
        code='export function filterAuctions(){return []}'
        with self.assertRaises(ValueError):
            build_page(template,code,{"events":[]})
        result=build_page(template,code,{"events":[{"title":"</script><img src=x onerror=1>"}]})
        self.assertNotIn('</script><img',result)
        self.assertIn(r'\u003c/script\u003e',result)

if __name__=="__main__":
    unittest.main()
