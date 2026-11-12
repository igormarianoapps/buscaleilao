"""Palácio dos Leilões first-party event-ID adapter.

The marketplace often lists historic and miscellaneous lots. Publish only
a future event when its own numbered details confirm vehicle category,
auction date/time, at least two actual lots and vehicle city/UF.
"""
import json,re,urllib.parse,urllib.request
from datetime import date,datetime,timezone
from pathlib import Path
from regional_collect import VisibleLinks
from auction_platform_watch import NoRedirect
from auction_clock import auction_today
ROOT=Path(__file__).resolve().parents[1]
HOSTS={"www.palaciodosleiloes.com.br","palaciodosleiloes.com.br"}
UF=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
EVENT=re.compile(r"/site/index\.php",re.I)
def auction_id(url):
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.hostname not in HOSTS or p.username or p.password or p.port not in (None,443) or p.fragment:
            return None
        q=urllib.parse.parse_qs(p.query,strict_parsing=True)
        if not EVENT.fullmatch(p.path) or set(q)!={"leilao_pesquisa"} or len(q["leilao_pesquisa"])!=1:
            return None
        value=q["leilao_pesquisa"][0]
        return value if re.fullmatch(r"\d{3,9}",value) else None
    except (ValueError,TypeError):
        return None
def extract_event(html,url,today=None):
    aid=auction_id(url)
    if not aid:return None
    today=today or auction_today()
    doc=VisibleLinks();doc.feed(html[:2_000_000])
    body=doc.text
    header=body[:3800]
    if not re.search(r"\bLeil[aã]o\s+(?:n[ºo.]+\s*)?"+re.escape(aid)+r"\b",header,re.I):
        return None
    if not re.search(r"\b(?:autom[oó]vel|ve[ií]culos|motociclet|carro|caminh[aã]o|sinistrados|sucatas)\b",header,re.I):
        return None
    if re.search(r"\b(?:finalizado|cancelado|suspenso|encerrado)\b",header[:550],re.I):
        return None
    m=re.search(r"(?:Data da realiza[cç][aã]o|Data do leil[aã]o|Realiza[cç][aã]o)\s*:\s*(\d{2})/(\d{2})/(20\d{2})\s+(?:[àa]s\s+)?(\d{1,2}):(\d{2})",header,re.I)
    if not m:return None
    dd,mm,yyyy,hh,minute=map(int,m.groups())
    try:
        when=date(yyyy,mm,dd)
        if when<today or hh>23 or minute>59:return None
    except ValueError:return None
    # Need an explicit first-party city/UF. A city alone is insufficient
    # because the marketplace operates in multiple states.
    places=re.findall(r"\b(?:Local do Bem|P[aá]tio|Localiza[cç][aã]o)\s*:\s*([A-Za-zÀ-ÿ ]{3,45})\s*[,/-]\s*([A-Z]{2})\b",header,re.I)
    states={uf.upper() for _,uf in places if uf.upper() in UF}
    if len(states)!=1:return None
    state=next(iter(states))
    city=next(city.strip().title() for city,uf in places if uf.upper()==state)
    lots=set(re.findall(r"\bLote\s*(?:n[º°.]?\s*)?:?\s*(\d{1,6})\b",body,re.I))
    if len(lots)<2:return None
    key=f"palacio-{aid}-{when.isoformat()}"
    return {"id":key,"event_id":key,
            "title":f"Leilão de veículos {aid} — Palácio dos Leilões",
            "state":state,"city":city,"auction_date":when.isoformat(),
            "auction_time":f"{hh:02}:{minute:02}","vehicle_count":None,
            "organizer":"Palácio dos Leilões","source_type":"private",
            "source_link_type":"event","source_url":url,"status":"scheduled",
            "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")}
def fetch(url):
    if not auction_id(url):raise ValueError("not first-party auction detail")
    req=urllib.request.Request(url,headers={
        "User-Agent":"BuscaLeilaoBot/0.9 (+https://github.com/igormarianoapps/buscaleilao)",
        "Accept":"text/html"})
    with urllib.request.build_opener(NoRedirect).open(req,timeout=12) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():
            raise ValueError("non HTML")
        return resp.read(2_000_001).decode("utf-8","replace")
def collect_palacio(today=None,loader=fetch,discovery_path=None):
    today=today or auction_today()
    path=Path(discovery_path) if discovery_path else ROOT/"app/auction-discovery-combined.json"
    try:
        combined=json.loads(path.read_text(encoding="utf-8"))
        rows=combined.get("platforms",{}).get("palacio",{}).get("candidate_events",[])
    except (OSError,ValueError):rows=[]
    urls=sorted({r["source_url"] for r in rows if auction_id(r.get("source_url"))})[:25]
    found,errors=[],[]
    for url in urls:
        try:
            html=loader(url)
            item=extract_event(html,url,today)
            if item:
                found.append(item)
            else:
                errors.append({"id":"palacio:"+url,"error":"not published: event date, individual vehicle lots or lot city/UF not independently confirmed"})
        except Exception as e:errors.append({"id":"palacio:"+url,"error":str(e)[:170]})
    if not urls:errors.append({"id":"palacio","error":"no first-party auction detail URLs discovered"})
    return found,errors
