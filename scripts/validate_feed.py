"""Fail-closed integrity gate before publishing the customer-facing auction feed."""
import json
import sys
from datetime import date, datetime, timedelta, timezone
from auction_clock import auction_today
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
STATES = set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())

def verify_link_classification(row):
    """Check that link labels describe URL shape, not assumed browser access."""
    from browser_collect import copart_detail_url, vip_detail_url, COPART_URL, VIP_URL
    kind=row.get("source_link_type")
    if kind not in (None,"event","calendar"):
        return "unknown link type"
    if kind is None:
        return None  # Curated official articles/documents have no such label.
    url=row.get("source_url") or ""
    org=row.get("organizer")
    if kind=="event":
        if org=="Copart":
            if copart_detail_url(url,row.get("auction_date")) is None:
                return "Copart event label requires a matching sale ID and date"
        elif org=="VIP Leilões":
            if vip_detail_url(url) is None:
                return "VIP event label requires an official individual event URL"
        elif org=="Detran MG":
            from mg_detran_collect import detail_identity
            if detail_identity(url) is None or row.get("date_kind")!="closing":
                return "Detran MG requires a direct official lot link"
        elif org in ("Vardana Leilões","Claudio Kuss Leilões"):
            from regional_collect import strict_url
            site="vardana" if org=="Vardana Leilões" else "claudio"
            if not strict_url(site,url):
                return "Regional auction needs a specific first-party lot page"
        elif org=="Bolsa de Leilões":
            from bolsa_collect import detail_id
            if detail_id(url) is None:
                return "Bolsa de Leilões requires an individual event URL"
        elif org=="Leilo":
            from leilo_collect import event_slug
            if event_slug(url) is None:
                return "Leilo requires a first-party lot-bearing edition page"
        elif org in ("Parque dos Leilões","Flex Leilões","Hisa Leilões"):
            from secondary_collect import trusted_url
            site={"Parque dos Leilões":"parque","Flex Leilões":"flex",
                  "Hisa Leilões":"hisa"}[org]
            if not trusted_url(site,url):
                return "Auction platform requires its own direct lot/event URL"
        elif org=="PMKLog":
            from pmklog_collect import event_id
            if event_id(url) is None:
                return "PMKLog requires a first-party individual edition"
        elif org=="Palácio dos Leilões":
            from palacio_collect import auction_id
            if auction_id(url) is None:
                return "Palácio requires first-party numbered event and lot page"
        else:
            return "event link classification has no verified adapter"
    else:
        if org=="Copart" and url.rstrip("/")!=COPART_URL.rstrip("/"):
            return "Copart calendar link must point to known official calendar"
        if org=="VIP Leilões" and url.rstrip("/")!=VIP_URL.rstrip("/"):
            return "VIP calendar link must point to known official calendar"
        if org not in ("Copart","VIP Leilões"):
            return "calendar link classification has no verified adapter"
    return None

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
        from auction_security import valid_destination
        if row.get('destination_verified') is not True or not valid_destination(row):
            errors.append(f'Event {index}: destination failed approval gate')
        from auction_links import destination_status
        allowed, reason = destination_status(row)
        if not allowed or row.get("link_verified") is not True:
            errors.append(f"Event {index}: destination not admitted: {reason}")
        link_issue=verify_link_classification(row)
        if link_issue:
            errors.append(f"Event {index}: {link_issue}")
        event_url = row.get("event_url")
        if event_url is not None and (not allowed or not row.get("link_verified")):
            errors.append(f"Event {index}: unverified auction destination")
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
