"""Conservative adapter for official Minas Gerais Detran vehicle auction lots.

Uses published closing time (NOT guessed opening time), checks the official
lot detail page and rejects all ambiguous or completed entries.
"""
import re
import urllib.parse
import urllib.request
from datetime import date
from html.parser import HTMLParser
from auction_clock import auction_today

HOME="https://leilao.transito.mg.gov.br/"
HOST="leilao.transito.mg.gov.br"
UA="BuscaLeilaoBot/0.6 (+https://github.com/igormarianoapps/buscaleilao)"
ROUTE=re.compile(r"^/lotes/lista-lotes/(\d{1,10})/(20\d{2})/?$")

def detail_identity(url):
    try:
        p=urllib.parse.urlsplit(url)
        if p.scheme!="https" or p.hostname!=HOST or p.username or p.password or p.port not in (None,443):
            return None
        if p.query or p.fragment or "\\" in url:
            return None
        match=ROUTE.fullmatch(p.path)
        return match.groups() if match else None
    except (TypeError,ValueError):
        return None

class Listing(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.words=[]
        self.links=[]
        self.href=None
        self.active=[]
        self.hidden=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript"):
            self.hidden+=1
        if tag=="a" and not self.hidden:
            self.href=dict(attrs).get("href")
            self.active=[]
    def handle_data(self,data):
        if not self.hidden:
            word=" ".join(data.split())
            if word:
                self.words.append(word)
                if self.href is not None:
                    self.active.append(word)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.links.append((self.href," ".join(self.active),len(self.words)))
            self.href=None
        if tag in ("script","style","noscript") and self.hidden:
            self.hidden-=1

CARD=re.compile(
    r"Edital de Leil[aã]o\s+(\d{1,6})/(20\d{2})\s+(.{2,90}?)\s+"
    r"\1\s+-\s+(.{2,180}?)\s+(Publicado|Em Andamento|Finalizado|Cancelado)"
    r"\s+Encerramento:\s+(\d{2})/(\d{2})/(20\d{2})\s+(\d{2}):(\d{2})",
    re.I|re.S)

def listing_candidates(html, today=None):
    today=today or auction_today()
    parser=Listing()
    parser.feed(html[:1_000_000])
    found=[]
    seen=set()
    for href,label,index in parser.links:
        target=urllib.parse.urljoin(HOME,href or "")
        ident=detail_identity(target)
        if ident is None or ident in seen:
            continue
        if "detalh" not in label.lower():
            continue
        # Last visible auction card before this individual details link.
        preceding=" ".join(parser.words[max(0,index-50):index])
        matches=list(CARD.finditer(preceding))
        if not matches:
            continue
        match=matches[-1]
        auction,year,city,pound,status,dd,mm,yyyy,hh,minute=match.groups()
        if status.casefold() not in ("publicado","em andamento"):
            continue
        try:
            ending=date(int(yyyy),int(mm),int(dd))
        except ValueError:
            continue
        if ending<today or int(hh)>23 or int(minute)>59:
            continue
        # URL internal ID and year need to agree with listing.
        if ident[1]!=year:
            continue
        found.append({
            "id":f"mg-detran-{ident[0]}-{ident[1]}",
            "event_id":f"mg-detran-{ident[0]}-{ident[1]}",
            "auction_number":f"{auction}/{year}",
            "title":f"Detran MG — Leilão {auction}/{year} (encerramento de lances)",
            "state":"MG", "city":city.strip().title(),
            "auction_date":ending.isoformat(),
            "auction_time":f"{int(hh):02}:{int(minute):02}",
            "date_kind":"closing",
            "vehicle_count":None, "organizer":"Detran MG",
            "source_type":"state","source_url":target,
            "source_link_type":"event","status":"scheduled"
        })
        seen.add(ident)
        if len(found)>=12:
            break
    return found

def fetch(url):
    request=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html"})
    with urllib.request.urlopen(request,timeout=12) as response:
        final=urllib.parse.urlsplit(response.geturl())
        expected=urllib.parse.urlsplit(url)
        if final.scheme!="https" or final.hostname!=HOST or final.path!=expected.path:
            raise ValueError("unexpected redirect from official Detran portal")
        if "html" not in response.headers.get("Content-Type","").lower():
            raise ValueError("official portal did not return HTML")
        return response.read(1_000_001).decode("utf-8",errors="replace")

def detail_confirms(html,auction_number):
    reader=Listing()
    reader.feed(html[:500_000])
    text=" ".join(reader.words)
    number=auction_number.split("/")[0]
    return bool(re.search(r"\bLeil[aã]o\s*"+re.escape(number)+r"\b",text,re.I)
                and re.search(r"\bLote\s+\d+\b",text,re.I)
                and not re.search(r"leil[aã]o\s+(?:cancelado|suspenso)",text,re.I))

def collect_mg(today=None,loader=fetch):
    today=today or auction_today()
    events,errors=[],[]
    try:
        candidates=listing_candidates(loader(HOME),today=today)
    except Exception as exc:
        return [],[{"id":"mg-detran","error":str(exc)[:180]}]
    for row in candidates:
        try:
            if not detail_confirms(loader(row["source_url"]),row["auction_number"]):
                raise ValueError("official detail page lacks matching number and lot evidence")
            events.append(row)
        except Exception as exc:
            errors.append({"id":row["id"],"error":str(exc)[:180]})
    return events,errors
