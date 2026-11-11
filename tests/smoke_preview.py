"""End-to-end test of deployed preview, without relying on hardcoded old auctions.

Run: PUBLIC_URL=https://buscaleilao-dev.vercel.app/ python tests/smoke_preview.py
Requires Playwright Chromium and HTTPS access.
"""
import asyncio
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.async_api import async_playwright

URL=os.environ.get("PUBLIC_URL","https://buscaleilao-dev.vercel.app/")

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=await browser.new_page(viewport={"width":1280,"height":800},
                                   locale="pt-BR",timezone_id="America/Sao_Paulo")
        errors=[]
        page.on("pageerror",lambda exc:errors.append(str(exc)))
        response=await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
        assert response is not None and response.status==200, "Preview is not HTTP 200"
        await page.wait_for_function("document.querySelector('#count')?.textContent?.includes('leilão')",timeout=15000)
        count=await page.locator(".card").count()
        assert count>0,"No upcoming verified auctions in preview"
        assert await page.locator('select[name="state"] option').count()==28
        embedded=json.loads(await page.locator("#embedded-feed").text_content())
        assert embedded.get("events"),"Missing embedded feed"
        links=await page.locator(".card a").evaluate_all("(rows)=>rows.map(x=>x.href)")
        assert len(links)==count
        assert all(x.startswith("https://") and not any(p in x.lower() for p in
            ("/noticias/","/editais/","/agenda", "/calendar")) for x in links),links
        assert not errors,"Browser errors: "+str(errors)
        # Use a real result to exercise state and date filtering; don't assume GO.
        first=await page.locator(".card").first.locator(".tag").inner_text()
        state=next((s for s in first.split() if len(s.strip(","))==2 and s.strip(",").isupper()),None)
        assert state, "Cannot identify a state in the first card"
        await page.locator('select[name="state"]').select_option(state.strip(","))
        await page.get_by_role("button",name="Buscar leilões").click()
        assert await page.locator(".card").count()>=1
        await page.get_by_role("button",name="Limpar filtros").click()
        assert await page.locator(".card").count()==count
        first_org=(await page.locator(".card").first.locator("p").inner_text()).split()[0]
        await page.locator('input[name="keyword"]').fill(first_org)
        await page.get_by_role("button",name="Buscar leilões").click()
        assert await page.locator(".card").count()>=1,"Keyword search lost known organizer"
        await page.get_by_role("button",name="Limpar filtros").click()
        assert await page.locator(".card").count()==count
        day=await page.locator(".card").first.locator(".meta span").first.inner_text()
        import re
        m=re.search(r"(\d{2})/(\d{2})/(\d{4})",day)
        assert m,day
        iso=f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
        await page.locator('input[name="start"]').fill(iso)
        await page.locator('input[name="end"]').fill(iso)
        await page.get_by_role("button",name="Buscar leilões").click()
        assert await page.locator(".card").count()>=1,"Date filter lost known event"
        await page.get_by_role("button",name="Limpar filtros").click()
        assert await page.locator(".card").count()==count
        await page.set_viewport_size({"width":390,"height":844})
        assert await page.locator('input[name="keyword"]').is_visible()
        assert await page.locator(".card").first.is_visible()
        overflow=await page.evaluate("document.documentElement.scrollWidth > window.innerWidth+1")
        assert not overflow,"Mobile page has horizontal overflow"
        assert not errors,"Browser errors: "+str(errors)
        print(f"PREVIEW E2E PASS: {count} upcoming distinct auctions; "
              "keyword/state/dates/reset/direct-link/mobile checks OK")
        await browser.close()

if __name__=="__main__":
    asyncio.run(main())
