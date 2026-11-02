"""Public event-calendar adapters for Copart and VIP. No lot-level scraping."""
import re
import unicodedata
import urllib.request
from datetime import date, datetime, timezone
from html.parser import HTMLParser

STATES=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
URLS={"Copart":"https://www.copart.com.br/salesListResult","VIP Leilões":"https://www.vipleiloes.com.br/"}
FALLBACKS={"Copart":["https://www.copart.com.br/auctionCalendar"],"VIP Leilões":["https://www.vipleiloes.com.br/index"]}

class Reader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts=[]
        self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"): self.skip+=1
        if tag in ("div","tr","td","li","article","section","p"): self.parts.append(" | ")
    def handle_endtag(self,tag):
        if tag in ("script","style","noscript") and self.skip: self.skip-=1
        if tag in ("div","tr","td","li","article","section","p"): self.parts.append(" | ")
    def handle_data(self,data):
        if not self.skip: self.parts.append(data)

def fetch(url):
    req=urllib.request.Request(url,headers={"User-Agent":"BuscaLeilaoBot/0.3 (+https://github.com/igormarianoapps/buscaleilao)","Accept":"text/html"})
    with urllib.request.urlopen(req,timeout=25) as response:
        if "html" not in response.headers.get("Content-Type","").lower(): raise ValueError("Not HTML")
        raw=response.read(3000000)
    parser=Reader()
    parser.feed(raw.decode("utf-8",errors="replace"))
    return re.sub(r"\s+"," "," ".join(parser.parts))

def parse_date(s):
    try:
        d=datetime.strptime(s,"%d/%m/%Y" if "/" in s else "%d.%m.%Y").date()
        return d.isoformat() if d>=date.today() else None
    except ValueError: return None

def make(source,identifier,title,state,city,day,hour=None,notes=None):
    return {"id":identifier,"title":title,"state":state,"city":city,
        "auction_date":day,"auction_time":hour,"vehicle_count":None,
        "organizer":source,"source_type":"private","source_url":URLS[source],
        "status":"scheduled","last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "notes":notes}

def parse_copart(page):
    found={}
    # Exact city-UF plus date, based on the official public sales-list table.
    pat=r"([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]{2,65}?)\s*-\s*([A-Z]{2})\s*(?:\|\s*){0,3}(\d{2}\.\d{2}\.\d{4})"
    for m in re.finditer(pat,page):
        city,state,raw=m.groups()
        day=parse_date(raw)
        city=re.sub(r"\s+"," ",city).strip(" |-")
        if not day or state not in STATES or len(city)>45 or any(x in city.casefold() for x in ("lista de vendas","pátio do leilão","leilões em")): continue
        slug=re.sub("[^a-z0-9]+","-",unicodedata.normalize("NFKD",city).encode("ascii","ignore").decode().lower()).strip("-")
        key=f"copart-{day}-{state.lower()}-{slug}"
        found[key]=make("Copart",key,f"Leilão de veículos — Copart {city}",state,city,day)
    return list(found.values())

def parse_vip(page):
    found={}
    pat=(r"(Conservado e Sucata|Financeiras|Seguradoras|Sucata|Conservado|Particulares|Detran\s*-\s*[A-Z]{2})"
         r".{0,160}?In[ií]cio\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}:\d{2})"
         r".{0,130}?Estados\s+((?:[A-Z]{2}-)*[A-Z]{2}|N[aã]o Informado)")
    for m in re.finditer(pat,page,re.I):
        name,raw,hour,rawstates=m.groups()
        day=parse_date(raw)
        states=rawstates.upper().split("-")
        if not day or any(s not in STATES for s in states): continue
        identity=f"{day}-{hour.replace(':','')}-{re.sub('[^a-z0-9]','-',name.lower())}"
        for state in states:
            key=f"vip-{identity}-{state.lower()}"
            found[key]=make("VIP Leilões",key,f"Leilão {name} — VIP Leilões",
                state,"Diversas localidades" if len(states)>1 else "Não informada",day,hour,
                "Evento multiestadual; não confundir lotes com quantidade de veículos." if len(states)>1 else None)
    return list(found.values())

def collect_platforms():
    events,errors=[],[]
    for name,parser in (("Copart",parse_copart),("VIP Leilões",parse_vip)):
        reasons=[]
        for url in [URLS[name],*FALLBACKS[name]]:
            try:
                found=parser(fetch(url))
                if not found: raise ValueError("Nenhum evento futuro identificado com segurança")
                for event in found:
                    event["source_url"]=url
                events.extend(found)
                print(f"PLATFORM {name}: {len(found)} eventos por estado via {url}")
                break
            except (OSError,ValueError) as exc:
                reasons.append(f"{url}: {str(exc)[:150]}")
        else:
            errors.append({"id":name,"error":"; ".join(reasons)[:500]})
            print(f"PLATFORM {name}: nenhuma fonte acessível com eventos validados")
    return events,errors
