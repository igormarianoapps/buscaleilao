"""Direct vehicle-auction adapter for Bolsa de Leilões.

The platform operates nationally; classify each event by the location shown
on its *own* detail page, never by the company's registered address.
"""
import re
import urllib.parse
from datetime import datetime,timezone
from auction_clock import auction_today
from regional_collect import VisibleLinks, fetch as regional_fetch
from auction_platform_watch import fetch as platform_fetch

SITE={"id":"bolsa","discovery_url":"https://www.bolsadeleiloes.com.br/",
      "allowed_hosts":["www.bolsadeleiloes.com.br","bolsadeleiloes.com.br"]}
HOSTS=set(SITE["allowed_hosts"])
UF=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())

def detail_id(url):
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.hostname not in HOSTS or p.username or p.password or p.port not in (None,443):
            return None
        if p.query or p.fragment or "\\" in url:
            return None
        m=re.fullmatch(r"/leilao/([0-9]{1,9})/?",p.path)
        return m.group(1) if m else None
    except (ValueError,TypeError):
        return None

def parse_details(html,url,today=None):
    ident=detail_id(url)
    if not ident:
        return None
    today=today or auction_today()
    doc=VisibleLinks()
    doc.feed(html[:2_000_000])
    text=doc.text
    # The event card appears near the top, before the lots. Do not extract
    # the date from other auction suggestions or the footer.
    header=text[:1800]
    if not re.search(r"leil[aã]o\s+(?:de\s+)?ve[ií]culos|ve[ií]culos\s+banco|motociclet|ve[ií]culos\s+recuperados",header,re.I):
        return None
    if re.search(r"encerrado|cancelado|suspenso",header,re.I):
        return None
    d=re.search(r"\b(\d{2})/(\d{2})/(20\d{2})\s+[àa]s\s+(\d{2}):(\d{2})",header,re.I)
    m=re.search(r"\bLOCAL\s*:\s*([A-ZÀ-Úa-zà-ú\s-]{3,70})\s*[,/-]\s*([A-Z]{2})\b",header)
    if not d or not m:
        return None
    from datetime import date
    try:
        when=date(int(d.group(3)),int(d.group(2)),int(d.group(1)))
        if when<today or int(d.group(4))>23 or int(d.group(5))>59 or m.group(2) not in UF:
            return None
    except ValueError:
        return None
    # Multiple real vehicle lots are required, not merely "31 lotes".
    if not (re.search(r"\bLOTE\s*1\b",text,re.I) and re.search(r"\bLOTE\s*2\b",text,re.I)):
        return None
    city=" ".join(m.group(1).title().split())
    key=f"bolsa-{ident}-{when.isoformat()}"
    return {"id":key,"event_id":key,
            "title":"Leilão de veículos — Bolsa de Leilões",
            "state":m.group(2),"city":city,
            "auction_date":when.isoformat(),
            "auction_time":d.group(4)+":"+d.group(5),
            "vehicle_count":None,
            "organizer":"Bolsa de Leilões",
            "source_type":"private","source_link_type":"event",
            "source_url":url,"status":"scheduled",
            "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}

def collect_bolsa(today=None,index_loader=platform_fetch,detail_loader=None):
    from auction_platform_watch import Links
    from auction_platform_watch import host_ok
    from auction_platform_watch import fetch as default_fetch
    from regional_collect import CONFIG
    # Bound the number of first-party detail requests; reject redirects.
    from urllib.request import Request,build_opener
    from auction_platform_watch import NoRedirect
    def load_direct(url):
        req=Request(url,headers={"User-Agent":"BuscaLeilaoBot/0.7 (+https://github.com/igormarianoapps/buscaleilao)","Accept":"text/html"})
        with build_opener(NoRedirect).open(req,timeout=12) as response:
            if not response.headers.get("Content-Type","").lower().startswith("text/html"):
                raise ValueError("non-HTML lot page")
            return response.read(2_000_001).decode("utf-8","replace")
    fetch_detail=detail_loader or load_direct
    events,errors=[],[]
    try:
        homepage=index_loader(SITE)
        doc=Links()
        doc.feed(homepage[:2_000_000])
        links=[]
        for href,label in doc.links:
            url=urllib.parse.urljoin(SITE["discovery_url"],href or "")
            if detail_id(url) and re.search(r"ve[ií]cul|autom[oó]vel|motociclet|carro",label,re.I):
                if url not in links:
                    links.append(url)
            if len(links)>=15:
                break
        if not links:
            errors.append({"id":"bolsa","error":"no identifiable vehicle-auction details on homepage"})
        for url in links:
            try:
                event=parse_details(fetch_detail(url),url,today=today)
                if event:
                    events.append(event)
                else:
                    errors.append({"id":"bolsa:"+url,"error":"event detail failed date/status/lot validation"})
            except Exception as exc:
                errors.append({"id":"bolsa:"+url,"error":str(exc)[:160]})
    except Exception as exc:
        errors.append({"id":"bolsa","error":str(exc)[:160]})
    return events,errors
