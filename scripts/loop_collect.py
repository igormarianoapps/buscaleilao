"""Loop Leilões: use its official auction site, NOT Loop Brasil corporate store.

An empty /eventos agenda correctly returns zero. Vehicle offers without an
actual scheduled auction edition are not BuscaLeilão events.
"""
import re,urllib.parse,urllib.request
from datetime import date,datetime,timezone
from auction_platform_watch import NoRedirect
from auction_clock import auction_today
from regional_collect import VisibleLinks
HOSTS={"loopleiloes.com.br","www.loopleiloes.com.br"}
AGENDA="https://loopleiloes.com.br/eventos"
def event_id(url):
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.hostname not in HOSTS or p.username or p.password or p.port not in (None,443) or p.fragment or p.query:
            return None
        m=re.fullmatch(r"/(?:eventos|evento)/([a-z0-9-]{3,80})/?",p.path,re.I)
        return m.group(1) if m else None
    except (TypeError,ValueError):return None
def agenda_urls(html):
    doc=VisibleLinks();doc.feed(html[:1_000_000])
    text=doc.text.lower()
    if "não há eventos agendados no momento" in text:
        return []
    urls=[]
    for href,_,_ in doc.links:
        full=urllib.parse.urljoin(AGENDA,href or "")
        if event_id(full) and full not in urls:urls.append(full)
    return urls[:20]
def parse_event(html,url,today=None):
    ident=event_id(url)
    if not ident:return None
    today=today or auction_today()
    doc=VisibleLinks();doc.feed(html[:2_000_000])
    text=doc.text[:13000]
    head=text[:2500]
    if re.search(r"encerrado|cancelado|suspenso|finalizado",head[:500],re.I):return None
    if not re.search(r"ve[ií]culos|carros|motos|autom[oó]veis|caminh[oõ]es",head,re.I):return None
    m=re.search(r"(?:Data do leil[aã]o|Data e hor[aá]rio|Leil[aã]o)\s*:\s*(\d{2})/(\d{2})/(20\d{2})\s+(?:[àa]s\s*)?(\d{1,2}):(\d{2})",head,re.I)
    local=re.search(r"(?:P[aá]tio|Local do evento|Local dos ve[ií]culos)\s*:\s*([A-Za-zÀ-ÿ\s-]{3,45})\s*[,/-]\s*([A-Z]{2})",head,re.I)
    if not m or not local:return None
    dd,mm,yyyy,h,mi=map(int,m.groups())
    try:
        d=date(yyyy,mm,dd)
        if d<today or h>23 or mi>59:return None
    except ValueError:return None
    states="AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()
    if local.group(2) not in states:return None
    lots=set(re.findall(r"\bLote\s+(\d{1,5})\b",text,re.I))
    if len(lots)<2:return None
    key=f"loop-{ident}-{d.isoformat()}"
    return {"id":key,"event_id":key,"title":"Leilão de veículos — Loop Leilões",
        "state":local.group(2),"city":local.group(1).strip().title(),
        "auction_date":d.isoformat(),"auction_time":f"{h:02}:{mi:02}",
        "vehicle_count":None,"organizer":"Loop Leilões","source_type":"private",
        "source_link_type":"event","source_url":url,"status":"scheduled",
        "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
def fetch(url):
    if url!=AGENDA and not event_id(url):raise ValueError("not Loop official individual auction")
    req=urllib.request.Request(url,headers={"User-Agent":"BuscaLeilaoBot/0.9 (+https://github.com/igormarianoapps/buscaleilao)","Accept":"text/html"})
    with urllib.request.build_opener(NoRedirect).open(req,timeout=12) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():raise ValueError("non HTML")
        return resp.read(2_000_001).decode("utf-8","replace")
def collect_loop(today=None,loader=fetch):
    today=today or auction_today()
    try:urls=agenda_urls(loader(AGENDA))
    except Exception as exc:return [],[{"id":"loop","error":str(exc)[:170]}]
    events,errors=[],[]
    for url in urls:
        try:
            event=parse_event(loader(url),url,today)
            if event:events.append(event)
        except Exception as exc:errors.append({"id":"loop:"+url,"error":str(exc)[:160]})
    return events,errors
