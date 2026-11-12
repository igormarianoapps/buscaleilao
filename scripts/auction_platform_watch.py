"""Monitor nominated auction domains safely.

Discover individual auction *candidates* from their public pages. Nothing here
promotes a website or candidate into a trusted event. Publication requires
the strict event-level checks in auction_security + auction_links.
"""
import concurrent.futures
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REGISTRY=ROOT/"app"/"auction-platforms.json"
REPORT=ROOT/"app"/"auction-platform-diagnostics.json"
UA="BuscaLeilaoBot/0.7 (+https://github.com/igormarianoapps/buscaleilao)"
STATES=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
DETAIL=re.compile(r"(?:leilao|leiloes|evento|eventos|pregao|detalhes|relacao-lista|relacao-foto|veiculos\.php|/lotes/[0-9]+)",re.I)
NOISE=re.compile(r"(?:login|cadastro|usuario|entrar|minha.conta|politica|contato|sobre|imovel|terreno|apartamento|curso|faq|facebook|instagram|whatsapp|youtube|trabalhe)",re.I)

def clean(value):
    norm=unicodedata.normalize("NFD",str(value or "")).casefold()
    return " ".join("".join(c for c in norm if not unicodedata.combining(c)).split())

class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth=0
        self.href=None
        self.buffer=[]
        self.links=[]
    def handle_starttag(self,tag,attrs):
        if tag in ("script","style","noscript","svg"):
            self.depth+=1
        if tag=="a" and self.depth==0:
            self.href=dict(attrs).get("href")
            self.buffer=[]
    def handle_data(self,data):
        if self.href is not None and self.depth==0:
            self.buffer.append(data)
    def handle_endtag(self,tag):
        if tag=="a" and self.href is not None:
            self.links.append((self.href," ".join(self.buffer).strip()))
            self.href=None
        if tag in ("script","style","noscript","svg") and self.depth:
            self.depth-=1

def host_ok(site,url):
    try:
        p=urllib.parse.urlsplit(url)
        return (p.scheme=="https" and p.hostname in site["allowed_hosts"]
                and not p.username and not p.password and p.port in (None,443)
                and not p.fragment and "\\" not in url and
                not any(ch.isspace() for ch in url))
    except (ValueError,TypeError):
        return False

def candidates(site,markup):
    if not host_ok(site,site["discovery_url"]):
        raise ValueError("discovery host not approved")
    doc=Links()
    doc.feed(markup[:2_000_000])
    result=[]
    seen=set()
    root=urllib.parse.urlsplit(site["discovery_url"])
    for raw,label in doc.links:
        url=urllib.parse.urljoin(site["discovery_url"],raw or "")
        if not host_ok(site,url):
            continue
        p=urllib.parse.urlsplit(url)
        if p.path.rstrip("/")==root.path.rstrip("/") and p.query==root.query:
            continue
        title=clean(label)
        route=clean(p.path)
        if not title or NOISE.search(title) or NOISE.search(route):
            continue
        if not DETAIL.search(p.path) and not DETAIL.search(title):
            continue
        if not re.search(r"(?:leilao|veicul|carro|moto|frota|pesad|lote|bem|financeir|detalhe)",title):
            continue
        if url in seen:
            continue
        # Known lot pages from Leilo are evidence of vehicles, not an event URL.
        # A category search in Freitas is not an individual auction either.
        from urllib.parse import urlsplit as _split
        kind = ("individual_lot" if site["id"]=="leilo" and
                re.fullmatch(r"/lote/[0-9a-f-]{36}/?",_split(url).path,re.I)
                else "generic_category" if site["id"]=="freitas" and
                _split(url).path.lower()=="/leiloes/pesquisar"
                else "possible_event")
        seen.add(url)
        result.append({
            "candidate_kind":kind,
            "platform_id":site["id"],"title":label[:180],
            "source_url":url,
            "state_hint":site["state_hint"],
            "status":"unverified_candidate",
            "review_status":"needs_event_date_lot_url_and_auctioneer_verification"
        })
        if len(result)==25:
            break
    return result

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        raise ValueError("unexpected redirect: blocked")

def fetch(site):
    if not host_ok(site,site["discovery_url"]):
        raise ValueError("untrusted discovery host")
    class ApprovedRedirect(urllib.request.HTTPRedirectHandler):
        def __init__(self):
            self.hops=0
        def redirect_request(self,req,fp,code,msg,headers,newurl):
            self.hops+=1
            if self.hops>3 or not host_ok(site,newurl):
                raise ValueError("redirect outside approved platform hosts")
            return super().redirect_request(req,fp,code,msg,headers,newurl)
    opener=urllib.request.build_opener(ApprovedRedirect())
    request=urllib.request.Request(site["discovery_url"],headers={
        "User-Agent":UA,"Accept":"text/html"})
    with opener.open(request,timeout=10) as response:
        if not host_ok(site,response.geturl()):
            raise ValueError("source changed to unapproved host")
        if "html" not in response.headers.get("Content-Type","").lower():
            raise ValueError("non-HTML response")
        return response.read(2_000_001).decode("utf-8","replace")

def monitor(sites,loader=fetch):
    result={}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(loader,site):site for site in sites}
        for task in concurrent.futures.as_completed(futures):
            site=futures[task]
            try:
                links=candidates(site,task.result())
                result[site["id"]]={
                    "status":"reachable","candidate_count":len(links),
                    "candidate_events":links,
                    "note":"Candidate links are not verified auctions"}
            except Exception as exc:
                result[site["id"]]={
                    "status":"unreachable","candidate_count":0,
                    "candidate_events":[],"error":str(exc).splitlines()[0][:180]}
    return result

def main():
    sites=json.loads(REGISTRY.read_text(encoding="utf-8"))
    result=monitor(sites)
    payload={"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
             "platforms_total":len(sites),
             "reachable":sum(x["status"]=="reachable" for x in result.values()),
             "unverified_candidates":sum(x["candidate_count"] for x in result.values()),
             "events_automatically_published":0,
             "platforms":{k:result[k] for k in sorted(result)}}
    REPORT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Platforms checked: {payload['reachable']}/{len(sites)} reachable; "
          f"{payload['unverified_candidates']} unverified candidate links, 0 published")
if __name__=="__main__":
    main()
