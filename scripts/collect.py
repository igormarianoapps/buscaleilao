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
    # Independently discover official state auction pages containing real lots.
    try:
        from mg_detran_collect import collect_mg
        mg_events, mg_failures = collect_mg(today=today)
    except Exception as exc:
        mg_events, mg_failures = [], [{"id":"mg-detran","error":str(exc)[:180]}]
    for event in mg_events:
        if event["id"] not in known_ids:
            events.append(event)
            known_ids.add(event["id"])
    failures.extend(mg_failures)
    try:
        from regional_collect import collect_regionals
        regional_events, regional_errors = collect_regionals(today=today)
    except Exception as exc:
        regional_events, regional_errors = [], [{"id":"regional","error":str(exc)[:180]}]
    for item in regional_events:
        if item["id"] not in known_ids:
            events.append(item)
            known_ids.add(item["id"])
    failures.extend(regional_errors)
    try:
        from bolsa_collect import collect_bolsa
        bolsa_events,bolsa_errors=collect_bolsa(today=today)
    except Exception as exc:
        bolsa_events,bolsa_errors=[],[{"id":"bolsa","error":str(exc)[:160]}]
    for item in bolsa_events:
        if item["id"] not in known_ids:
            events.append(item)
            known_ids.add(item["id"])
    failures.extend(bolsa_errors)
    try:
        from leilo_collect import collect_leilo
        leilo_events,leilo_errors=collect_leilo(today=today)
    except Exception as exc:
        leilo_events,leilo_errors=[],[{"id":"leilo","error":str(exc)[:180]}]
    for item in leilo_events:
        if item["id"] not in known_ids:
            events.append(item)
            known_ids.add(item["id"])
    failures.extend(leilo_errors)
    try:
        from secondary_collect import collect_secondary
        other_events,other_errors=collect_secondary(today=today)
    except Exception as exc:
        other_events,other_errors=[],[{"id":"secondary","error":str(exc)[:180]}]
    for item in other_events:
        if item["id"] not in known_ids:
            events.append(item)
            known_ids.add(item["id"])
    failures.extend(other_errors)
    # Preserve a discovered-at timestamp only for newly observed identities.
    try:
        previous=json.loads(OUTPUT.read_text(encoding="utf-8")).get("events",[])
    except (OSError,ValueError):
        previous=[]
    known_first={}
    known_previous_ids=set()
    for event in previous:
        key=(event.get("organizer"),event.get("event_id") or event.get("id"))
        known_previous_ids.add(key)
        if event.get("first_seen_at"):
            known_first[key]=event["first_seen_at"]
    from auction_links import certify_links
    from auction_security import valid_destination
    certify_links(events)
    safe_events, quarantined=[],[]
    for item in events:
        key=(item.get("organizer"),item.get("event_id") or item.get("id"))
        if (item.get("status") != "scheduled" or
                date.fromisoformat(item["auction_date"]) < today):
            reason="expired, canceled or not scheduled"
        elif not item.get("link_verified"):
            reason=item.get("link_review_reason","unapproved event URL")
        elif not valid_destination(item):
            reason="individual event not corroborated by trusted source"
        else:
            reason=None
        if reason:
            quarantined.append({"id":item.get("id"),"organizer":item.get("organizer"),
                                "source_url":item.get("source_url"),"reason":reason})
            failures.append({"id":item.get("id"),"error":"quarantined: "+reason})
            continue
        item["destination_verified"]=True
        item["link_review"]="approved"
        if key in known_first:
            item["first_seen_at"]=known_first[key]
        elif key not in known_previous_ids:
            item["first_seen_at"]=checked
        safe_events.append(item)
    events=safe_events
    quarantine_path=ROOT/"app/quarantine-report.json"
    quarantine_path.write_text(json.dumps({"checked_at":checked,
        "quarantined":quarantined,"total":len(quarantined)},
        ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
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
        "official_state_events":sum(e.get("organizer")=="Detran MG" for e in events),
        "regional_private_events":sum(e.get("organizer") in ("Vardana Leilões","Claudio Kuss Leilões") for e in events),
        "regional_adapter_failures":len(regional_errors),
        "bolsa_events":sum(e.get("organizer")=="Bolsa de Leilões" for e in events),
        "leilo_events":len({e.get("event_id") or e["id"] for e in events if e.get("organizer")=="Leilo"}),
        "secondary_events":sum(e.get("organizer") in ("Parque dos Leilões","Flex Leilões","Hisa Leilões") for e in events),
        "leilo_errors":len(leilo_errors),
        "secondary_errors":len(other_errors),
        "new_discoveries":len({e.get("event_id") or e["id"] for e in events if e.get("first_seen_at")==checked}),
        "failed":failures
    }
    REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Confirmed {len(unique)} events; {len(failures)} source errors")

if __name__ == "__main__":
    main()
