"""Turn unverified RSS news into a prioritized HUMAN-REVIEW queue.

This never promotes news headlines to verified events.
"""
import json
import re
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "app" / "discovery-candidates.json"
OUTPUT = ROOT / "app" / "review-queue.json"


MONTHS = {
    "janeiro":1, "fevereiro":2, "marco":3, "abril":4, "maio":5, "junho":6,
    "julho":7, "agosto":8, "setembro":9, "outubro":10,
    "novembro":11, "dezembro":12
}

def explicit_auction_date(headline, published):
    """Return a date only when the headline supplies enough evidence.

    This is a triage hint, NEVER an auction date for publication to the app.
    """
    import unicodedata
    from datetime import date
    title = "".join(ch for ch in unicodedata.normalize("NFKD",headline.lower())
                    if not unicodedata.combining(ch))
    m = re.search(r"\b(\d{1,2})[./-](\d{1,2})[./-](20\d{2})\b", title)
    if m:
        try:
            return date(int(m.group(3)),int(m.group(2)),int(m.group(1)))
        except ValueError:
            return None
    m = re.search(r"\b(?:dia\s+)?(\d{1,2})\s+de\s+("+"|".join(MONTHS)+r")(?:\s+de\s+(20\d{2}))?\b",title)
    if m:
        try:
            year = int(m.group(3)) if m.group(3) else published.year
            month = MONTHS[m.group(2)]
            # Publication in December for an explicitly named January event:
            # cannot assume the year without an independent document.
            if not m.group(3) and month < published.month:
                return None
            return date(year,month,int(m.group(1)))
        except ValueError:
            return None
    # "próximo dia 28" in a publication on October 19 refers to Oct 28
    # only when the publication month is unambiguous. Never guess next month.
    m = re.search(r"\b(?:proximo|neste|no)\s+dia\s+(\d{1,2})\b",title)
    if m and int(m.group(1)) >= published.day:
        try:
            return date(published.year,published.month,int(m.group(1)))
        except ValueError:
            return None
    return None

def prioritize(items, now=None):
    now = now or datetime.now(timezone.utc)
    selected = []
    for item in items:
        try:
            publication = parsedate_to_datetime(item["published"])
            if publication.tzinfo is None:
                publication = publication.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError, OverflowError, KeyError):
            continue
        if not (now - timedelta(days=75) <= publication <= now + timedelta(days=1)):
            continue
        title = item.get("title", "")
        if not re.search(r"leil[aã]o", title, re.I) or not re.search(
                r"ve[ií]cul|carro|moto|sucata|autom[oó]v", title, re.I):
            continue
        explicit = explicit_auction_date(title, publication)
        if explicit and explicit < now.date():
            continue  # Known past auction, not a current research priority.
        official = item.get("source_priority") == "official"
        # Recent press releases naming an upcoming date are good research leads.
        forward = bool(re.search(
            r"realizar[aá]|promover[aá]|acontecer[aá]|pr[oó]xim|edital|novembro|dezembro",
            title, re.I))
        score = (5 if official else 0) + (2 if forward else 0)
        score += 1 if (now - publication).days <= 21 else 0
        if explicit and explicit >= now.date():
            score += 4
        selected.append({
            "title": title, "news_url": item["url"],
            "publisher_url": item.get("publisher_url"),
            "published": item["published"],
            "priority": score,
            "date_hint":explicit.isoformat() if explicit else None,
            "date_hint_status":"headline_only_unverified" if explicit else "not_available",
            "review_status": "needs_official_event_page",
            "next_step": "Locate original notice and verify future date, location, event type and source"
        })
    selected.sort(key=lambda x: (-x["priority"], -parsedate_to_datetime(x["published"]).timestamp()))
    return selected[:80]

