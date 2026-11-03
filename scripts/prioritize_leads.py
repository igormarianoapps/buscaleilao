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
        official = item.get("source_priority") == "official"
        # Recent press releases naming an upcoming date are good research leads.
        forward = bool(re.search(
            r"realizar[aá]|promover[aá]|acontecer[aá]|pr[oó]xim|edital|novembro|dezembro",
            title, re.I))
        score = (5 if official else 0) + (2 if forward else 0)
        score += 1 if (now - publication).days <= 21 else 0
        selected.append({
            "title": title, "news_url": item["url"],
            "publisher_url": item.get("publisher_url"),
            "published": item["published"],
            "priority": score,
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
