"""Resilient source-specific verification for curated public auction announcements.

One HTTP request per unique page; a failure is isolated to that source.
No insecure TLS, CAPTCHA bypass, guessed dates, or publication of RSS leads.
"""
import asyncio
import json
import re
import time
import urllib.error
import urllib.request
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / "app" / "source-health.json"
UA = "BuscaLeilaoBot/0.5 (+https://github.com/igormarianoapps/buscaleilao)"

class VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.ignored = 0
    def handle_starttag(self, tag, attrs):
        if tag in ("script","style","noscript","svg"):
            self.ignored += 1
        if not self.ignored and tag in ("p","div","section","li","tr","td","h1","h2","h3"):
            self.parts.append(" ")
    def handle_endtag(self, tag):
        if tag in ("script","style","noscript","svg") and self.ignored:
            self.ignored -= 1
        elif not self.ignored and tag in ("p","div","section","li","tr","td","h1","h2","h3"):
            self.parts.append(" ")
    def handle_data(self, data):
        if not self.ignored:
            self.parts.append(data)

def norm(text):
    text = unicodedata.normalize("NFKD", str(text)).casefold()
    return re.sub(r"\s+", " ", "".join(c for c in text if not unicodedata.combining(c))).strip()

def validate(text, source):
    page = norm(text)
    missing = [item for item in source.get("evidence", []) if norm(item) not in page]
    if missing:
        raise ValueError("missing evidence: " + "; ".join(missing)[:160])
    if "leilao cancelado" in page or "leilao foi cancelado" in page:
        raise ValueError("possible cancellation (requires review)")
    return True

def fetch_text(url):
    request = urllib.request.Request(url, headers={"User-Agent":UA,"Accept":"text/html"})
    with urllib.request.urlopen(request, timeout=12) as response:
        if "html" not in response.headers.get("Content-Type","").lower():
            raise ValueError("Not a public HTML page")
        raw = response.read(2_000_000)
    reader = VisibleText()
    reader.feed(raw.decode("utf-8", errors="replace"))
    return " ".join(reader.parts)

async def browser_fetch(urls):
    """One browser context, independent pages; normal HTTPS verification."""
    from playwright.async_api import async_playwright
    result = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await browser.new_context(locale="pt-BR", ignore_https_errors=False)
        for url in urls:
            page = await ctx.new_page()
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                if not response or response.status >= 400:
                    raise ValueError(f"HTTP {response.status if response else 'unknown'}")
                result[url] = (await page.locator("body").inner_text(timeout=5000), None)
            except Exception as exc:
                result[url] = (None, str(exc).splitlines()[0][:180])
            finally:
                await page.close()
        await browser.close()
    return result

def collect_curated(sources, previous_health=None, checked=None, browser_loader=None):
    checked = checked or datetime.now(timezone.utc).isoformat(timespec="seconds")
    previous = (previous_health or {}).get("sources", {})
    grouped = {}
    for source in sources:
        grouped.setdefault(source["source_url"], []).append(source)
    pages = {}
    with ThreadPoolExecutor(max_workers=5) as pool:
        futures = {pool.submit(fetch_text,url):url for url in grouped}
        for future in as_completed(futures):
            url = futures[future]
            try:
                pages[url] = (future.result(), None)
            except Exception as exc:
                pages[url] = (None, str(exc)[:200])
    # Browser fallback is only for pages that are temporarily unavailable or
    # render required information with JavaScript. Never retry explicit 403/401.
    retry_urls = []
    for url, associated in grouped.items():
        content, error = pages[url]
        if error and ("403" in error or "401" in error):
            continue
        if error or any(not all(norm(e) in norm(content) for e in src.get("evidence",[])) for src in associated):
            retry_urls.append(url)
    if retry_urls and browser_loader is not None:
        fallback = browser_loader(retry_urls)
        for url in retry_urls:
            txt, err = fallback.get(url,(None,"No browser response"))
            if txt:
                # Keep valid static evidence when a shared URL supports several
                # sessions and the browser exposes only part of the page.
                original, old_error = pages[url]
                if original and not old_error:
                    pages[url] = (original + "\\n" + txt, None)
                else:
                    pages[url] = (txt, None)
            elif pages[url][0] is None:
                pages[url] = (None,err)
    events, failed, statuses = [], [], {}
    for src in sources:
        content, error = pages[src["source_url"]]
        try:
            if error: raise ValueError(error)
            validate(content, src)
            event = {k:v for k,v in src.items() if k != "evidence"}
            event.update(status="scheduled",last_checked_at=checked)
            events.append(event)
            statuses[src["id"]] = {"status":"ok","last_success_at":checked,"consecutive_failures":0}
        except ValueError as exc:
            prior = previous.get(src["id"],{})
            reason = str(exc)[:220]
            failed.append({"id":src["id"],"error":reason})
            statuses[src["id"]] = {"status":"failed","reason":reason,
                "last_success_at":prior.get("last_success_at"),
                "consecutive_failures":prior.get("consecutive_failures",0)+1}
    return events, failed, {"checked_at":checked, "sources":statuses,
        "source_count":len(sources), "successful_sources":len(events),
        "failed_sources":len(failed)}
