"""Verified event adapter for Leilo recurring auction editions.

The stable event URL always presents its current edition. A row is published
only when the page itself contains >=2 individual lots with matching future
auction date/time, and UFs are extracted from those lots (NOT from HQ).
"""
import re
import urllib.parse
import urllib.request
from collections import defaultdict
from datetime import date,datetime,timezone
from auction_clock import auction_today
from regional_collect import VisibleLinks
from auction_platform_watch import fetch as fetch_home,host_ok

SITE={"id":"leilo","discovery_url":"https://leilo.com.br/leilao/",
      "allowed_hosts":["leilo.com.br","www.leilo.com.br"]}
SEEDS=("leilao-de-veiculos-super-terca","leilao-de-pesados",
       "leilao-de-carros-antigos-e-premium","leilao-de-veiculos")
UF=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
LOT_RE=re.compile(r"\bLOTE\s+(\d{1,5})\s+([A-Z]{2})\b",re.I)
DATE_RE=re.compile(r"Leil[aã]o:\s*(\d{2})/(\d{2})/(20\d{2})[\s\S]{0,75}?(\d{2}):(\d{2})",re.I)
def event_slug(url):
    try:
        p=urllib.parse.urlsplit(url)
        if not host_ok(SITE,url) or p.query:
            return None
        m=re.fullmatch(r"/leilao/evento/([a-z0-9-]{5,95})/?",p.path,re.I)
        return m.group(1) if m else None
    except (ValueError,TypeError):
        return None
def discover_event_urls(html):
    parser=VisibleLinks()
    parser.feed(html[:1_200_000])
    result={f"https://leilo.com.br/leilao/evento/{seed}/" for seed in SEEDS}
    for href,_label,_ in parser.links:
        url=urllib.parse.urljoin(SITE["discovery_url"],href or "")
        if event_slug(url):
            result.add(url)
    return sorted(result)[:14]
def events_from_event_page(html,url,today=None):
    slug=event_slug(url)
    if not slug:return []
    today=today or auction_today()
    parser=VisibleLinks();parser.feed(html[:2_000_000])
    content=parser.text
    if not re.search(r"leil[aã]o recorrente|pr[oó]xima edi[cç][aã]o",content,re.I):
        return []
    # Do not rely on the global "próximos leilões" list or old editions.
    content=content.split("Leilão recorrente",1)[0]
    if not re.search(r"\b\d{1,4}\s+lotes\b",content,re.I):
        return []
    lots=list(LOT_RE.finditer(content))
    groups=defaultdict(lambda:{"states":set(),"lots":set()})
    for index,lot in enumerate(lots):
        uf=lot.group(2).upper()
        if uf not in UF:continue
        chunk=content[lot.end():lots[index+1].start() if index+1<len(lots) else len(content)]
        timestamp=DATE_RE.search(chunk)
        if not timestamp:continue
        dd,mm,yyyy,hh,mi=map(int,timestamp.groups())
        try:
            d=date(yyyy,mm,dd)
        except ValueError:
            continue
        if d<today or hh>23 or mi>59:continue
        key=(d.isoformat(),f"{hh:02}:{mi:02}")
        groups[key]["states"].add(uf)
        groups[key]["lots"].add((lot.group(1),uf))
    output=[]
    for (day,hour),group in groups.items():
        if len(group["lots"])<2:continue
        states=sorted(group["states"])
        event_id=f"leilo-{slug}-{day}-{hour.replace(':','')}"
        for uf in states:
            output.append({
                "id":event_id+"-"+uf.lower(),"event_id":event_id,
                "title":"Leilão de veículos — Leilo ("+slug.replace("-"," ").title()+")",
                "state":uf,"states":states,
                "city":"Local informado no lote",
                "auction_date":day,"auction_time":hour,
                "vehicle_count":None,"organizer":"Leilo",
                "source_type":"private","source_link_type":"event",
                "source_url":url,"status":"scheduled",
                "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")
            })
    return output

def fetch_event(url):
    from auction_platform_watch import NoRedirect
    if not event_slug(url):raise ValueError("not a first-party event")
    request=urllib.request.Request(url,headers={
        "User-Agent":"BuscaLeilaoBot/0.7 (+https://github.com/igormarianoapps/buscaleilao)",
        "Accept":"text/html"})
    with urllib.request.build_opener(NoRedirect).open(request,timeout=12) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():
            raise ValueError("non HTML")
        return resp.read(2_000_001).decode("utf-8","replace")
def collect_leilo(today=None,homepage_loader=fetch_home,event_loader=fetch_event):
    today=today or auction_today()
    try:
        targets=discover_event_urls(homepage_loader(SITE))
    except Exception as e:
        # Known official slugs are usable even when the global listing is blocked.
        targets=[f"https://leilo.com.br/leilao/evento/{slug}/" for slug in SEEDS]
        failures=[{"id":"leilo:index","error":str(e)[:150]}]
    else:failures=[]
    found=[]
    for url in targets:
        try:found.extend(events_from_event_page(event_loader(url),url,today))
        except Exception as e:failures.append({"id":"leilo:"+url,"error":str(e)[:150]})
    dedup={}
    for item in found:dedup[item["id"]]=item
    return list(dedup.values()),failures
