"""Public Freitas Leiloeiro vehicle calendar adapter.

Find event-detail URLs on the public homepage and validate the auction closing
date on each original event page before publishing it. No individual lot scraping.
"""
import re
from datetime import date, datetime, timezone
from urllib.parse import urlparse, parse_qs
from browser_collect import event

HOME = "https://www.freitasleiloeiro.com.br/"
DETAIL = "https://www.freitasleiloeiro.com.br/Leiloes/Lotes?leilaoId="

def official_id(url):
    parsed = urlparse(url)
    if parsed.hostname not in ("www.freitasleiloeiro.com.br", "freitasleiloeiro.com.br"):
        return None
    if parsed.path.lower() != "/leiloes/lotes":
        return None
    value = parse_qs(parsed.query).get("leilaoId", [None])[0]
    return value if value and value.isdigit() else None

def parse_detail(text, url, today=None):
    """Return a single source-verified event or None; never infer from lot lines."""
    identifier = official_id(url)
    if not identifier: return None
    today = today or date.today()
    head = text[:8000]
    closing = re.search(
        r"Fechamento\s+a\s+partir\s+das\s+(\d{1,2})h(\d{2})\s+do\s+dia\s+(\d{2})/(\d{2})/(\d{4})",
        head, re.I
    )
    if not closing: return None
    # Look at the event heading immediately before the closing announcement;
    # the global navigation menu also contains the word "Veículos".
    title_lines = [line.strip() for line in head[:closing.start()].splitlines() if line.strip()]
    heading = title_lines[-1] if title_lines else ""
    if not re.search(r"ve[ií]culos|caminh[oõ]es|motocicletas|motos", heading, re.I):
        return None
    hh, mm, dd, mo, yyyy = map(int, closing.groups())
    try:
        when = date(yyyy,mo,dd)
        if when < today or hh > 23 or mm > 59: return None
    except ValueError:
        return None
    location = re.search(r"Local\s+do\s+leil[aã]o\s*:?\s*(.{0,240})", head,re.I|re.S)
    if not location: return None
    address = location.group(1).split("Condições")[0].split("\n\n")[0].strip()
    state = re.search(r"(?:/|-)\s*([A-Z]{2})\b",address)
    if not state: return None
    uf = state.group(1)
    if uf not in set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()):
        return None
    # City is not always available in the free-form address. Do not guess it.
    title = "Leilão de veículos — Freitas Leiloeiro"
    identifier_key = f"freitas-{identifier}-{when.isoformat()}"
    e = event(identifier_key,title,uf,"Local indicado no edital",
              when.isoformat(),f"{hh:02}:{mm:02}","Freitas Leiloeiro",
              DETAIL + identifier)
    return e

async def collect_freitas_browser(browser):
    """Conservative discovery; failure leaves the other collectors unaffected."""
    ctx = await browser.new_context(locale="pt-BR",timezone_id="America/Sao_Paulo")
    page = await ctx.new_page()
    try:
        response = await page.goto(HOME,wait_until="domcontentloaded",timeout=25000)
        if not response or response.status >= 400:
            raise ValueError("Freitas homepage unavailable")
        await page.wait_for_timeout(2500)
        links = await page.locator("a[href*='leilaoId=']").evaluate_all(
            "(anchors) => anchors.map(a => a.href)")
        found = {}
        for url in links:
            ident = official_id(url)
            if ident: found[ident] = DETAIL + ident
        events = []
        for url in list(found.values())[:16]:
            detail = await ctx.new_page()
            try:
                result = await detail.goto(url,wait_until="domcontentloaded",timeout=12000)
                if not result or result.status >= 400: continue
                text = await detail.locator("body").inner_text(timeout=6000)
                parsed = parse_detail(text,url)
                if parsed: events.append(parsed)
            except Exception:
                continue
            finally:
                await detail.close()
        if not events:
            raise ValueError("No valid vehicle events in public Freitas homepage links")
        return events
    finally:
        await ctx.close()
