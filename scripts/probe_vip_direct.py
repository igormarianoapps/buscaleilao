"""Inspect public VIP calendar links without guessing routes or bypassing access."""
import asyncio
import json
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=await browser.new_page(locale="pt-BR",timezone_id="America/Sao_Paulo")
        response=await page.goto("https://www.vipleiloes.com.br/agenda",wait_until="domcontentloaded",timeout=35000)
        await page.wait_for_timeout(3000)
        result=await page.evaluate(r"""() => {
          const nodes=[...document.querySelectorAll('body *')];
          const date='04/11/2026';
          const matches=nodes.filter(n=>n.children.length===0 && (n.textContent||'').includes(date)).slice(0,30);
          const findings=[];
          for(const leaf of matches){
            let el=leaf;
            for(let depth=0; depth<9 && el;depth++,el=el.parentElement){
              const text=(el.innerText||'').trim();
              if(text.length>2500)break;
              findings.push({depth,tag:el.tagName,className:String(el.className||'').slice(0,130),
                text:text.slice(0,340),click:el.getAttribute('onclick'),role:el.getAttribute('role'),
                links:[...el.querySelectorAll('a[href]')].slice(0,12).map(a=>({text:(a.innerText||'').slice(0,50),href:a.href})),
                html:depth===4?el.outerHTML.slice(0,1300):undefined});
              if(text.includes('14:00') && text.includes('GO') && text.includes('33'))break;
            }
          }
          return {totalAnchors:document.querySelectorAll('a[href]').length,
            candidates:[...document.querySelectorAll('a[href]')].map(a=>a.href)
              .filter(h=>/evento\/detalhes|leilao\//i.test(h)).slice(0,35),
            findings:findings.slice(0,45)};
        }""")
        print("VIP RESPONSE",response.status if response else None)
        print(json.dumps(result,ensure_ascii=False,indent=2)[:22000])
        from browser_collect import extract_vip_cards, choose_vip_events
        cards=await extract_vip_cards(page)
        body=await page.locator("body").inner_text(timeout=10000)
        verified, mode=choose_vip_events(cards,body)
        print("VIP PARSER",json.dumps({"cards":len(cards),"mode":mode,
              "direct_events":len({e["event_id"] for e in verified}),
              "direct_records":len(verified)},ensure_ascii=False))
        summary={}
        for e in verified:
            summary.setdefault(e["event_id"],{
                "date":e["auction_date"],"time":e["auction_time"],
                "states":e["states"],"url":e["source_url"]})
        print("VIP DIRECT SUMMARY",json.dumps(list(summary.values()),ensure_ascii=False))
        await browser.close()

if __name__=="__main__":
    asyncio.run(main())
