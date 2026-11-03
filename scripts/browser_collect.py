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

def copart_detail_url(url, expected_day):
    """Accept only a Copart sale-details URL that names this exact auction day."""
    from urllib.parse import urlsplit, urlunsplit
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ("copart.com.br", "www.copart.com.br"):
        return None
    match = re.fullmatch(r"/saleListResult/([0-9]+)/([0-9]{4}-[0-9]{2}-[0-9]{2})/?", parsed.path, re.I)
    if not match or match.group(2) != expected_day:
        return None
    # Query parameters may carry verified auction metadata provided by Copart.
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, parsed.query, ""))

def parse_copart_linked_rows(rows):
    """Extract separate sale IDs; dates without links use the yard-level fallback.

    Each row is {"cells":[yard,current,next,...],
                 "links":[{"text":"dd.mm.yyyy","href":"https://..."}]}.
    Never merge distinct Copart sale IDs merely because date and yard match.
    """
    results = {}
    yard_pattern = re.compile(r"^(.{3,75}?)\s*-\s*([A-Z]{2})$")
    for row in rows:
        cells = row.get("cells", [])
        if len(cells) < 2:
            continue
        yard = re.sub(r"\s+", " ", cells[0]).strip()
        matched = yard_pattern.fullmatch(yard)
        if not matched:
            continue
        city, state = matched.groups()
        if state not in STATES:
            continue
        day_links = {}
        for link in row.get("links", []):
            match_date = re.search(DATE, link.get("text", ""))
            if match_date:
                day = future_date(match_date.group(1))
            elif re.search(r"\bLIVE\s+NOW\b", link.get("text", ""), re.I):
                # "LIVE NOW" replaces the date in current-sale cells. The
                # event detail path itself must independently contain a date.
                from urllib.parse import urlsplit
                match_path = re.fullmatch(
                    r"/saleListResult/[0-9]+/([0-9]{4}-[0-9]{2}-[0-9]{2})/?",
                    urlsplit(link.get("href", "")).path, re.I)
                if not match_path:
                    continue
                try:
                    linked_day = date.fromisoformat(match_path.group(1))
                    day = linked_day.isoformat() if linked_day >= date.today() else None
                except ValueError:
                    day = None
            else:
                continue
            if not day:
                continue
            trusted = copart_detail_url(link.get("href", ""), day)
            if not trusted:
                continue
            from urllib.parse import urlsplit
            sale_id = re.search(r"/saleListResult/([0-9]+)/", urlsplit(trusted).path, re.I).group(1)
            key = f"copart-{sale_id}-{day}"
            entry = event(key, f"Leilão Copart — {city}", state, city,
                          day, None, "Copart", trusted)
            entry["source_link_type"] = "event"
            results[key] = entry
            day_links[day] = True
        # If a column has no independently confirmed link, expose its
        # date as a yard-level calendar listing, never a fabricated detail URL.
        for col in cells[1:3]:
            matched_date = re.search(DATE, col)
            if not matched_date:
                continue
            day = future_date(matched_date.group(1))
            if not day or day_links.get(day):
                continue
            key = f"copart-{day}-{state.lower()}-{slug(city)}"
            fallback = event(key, f"Leilão Copart — {city}", state, city,
                             day, None, "Copart", COPART_URL)
            fallback["source_link_type"] = "calendar"
            results[key] = fallback
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
            entry["source_link_type"] = "calendar"
            entry["event_id"] = event_id
            entry["states"] = sorted(set(states))
            results.append(entry)
    return results

def vip_detail_url(raw):
    """Allow only likely VIP event-detail links on the official HTTPS domain."""
    from urllib.parse import urlsplit, urlunsplit
    try:
        parts = urlsplit(raw)
    except ValueError:
        return None
    if parts.scheme != "https" or parts.hostname not in ("vipleiloes.com.br", "www.vipleiloes.com.br"):
        return None
    route = parts.path.rstrip("/").lower()
    if not re.search(r"/(?:leilao|leiloes|evento|eventos)/[a-z0-9][a-z0-9/_-]*", route):
        return None
    if any(part in route for part in ("/lote/", "/lotes/", "/login/", "/cadastro/")):
        return None
    return urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))

def parse_vip_cards(cards):
    """Conservative localized DOM card parser, never infer same-day identity."""
    results = []
    for card in cards:
        body = card.get("text", "")
        if len(body) > 1300 or len(re.findall(r"\bIn[ií]cio\s*:?\s*\d{2}/\d{2}/\d{4}", body, re.I)) != 1:
            continue
        parsed = parse_vip_text(body)
        if not parsed:
            continue
        links = {candidate for u in card.get("links", []) if (candidate := vip_detail_url(u))}
        if len(links) == 1:
            direct = next(iter(links))
            identity = hashlib.sha256(direct.encode("utf-8")).hexdigest()[:16]
            group = f"vip-direct-{identity}"
            for entry in parsed:
                entry["id"] = f"{group}-{entry['state'].lower()}"
                entry["event_id"] = group
                entry["source_url"] = direct
                entry["source_link_type"] = "event"
        results.extend(parsed)
    return results

async def extract_vip_cards(page):
    """Choose the smallest DOM ancestor containing an event and its states."""
    return await page.evaluate("""() => {
      const marks = Array.from(document.querySelectorAll('body *'))
        .filter(el => el.children.length === 0 &&
          /In[ií]cio\\s*:?\\s*\\d{2}\\/\\d{2}\\/\\d{4}/i.test(el.textContent || ''));
      const cards = [], seen = new Set();
      for (const mark of marks) {
        let node = mark;
        for (let n = 0; n < 5 && node; n++, node = node.parentElement) {
          const text = node.innerText || '';
          if (text.length > 1300) break;
          if (/Estados\\s*:?/i.test(text) && /In[ií]cio\\s*:?/i.test(text)) {
            if (!seen.has(node)) {
              seen.add(node);
              cards.push({text, links: Array.from(node.querySelectorAll('a[href]'))
                .map(a => a.href)});
            }
            break;
          }
        }
      }
      return cards;
    }""")

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
                        """(trs) => trs.map(tr => ({
                          cells: Array.from(tr.querySelectorAll('td')).map(td => td.innerText.trim()),
                          links: Array.from(tr.querySelectorAll('td a[href]')).map(a => ({
                            text: a.innerText.trim(), href: a.href
                          }))
                        }))""")
                    found = parse_copart_linked_rows(rows)
                else:
                    cards = await extract_vip_cards(page)
                    found = parse_vip_cards(cards)
                    if not found:
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
        # Third independent platform: Freitas public calendar and auction pages.
        # A failure here never blocks Copart or VIP.
        try:
            from freitas_collect import collect_freitas_browser
            freitas_events = await collect_freitas_browser(browser)
            all_events.extend(freitas_events)
            print(f"BROWSER Freitas: {len(freitas_events)} event(s) verified")
        except Exception as exc:
            errors.append({"id":"Freitas Leiloeiro",
                           "error":str(exc).splitlines()[0][:250]})
            print(f"BROWSER Freitas: {errors[-1]['error']}")
        await browser.close()
    return all_events, errors

def collect_platforms():
    return asyncio.run(collect_browser())
