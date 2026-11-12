"""Auditable 17-platform integration matrix (not a proof of complete market coverage).

Distinguish accessible websites from working event collectors. A zero-event
source must never be advertised as integrated without a validated event.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Explicit blockers are operational research notes, not claims of permanent outage.
BLOCKERS = {
    "mcleilao": "SPA exposes no verifiable public dated individual auction in current discovery",
    "flex": "Vehicle lots and schedule found, but event-specific vehicle location not corroborated",
    "parque": "Mixed categories: require a vehicle-only event with date, site and lots",
    "sodre": "Public links found are primarily category searches, not specific auctions; some detail access denied",
    "loop": "HTTP 429; respect source rate limit and seek authorized data access",
    "milan": "HTTP 403; seek authorized public export, API or permission",
    "hisa": "Observed candidates include non-vehicles; individual details may return HTTP 403",
    "claudio": "Candidate lot detail not proven to have published vehicles for active edition",
    "palacio": "Dated card labels are not enough; event detail must corroborate full year, lot list and lot location",
    "rogerio": "No verifiable individual vehicle event discovered in public index",
    "pmklog": "Most recent known Detran-GO edition ended; new edition needs its own date and lot evidence",
}

def assess(sites, quality, feed, combined, evidence=None, checked_at=None):
    quality_by = quality.get("per_platform", {})
    known = combined.get("platforms", {})
    evidence_by = (evidence or {}).get("platforms", {})
    rows = []
    for site in sites:
        key = site["id"]
        q = quality_by.get(key, {})
        discovery = known.get(key, {})
        proof = evidence_by.get(key, {})
        count = q.get("verified_events", 0)
        access = discovery.get("availability", "not_checked")
        leads = discovery.get("discovered_links", 0)
        if count > 0:
            state = "events_verified"
            blocker = None
        elif access == "unavailable":
            state = "access_limited"
            blocker = BLOCKERS.get(key, "Public source inaccessible; no verified auction")
        elif access == "not_checked" or key not in quality_by:
            state = "not_checked"
            blocker = "Missing current source diagnostics"
        elif leads:
            state = "candidates_not_verified"
            blocker = BLOCKERS.get(key, "Candidates lack required event-specific evidence")
        else:
            state = "no_verified_event"
            blocker = BLOCKERS.get(key, "No active vehicle event confirmed by this adapter")
        rows.append({
            "id": key, "name": site["name"],
            "state": state, "access": access,
            "verified_events": count, "candidate_links": leads,
            "detail_pages_scanned": proof.get("sites_scanned", 0),
            "detail_pages_extracted": proof.get("extracted", 0),
            "blocker": blocker,
            "source_error": q.get("source_error"),
            "approved_for_publication": count > 0,
        })
    return {
        "generated_at": checked_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feed_checked_at": feed.get("updated_at"),
        "sites_total": len(sites),
        "sites_diagnosed": sum(row["state"] != "not_checked" for row in rows),
        "sites_with_verified_events": sum(row["verified_events"] > 0 for row in rows),
        "sites_with_no_verified_events": sum(row["verified_events"] == 0 for row in rows),
        "full_integration_complete": all(row["state"] == "events_verified" for row in rows),
        "priority_four": ["flex", "parque", "palacio", "hisa"],
        "priority_four_verified": sum(row["state"] == "events_verified" and row["id"] in ("flex", "parque", "palacio", "hisa") for row in rows),
        "priority_four_complete": all(any(row["id"] == key and row["state"] == "events_verified" for row in rows) for key in ("flex", "parque", "palacio", "hisa")),
        "event_count_unique": len({event.get("event_id") or event.get("id")
                                  for event in feed.get("events", [])}),
        "note": "No events can mean no active vehicle auctions, missing evidence, or blocked access. Site monitoring is not event extraction.",
        "sources": rows
    }

def main():
    def load(name, default):
        try:
            return json.loads((ROOT / "app" / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return default
    report = assess(
        load("auction-platforms.json", []),
        load("platform-quality.json", {}),
        load("events.json", {}),
        load("auction-discovery-combined.json", {}),
        load("auction-event-evidence.json", {}),
    )
    if report["sites_total"] != 17 or report["sites_diagnosed"] != 17:
        raise SystemExit("Coverage audit incomplete: not all 17 sources diagnosed")
    target = ROOT / "app" / "platform-coverage-gate.json"
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Coverage gate: {report['sites_with_verified_events']}/17 verified, "
          f"{report['sites_diagnosed']}/17 diagnosed; full integration="
          f"{report['full_integration_complete']}")

if __name__ == "__main__":
    main()
