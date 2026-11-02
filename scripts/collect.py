"""Conservative collector: verify curated municipal auction pages and publish a static feed.

Does NOT discover new sites yet. Missing or blocked pages are reported, not bypassed.
Run: python scripts/collect.py
"""
import json
import re
import unicodedata
import urllib.error
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "app" / "sources.json"
OUTPUT = ROOT / "app" / "events.json"
REPORT = ROOT / "app" / "collection-report.json"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.ignored = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.ignored += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript") and self.ignored:
            self.ignored -= 1

    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)


def normalize(value):
    value = unicodedata.normalize("NFKD", value).casefold()
    return re.sub(r"\s+", " ", "".join(c for c in value if not unicodedata.combining(c))).strip()


def check(source):
    request = urllib.request.Request(
        source["source_url"],
        headers={"User-Agent": "BuscaLeilaoBot/0.1 (+https://github.com/igormarianoapps/buscaleilao)",
                 "Accept": "text/html"}
    )
    with urllib.request.urlopen(request, timeout=18) as response:
        content_type = response.headers.get("Content-Type", "")
        if "text/html" not in content_type:
            raise ValueError("unsupported content type: " + content_type)
        raw = response.read(2_000_000)
    parser = TextExtractor()
    parser.feed(raw.decode("utf-8", errors="replace"))
    page = normalize(" ".join(parser.parts))
    absent = [e for e in source["evidence"] if normalize(e) not in page]
    if absent:
        raise ValueError("missing evidence: " + ", ".join(absent))
    if "cancelado" in page and "leilao cancelado" in page:
        raise ValueError("possible cancellation: manual review required")
    return page


def main():
    today = date.today()
    checked = datetime.now(timezone.utc).isoformat(timespec="seconds")
    events = []
    failures = []
    for source in json.loads(SOURCES.read_text(encoding="utf-8")):
        if date.fromisoformat(source["auction_date"]) < today:
            continue
        try:
            check(source)
            event = {k: v for k, v in source.items() if k != "evidence"}
            event.update(status="scheduled", last_checked_at=checked)
            events.append(event)
            print("OK:", source["id"])
        except (urllib.error.URLError, TimeoutError, ValueError, OSError) as exc:
            failures.append({"id": source["id"], "error": str(exc)[:300]})
            print("SKIP:", source["id"], str(exc)[:100])
    events.sort(key=lambda e: (e["auction_date"], e["auction_time"] or "", e["city"]))
    # Do not erase the complete feed on a transient outage.
    if events:
        OUTPUT.write_text(json.dumps({"updated_at": checked, "events": events}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REPORT.write_text(json.dumps({"checked_at": checked, "verified": len(events), "failed": failures}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(events)}; blocked/unconfirmed {len(failures)}")


if __name__ == "__main__":
    main()
