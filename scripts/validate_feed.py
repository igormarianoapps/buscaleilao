"""Fail-closed integrity gate before publishing the customer-facing auction feed."""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from auction_clock import auction_today
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STATES = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())

def validate_feed(feed, report, now=None):
    now = now or datetime.now(timezone.utc)
    errors = []
    if not isinstance(feed, dict) or not isinstance(report, dict):
        return ["Feed or report is not a JSON object"]
    rows = feed.get("events")
    if not isinstance(rows, list) or not rows:
        return ["Feed has no verified events; refuse to overwrite last valid publication"]
    stamp = feed.get("updated_at")
    try:
        updated = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if updated.tzinfo is None or not (now-timedelta(hours=2) <= updated <= now+timedelta(minutes=5)):
            errors.append("Feed timestamp missing, stale or too far in the future")
    except (AttributeError, ValueError):
        errors.append("Invalid feed updated_at")
    ids = set()
    unique = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            errors.append(f"Event {index}: not an object")
            continue
        ident = row.get("id")
        if not isinstance(ident, str) or not ident:
            errors.append(f"Event {index}: no ID")
        elif ident in ids:
            errors.append(f"Event {index}: duplicate ID {ident}")
        else:
            ids.add(ident)
        unique.add(row.get("event_id") or ident)
        try:
            when = date.fromisoformat(row.get("auction_date", ""))
            if when < auction_today(now):
                errors.append(f"Event {index}: expired date")
        except (TypeError, ValueError):
            errors.append(f"Event {index}: invalid auction date")
        state = row.get("state")
        if state not in STATES:
            errors.append(f"Event {index}: invalid state")
        associated = row.get("states")
        if associated is not None and (
                not isinstance(associated, list) or not associated or
                any(s not in STATES for s in associated) or state not in associated):
            errors.append(f"Event {index}: inconsistent multistate record")
        if not row.get("organizer") or not row.get("title"):
            errors.append(f"Event {index}: missing organizer or title")
        url = row.get("source_url") or ""
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname or parts.username or parts.password:
            errors.append(f"Event {index}: untrusted source URL")
    if report.get("verified") != len(rows):
        errors.append("Report event count disagrees with feed")
    if report.get("unique_events") != len(unique):
        errors.append("Report unique-event count disagrees with feed")
    if report.get("checked_at") != stamp:
        errors.append("Report timestamp disagrees with feed")
    return errors

def main():
    feed = json.loads((ROOT/"app/events.json").read_text(encoding="utf-8"))
    report = json.loads((ROOT/"app/collection-report.json").read_text(encoding="utf-8"))
    errors = validate_feed(feed, report)
    if errors:
        for message in errors[:25]:
            print("INVALID FEED:", message, file=sys.stderr)
        raise SystemExit(1)
    print(f"Feed integrity OK: {report['unique_events']} unique events, {report['verified']} records")

if __name__ == "__main__":
    main()
