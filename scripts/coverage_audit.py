"""Coverage reporting is descriptive, not a claim of national completeness."""
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
STATES=set("AC AL AP AM BA CE DF ES GO MA MT MS MG PA PB PR PE PI RJ RN RS RO RR SC SP SE TO".split())

def audit(feed, registry, queue=None, portal=None):
    events=feed.get("events",[])
    identities=set()
    organizer_counts=Counter()
    state_counts=Counter()
    host_counts=Counter()
    for event in events:
        identity=(event.get("organizer"),event.get("event_id") or event.get("id"))
        if identity in identities:
            continue  # Multistate feed rows for one event must not inflate coverage.
        identities.add(identity)
        organizer_counts[event.get("organizer","unknown")]+=1
        host=urlsplit(event.get("event_url") or event.get("source_url") or "").hostname
        if host: host_counts[host]+=1
        for state in set(event.get("states") or [event.get("state")]):
            if state in STATES:
                state_counts[state]+=1
    region_states={r["state"] for r in registry if r.get("state") in STATES}
    statuses=(portal or {}).get("source_statuses",[])
    lead_items=(queue or {}).get("items",[])
    return {
        "snapshot_checked_at":feed.get("updated_at"),
        "unique_events":len(identities),
        "event_rows":len(events),
        "states_with_events":sorted(state_counts),
        "states_without_events":sorted(STATES-set(state_counts)),
        "events_by_state":dict(sorted(state_counts.items())),
        "events_by_organizer":dict(sorted(organizer_counts.items())),
        "rows_by_destination_host":dict(sorted(host_counts.items())),
        "source_registry_total":len(registry),
        "registry_states":sorted(region_states),
        "registry_sources_checked":len(statuses),
        "registry_sources_reachable":sum(s.get("status")=="ok" for s in statuses),
        "unverified_portal_leads":(portal or {}).get("candidates_count",0),
        "review_queue_items":len(lead_items),
        "coverage_definition":"States with >=1 distinct event, not percentage of national auctions; registry entries are research sources, not active collectors or verified events",
    }

def main():
    def load(name, fallback):
        try:
            return json.loads((ROOT/"app"/name).read_text(encoding="utf-8"))
        except (OSError,ValueError):
            return fallback
    report=audit(load("events.json",{"events":[]}),
                 load("portal-sources.json",[]),
                 load("review-queue.json",{}),
                 load("portal-candidates.json",{}))
    report["generated_at"]=datetime.now(timezone.utc).isoformat(timespec="seconds")
    (ROOT/"app/coverage-audit.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Coverage audit: {report['unique_events']} events; "
          f"{len(report['states_with_events'])} states; "
          f"{report['unverified_portal_leads']} new portal leads")
if __name__=="__main__":
    main()
