"""Public-browser discovery fallback for all 16 nominated auction sites.

Public, no-login Playwright navigation, no stealth, no CAPTCHA bypass, no
cross-host expansion.  Results are *unverified candidates* and never
published by this module.
"""
import asyncio,json
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from auction_platform_watch import candidates,host_ok
ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"app/auction-platforms.json"
REPORT=ROOT/"app/auction-browser-diagnostics.json"

async def scan(sites,browser=None,timeout_ms=15000):
    from playwright.async_api import async_playwright
    results={}
    async with async_playwright() as p:
        owned=browser is None
        if owned:
            browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        context=await browser.new_context(locale="pt-BR",ignore_https_errors=False)
        for s in sites:
            page=None
            try:
                page=await context.new_page()
                res=await page.goto(s["discovery_url"],wait_until="domcontentloaded",timeout=timeout_ms)
                if res is None or res.status>=400:
                    raise ValueError("HTTP "+str(res.status if res else "no response"))
                final=page.url
                if not host_ok(s,final):
                    # Preserve one real URL hostname check; never follow off-site content.
                    raise ValueError("redirected outside first-party host")
                html=(await page.content())[:2_000_000]
                links=candidates(s,html)
                results[s["id"]]={"status":"reachable","final_url":final,
                    "links":links,"candidates":len(links),"mode":"public_browser",
                    "publication_allowed":False}
            except Exception as e:
                results[s["id"]]={"status":"blocked_or_unavailable","error":str(e).splitlines()[0][:200],
                    "links":[],"candidates":0,"publication_allowed":False}
            finally:
                if page:await page.close()
        await context.close()
        if owned:await browser.close()
    return results

async def main_async():
    sites=json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows=await scan(sites)
    out={"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total":len(sites),
        "reachable":sum(x["status"]=="reachable" for x in rows.values()),
        "candidate_links":sum(x["candidates"] for x in rows.values()),
        "published":0,"platforms":rows}
    REPORT.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Browser discovery: {out['reachable']}/{out['total']} reachable; "
          f"{out['candidate_links']} unverified candidates; 0 events published")
if __name__=="__main__":asyncio.run(main_async())
