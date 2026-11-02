"""Find potential municipal vehicle auctions via public RSS search results.

Discovery candidates are NEVER published as confirmed auctions.
Candidates require review and source-specific evidence before joining sources.json.
"""
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "app" / "discovery-candidates.json"
STATES = ["GO", "SP", "MG", "PR"]
QUERIES = [
    'leilão veículos prefeitura edital 2026',
    'leilão veículos detran 2026',
    'leilão de veículos municipal novembro 2026',
]
UA = "BuscaLeilao/0.2 (https://github.com/igormarianoapps/buscaleilao)"
MAX_ITEMS = 50


def discover(queries=QUERIES):
    found = {}
    errors = []
    for term in queries:
        url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
            "q": term, "hl": "pt-BR", "gl": "BR", "ceid": "BR:pt-419"
        })
        try:
            request = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(request, timeout=20) as response:
                data = response.read(1_000_000)
            tree = ET.fromstring(data)
            for item in tree.findall(".//channel/item"):
                title = (item.findtext("title") or "").strip()
                link = (item.findtext("link") or "").strip()
                pub = (item.findtext("pubDate") or "").strip()
                if not link.startswith("https://") or not re.search(r"leil[aã]o", title, re.I):
                    continue
                if not re.search(r"ve[ií]cul|autom[oó]v|moto|sucata", title, re.I):
                    continue
                found[link] = {"title": title[:220], "url": link, "published": pub,
                               "discovered_by": "news_rss", "status": "unverified"}
                if len(found) >= MAX_ITEMS:
                    break
        except (OSError, ValueError, ET.ParseError) as exc:
            errors.append({"query": term, "error": str(exc)[:200]})
    return list(found.values()), errors


def main():
    candidates, errors = discover()
    payload = {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "candidates": candidates, "errors": errors,
               "note": "Candidates are unverified leads, not auction events."}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Discovery: {len(candidates)} candidates, {len(errors)} query errors")


if __name__ == "__main__":
    main()
