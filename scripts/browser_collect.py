"""Extract PUBLIC auction calendar entries using a real browser.

No logins, bypasses, lot details, or assumptions about vehicle counts.
"""
import asyncio
import hashlib
import re
import unicodedata
from datetime import date, datetime, timezone

COPART_URL = "https://www.copart.com.br/salesListResult/"
VIP_URL = "https://www.vipleiloes.com.br/agenda"
STATES = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
DATE = r"(\d{2}[./]\d{2}[./]\d{4})"

def future_date(raw):
    try:
        day, month, year = map(int, re.split(r"[./]", raw))
        d = date(year, month, day)
        return d.isoformat() if d >= date.today() else None
    except (ValueError, TypeError):
        return None

def slug(value):
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", value).strip("-")

def event(key, title, state, city, day, hour, organizer, url):
    return {
        "id":key, "title":title, "state":state, "city":city,
        "auction_date":day, "auction_time":hour, "vehicle_count":None,
        "organizer":organizer, "source_type":"private", "source_url":url,
        "status":"scheduled", "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")
    }

def parse_copart_rows(rows):
    """Each public sales-list row is [yard, sale date, next sale date, count].
    The last column is NOT a verified vehicle count and is ignored.
    """
    results = {}
    yard_pattern = re.compile(r"^(.{3,75}?)\s*-\s*([A-Z]{2})$")
    for row in rows:
        if len(row) < 2:
            continue
        yard = re.sub(r"\s+", " ", row[0]).strip()
        matched = yard_pattern.fullmatch(yard)
        if not matched: continue
        city, state = matched.groups()
        if state not in STATES: continue
        dates = []
        # Sales-list may contain current and next auction dates for same yard.
        for col in row[1:3]:
            m = re.search(DATE, col)
            if m:
                day = future_date(m.group(1))
                if day: dates.append(day)
        for day in set(dates):
            key = f"copart-{day}-{state.lower()}-{slug(city)}"
            results[key] = event(key, f"Leilão Copart — {city}", state, city, day, None, "Copart", COPART_URL)
    return list(results.values())

def parse_vip_text(text):
    """Only publish a VIP listing if its own block names a future date and UFs.

    Each listing gets a shared event_id across UFs. Avoid assuming that
    category/date/time uniquely identify an auction.
    """
    results = []
    normalized = re.sub(r"\r", "", text)
    sections = re.split(
        r"(?=\bIn[ií]cio\s*:?[ \t]*\d{2}/\d{2}/\d{4})",
        normalized, flags=re.I
    )
    for block in sections[1:]:
        match = re.search(
            r"\bIn[ií]cio\s*:?[ \t]*(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})",
            block, re.I
        )
        if not match:
            continue
        day = future_date(match.group(1))
        if not day:
            continue
        states_match = re.search(
            r"\bEstados\s*:?\s*([A-Z]{2}(?:\s*[-,/]\s*[A-Z]{2})*)\b",
            block
        )
        if not states_match:
            continue
        states = re.split(r"\s*[-,/]\s*", states_match.group(1))
        if not states or any(state not in STATES for state in states):
            continue
        hour = match.group(2)
        # Hash the public listing itself, not just its category and clock time.
        # No vehicle count can be inferred from the number of lots.
        identity = hashlib.sha256(block.strip().encode("utf-8")).hexdigest()[:14]
        event_id = f"vip-{day}-{hour.replace(':', '')}-{identity}"
        for state in dict.fromkeys(states):
            entry = event(f"{event_id}-{state.lower()}",
                          "Leilão de veículos — VIP Leilões", state,
                          "Local não informado", day, hour, "VIP Leilões", VIP_URL)
            entry["event_id"] = event_id
            entry["states"] = sorted(set(states))
            results.append(entry)
    return results

async def collect_browser():
    from playwright.async_api import async_playwright
    all_events, errors = [], []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for name,url in (("Copart", COPART_URL),("VIP Leilões",VIP_URL)):
            context = await browser.new_context(locale="pt-BR", timezone_id="America/Sao_Paulo")
            page = await context.new_page()
            try:
                response = await page.goto(url, wait_until="domcontentloaded",timeout=30000)
                if response and response.status >= 400:
                    raise ValueError(f"HTTP {response.status}")
                await page.wait_for_timeout(2500)
                if name == "Copart":
                    rows = await page.locator("table tbody tr").evaluate_all(
                        "(trs) => trs.map(tr => Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim()))")
                    found = parse_copart_rows(rows)
                else:
                    body = await page.locator("body").inner_text(timeout=10000)
                    found = parse_vip_text(body)
                if not found:
                    raise ValueError("Nenhum evento validável extraído da página pública")
                all_events.extend(found)
                print(f"BROWSER {name}: {len(found)} eventos indexados")
            except Exception as exc:
                errors.append({"id": name, "error": str(exc).splitlines()[0][:250]})
                print(f"BROWSER {name}: {errors[-1]['error']}")
            finally:
                await context.close()
        await browser.close()
    return all_events, errors

def collect_platforms():
    return asyncio.run(collect_browser())
