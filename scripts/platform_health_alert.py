"""Collector health report for all 16 sources. Never changes public events.

A single inaccessible site is a warning, not a reason to discard valid
auction data. Severe drops in source coverage are explicit, not silent.
"""
import json,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def assess(platforms,combined,quality,feed,now=None):
    now=now or datetime.now(timezone.utc)
    sites=combined.get("platforms",{})
    verified=quality.get("per_platform",{})
    warnings=[]
    status={}
    for p in platforms:
        name=p["id"]
        row=sites.get(name,{})
        approved=verified.get(name,{})
        accessible=row.get("availability")=="reachable"
        events=approved.get("verified_events",0)
        status[name]={"reachable":accessible,"verified_events":events,
                      "candidates":row.get("discovered_links",0)}
        if not accessible:warnings.append(f"{name}: no authorized public connection")
        if not approved:warnings.append(f"{name}: no per-platform audit found")
    stamp=feed.get("updated_at")
    freshness=None
    try:
        when=datetime.fromisoformat(str(stamp).replace("Z","+00:00"))
        freshness=when.tzinfo is not None and timedelta(0)<=now-when<=timedelta(hours=2)
    except (ValueError,TypeError):
        freshness=False
    if not freshness:warnings.append("last validated feed is missing or stale")
    unique=len({e.get("event_id") or e.get("id") for e in feed.get("events",[])})
    if not unique:warnings.append("feed has no confirmed events")
    if len(sites)!=len(platforms):warnings.append("not all 16 sources have discovery results")
    return {"checked_at":now.isoformat(timespec="seconds"),
            "total_sources":len(platforms),
            "sources_reachable":sum(x["reachable"] for x in status.values()),
            "sources_with_events":sum(x["verified_events"]>0 for x in status.values()),
            "unique_feed_events":unique,
            "feed_fresh":freshness,"warning_count":len(warnings),
            "warnings":warnings,"sources":status}
def main():
    def load(name,fallback):
        try:return json.loads((ROOT/"app"/name).read_text(encoding="utf-8"))
        except (OSError,ValueError):return fallback
    data=assess(load("auction-platforms.json",[]),
        load("auction-discovery-combined.json",{}),
        load("platform-quality.json",{}),
        load("events.json",{}))
    path=ROOT/"app/platform-health-alert.json"
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Platform health: {data['sources_reachable']}/{data['total_sources']} reachable, "
        f"{data['sources_with_events']} with events; {data['warning_count']} warnings")
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as file:
            file.write(f"\n## Saúde das 16 plataformas\n\n"
                f"- Acessíveis: {data['sources_reachable']}/{data['total_sources']}\n"
                f"- Com eventos confirmados: {data['sources_with_events']}/{data['total_sources']}\n"
                f"- Eventos distintos: {data['unique_feed_events']}\n"
                f"- Alertas: {data['warning_count']}\n")
            for warning in data["warnings"][:16]:
                file.write(f"  - {warning}\n")
if __name__=="__main__":main()
