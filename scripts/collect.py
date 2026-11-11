"""Conservative collector: verify curated municipal auction pages and publish a static feed.

Does NOT discover new sites yet. Missing or blocked pages are reported, not bypassed.
Run: python scripts/collect.py
"""
import json
import re
import unicodedata
import urllib.error
import urllib.request
import time
from datetime import date, datetime, timezone
from auction_clock import auction_today
from html.parser import HTMLParser
from pathlib import Path
from browser_collect import collect_platforms

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
    raw = None
    for attempt in range(2):
        try:
            with urllib.request.urlopen(request, timeout=18) as response:
                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    raise ValueError("unsupported content type: " + content_type)
                raw = response.read(2_000_000)
            break
        except (TimeoutError, OSError, urllib.error.URLError):
            if attempt:
                raise
            time.sleep(1)
    parser = TextExtractor()
    parser.feed(raw.decode("utf-8", errors="replace"))
    page = normalize(" ".join(parser.parts))
    absent = [e for e in source["evidence"] if normalize(e) not in page]
    if absent:
        raise ValueError("missing evidence: " + ", ".join(absent))
    if "cancelado" in page and "leilao cancelado" in page:
        raise ValueError("possible cancellation: manual review required")
    return page


def retry_with_browser(sources):
    """Retry temporarily unreachable curated pages using Chromium's normal TLS checks.

    No certificate bypass. Return verified records only.
    """
    import asyncio
    async def run():
        from playwright.async_api import async_playwright
        verified, errors = [], []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            context = await browser.new_context(locale="pt-BR", ignore_https_errors=False)
            for source in sources:
                page = None
                try:
                    page = await context.new_page()
                    response = await page.goto(
                        source["source_url"], wait_until="domcontentloaded", timeout=20000
                    )
                    if not response or response.status >= 400:
                        raise ValueError("HTTP " + str(response.status if response else "unknown"))
                    text = normalize(await page.locator("body").inner_text(timeout=7000))
                    missing = [e for e in source["evidence"] if normalize(e) not in text]
                    if missing:
                        raise ValueError("missing evidence: " + ", ".join(missing))
                    if "cancelado" in text and "leilao cancelado" in text:
                        raise ValueError("possible cancellation: manual review required")
                    verified.append(source)
                    print("BROWSER RETRY OK:", source["id"])
                except Exception as exc:
                    errors.append({"id": source["id"], "error": "browser retry: " + str(exc).splitlines()[0][:200]})
                finally:
                    if page is not None:
                        await page.close()
            await browser.close()
        return verified, errors
    return asyncio.run(run())

def main():
    from source_collector import collect_curated, browser_fetch, HEALTH
    import asyncio
    today = auction_today()
    checked = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sources = [s for s in json.loads(SOURCES.read_text(encoding="utf-8"))
               if date.fromisoformat(s["auction_date"]) >= today]
    try:
        old_health = json.loads(HEALTH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        old_health = {}
    def browser_loader(urls):
        try:
            return asyncio.run(browser_fetch(urls))
        except Exception as exc:
            return {url:(None, str(exc).splitlines()[0][:180]) for url in urls}
    events, failures, health = collect_curated(
        sources, previous_health=old_health, checked=checked,
        browser_loader=browser_loader)
    HEALTH.write_text(json.dumps(health,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    try:
        platform_events, platform_failures = collect_platforms()
    except Exception as exc:
        platform_events = []
        platform_failures = [{"id":"platforms", "error":str(exc).splitlines()[0][:220]}]
    # Platform adapters can rediscover the same auction under a different ID.
    # Deduplicate only by their specific, normalized official detail URL.
    # Broad agenda/homepage URLs are never strong enough to merge events.
    from urllib.parse import urlsplit, parse_qs
    def detail_key(e):
        url = e.get("source_url") or ""
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
        if host in ("freitasleiloeiro.com.br", "www.freitasleiloeiro.com.br") and parsed.path.lower() == "/leiloes/lotes":
            auction_id = parse_qs(parsed.query).get("leilaoId", [""])[0]
            if auction_id.isdigit():
                return ("freitas", auction_id, e.get("auction_date"))
        if host == "exchange.superbid.net" and parsed.path.startswith("/evento/"):
            return ("superbid", parsed.path.rstrip("/").lower(), e.get("auction_date"))
        return None
    known_ids = {e["id"] for e in events}
    known_details = {key for e in events if (key := detail_key(e))}
    for item in platform_events:
        key = detail_key(item)
        if item["id"] not in known_ids and (key is None or key not in known_details):
            events.append(item)
            known_ids.add(item["id"])
            if key is not None:
                known_details.add(key)
    failures.extend(platform_failures)
    from auction_links import certify_links
    certify_links(events)
    quarantined = [e for e in events if not e.get("link_verified")]
    events = [e for e in events if e.get("link_verified")]
    failures.extend({"id":e["id"], "error":"quarantined: "+e.get("link_review_reason","unverified destination")} for e in quarantined)
    # Publish only independently approved event-level destinations.
    # Unverified official notices remain research leads, never user-facing links.
    from auction_security import valid_destination
    safe_events = []
    for item in events:
        if valid_destination(item):
            item['destination_verified'] = True
            safe_events.append(item)
        else:
            failures.append({'id':item['id'],'error':'Individual auction destination not approved; quarantined'})
    events = safe_events
    events.sort(key=lambda e:(e["auction_date"],e["auction_time"] or "",e["city"]))
    # Failed validation does not silently carry an unverified event into the feed.
    OUTPUT.write_text(json.dumps({"updated_at":checked,"events":events},
        ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    unique = {a.get("event_id") or a["id"] for a in events}
    by_org = {}
    for a in events:
        by_org.setdefault(a["organizer"],set()).add(a.get("event_id") or a["id"])
    all_states = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
    present = {state for a in events for state in (a.get("states") or [a["state"]])}
    report = {
        "checked_at":checked,"verified":len(events),"unique_events":len(unique),
        "states_with_events":sorted(present),
        "states_without_events":sorted(all_states - present),
        "state_presence_percent":round(100 * len(present) / len(all_states),1),
        "coverage_definition":"Presence of at least one event, not fraction of all auctions discovered",
        "organizers":{k:len(v) for k,v in sorted(by_org.items())},
        "platform_events":sum(e.get("source_type")=="private" for e in events),
        "direct_event_links":len(events),
        "calendar_links":sum(e.get("source_link_type") == "calendar" for e in events),
        "curated_source_links":sum(bool(e.get("event_url")) for e in events),
        "curated_success":health["successful_sources"],
        "curated_failure":health["failed_sources"],
        "quarantined_links":len(quarantined),
        "failed":failures
    }
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Confirmed {len(unique)} events; {len(failures)} source errors")

if __name__ == "__main__":
    main()
