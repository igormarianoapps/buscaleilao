"""Playwright browser diagnostics for public auction calendars.

No authentication, CAPTCHA solving, or access-control bypass.
Does not publish auction events; writes sanitized diagnostics only.
"""
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = {
    "Copart sales": "https://www.copart.com.br/salesListResult",
    "Copart calendar": "https://www.copart.com.br/auctionCalendar",
    "VIP homepage": "https://www.vipleiloes.com.br/",
    "VIP agenda": "https://www.vipleiloes.com.br/agenda",
}
OUTPUT = ROOT / "app" / "browser-diagnostics.json"

def useful(text):
    lines = re.split(r"[\n\r]+", text)
    return [re.sub(r"\s+", " ", x.strip())[:180] for x in lines
            if re.search(r"leil[aã]o|p[aá]tio|\d{2}[./]\d{2}[./]\d{4}|in[ií]cio|estados", x, re.I)][:12]

async def main():
    from playwright.async_api import async_playwright
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        for name, url in TARGETS.items():
            browser_context = await browser.new_context(locale="pt-BR", timezone_id="America/Sao_Paulo")
            page = await browser_context.new_page()
            entry = {"source": name, "url": url, "status": "failed"}
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=25000)
                await page.wait_for_timeout(2000)
                html = await page.content()
                body = await page.locator("body").inner_text(timeout=6000)
                entry.update({
                    "status": "loaded",
                    "http_status": response.status if response else None,
                    "final_url": page.url[:350],
                    "title": (await page.title())[:120],
                    "html_bytes": len(html),
                    "text_length": len(body),
                    "tables": await page.locator("table").count(),
                    "iframes": await page.locator("iframe").count(),
                    "date_strings": len(re.findall(r"\b\d{2}[./]\d{2}[./]\d{4}\b",body)),
                    "examples": useful(body)
                })
            except Exception as exc:
                entry["error"] = str(exc).splitlines()[0][:250]
            finally:
                results.append(entry)
                await browser_context.close()
        await browser.close()
    OUTPUT.write_text(json.dumps({"checked_at": datetime.now(timezone.utc).isoformat(),
                                  "results": results}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    for item in results:
        print(item["source"], item["status"], item.get("http_status"), item.get("error",""),
              "dates",item.get("date_strings",0))

if __name__ == "__main__":
    asyncio.run(main())
