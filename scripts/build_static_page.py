"""Build the self-contained static page from the validated auction feed.

Avoid fragile runtime JS module / JSON fetches on static hosts with rewritten
root paths. No network, dependencies or changes to verified source records.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "app" / "index.template.html"
AGENDA = ROOT / "app" / "agenda.mjs"
FEED = ROOT / "app" / "events.json"
OUTPUT = ROOT / "app" / "index.html"
CODE_MARKER = "/* __AGENDA_CODE__ */"
FEED_MARKER = "__EMBEDDED_FEED__"


def build_page(template, agenda_source, feed):
    if template.count(CODE_MARKER) != 1 or template.count(FEED_MARKER) != 1:
        raise ValueError("HTML template placeholders missing or duplicated")
    if not isinstance(feed, dict) or not isinstance(feed.get("events"), list):
        raise ValueError("Invalid verified events feed")
    if not feed["events"]:
        raise ValueError("Refuse to publish an empty verified feed")
    if "export " not in agenda_source:
        raise ValueError("Unexpected auction module format")
    # Keep a single implementation of sorting, filtering and source labels.
    inline_code = agenda_source.replace("export function ", "function ")
    if "export " in inline_code or "import " in inline_code:
        raise ValueError("Agenda source has unsupported module statements")
    # A JSON script must never contain a literal closing HTML script tag.
    payload = json.dumps(feed, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    output = template.replace(CODE_MARKER, inline_code).replace(FEED_MARKER, payload)
    if CODE_MARKER in output or FEED_MARKER in output:
        raise ValueError("Unexpanded placeholders")
    return output


def main():
    page = build_page(
        TEMPLATE.read_text(encoding="utf-8"),
        AGENDA.read_text(encoding="utf-8"),
        json.loads(FEED.read_text(encoding="utf-8")),
    )
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"Built standalone HTML with {len(json.loads(FEED.read_text(encoding='utf-8'))['events'])} verified records")


if __name__ == "__main__":
    main()
