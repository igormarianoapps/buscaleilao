"""Inspect public browser DOM for unresolved auction sources without logging secrets.

Only inspect the user-supplied official origins and known public catalog pages.
Output is research-only; no events are published by this tool.
"""
import asyncio,json,re
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin,urlsplit,urldefrag
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"app/auction-platforms.json"
OUT=ROOT/"app/platform-dom-probe.json"
IDS={"mcleilao","sodre","milan","hisa","parque","palacio","rogerio","loop","flex"}
def keep(link,site):
    try:
        x=urlsplit(urldefrag(link).url)
        return x.scheme=="https" and x.hostname in site["allowed_hosts"] and x.username is None and x.password is None
    except (TypeError,ValueError):return False
async def probe(sites):
    from playwright.async_api import async_playwright
    results={}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        context=await browser.new_context(locale="pt-BR",ignore_https_errors=False)
        for site in sites:
            urls=[site["discovery_url"]]+site.get("additional_discovery_urls",[])
            if site["id"]=="sodre":urls+=["https://www.sodresantoro.com.br/leilao"]
            if site["id"]=="loop":urls+=["https://loopleiloes.com.br/eventos"]
            if site["id"]=="flex":urls+=["https://www.flexleiloes.com.br/shop/"]
            rows=[]
            for url in list(dict.fromkeys(urls))[:3]:
                page=None
                try:
                    if not keep(url,site):continue
                    page=await context.new_page()
                    response=await page.goto(url,wait_until="domcontentloaded",timeout=12000)
                    if response is None or response.status>=400:raise ValueError("HTTP "+str(response.status if response else "none"))
                    if not keep(page.url,site):raise ValueError("off-host redirect")
                    await page.wait_for_timeout(1200)
                    text=await page.locator("body").inner_text(timeout=6000)
                    lines=[" ".join(x.split()) for x in text.splitlines()]
                    hints=[x[:270] for x in lines if re.search(r"leil[aã]o|eventos?|lotes?|calend[aá]rio|nenhum|sem\s+leil[aã]o|ve[ií]culos",x,re.I)][:32]
                    anchors=await page.locator("a[href]").evaluate_all(
                        "(a)=>a.map(x=>({href:x.href,label:(x.innerText||x.textContent||'').trim().slice(0,150)})).slice(0,240)")
                    found=[]
                    for a in anchors:
                        if keep(a["href"],site) and re.search(r"leilao|leil[aã]o|event|lote|veicul|agenda|calend",a["href"]+" "+a["label"],re.I):
                            found.append(a)
                    rows.append({"url":url,"status":"ok","title":await page.title(),
                                 "headlines":hints,"anchors":found[:30]})
                except Exception as e:
                    rows.append({"url":url,"status":"error","reason":str(e).splitlines()[0][:150]})
                finally:
                    if page:await page.close()
            results[site["id"]]=rows
        await browser.close()
    return results
async def main():
    sites=[x for x in json.loads(INPUT.read_text(encoding="utf-8")) if x["id"] in IDS]
    results=await probe(sites)
    OUT.write_text(json.dumps({"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "sources":results,"publication_allowed":False},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("DOM probe:",len(results),"sources,",
          sum(sum(len(p.get("anchors",[])) for p in pages) for pages in results.values()),"first-party candidate anchors")
if __name__=="__main__":asyncio.run(main())
