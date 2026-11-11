"""Per-platform audit: evidence, counts and honest integration status.

Report distinguishes a monitored URL, a vehicle lead, and an independently
admitted event. Multi-state rows share one event identity.
"""
import json
from collections import Counter
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
def audit(sites,diagnostics,triage,feed,quarantine,report):
    rows=feed.get("events",[])
    errors=report.get("failed",[])
    result={"generated_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "feed_checked_at":feed.get("updated_at"),
        "platforms_total":len(sites),"per_platform":{},
        "disclaimer":"A monitored domain does not prove auctioneer legitimacy. An admitted event requires specific URL and evidence. Zero verified events may be legitimate."}
    for site in sites:
        ident=site["id"]
        hosts=set(site.get("allowed_hosts",[]))
        verified=set()
        states=set()
        for e in rows:
            try:host=urlsplit(e.get("event_url") or e.get("source_url") or "").hostname
            except ValueError:host=None
            if host not in hosts:continue
            if e.get("link_verified") is not True or e.get("destination_verified") is not True:
                continue
            verified.add((e.get("organizer"),e.get("event_id") or e.get("id")))
            states.update(e.get("states") or [e.get("state")])
        diag=diagnostics.get("platforms",{}).get(ident,{})
        tri=triage.get("platforms",{}).get(ident,{})
        adapter_error=[str(x.get("error",""))[:150] for x in errors if
            str(x.get("id","")).lower().startswith(ident)]
        quarantine_count=sum(1 for x in quarantine.get("quarantined",[]) if
            str(x.get("id","")).lower().startswith(ident))
        availability=diag.get("status","not_checked")
        status=("verified_events" if verified else
                "access_limited" if availability=="unreachable" else
                "monitoring_no_verified_vehicle_event")
        result["per_platform"][ident]={
            "name":site["name"],"batch":site["batch"],"availability":availability,
            "integration_status":status,"verified_events":len(verified),
            "states_with_verified_events":sorted(s for s in states if s),
            "unverified_leads":tri.get("candidates_total",diag.get("candidate_count",0)),
            "vehicle_candidates":tri.get("vehicle_candidates",0),
            "lot_only_candidates":tri.get("individual_lot_only",0),
            "quarantined":quarantine_count,
            "sample_errors":adapter_error[:5],
            "source_error":diag.get("error"),
            "checked_at":diagnostics.get("checked_at"),
        }
    result["platforms_with_verified_events"]=sum(bool(x["verified_events"]) for x in result["per_platform"].values())
    result["platforms_reachable"]=sum(x["availability"]=="reachable" for x in result["per_platform"].values())
    result["total_verified_events_from_nominated_platforms"]=sum(x["verified_events"] for x in result["per_platform"].values())
    return result
def main():
    def load(filename,fallback):
        try:return json.loads((ROOT/"app"/filename).read_text(encoding="utf-8"))
        except (OSError,ValueError):return fallback
    result=audit(load("auction-platforms.json",[]),
                 load("auction-platform-diagnostics.json",{}),
                 load("platform-triage.json",{}),
                 load("events.json",{}),
                 load("quarantine-report.json",{}),
                 load("collection-report.json",{}))
    path=ROOT/"app/platform-quality.json"
    path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Platform quality: {result['platforms_with_verified_events']}/{result['platforms_total']} sites with admitted events")
if __name__=="__main__":main()
