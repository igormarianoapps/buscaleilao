"""Find potential municipal vehicle auctions via public RSS search results.

Discovery candidates are NEVER published as confirmed auctions.
Candidates require review and source-specific evidence before joining sources.json.
"""
import json
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from urllib.parse import urlparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "app" / "discovery-candidates.json"
STATES = ["GO", "SP", "MG", "PR", "RJ", "RS", "SC", "BA", "PE", "CE", "PA", "MT", "MS", "MA", "ES", "DF", "AM", "PB", "RN", "PI", "TO", "RO", "AC", "AL", "AP", "RR", "SE"]
YEAR = datetime.now(timezone.utc).year
QUERIES = [
    f'leilão veículos prefeitura edital {YEAR}',
    f'leilão veículos detran {YEAR}',
    f'leilão de veículos municipal {YEAR}',
    f'leilão veículos leiloeiro {YEAR}',
    f'leilão carros motos seguradoras {YEAR}',
    f'leilão veículos prefeitura cidade pequena {YEAR}',
    f'leilão veículos Polícia Rodoviária Federal edital {YEAR}',
    f'leilão veículos Freitas Superbid Sodré Guariglia {YEAR}',
    f'leilão carros veículos edital municípios interior {YEAR}',
]
UA = "BuscaLeilao/0.2 (https://github.com/igormarianoapps/buscaleilao)"
MAX_ITEMS = 180
MAX_AGE_DAYS = 120



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
                try:
                    published = parsedate_to_datetime(pub)
                    if published.tzinfo is None:
                        published = published.replace(tzinfo=timezone.utc)
                    if published < datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS):
                        continue
                except (TypeError, ValueError, OverflowError):
                    continue
                publisher = item.find("source")
                domain = publisher.attrib.get("url", "") if publisher is not None else ""
                host = (urlparse(domain).hostname or "").lower()
                rank = "official" if (host.endswith(".gov.br") or host.endswith(".leg.br") or host.endswith(".jus.br")) else "other"
                found[link] = {"title": title[:220], "url": link, "published": pub,
                               "publisher_url": domain, "source_priority": rank,
                               "discovered_by": "news_rss", "status": "unverified"}
                if len(found) >= MAX_ITEMS:
                    break
        except (OSError, ValueError, ET.ParseError) as exc:
            errors.append({"query": term, "error": str(exc)[:200]})
    results = list(found.values())
    results.sort(key=lambda x: (x["source_priority"] != "official", -parsedate_to_datetime(x["published"]).timestamp()))
    return results, errors


def main():
    candidates, errors = discover()
    payload = {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "candidates": candidates, "errors": errors,
               "note": "Candidates are unverified leads, not auction events."}
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Discovery: {len(candidates)} candidates, {len(errors)} query errors")


if __name__ == "__main__":
    main()
