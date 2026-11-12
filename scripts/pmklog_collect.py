"""PMKLog current-edition collector (never publishes archived lots).

A recurring auction URL isn't evidence that its most recent edition is active.
Only an explicitly announced future edition, full dated vehicle lots, and
a matching first-party event identity can produce a public feed row.
"""
import json,re,urllib.parse,urllib.request
from datetime import date,datetime,timezone
from pathlib import Path
from regional_collect import VisibleLinks
from auction_clock import auction_today
from auction_platform_watch import NoRedirect
ROOT=Path(__file__).resolve().parents[1]
HOSTS={"pmklog.com.br","www.pmklog.com.br"}
EVENT_PATH=re.compile(r"/leilao/evento/([a-z0-9-]{5,110})/?",re.I)
UUID=re.compile(r"[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}",re.I)
DATE=re.compile(r"\b(\d{2})/(\d{2})/(20\d{2})\b")
LOT=re.compile(r"\b(?:Finalizado\s+)?Lote\s+(\d{1,5})\b",re.I)
UF=re.compile(r"\b(?:PATIO|PÁTIO|GOIANIA|GOIÂNIA|ANÁPOLIS|ANAPOLIS)[^.;]{0,90}/([A-Z]{2})\b",re.I)
KNOWN="https://pmklog.com.br/leilao/evento/leilao-detran/?evento=fa724af3-d396-11f1-a2f8-02420a000014"
INDEX_URLS=("https://pmklog.com.br/","https://pmklog.com.br/leilao/","https://pmklog.com.br/nossos-leiloes")
def event_id(url):
    try:
        p=urllib.parse.urlsplit(url)
        if (p.scheme!="https" or p.hostname not in HOSTS or p.username or
            p.password or p.port not in (None,443) or p.fragment or "\\" in url):
            return None
        m=EVENT_PATH.fullmatch(p.path)
        values=urllib.parse.parse_qs(p.query,strict_parsing=True)
        if not m or set(values)!={"evento"} or len(values["evento"])!=1 or not UUID.fullmatch(values["evento"][0]):
            return None
        return m.group(1),values["evento"][0].lower()
    except (ValueError,TypeError):
        return None
def discover_urls(home_html):
    parser=VisibleLinks();parser.feed(home_html[:2_000_000])
    found={KNOWN}
    for href,label,_ in parser.links:
        full=urllib.parse.urljoin("https://pmklog.com.br/",href or "")
        if event_id(full):
            found.add(full)
    return sorted(found)[:20]
def parse_edition(html,url,today=None):
    key=event_id(url)
    if not key:return None
    today=today or auction_today()
    parser=VisibleLinks();parser.feed(html[:2_000_000])
    body=parser.text
    next_pos=body.find("Próxima edição")
    if next_pos<0:return None
    portion=body[next_pos:next_pos+500]
    if re.search(r"não há uma nova edição prevista|nenhuma nova edição|sem próxima edição",portion,re.I):
        return None
    if re.search(r"Finalizado|Encerrado|Cancelado",body[:min(next_pos,800)],re.I):
        return None
    # The current edition's date needs a full year: month/day-only cards can be archived.
    dates=[]
    for m in DATE.finditer(portion):
        try:
            d=date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
            if d>=today:dates.append(d)
        except ValueError:pass
    if len(set(dates))!=1:return None
    d=dates[0]
    # Require matching new-edition lot dates, never just the archived lot inventory.
    intro=body[:next_pos]
    lot_nums=set(LOT.findall(intro))
    date_str=d.strftime("%d/%m/%Y")
    if len(lot_nums)<2 or date_str not in intro:return None
    if re.search(r"Finalizado\s+Lote",intro,re.I):
        # Mixed past/new lots require a per-lot partitioning adapter; fail closed.
        return None
    uf_codes=set(x.upper() for x in UF.findall(body[next_pos:next_pos+1200]))
    if len(uf_codes)!=1:return None
    state=next(iter(uf_codes))
    time_match=re.search(r"\b(?:às|as)\s*(\d{1,2})[h:](\d{2})",portion,re.I)
    if not time_match:return None
    hour,minute=map(int,time_match.groups())
    if hour>23 or minute>59:return None
    slug,edition=key
    auction_id=f"pmklog-{edition}-{d.isoformat()}"
    return {"id":auction_id,"event_id":auction_id,
            "title":"Leilão de veículos — PMKLog",
            "state":state,"city":"Local informado no edital",
            "auction_date":d.isoformat(),"auction_time":f"{hour:02}:{minute:02}",
            "vehicle_count":None,"organizer":"PMKLog","source_type":"private",
            "source_link_type":"event","source_url":url,"status":"scheduled",
            "edition_id":edition,
            "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
def fetch(url):
    if url not in INDEX_URLS and not event_id(url):
        raise ValueError("unapproved PMKLog URL")
    req=urllib.request.Request(url,headers={"User-Agent":"BuscaLeilaoBot/0.9 (+https://github.com/igormarianoapps/buscaleilao)","Accept":"text/html"})
    with urllib.request.build_opener(NoRedirect).open(req,timeout=11) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():
            raise ValueError("not HTML")
        return resp.read(2_000_001).decode("utf-8","replace")
def collect_pmklog(today=None,loader=fetch):
    """Check three first-party public calendars and revalidate actual edition pages.

    If one index fails, other indexes and the known archived event are still
    checked. Nothing from an index is directly published.
    """
    today=today or auction_today()
    errors=[]
    urls={KNOWN}
    accessed=0
    for index in INDEX_URLS:
        try:
            urls.update(discover_urls(loader(index)))
            accessed+=1
        except Exception as exc:
            errors.append({"id":"pmklog:index:"+index,"error":str(exc)[:160]})
    events=[]
    for url in sorted(urls)[:40]:
        try:
            event=parse_edition(loader(url),url,today)
            if event:events.append(event)
        except Exception as exc:
            errors.append({"id":"pmklog:"+url,"error":str(exc)[:160]})
    if not accessed:
        errors.append({"id":"pmklog","error":"all authorized indexes unavailable"})
    return events,errors
