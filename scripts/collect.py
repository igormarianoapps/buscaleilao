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
    today = date.today()
    checked = datetime.now(timezone.utc).isoformat(timespec="seconds")
    events = []
    failures = []
    retry_sources = []
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
            if isinstance(exc, (urllib.error.URLError, TimeoutError, OSError)) or (isinstance(exc, ValueError) and "missing evidence:" in str(exc)):
                retry_sources.append(source)
            print("SKIP:", source["id"], str(exc)[:100])
    if retry_sources:
        recovered, browser_errors = retry_with_browser(retry_sources)
        recovered_ids = {s["id"] for s in recovered}
        failures = [f for f in failures if f["id"] not in recovered_ids]
        for source in recovered:
            record = {k: v for k, v in source.items() if k != "evidence"}
            record.update(status="scheduled", last_checked_at=checked)
            events.append(record)
        errors_by_id = {e["id"]: e["error"] for e in browser_errors}
        for failure in failures:
            if failure["id"] in errors_by_id:
                failure["browser_error"] = errors_by_id[failure["id"]]
    platform_events, platform_failures = collect_platforms()
    events.extend(platform_events)
    failures.extend(platform_failures)
    events.sort(key=lambda e: (e["auction_date"], e["auction_time"] or "", e["city"]))
    # A failed verification must not leave outdated or unverified events visible.
    OUTPUT.write_text(json.dumps({"updated_at": checked, "events": events}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    event_keys = {a.get("event_id") or a["id"] for a in events}
    state_coverage = sorted({a["state"] for a in events})
    by_organizer = {}
    for a in events:
        by_organizer.setdefault(a["organizer"], set()).add(a.get("event_id") or a["id"])
    report = {
        "checked_at": checked, "verified": len(events),
        "unique_events": len(event_keys),
        "states_with_events": state_coverage,
        "organizers": {k: len(v) for k, v in sorted(by_organizer.items())},
        "platform_events": len(platform_events), "failed": failures
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Verified {len(events)}; blocked/unconfirmed {len(failures)}")


if __name__ == "__main__":
    main()
