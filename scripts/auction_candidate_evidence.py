"""Read first-party auction candidate pages from all 16 nominated platforms.

This is source *extraction and verification triage*, not an event publisher.
Potential auction dates, states and lot counts are evidence hints only.
"""
import asyncio,json,re,urllib.parse,unicodedata
from datetime import date,datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"app/auction-platforms.json"
DISCOVERY=ROOT/"app/auction-discovery-combined.json"
REPORT=ROOT/"app/auction-event-evidence.json"
BR_DATE=re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b")
YEAR_MONTH_DAY=re.compile(r"\b(20\d{2})-(\d{2})-(\d{2})\b")
UF=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
VEHICLES=re.compile(r"\b(?:ve[ií]cul|autom[oó]ve|motociclet|caminh[aã]o|carro|moto|van|ônibus|onibus)\w*",re.I)
NEGATIVE=re.compile(r"\b(?:apartamento|im[oó]vel|terreno|geladeira|refrigerador|fog[aã]o|vestu[aá]rio|eletrodom[eé]stico)\w*",re.I)
EXPIRED=re.compile(r"\b(?:encerrado|cancelado|suspenso|finalizado|conclu[ií]do)\b",re.I)
LOTS=re.compile(r"\b(?:Lote\s*[0-9]{1,5}|[0-9]{1,5}\s+lotes)\b",re.I)
def trusted(site,url):
    try:
        p=urllib.parse.urlsplit(url)
        return (p.scheme=="https" and p.hostname in site.get("allowed_hosts",[])
            and not p.username and not p.password and p.port in (None,443)
            and not p.fragment and "\\" not in url and len(url)<1000)
    except (ValueError,TypeError):return False
def dates_from_text(text,today=None):
    today=today or date.today()
    out=set()
    for d,m,y in BR_DATE.findall(text):
        try:
            dt=date(int(y),int(m),int(d))
            if today<=dt<=date(today.year+2,12,31):out.add(dt.isoformat())
        except ValueError:pass
    for y,m,d in YEAR_MONTH_DAY.findall(text):
        try:
            dt=date(int(y),int(m),int(d))
            if today<=dt<=date(today.year+2,12,31):out.add(dt.isoformat())
        except ValueError:pass
    return sorted(out)[:10]
def extract(site,url,text,today=None):
    if not trusted(site,url):return None
    body=" ".join(text.split())[:22000]
    dates=dates_from_text(body,today)
    vehicle=bool(VEHICLES.search(body))
    negative=bool(NEGATIVE.search(body))
    lot_count=len(LOTS.findall(body))
    # Do not equate multiple dates appearing anywhere on a marketplace page
    # with an auction's scheduled date.
    status=("unavailable_or_expired" if EXPIRED.search(body[:1500]) else
            "unconfirmed_event")
    return {"platform_id":site["id"],"candidate_url":url,
        "date_mentions":dates,"vehicle_text_found":vehicle,
        "nonvehicle_text_found":negative,"lot_mentions":lot_count,
        "status":status,"approved_for_publication":False,
        "requirements_missing":["matching_individual_event_identity","date_and_time_corroboration",
                                "lot_list_corroboration","verified_vehicle_location",
                                "auctioneer_registration_check"]}

async def investigate(sites,combined,limit_per_site=5):
    from playwright.async_api import async_playwright
    result={}
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        context=await browser.new_context(ignore_https_errors=False,locale="pt-BR")
        for site in sites:
            entry=combined.get("platforms",{}).get(site["id"],{})
            urls=[]
            seen=set()
            for row in entry.get("candidate_events",[]):
                url=row.get("source_url")
                if url and url not in seen and trusted(site,url):
                    seen.add(url);urls.append(url)
                if len(urls)>=limit_per_site:break
            samples=[]
            errors=[]
            for url in urls:
                page=None
                try:
                    page=await context.new_page()
                    response=await page.goto(url,wait_until="domcontentloaded",timeout=12000)
                    if not response or response.status>=400:
                        raise ValueError("HTTP "+str(response.status if response else "no response"))
                    if not trusted(site,page.url):
                        raise ValueError("redirect outside permitted domain")
                    content=await page.locator("body").inner_text(timeout=5000)
                    evidence=extract(site,page.url,content)
                    if evidence:samples.append(evidence)
                except Exception as e:
                    errors.append({"url":url,"reason":str(e).splitlines()[0][:155]})
                finally:
                    if page:await page.close()
            result[site["id"]]={"sites_scanned":len(urls),"extracted":len(samples),
                "unverified_evidence":samples,"errors":errors,
                "verified_events":0}
        await context.close();await browser.close()
    return result
async def main_async():
    sites=json.loads(REGISTRY.read_text(encoding="utf-8"))
    try:discovery=json.loads(DISCOVERY.read_text(encoding="utf-8"))
    except (OSError,ValueError):discovery={}
    report=await investigate(sites,discovery)
    data={"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
          "sources_attempted":len(sites),"events_published":0,
          "pages_checked":sum(x["sites_scanned"] for x in report.values()),
          "pages_extracted":sum(x["extracted"] for x in report.values()),
          "platforms":report}
    REPORT.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Candidate evidence: {data['pages_extracted']}/{data['pages_checked']} pages; "
          "0 events published from unreviewed pages")
if __name__=="__main__":asyncio.run(main_async())
