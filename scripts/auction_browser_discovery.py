"""Public-browser discovery fallback for all 16 nominated auction sites.

Public, no-login Playwright navigation, no stealth, no CAPTCHA bypass, no
cross-host expansion.  Results are *unverified candidates* and never
published by this module.
"""
import asyncio,json
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urldefrag
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
            pages=[s["discovery_url"]]+s.get("additional_discovery_urls",[])
            discovered=[]
            errors=[]
            completed=0
            for target in pages[:3]:
                page=None
                try:
                    if not host_ok(s,urldefrag(target).url):
                        raise ValueError("unapproved discovery page")
                    page=await context.new_page()
                    res=await page.goto(target,wait_until="domcontentloaded",timeout=timeout_ms)
                    if res is None or res.status>=400:
                        raise ValueError("HTTP "+str(res.status if res else "no response"))
                    # The approved hostname may use a #/home client route (SPA).
                    # A fragment is fine only for the source page, never for an event link.
                    canonical=urldefrag(page.url).url
                    if not host_ok(s,canonical):
                        raise ValueError("redirected outside first-party host")
                    if s.get("id") in ("mcleilao","palacio","rogerio"):
                        await page.wait_for_timeout(1000)
                    html=(await page.content())[:2_000_000]
                    discovered+=candidates(s,html)
                    completed+=1
                except Exception as e:
                    errors.append(str(e).splitlines()[0][:160])
                finally:
                    if page:await page.close()
            unique={}
            for item in discovered:
                if item.get("source_url"):
                    unique[item["source_url"]]=item
            links=list(unique.values())[:60]
            results[s["id"]]={"status":"reachable" if completed else "blocked_or_unavailable",
                "scanned_pages":len(pages[:3]),"pages_reached":completed,
                "links":links,"candidates":len(links),"mode":"public_browser",
                "publication_allowed":False,"errors":errors[:3]}
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
