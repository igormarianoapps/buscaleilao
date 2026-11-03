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

def main():
    payload = json.loads(INPUT.read_text(encoding="utf-8"))
    queue = prioritize(payload.get("candidates", []))
    output = {"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "unverified_count":len(queue), "events_automatically_published":0,
              "items":queue}
    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2)+"\n",encoding="utf-8")
    print(f"Review queue: {len(queue)} unverified leads")

if __name__ == "__main__":
    main()
