"""Bounded, no-bypass discovery of auction leads from known official portals.

This adapter NEVER creates events.json rows: links and real auction dates need
independent source/lot validation before being made customer-facing.
"""
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "app" / "portal-sources.json"
OUTPUT = ROOT / "app" / "portal-candidates.json"
UA = "BuscaLeilaoBot/0.6 (+https://github.com/igormarianoapps/buscaleilao)"
STATES = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())

def normalize(value):
    text = unicodedata.normalize("NFKD", str(value or "")).casefold()
    return " ".join("".join(x for x in text if not unicodedata.combining(x)).split())

class AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.href = None
        self.words = []
        self.ignored = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self.ignored += 1
        if tag == "a" and not self.ignored:
            self.href = dict(attrs).get("href")
            self.words = []
    def handle_data(self, data):
        if self.href is not None and not self.ignored:
            self.words.append(data)
    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(self.words).strip()))
            self.href = None
            self.words = []
        if tag in ("script", "style", "noscript") and self.ignored:
            self.ignored -= 1

def valid_source(source):
    p = urllib.parse.urlsplit(source.get("url", ""))
    return bool(p.scheme == "https" and p.hostname == source.get("host")
                and p.username is None and p.password is None and
                p.port in (None, 443) and source.get("state") in STATES and
                source.get("review_required") is True and
                source.get("status") == "discovery_only")

def candidate_links(source, html):
    """Only same-host leads; never infer date, count, or legitimacy."""
    if not valid_source(source):
        raise ValueError("untrusted registry source")
    parser = AnchorParser()
    parser.feed(html[:1_000_000])
    seen = set()
    result = []
    for href, label in parser.links:
        target = urllib.parse.urljoin(source["url"], href)
        parsed = urllib.parse.urlsplit(target)
        if (parsed.scheme != "https" or parsed.hostname != source["host"] or
                parsed.username or parsed.password or parsed.port not in (None,443)):
            continue
        # An auction headline/link is a research lead, not proof of vehicles.
        # Navigation fragments, print links and search controls are not leads.
        origin = urllib.parse.urlsplit(source["url"])
        if parsed.fragment or (parsed.path == origin.path and parsed.query != origin.query):
            continue
        if target.rstrip("/") == source["url"].rstrip("/") or target in seen:
            continue
        label_text = normalize(label)
        leaf = normalize(parsed.path.rstrip("/").split("/")[-1])
        if not label_text or any(word in label_text for word in (
                "ir para", "skip navigation", "rastreamento",
                "credenciamento", "imprimir", "aeronave")):
            continue
        if label_text in ("leiloes", "leilao", "editais", "edital"):
            continue
        # Require event-specific evidence in the link text or filename:
        # the source page path alone often contains the word "leiloes".
        if not (re.search(r"leilao", label_text) or
                re.search(r"leilao", leaf) or
                (re.search(r"edital", label_text) and
                 re.search(r"veicul|moto|sucata", label_text))):
            continue
        years = [int(y) for y in re.findall(r"\b20\d{2}\b", label_text + " " + leaf)]
        if years and max(years) < datetime.now(timezone.utc).year:
            continue
        seen.add(target)
        result.append({"title": (label or "Documento de leilão")[:240],
            "source_url": target, "source_kind": "official_portal",
            "state_hint": source["state"], "source_registry_id": source["id"],
            "review_status": "needs_edital_and_individual_lot_link",
            "date_hint": None, "date_hint_status": "not_verified"})
        if len(result) >= 30:
            break
    return result

def fetch_html(source):
    if not valid_source(source):
        raise ValueError("untrusted registry source")
    request = urllib.request.Request(source["url"], headers={
        "User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(request, timeout=12) as resp:
        final = urllib.parse.urlsplit(resp.geturl())
        if final.scheme != "https" or final.hostname != source["host"]:
            raise ValueError("redirected outside official source host")
        if "html" not in resp.headers.get("Content-Type", "").lower():
            raise ValueError("unexpected content type")
        return resp.read(1_000_001).decode("utf-8", errors="replace")

def scan(sources, loader=fetch_html):
    leads, statuses, seen = [], [], set()
    for source in sources:
        try:
            html = loader(source)
            candidates = candidate_links(source, html)
            new = [x for x in candidates if x["source_url"] not in seen]
            seen.update(x["source_url"] for x in new)
            leads.extend(new)
            statuses.append({"id": source["id"], "status": "ok",
                             "candidates": len(new)})
        except Exception as exc:
            statuses.append({"id": source.get("id"), "status": "failed",
                             "reason": str(exc).splitlines()[0][:160],
                             "candidates": 0})
    return leads, statuses

def main():
    sources = json.loads(REGISTRY.read_text(encoding="utf-8"))
    candidates, statuses = scan(sources)
    report = {"checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "sources_checked": len(sources),
              "sources_reachable": sum(x["status"] == "ok" for x in statuses),
              "candidates_count": len(candidates),
              "events_automatically_published": 0,
              "source_statuses": statuses, "candidates": candidates}
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(f"Official portals: {report['sources_reachable']}/{len(sources)} reached; "
          f"{len(candidates)} unverified leads, 0 published")
if __name__ == "__main__":
    main()
