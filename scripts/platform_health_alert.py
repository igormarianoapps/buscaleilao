"""Operational health classification for the 17 sources and validated feed.

Do not mistake 0 events for parser failure, or old feed for newly verified data.
Warnings never authorize publication of stale/unverified events.
"""
import json,os
from datetime import datetime,timezone,timedelta
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def _iso(value):
    try:
        dt=datetime.fromisoformat(str(value).replace("Z","+00:00"))
        return dt.astimezone(timezone.utc) if dt.tzinfo else None
    except (ValueError,TypeError,OverflowError):
        return None

def assess(platforms,combined,quality,feed,now=None,previous=None):
    now=now or datetime.now(timezone.utc)
    previous=previous or {}
    sites=combined.get("platforms",{})
    verified=quality.get("per_platform",{})
    previous_sources=previous.get("sources",{})
    warnings=[]
    status={}
    for p in platforms:
        name=p["id"]
        row=sites.get(name,{})
        approved=verified.get(name,{})
        available=row.get("availability")
        accessible=available=="reachable"
        events=approved.get("verified_events",0)
        candidates=row.get("discovered_links",0)
        last=previous_sources.get(name,{})
        last_events=last.get("verified_events")
        if name not in sites:
            condition="not_checked"
        elif not accessible:
            condition="blocked_or_unavailable"
        elif name not in verified:
            condition="audit_missing"
        elif events>0:
            condition="verified_events"
        elif candidates>0:
            condition="candidates_unverified"
        else:
            condition="reachable_no_verified_events"
        status[name]={"reachable":accessible,"verified_events":events,
                      "candidates":candidates,"condition":condition}
        if not accessible:
            warnings.append(f"{name}: unavailable or access restricted")
        if name not in verified:
            warnings.append(f"{name}: no per-platform audit found")
        if isinstance(last_events,int) and last_events>0 and events==0:
            warnings.append(f"{name}: lost all {last_events} previously verified events")
        if isinstance(last_events,int) and last_events>=5 and events < last_events*0.5:
            warnings.append(f"{name}: large drop from {last_events} to {events} verified events")
    stamp=feed.get("updated_at")
    when=_iso(stamp)
    fresh=bool(when and timedelta(0)<=now.astimezone(timezone.utc)-when<=timedelta(hours=2))
    if not fresh:
        warnings.append("last validated feed is missing or stale")
    unique=len({e.get("event_id") or e.get("id") for e in feed.get("events",[])})
    if not unique:
        warnings.append("feed has no confirmed events")
    previous_unique=previous.get("unique_feed_events")
    if isinstance(previous_unique,int) and previous_unique>=10 and unique<previous_unique*.5:
        warnings.append(f"feed event count dropped sharply: {previous_unique} to {unique}")
    if len(sites)!=len(platforms):
        warnings.append("not all registered sources have discovery results")
    return {"checked_at":now.isoformat(timespec="seconds"),
            "total_sources":len(platforms),
            "sources_reachable":sum(x["reachable"] for x in status.values()),
            "sources_with_events":sum(x["verified_events"]>0 for x in status.values()),
            "unique_feed_events":unique,
            "feed_fresh":fresh,"feed_status":"current" if fresh else "stale_or_unavailable",
            "warning_count":len(warnings),"warnings":warnings,"sources":status}

def main():
    def load(name,fallback):
        try:return json.loads((ROOT/"app"/name).read_text(encoding="utf-8"))
        except (OSError,ValueError):return fallback
    old=load("platform-health-alert.json",{})
    data=assess(load("auction-platforms.json",[]),
        load("auction-discovery-combined.json",{}),
        load("platform-quality.json",{}),
        load("events.json",{}),previous=old)
    path=ROOT/"app/platform-health-alert.json"
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Platform health: {data['sources_reachable']}/{data['total_sources']} reachable, "
        f"{data['sources_with_events']} with events; {data['warning_count']} warnings")
    summary=os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary,"a",encoding="utf-8") as file:
            file.write(f"\n## Saúde dos coletores\n\n"
                f"- Fontes acessíveis: {data['sources_reachable']}/{data['total_sources']}\n"
                f"- Fontes com eventos: {data['sources_with_events']}/{data['total_sources']}\n"
                f"- Eventos únicos: {data['unique_feed_events']}\n"
                f"- Feed: {data['feed_status']}\n"
                f"- Alertas: {data['warning_count']}\n")
            for warning in data["warnings"][:25]:
                file.write(f"  - {warning}\n")

if __name__=="__main__":main()
