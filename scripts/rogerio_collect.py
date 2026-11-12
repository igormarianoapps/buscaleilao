"""Read-only Rogério Menezes public vehicle-auction adapter.

Only first-party individual event pages with future dated sessions, published
vehicle lots and event-specific city/UF can enter the verified feed.
The index may legitimately have no upcoming auctions.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from auction_clock import auction_today
from regional_collect import VisibleLinks
from auction_platform_watch import NoRedirect

ROOT=Path(__file__).resolve().parents[1]
HOSTS={"rogeriomenezes.com.br","www.rogeriomenezes.com.br"}
INDEXES=("https://rogeriomenezes.com.br/leiloes",
         "https://www.rogeriomenezes.com.br/leiloes-judiciais")
DETAIL=re.compile(r"/leilao/([0-9]{1,10})/?",re.I)
UF=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
DATE_TIME=re.compile(r"\b(\d{2})/(\d{2})/(20\d{2})\s+[àa]s\s+(\d{1,2}):(\d{2})h?\b",re.I)
PLACE=re.compile(r"\b(?:No dia do leil[aã]o|Visita[cç][aã]o|Local do leil[aã]o).{0,220}?\b([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ ]{2,38})\s*[/,-]\s*([A-Z]{2})\b",re.I)
VEHICLE=re.compile(r"\b(?:ve[ií]culos?|carros?|motos?|caminh[oõ]es?|autom[oó]veis?|financeiras|seguradoras)\b",re.I)
REJECT=re.compile(r"\b(?:cancelado|suspenso|encerrado|finalizado)\b",re.I)
LOT=re.compile(r"\bLOTE\s*(?:N[º°.]?\s*)?(\d{1,5})\b",re.I)

def detail_id(url):
    if not isinstance(url,str):return None
    try:
        p=urllib.parse.urlsplit(url)
        if (p.scheme!="https" or p.hostname not in HOSTS or p.port not in (None,443)
                or p.username or p.password or p.query or p.fragment or "\\" in url):
            return None
        m=DETAIL.fullmatch(p.path)
        return m.group(1) if m else None
    except (ValueError,TypeError):
        return None

def parse_event(html,url,today=None):
    identifier=detail_id(url)
    if not identifier:return None
    today=today or auction_today()
    parser=VisibleLinks();parser.feed(html[:2_000_000])
    text=parser.text
    # The specific event date, title, venue and actual lots must be present
    # in the event itself rather than only in its related auctions or footer.
    top=text[:1400]
    if REJECT.search(top[:120]) or re.search(r"\b(?:Rascunho|0\s+lotes)\b",top[:500],re.I):
        return None
    if not VEHICLE.search(top):return None
    date_match=DATE_TIME.search(top)
    if not date_match:return None
    dd,mm,yyyy,hh,minute=map(int,date_match.groups())
    try:
        when=date(yyyy,mm,dd)
    except ValueError:return None
    if when<today or hh>23 or minute>59:return None
    match=PLACE.search(top)
    if not match:return None
    city=" ".join(match.group(1).split()).strip().title()
    state=match.group(2).upper()
    if state not in UF or len(city)<3:return None
    lots=set(LOT.findall(text))
    # Never treat category filters (e.g. 84 Financeiras, 20 Seguradoras)
    # as actual published lots.
    if len(lots)<2:return None
    if re.search(r"\bNenhum lote encontrado\b",text,re.I):return None
    key=f"rogerio-{identifier}-{when.isoformat()}"
    return {"id":key,"event_id":key,
        "title":"Leilão de veículos — Rogério Menezes",
        "state":state,"city":city,"auction_date":when.isoformat(),
        "auction_time":f"{hh:02}:{minute:02}","vehicle_count":None,
        "organizer":"Rogério Menezes","source_type":"private",
        "source_link_type":"event","source_url":url,"status":"scheduled",
        "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}

def fetch(url):
    if url not in INDEXES and not detail_id(url):
        raise ValueError("unapproved first-party event URL")
    req=urllib.request.Request(url,headers={
        "User-Agent":"BuscaLeilaoBot/1.0 (+https://github.com/igormarianoapps/buscaleilao)",
        "Accept":"text/html"})
    with urllib.request.build_opener(NoRedirect).open(req,timeout=12) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():
            raise ValueError("not HTML")
        return resp.read(2_000_001).decode("utf-8","replace")

def discover(html,index):
    doc=VisibleLinks();doc.feed(html[:2_000_000])
    found=set()
    for href,label,_ in doc.links:
        url=urllib.parse.urljoin(index,href or "")
        if detail_id(url):found.add(url)
    return sorted(found)[:35]

def collect_rogerio(today=None,loader=fetch):
    today=today or auction_today()
    errors=[]
    candidates=set()
    success=0
    for index in INDEXES:
        try:
            candidates.update(discover(loader(index),index))
            success+=1
        except Exception as exc:
            errors.append({"id":"rogerio:index:"+index,"error":str(exc)[:180]})
    events=[]
    for url in sorted(candidates)[:40]:
        try:
            row=parse_event(loader(url),url,today)
            if row:events.append(row)
        except Exception as exc:
            errors.append({"id":"rogerio:"+url,"error":str(exc)[:180]})
    if not success:errors.append({"id":"rogerio","error":"no approved index reachable"})
    return events,errors
