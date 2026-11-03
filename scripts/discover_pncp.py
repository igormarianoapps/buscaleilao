"""Discover vehicle-auction notices from the official PNCP public consultation API.

PNCP records are research candidates. Even a PNCP record does not prove
that the auction will happen as scheduled; check its edital and current status
before admitting the event to the public agenda.
"""
import json
import re
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT / "app" / "pncp-candidates.json"
BASE="https://pncp.gov.br/api/consulta/v1/contratacoes/publicacao"
MODALITIES=(1,13)  # PNCP: Leilão Eletrônico / Leilão Presencial
VEHICLES=re.compile(r"ve[ií]cul|autom[oó]v|motociclet|motocicl|caminh[aã]o|micro.?[oô]nibus|frota|sucata de carro",re.I)
CANCELLED=re.compile(r"cancelad|anulad|revogad|suspens",re.I)

def official_record_url(record):
    """Build PNCP's official detail path only from a valid PNCP control number."""
    ident=str(record.get("numeroControlePNCP") or "")
    m=re.fullmatch(r"(\d{14})-1-(\d{1,8})/(20\d{2})", ident)
    if not m: return None
    cnpj,seq,year=m.groups()
    return f"https://pncp.gov.br/app/editais/{cnpj}/{year}/{int(seq)}"

def candidate(record, today=None):
    """Extract a promising *unverified* future auction. Never manufacture time/UF."""
    today=today or date.today()
    if not isinstance(record,dict): return None
    obj=str(record.get("objetoCompra") or "").strip()
    if not VEHICLES.search(obj): return None
    status=str(record.get("situacaoCompraNome") or "")
    if CANCELLED.search(status): return None
    raw=record.get("dataEncerramentoProposta")
    if not isinstance(raw,str): return None
    try:
        due=date.fromisoformat(raw[:10])
    except ValueError:
        return None
    if due<today or due>today+timedelta(days=120): return None
    location=record.get("unidadeOrgao") or {}
    if not isinstance(location,dict): return None
    uf=str(location.get("ufSigla") or "").upper()
    city=str(location.get("municipioNome") or "")
    if uf not in set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split()):
        return None
    url=official_record_url(record)
    if not url: return None
    org=record.get("orgaoEntidade") or {}
    org_name=str(org.get("razaoSocial") or "") if isinstance(org,dict) else ""
    return {"title":obj[:260],"state":uf,"city":city,"organizer":org_name[:140],
            "date_hint":due.isoformat(),"date_hint_status":"pncp_deadline_unverified",
            "source_url":url,"pncp_control":record["numeroControlePNCP"],
            "review_status":"needs_edital_confirmation",
            "note":"PNCP proposal deadline is not independently verified auction start date.",
            "source":"pncp_official_api"}

def build_url(start,end,modality,page=1):
    return BASE+"?"+urllib.parse.urlencode({
        "dataInicial":start.strftime("%Y%m%d"),
        "dataFinal":end.strftime("%Y%m%d"),
        "codigoModalidadeContratacao":modality,"pagina":page,"tamanhoPagina":50
    })

def get_page(url):
    request=urllib.request.Request(url,headers={"Accept":"application/json",
        "User-Agent":"BuscaLeilao/0.5 (https://github.com/igormarianoapps/buscaleilao)"})
    with urllib.request.urlopen(request,timeout=18) as response:
        return json.loads(response.read(3_000_000))

def discover(now=None,pages_per_modality=4,fetch=get_page):
    now=now or datetime.now(timezone.utc)
    today=now.date()
    start=today-timedelta(days=45)
    candidates={}
    errors=[]
    requested=0
    for modality in MODALITIES:
        for page in range(1,pages_per_modality+1):
            url=build_url(start,today,modality,page)
            requested+=1
            try:
                response=fetch(url)
                rows=response.get("data",[])
                if not isinstance(rows,list): raise ValueError("Unexpected PNCP API response")
                for row in rows:
                    event=candidate(row,today)
                    if event:
                        candidates[event["pncp_control"]]=event
                total=response.get("totalPaginas")
                if not rows or (isinstance(total,int) and page>=total):
                    break
            except (OSError,ValueError,KeyError,TypeError) as exc:
                errors.append({"modality":modality,"page":page,"error":str(exc)[:220]})
                break
    return list(candidates.values()),errors,requested

def main():
    candidates,errors,requested=discover()
    payload={"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidates":candidates,"count":len(candidates),
        "requests":requested,"errors":errors,
        "events_automatically_published":0,
        "note":"PNCP auctions are unverified candidates, not public scheduled events."}
    OUTPUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PNCP discovery: {len(candidates)} candidate(s); {requested} request(s); {len(errors)} error(s)")

if __name__=="__main__":
    main()
