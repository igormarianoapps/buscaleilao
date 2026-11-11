"""Direct vehicle-list adapters for Vardana and Claudio Kuss.

Each listing requires (1) a specific first-party lot URL obtained from its
public event page, (2) an independently matching future date on the lot page,
and (3) actual vehicle lot entries. Otherwise it is not published.
"""
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import date,datetime,timezone
from html.parser import HTMLParser
from auction_clock import auction_today

CONFIG={
 "vardana":{
   "home":"https://www.vardanaleiloes.com.br/vardana/index",
   "hosts":{"www.vardanaleiloes.com.br","vardanaleiloes.com.br"},
   "path":r"/vardana/veiculos\.php",
   "label":r"ver relacao de lotes|ver relacao de veiculos",
   "organizer":"Vardana Leilões"
 },
 "claudio":{
   "home":"https://www.claudiokussleiloes.com.br/?acao=home",
   "hosts":{"www.claudiokussleiloes.com.br","claudiokussleiloes.com.br"},
   "path":r"/relacao-(?:lista|foto)/\d{1,8}",
   "label":r"acessar leilao",
   "organizer":"Claudio Kuss Leilões"
 }
}
class VisibleLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
        self.links=[]
        self.href=None
        self.active=[]
        self.ignored=0
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript","svg"):
            self.ignored+=1
        if tag=="a" and self.ignored==0:
            self.href=dict(attrs).get("href")
            self.active=[]
    def handle_data(self,data):
        if not self.ignored:
            data=" ".join(data.split())
            if data:
                self.parts.append(data)
                if self.href is not None:
                    self.active.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.links.append((self.href," ".join(self.active),len(self.parts)))
            self.href=None
        if tag in ("script","style","noscript","svg") and self.ignored:
            self.ignored-=1
    @property
    def text(self):
        return " ".join(self.parts)

def strict_url(site,url):
    if site not in CONFIG or not isinstance(url,str):
        return False
    try:
        p=urllib.parse.urlsplit(url)
        c=CONFIG[site]
        if p.scheme!="https" or p.hostname not in c["hosts"] or p.username or p.password:
            return False
        if p.port not in (None,443) or p.fragment or "\\" in url or any(x.isspace() for x in url):
            return False
        if not re.fullmatch(c["path"],p.path,re.I):
            return False
        if site=="vardana":
            q=urllib.parse.parse_qs(p.query,strict_parsing=True)
            return set(q)=={"lei"} and len(q["lei"])==1 and q["lei"][0].isdigit()
        return not p.query
    except ValueError:
        return False

def fetch(site,url):
    from auction_platform_watch import NoRedirect
    p=urllib.parse.urlsplit(url)
    allowed=CONFIG[site]["hosts"]
    if p.scheme!="https" or p.hostname not in allowed:
        raise ValueError("untrusted regional fetch host")
    opener=urllib.request.build_opener(NoRedirect)
    request=urllib.request.Request(url,headers={"User-Agent":"BuscaLeilaoBot/0.7 (+https://github.com/igormarianoapps/buscaleilao)","Accept":"text/html"})
    with opener.open(request,timeout=11) as resp:
        if "html" not in resp.headers.get("Content-Type","").lower():
            raise ValueError("non HTML response")
        return resp.read(1_000_001).decode("utf-8","replace")

def dated_event_day(raw,today):
    try:
        dd,mm,yyyy=map(int,raw.split("/"))
        result=date(yyyy,mm,dd)
        return result if result>=today else None
    except (ValueError,AttributeError):
        return None

def candidates(site,html,today=None):
    today=today or auction_today()
    config=CONFIG[site]
    parser=VisibleLinks()
    parser.feed(html[:1_000_000])
    results=[]
    seen=set()
    text=parser.parts
    for href,label,index in parser.links:
        normalized_label="".join(ch for ch in unicodedata.normalize("NFD",label.lower()) if not unicodedata.combining(ch))
        if not re.search(config["label"],normalized_label,re.I):
            continue
        full=urllib.parse.urljoin(config["home"],href or "")
        if not strict_url(site,full) or full in seen:
            continue
        # A short preceding region belongs to this event card; no global
        # date inference from footer, navigation or another listing.
        context=" ".join(text[max(0,index-55):index])
        if site=="vardana":
            # Card uses DD/MM, year appears on its specific lot page.
            match=re.findall(r"\b(\d{2})/(\d{2})(?:/(20\d{2}))?\b",context)
            if not match: continue
            dd,mm,yr=match[-1]
            year=int(yr) if yr else today.year
            try:day=date(year,int(mm),int(dd))
            except ValueError:continue
            if day<today: continue
            hour=re.search(r"(?:as|às)\s*(\d{1,2})h",context,re.I)
            clock=f"{int(hour.group(1)):02}:00" if hour else None
        else:
            match=re.search(r"(\d{2}/\d{2}/20\d{2})\s+[àa]s\s*(\d{1,2}):(\d{2})",context,re.I)
            if not match:continue
            day=dated_event_day(match.group(1),today)
            if not day: continue
            clock=f"{int(match.group(2)):02}:{match.group(3)}"
        seen.add(full)
        results.append((full,day.isoformat(),clock))
        if len(results)>=8:break
    return results

def verified_lots(site,html,iso):
    page=VisibleLinks()
    page.feed(html[:1_000_000])
    body=page.text
    dd=f"{iso[8:]}/{iso[5:7]}/{iso[:4]}"
    if dd not in body:
        return False
    if not re.search(r"leil[aã]o\s+(?:de\s+)?ve[ií]culos|listagem\s+de\s+ve[ií]culos",body,re.I):
        return False
    if re.search(r"leil[aã]o encerrado|leil[aã]o cancelado",body,re.I):
        return False
    if re.search(r"em breve os lotes est[aã]o|rela[cç][aã]o em breve",body,re.I):
        return False
    if site=="vardana":
        return bool(re.search(r"\bLote\s+1\s+.{2,60}",body,re.I))
    return bool(re.search(r"\b(?:Lote\s+00?1\b|001\s+[A-Z]{2,})",body,re.I))

def collect_regionals(today=None,loader=fetch):
    today=today or auction_today()
    rows,errors=[],[]
    for site,config in CONFIG.items():
        try:
            main=loader(site,config["home"])
            pairs=candidates(site,main,today=today)
            if not pairs:
                errors.append({"id":site,"error":"no future individual vehicle auction link"})
                continue
            for url,day,hour in pairs:
                try:
                    detail=loader(site,url)
                    if not verified_lots(site,detail,day):
                        raise ValueError("lot page not confirmed / no published lots")
                    q=urllib.parse.urlsplit(url)
                    ident=(urllib.parse.parse_qs(q.query).get("lei") or [q.path.rsplit("/",1)[-1]])[0]
                    key=f"{site}-{ident}-{day}"
                    rows.append({
                        "id":key,"event_id":key,
                        "title":f"Leilão de veículos — {config['organizer']}",
                        "state":"PR","city":"Curitiba","auction_date":day,
                        "auction_time":hour,"vehicle_count":None,
                        "organizer":config["organizer"],"source_type":"private",
                        "source_url":url,"source_link_type":"event",
                        "status":"scheduled",
                        "last_checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds")
                    })
                except Exception as exc:
                    errors.append({"id":f"{site}:{url}","error":str(exc)[:180]})
        except Exception as exc:
            errors.append({"id":site,"error":str(exc).splitlines()[0][:180]})
    return rows,errors
