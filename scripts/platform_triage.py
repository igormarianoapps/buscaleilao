"""Evidence-based per-platform candidate triage. NO candidate is auto-approved.

All fields come from the candidate's visible label or first-party direct URL,
not from the auctioneer headquarters, nor from a fabricated date.
"""
import json,re,unicodedata
from datetime import date,datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
STATES=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())
NONVEHICLES=re.compile(r"\b(?:imoveis?|apartamentos?|terrenos?|galpoes?|eletrodomesticos?|eletronicos?|geladeiras?|refrigeradores?|fogoes?|moveis?|mobiliario|aeronaves?|pneus|vestuario|joias)\b")
VEHICLES=re.compile(r"\b(?:veiculos?|automoveis?|carros?|motos?|motocicletas?|caminhoes?|onibus|caminhonetes?|frotas?)\b")
DATE_BR=re.compile(r"\b(\d{2})/(\d{2})/(20\d{2})\b")
DATETIME_BR=re.compile(r"\b(\d{2})/(\d{2})/(20\d{2})\s+(?:às|as|-\s*)\s*(\d{1,2})[:h](\d{2})")
UF_IN_LOCATION=re.compile(r"\b(?:[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s-]{2,45})\s*[,/-]\s*([A-Z]{2})\b")
DIRECT={
    "parque":r"/leilao/[0-9]{1,10}/detalhes/?",
    "flex":r"/lotes/[0-9]{1,10}/?",
    "hisa":r"/leilao/[0-9]{1,10}/?",
    "bolsa":r"/leilao/[0-9]{1,10}/?",
    "vardana":r"/vardana/veiculos\.php",
    "claudio":r"/relacao-(?:foto|lista)/[0-9]{1,10}/?",
    "leilo":r"/leilao/evento/[a-z0-9-]+/?",
    "vip":r"/evento/detalhes/[a-z0-9_-]+/?",
    "copart":r"/saleListResult/[0-9]+/20[0-9]{2}-[0-9]{2}-[0-9]{2}/?",
    "freitas":r"/Leiloes/Lotes",
}
def normalize(value):
    x=unicodedata.normalize("NFD",str(value or "")).casefold()
    return "".join(c for c in x if not unicodedata.combining(c))
def classify(row,site,today=None):
    today=today or date.today()
    raw=row.get("title","")
    normalized=normalize(raw)
    url=row.get("source_url") or ""
    p=urlsplit(url)
    hosts=set(site.get("allowed_hosts",[]))
    if p.scheme!="https" or p.hostname not in hosts or p.username or p.password or p.fragment:
        return None
    if not re.fullmatch(DIRECT.get(site["id"],r"(?!)"),p.path,re.I) or (
        site["id"] not in ("vardana","freitas") and p.query):
        url_kind="not_direct_event"
    elif site["id"]=="leilo":
        # Recurring event pages need corroboration of that *edition* and its lots.
        url_kind="recurring_event_needs_edition"
    else:
        url_kind="candidate_direct"
    if row.get("candidate_kind")=="individual_lot":
        url_kind="individual_lot_not_auction"
    if row.get("candidate_kind")=="generic_category":
        url_kind="generic_category_not_auction"
    has_vehicle=bool(VEHICLES.search(normalized))
    has_nonvehicle=bool(NONVEHICLES.search(normalized))
    category="vehicle" if has_vehicle and not has_nonvehicle else (
        "non_vehicle" if has_nonvehicle else "unknown")
    match=DATE_BR.search(raw)
    date_hint=None
    if match:
        try:
            val=date(int(match.group(3)),int(match.group(2)),int(match.group(1)))
            if val>=today:date_hint=val.isoformat()
        except ValueError:pass
    hour=None
    dt=DATETIME_BR.search(normalized)
    if dt and date_hint:
        h,m=int(dt.group(4)),int(dt.group(5))
        if h<24 and m<60:hour=f"{h:02}:{m:02}"
    # Only an explicit city / UF near listing title counts; platform HQ is not evidence.
    uf=None
    for found in UF_IN_LOCATION.finditer(raw):
        if found.group(1).lower().strip() not in ("leilao",):
            candidate=found.group(1)
            if candidate in STATES:uf=candidate
    reasons=[]
    if category!="vehicle":reasons.append("vehicle_category_not_confirmed")
    if not date_hint:reasons.append("event_date_unverified_or_expired")
    if url_kind!="candidate_direct":reasons.append(url_kind)
    if not uf:reasons.append("event_location_unverified")
    reasons.append("requires_live_lot_page_and_auctioneer_identity_verification")
    return {
        "platform_id":site["id"],"title":raw[:180],"source_url":url,
        "category_hint":category,"date_hint":date_hint,"time_hint":hour,
        "state_hint_verified_from_event":uf,"url_kind":url_kind,
        "status":"needs_review","review_reasons":reasons,
        "published":False
    }
def summarize(sites,diagnostics,today=None):
    result={"generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "platforms_total":len(sites),"events_automatically_published":0,"platforms":{}}
    for site in sites:
        raw=diagnostics.get("platforms",{}).get(site["id"],{})
        found=[x for row in raw.get("candidate_events",[])
               if (x:=classify(row,site,today=today))]
        result["platforms"][site["id"]]={
            "name":site["name"],"batch":site["batch"],
            "access_status":raw.get("status","not_checked"),
            "access_error":raw.get("error"),
            "candidates_total":len(found),
            "vehicle_candidates":sum(x["category_hint"]=="vehicle" for x in found),
            "dated_vehicle_candidates":sum(x["category_hint"]=="vehicle" and x["date_hint"] is not None for x in found),
            "individual_lot_only":sum(x["url_kind"]=="individual_lot_not_auction" for x in found),
            "not_vehicle":sum(x["category_hint"]=="non_vehicle" for x in found),
            "candidates":found
        }
    return result
def main():
    sites=json.loads((ROOT/"app/auction-platforms.json").read_text(encoding="utf-8"))
    diagnostic=json.loads((ROOT/"app/auction-platform-diagnostics.json").read_text(encoding="utf-8"))
    payload=summarize(sites,diagnostic)
    (ROOT/"app/platform-triage.json").write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Platform triage:",len(sites),"sources,",
          sum(x["vehicle_candidates"] for x in payload["platforms"].values()),"vehicle candidates, 0 published")
if __name__=="__main__":main()
