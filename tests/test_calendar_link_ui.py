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

    def test_html_has_no_literal_newline_escape_artifacts(self):
        html=HTML.read_text(encoding="utf-8")
        self.assertNotIn("\\n.topline",html)
        self.assertNotIn("\\n.link-note",html)
        self.assertNotIn('</a>\\n',html)

    def test_mobile_layout_and_keyboard_focus_exist(self):
        html=HTML.read_text(encoding="utf-8")
        self.assertIn("@media(max-width:600px)",html)
        self.assertIn(":focus-visible",html)
        self.assertIn(".filters button{flex-basis:100%",html)

    def test_filters_do_not_refetch_feed_on_each_search(self):
        html=HTML.read_text(encoding="utf-8")
        self.assertEqual(html.count('fetch("/app/events.json"'),1)
        self.assertIn('filters.addEventListener("submit",e=>{e.preventDefault();applyFilters()})',html)
        self.assertIn('filters.addEventListener("reset"',html)
        self.assertIn('let currentFeed=null',html)
        self.assertIn('emptyResultsMessage({state:form.get("state"),day:form.get("day")})',html)

    def test_page_inline_module_parses_in_node(self):
        import re
        import subprocess
        html=HTML.read_text(encoding="utf-8")
        match=re.search(r'<script type="module">([\s\S]+?)</script>',html)
        self.assertIsNotNone(match)
        parsed=subprocess.run(
            ["node","--check","--input-type=module"],
            input=match.group(1),text=True,capture_output=True)
        self.assertEqual(parsed.returncode,0,parsed.stderr)

    def test_external_links_preserve_security_and_source_type(self):
        html=HTML.read_text(encoding="utf-8")
        self.assertIn('rel="noopener noreferrer"',html)
        self.assertIn('target="_blank"',html)
        self.assertIn('a.source_link_type==="event"?"Ver leilão específico',html)
        self.assertIn("escapeHTML(a.source_url)",html)

if __name__=="__main__":
    unittest.main()