def merge_review_sources(news_items, pncp_items, existing_sources=None, limit=120, uncovered_states=None, portal_items=None):
    """Combine official PNCP and RSS research without treating either as events.

    Prioritize official future-dated notices and skip cases already present in
    the curated-source registry. PNCP never supplies an auction_date here.
    """
    from urllib.parse import urlsplit
    def normalize_url(url):
        p=urlsplit(url or "")
        return (p.hostname or "").lower(),p.path.rstrip("/").lower()
    known={normalize_url(s.get("source_url")) for s in (existing_sources or [])}
    merged=[]
    dedup=set()
    uncovered=set(uncovered_states or [])
    for item in pncp_items:
        url=item.get("source_url")
        if not url or normalize_url(url) in known or url in dedup:
            continue
        dedup.add(url)
        merged.append({
            "title":item.get("title","")[:260],
            "news_url":url,
            "publisher_url":"https://pncp.gov.br",
            "source_kind":"pncp",
            "state_hint":item.get("state"),
            "city_hint":item.get("city"),
            "date_hint":item.get("date_hint"),
            "date_hint_status":item.get("date_hint_status","missing_auction_date"),
            "priority":(12 if item.get("date_hint") else 9) + (5 if item.get("state") in uncovered else 0),
            "coverage_gap":item.get("state") in uncovered,
            "review_status":"needs_edital_confirmation",
            "next_step":"Check edital, actual event date, current status and official auction URL",
            "pncp_control":item.get("pncp_control")
        })
    for item in (portal_items or []):
        url=item.get("source_url")
        if not url or normalize_url(url) in known or url in dedup:
            continue
        dedup.add(url)
        state=item.get("state_hint")
        merged.append({
            "title":item.get("title","")[:260], "news_url":url,
            "publisher_url":url, "source_kind":"official_portal",
            "state_hint":state, "priority":10+(5 if state in uncovered else 0),
            "coverage_gap":state in uncovered,
            "review_status":"needs_edital_and_individual_lot_link",
            "date_hint":None, "date_hint_status":"not_verified",
            "source_registry_id":item.get("source_registry_id"),
            "next_step":"Verify event date, vehicle category, authorized auctioneer and direct lot URL"
        })
    for item in news_items:
        url=item.get("news_url")
        if not url or url in dedup:
            continue
        dedup.add(url)
        row=dict(item)
        row["source_kind"]="news_rss"
        merged.append(row)
    ranked=sorted(merged,key=lambda x:(-x.get("priority",0),
             x.get("date_hint") is None,x.get("title","")))
    # Cap each state's PNCP entries to avoid crowding out smaller states.
    result=[]
    per_state={}
    for item in ranked:
        if item.get("source_kind")=="pncp":
            state=item.get("state_hint")
            if per_state.get(state,0)>=10:
                continue
            per_state[state]=per_state.get(state,0)+1
        result.append(item)
        if len(result)>=limit:
            break
    return result

def load_current_candidates(path, now=None, max_age_hours=6):
    """Do not reuse prior run's PNCP/RSS candidates after a failed refresh.

    This does not validate auction dates. It validates research file freshness.
    """
    now=now or datetime.now(timezone.utc)
    try:
        payload=json.loads(path.read_text(encoding="utf-8"))
        stamp=datetime.fromisoformat(str(payload["checked_at"]).replace("Z","+00:00"))
        if stamp.tzinfo is None or not (timedelta(0) <= now-stamp <= timedelta(hours=max_age_hours)):
            return [],False
        candidates=payload.get("candidates",[])
        if not isinstance(candidates,list):
            return [],False
        return candidates,True
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        return [],False

def main():
    now=datetime.now(timezone.utc)
    rss_candidates, rss_fresh=load_current_candidates(INPUT,now)
    news = prioritize(rss_candidates,now)
    pncp_path = ROOT / "app" / "pncp-candidates.json"
    sources_path = ROOT / "app" / "sources.json"
    pncp, pncp_fresh=load_current_candidates(pncp_path,now)
    try:
        sources = json.loads(sources_path.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        sources = []
    report_path=ROOT / "app" / "collection-report.json"
    try:
        uncovered=json.loads(report_path.read_text(encoding="utf-8")).get("states_without_events",[])
    except (OSError,ValueError):
        uncovered=[]
    portals,portal_fresh=load_current_candidates(ROOT/"app"/"portal-candidates.json",now)
    queue=merge_review_sources(news,pncp,sources,uncovered_states=uncovered,portal_items=portals)
    output = {"checked_at":now.isoformat(timespec="seconds"),
              "rss_fresh":rss_fresh,"pncp_fresh":pncp_fresh,"portal_fresh":portal_fresh,
              "unverified_count":len(queue), "pncp_leads":sum(x["source_kind"]=="pncp" for x in queue),
              "rss_leads":sum(x["source_kind"]=="news_rss" for x in queue),
              "portal_leads":sum(x["source_kind"]=="official_portal" for x in queue),
              "pncp_gap_leads":sum(x.get("coverage_gap",False) for x in queue),
              "events_automatically_published":0, "items":queue}
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(f"Review queue: {len(queue)} unverified leads")

if __name__ == "__main__":
    main()
