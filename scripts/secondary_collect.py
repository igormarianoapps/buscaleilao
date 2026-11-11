"""Fail-closed first-party collectors for Parque, Flex and Hisa.

No publication without a future event date, a first-party event/lots URL,
actual vehicle-lot evidence and a location explicitly attached to the event.
No address is inferred from company headquarters.
"""
import re
import urllib.parse
import urllib.request
from datetime import date,datetime,timezone
from auction_clock import auction_today
from regional_collect import VisibleLinks
from auction_platform_watch import fetch as platform_fetch,NoRedirect

SITES={
 "parque":("Parque dos Leilões","https://www.parquedosleiloes.com.br/leiloes",
           {"parquedosleiloes.com.br","www.parquedosleiloes.com.br"},
           r"/leilao/[0-9]{1,10}/detalhes/?"),
 "flex":("Flex Leilões","https://www.flexleiloes.com.br/",
           {"flexleiloes.com.br","www.flexleiloes.com.br"},
           r"/lotes/[0-9]{1,10}/?"),
 "hisa":("Hisa Leilões","https://hisaleiloes.com.br/",
           {"hisaleiloes.com.br","www.hisaleiloes.com.br"},
           r"/leilao/[0-9]{1,10}/?")
}
UF=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
PT_MONTHS={"jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,
           "jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12}
BR_DATE=re.compile(r"(\d{2})/(\d{2})/(20\d{2})")
DATE_PT=re.compile(r"Data\s+(\d{1,2})\s+de\s+(jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez)\w*\s+de\s+(20\d{2})\s+[àa]s\s+(\d{1,2}):(\d{2})",re.I)
DATE_NUM=re.compile(r"\b(\d{2})/(\d{2})/(20\d{2})\s*(?:[-–]\s*|[àa]s\s+)(\d{1,2})[:h](\d{2})",re.I)
CITY_UF=re.compile(r"\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]{2,40})\s*[,/-]\s*([A-Z]{2})\b")
TITLE_VEHICLES=re.compile(r"ve[ií]culos|motociclet|caminh[oõ]es|autom[oó]veis",re.I)
NONVEHICLES=re.compile(r"im[oó]veis|apartamentos?|terrenos?|eletrodom[eé]sticos|m[oó]veis diversos|pneus|vestu[aá]rio|equipamentos",re.I)
BRANDS=re.compile(r"FIAT|FORD|CHEVROLET|RENAULT|VOLKSWAGEN|HONDA|HYUNDAI|TOYOTA|NISSAN|JEEP|MERCEDES|IVECO|DAF|YAMAHA|KIA|BYD",re.I)
def trusted_url(site,url):
    if site not in SITES or not isinstance(url,str):return False
    _,_,hosts,pattern=SITES[site]
    try:
        p=urllib.parse.urlsplit(url)
        return bool(p.scheme=="https" and p.hostname in hosts
            and p.port in (None,443) and not p.username and not p.password
            and not p.query and not p.fragment and "\\" not in url
            and re.fullmatch(pattern,p.path,re.I))
    except ValueError:return False

def event_date(text,today=None):
    match=DATE_PT.search(text)
    if match:
        dd,mon,yyyy,hh,mi=match.groups()
        nums=(int(yyyy),PT_MONTHS[mon.lower()[:3]],int(dd),int(hh),int(mi))
    else:
        match=DATE_NUM.search(text)
        if not match:return None
        dd,mm,yyyy,hh,mi=match.groups()
        nums=(int(yyyy),int(mm),int(dd),int(hh),int(mi))
    try:
        yyyy,mm,dd,hh,mi=nums
        d=date(yyyy,mm,dd)
        if d<(today or auction_today()) or hh>23 or mi>59:return None
        return d.isoformat(),f"{hh:02}:{mi:02}"
    except ValueError:return None

def place(text):
    # A location must appear in the event card/detail itself.
    for match in CITY_UF.finditer(text):
        city=" ".join(match.group(1).split()).strip()
        uf=match.group(2)
        if uf in UF and len(city)>2 and len(city.split())<=6:
            return city.title(),uf
    return None

def lot_evidence(text,site):
    if site=="flex":
        # The first-party page lists number + vehicle description in a table.
        return len(re.findall(r"\b(?:0\d{2}|\d{3})\s+(?:(?:I/)?(?:FIAT|FORD|CHEVROLET|RENAULT|VW|VOLKSWAGEN|HONDA|HYUNDAI|TOYOTA|JEEP)\b)",text,re.I))>=2
    # A lot count is not proof of any vehicle lots.
    return bool(re.search(r"\b(?:Lote\s*[01]?\d+|\d{1,2}\s*lote)\b",text,re.I)
                and BRANDS.search(text))

def parse_event(site,card,detail,url,today=None):
    if not trusted_url(site,url):return None
    today=today or auction_today()
    body=VisibleLinks();body.feed(detail[:2_000_000])
    text=body.text
    header=text[:1700]
    label=" ".join(card.split())
    if site=="parque":
        if not re.search(r"Categoria\s+VE[IÍ]CULOS",header,re.I):
            return None
        if not TITLE_VEHICLES.search(header):
            return None
        when=event_date(header,today)
        location=place(header[:1500])
    elif site=="hisa":
        if not TITLE_VEHICLES.search(label[:240]):
            return None
        if NONVEHICLES.search(label[:240]):
            return None
        when=event_date(label,today)
        # Require same event date on detail, not unrelated suggestions.
        if not when or when[0][8:]+"/"+when[0][5:7]+"/"+when[0][:4] not in text[:2000]:
            return None
        location=place(label[:250])
    else:
        if not TITLE_VEHICLES.search(label[:220]) or NONVEHICLES.search(label[:220]):
            return None
        when=event_date(label,today)
        location=place(label[:300])
    if not when or not location or not lot_evidence(text,site):
        return None
    if re.search(r"^(?:Encerrado|Cancelado|Suspenso)\b",header,re.I):
        return None
    city,uf=location
    ident=urllib.parse.urlsplit(url).path.strip("/").split("/")[-2 if site=="parque" else -1]
    key=f"{site}-{ident}-{when[0]}"
    return {"id":key,"event_id":key,
        "title":f"Leilão de veículos — {SITES[site][0]}",
        "state":uf,"city":city,
        "auction_date":when[0],"auction_time":when[1],
        "vehicle_count":None,"organizer":SITES[site][0],
        "source_type":"private","source_link_type":"event",
        "source_url":url,"status":"scheduled",
        "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}

def get_page(site,url):
    if url!=SITES[site][1] and not trusted_url(site,url):
        raise ValueError("untrusted event URL")
    class CanonicalRedirect(urllib.request.HTTPRedirectHandler):
        def __init__(self):
            self.count=0
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            self.count+=1
            initial=urllib.parse.urlsplit(req.full_url)
            target=urllib.parse.urlsplit(newurl)
            # Only permit the same individual auction path with an optional
            # trailing slash, on the same approved host.
            if (self.count>2 or target.scheme!="https" or
                target.hostname!=initial.hostname or
                target.path.rstrip("/")!=initial.path.rstrip("/") or
                target.query!=initial.query or target.fragment or
                not trusted_url(site,newurl)):
                raise ValueError("redirect outside identical first-party auction")
            return super().redirect_request(req,fp,code,msg,headers,newurl)
    req=urllib.request.Request(url,headers={"Accept":"text/html",
        "User-Agent":"BuscaLeilaoBot/0.7 (+https://github.com/igormarianoapps/buscaleilao)"})
    with urllib.request.build_opener(CanonicalRedirect()).open(req,timeout=11) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():raise ValueError("not HTML")
        if url!=SITES[site][1] and not trusted_url(site,resp.geturl()):
            raise ValueError("unexpected final URL")
        return resp.read(2_000_001).decode("utf-8","replace")

def collect_secondary(today=None,loader=get_page):
    today=today or auction_today()
    found,errors=[],[]
    for site,(name,home,hosts,pattern) in SITES.items():
        try:
            doc=VisibleLinks();doc.feed(loader(site,home))
            unique={}
            for raw,label,idx in doc.links:
                url=urllib.parse.urljoin(home,raw or "")
                if trusted_url(site,url):
                    # Parque's "Detalhes" links have context on the details page.
                    unique.setdefault(url,label)
                if len(unique)>=20:break
            if not unique:
                errors.append({"id":site,"error":"no first-party auction detail URLs"})
            for url,label in unique.items():
                try:
                    item=parse_event(site,label,loader(site,url),url,today)
                    if item:found.append(item)
                except Exception as e:
                    errors.append({"id":site+":"+url,"error":str(e)[:160]})
        except Exception as e:
            errors.append({"id":site,"error":str(e)[:160]})
    dedup={r["id"]:r for r in found}
    return list(dedup.values()),errors
