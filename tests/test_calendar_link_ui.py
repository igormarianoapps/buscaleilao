"""Regression checks for honest calendar-link labelling in static MVP UI."""
import unittest
from pathlib import Path

HTML=(Path(__file__).resolve().parents[1]/"app/index.html")

class CalendarLinkUXTests(unittest.TestCase):
    def test_calendar_is_not_described_as_specific_auction(self):
        html=HTML.read_text(encoding="utf-8")
        self.assertIn("Consultar agenda geral do leiloeiro",html)
        self.assertIn("Este link leva à agenda geral, não ao evento.",html)
        self.assertIn('a.source_link_type==="calendar"?',html)
        self.assertIn("Procure a data e o estado indicados acima.",html)

    def test_external_links_preserve_security_and_source_type(self):
        html=HTML.read_text(encoding="utf-8")
        self.assertIn('rel="noopener noreferrer"',html)
        self.assertIn('target="_blank"',html)
        self.assertIn('a.source_link_type==="event"?"Ver leilão específico',html)
        self.assertIn("escapeHTML(a.source_url)",html)

if __name__=="__main__":
    unittest.main()
