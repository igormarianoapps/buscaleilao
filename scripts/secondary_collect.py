"""Fail-closed first-party collectors for Parque, Flex and Hisa.

No publication without a future event date, a first-party event/lots URL,
actual vehicle-lot evidence and a location explicitly attached to the event.
No address is inferred from company headquarters.
"""
import json
from pathlib import Path
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
PUBLIC_INDEXES={"parque":{"https://www.parquedosleiloes.com.br/","https://www.parquedosleiloes.com.br/leiloes"}}
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

def verified_lot_location(header):
    # Location must be attached to vehicle inspection / storage, NOT the
    # auction house footer or a generic headquarters address.
    matches=re.findall(
        r"(?:Visita[cç][aã]o|Local do Bem|P[aá]tio)\s*:\s*([^.;]{5,200})",
        header[:1700],re.I)
    for match in matches:
        possible=place(match[-100:])
        if possible and not re.search(r"endere[cç]o\s+(?:da\s+)?(?:empresa|sede)",match,re.I):
            city,uf=possible
            city=re.sub(r"^(?:P[aá]tio|Local do Bem)\s+","",city,flags=re.I).strip()
            return (city,uf) if city else None
    return None

def lot_evidence(text,site):
    if site=="flex":
        # The first-party page lists number + vehicle description in a table.
        return len(re.findall(r"\b(?:0\d{2}|\d{3})\s+(?:(?:I/)?(?:FIAT|FORD|CHEVROLET|RENAULT|VW|VOLKSWAGEN|HONDA|HYUNDAI|TOYOTA|JEEP)\b)",text,re.I))>=2
    # A lot count is not proof of any vehicle lots.
    return bool(re.search(r"\b(?:Lote\s*[01]?\d+|\d{1,2}\s*lote)\b",text,re.I)
                and BRANDS.search(text))

def rejection_reason(site,card,detail,url,today=None):
    """Give operators a source-specific reason without approving any candidate."""
    if not trusted_url(site,url):
        return "unapproved_individual_url"
    body=VisibleLinks()
    body.feed(detail[:2_000_000])
    text=body.text
    header=text[:1700]
    label=" ".join(card.split())
    if site=="hisa" and re.search(r"LOTES EM BREVE|SEM LOTES",header[:360],re.I):
        return "lots_not_published"
    if site=="parque":
        if not re.search(r"Categoria\s+VE[IÍ]CULOS",header,re.I):
            return "not_vehicle_category"
        when=event_date(header,today)
        location=place(header[:1500])
    elif site=="hisa":
        if not TITLE_VEHICLES.search(label[:240]) or NONVEHICLES.search(label[:240]):
            return "not_vehicle_category"
        when=event_date(label,today)
        if when and when[0][8:]+"/"+when[0][5:7]+"/"+when[0][:4] not in text[:2000]:
            return "event_date_not_confirmed_on_detail"
        location=place(label[:250])
    else:
        if not TITLE_VEHICLES.search(label[:220]) or NONVEHICLES.search(label[:220]):
            return "not_vehicle_category"
        when=event_date(label,today)
        location=place(label[:300]) or verified_lot_location(header)
    if not when:return "no_verified_future_event_date"
    if not location:return "event_or_lot_location_unverified"
    if not lot_evidence(text,site):return "vehicle_lots_not_confirmed"
    if re.search(r"^(?:Encerrado|Cancelado|Suspenso)\b",header,re.I):
        return "event_inactive"
    return "other_unverified_event_evidence"


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
        # The numbered event title can be the court name. Category and
        # actual vehicle lots provide stronger evidence than the title.
        when=event_date(header,today)
        location=place(header[:1500])
    elif site=="hisa":
        if re.search(r"LOTES EM BREVE|SEM LOTES|CANCELADO|ENCERRADO",header[:360],re.I):
            return None
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
        location=place(label[:300]) or verified_lot_location(header)
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
    if url not in PUBLIC_INDEXES.get(site,{SITES[site][1]}) and not trusted_url(site,url):
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
        if url not in PUBLIC_INDEXES.get(site,{SITES[site][1]}) and not trusted_url(site,resp.geturl()):
            raise ValueError("unexpected final URL")
        return resp.read(2_000_001).decode("utf-8","replace")

def fallback_candidates(site,combined):
    # Browser diagnostics are a *discovery index only*. Every detail is
    # freshly re-fetched and must pass the same strict event checks.
    rows=combined.get("platforms",{}).get(site,{}).get("candidate_events",[])
    unique={}
    for row in rows:
        url=row.get("source_url")
        if trusted_url(site,url):
            unique.setdefault(url,row.get("title") or "")
        if len(unique)>=20:break
    return unique

def collect_secondary(today=None, loader=get_page, discovery_path=None):
    """Merge current first-party links with previously discovered direct URLs.

    A blocked homepage must not prevent independently rechecking event URLs.
    Discovery data never bypasses parse_event's date, location or lot checks.
    """
    today = today or auction_today()
    found, errors = [], []
    path = Path(discovery_path) if discovery_path else (
        Path(__file__).resolve().parents[1] / "app/auction-discovery-combined.json"
    )
    combined = {}
    if loader is get_page or discovery_path is not None:
        try:
            combined = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append({"id": "secondary:discovery", "error": str(exc)[:160]})
    for site, (name, home, hosts, pattern) in SITES.items():
        unique = {}
        for index_url in sorted(PUBLIC_INDEXES.get(site,{home})):
            try:
                doc = VisibleLinks()
                doc.feed(loader(site, index_url))
                for raw,label,idx in doc.links:
                    url = urllib.parse.urljoin(index_url, raw or "")
                    if trusted_url(site,url):
                        unique.setdefault(url,label)
                    if len(unique)>=20:
                        break
            except Exception as exc:
                errors.append({"id":site+":index","error":str(exc)[:160]})
        # Use cached discovery solely as a URL index, including when the home
        # page is blocked or partially rendered. Every detail is fetched live.
        for url, label in fallback_candidates(site, combined).items():
            if len(unique) >= 25 and url not in unique:
                break
            # Homepage links can be icon-only ("Detalhes") while the public
            # discovery card contains its full vehicle title and date.
            # Prefer the corroborated candidate label, never candidate data
            # as proof of lot inventory, date or location on the detail page.
            old_label = unique.get(url, "")
            if (url not in unique or
                    (TITLE_VEHICLES.search(label[:220]) and
                     event_date(label,today) and
                     (not TITLE_VEHICLES.search(old_label[:220]) or
                      not event_date(old_label,today)))):
                unique[url] = label
        if not unique:
            errors.append({"id": site, "error": "no first-party auction detail URLs"})
        for url, label in unique.items():
            try:
                detail = loader(site, url)
                item = parse_event(site, label, detail, url, today)
                if item:
                    found.append(item)
                else:
                    errors.append({"id":site+":"+url,"error":"not published: "+rejection_reason(site,label,detail,url,today)})
            except Exception as exc:
                errors.append({"id": site + ":" + url, "error": str(exc)[:160]})
    dedup = {row["id"]: row for row in found}
    return list(dedup.values()), errors
