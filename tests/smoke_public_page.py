"""Smoke test the real deployed BuscaLeilão website, not repository files."""
import asyncio
import json
import os
from playwright.async_api import async_playwright

URL=os.environ.get("PUBLIC_URL","https://buscaleilao-nine.vercel.app/")

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=await browser.new_page(locale="pt-BR",timezone_id="America/Sao_Paulo")
        errors=[]
        page.on("pageerror",lambda exc: errors.append(str(exc)))
        response=await page.goto(URL,wait_until="domcontentloaded",timeout=45000)
        print("PUBLIC URL:",page.url,"HTTP:",response.status if response else "no response")
        await page.wait_for_timeout(2000)
        options=await page.locator('select[name="state"] option').count()
        print("STATE OPTIONS:",options)
        if options!=28:
            raise AssertionError(f"Expected 27 UFs plus all states, found {options}; browser errors: {errors}")
        await page.locator("#count").get_by_text("leilão",exact=False).wait_for(timeout=12000)
        total=await page.locator(".card").count()
        print("UNFILTERED EVENTS:",total,"BROWSER ERRORS:",errors)
        if not total:
            raise AssertionError("No public auction cards loaded")
        if errors:
            raise AssertionError("Browser JS runtime errors: "+str(errors))
        await page.locator('select[name="state"]').select_option("GO")
        await page.get_by_role("button",name="Buscar leilões").click()
        go=await page.locator(".card").count()
        print("GO EVENTS:",go)
        if go<1:
            raise AssertionError("State filter GO returned no events")
        await page.locator('input[name="start"]').fill("2026-11-04")
        await page.locator('input[name="end"]').fill("2026-11-25")
        await page.get_by_role("button",name="Buscar leilões").click()
        period=await page.locator(".card").count()
        print("GO WITH DATE RANGE:",period)
        if period<1:
            raise AssertionError("Date range filter produced no results")
        await page.get_by_role("button",name="Limpar filtros").click()
        reset=await page.locator(".card").count()
        print("RESET EVENTS:",reset)
        if reset!=total:
            raise AssertionError(f"Reset returned {reset}, expected {total}")
        await browser.close()
        print("PUBLIC SMOKE PASS")

if __name__=="__main__":
    asyncio.run(main())
