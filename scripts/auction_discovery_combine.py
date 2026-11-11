"""Merge 16-site HTTP and public browser diagnostics; never imply verified event."""
import json
from pathlib import Path
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[1]
def aggregate(sites,http,browser):
    http_rows=http.get("platforms",{})
    browser_rows=browser.get("platforms",{})
    result={}
    for s in sites:
        key=s["id"]
        a=http_rows.get(key,{})
        b=browser_rows.get(key,{})
        reachable=a.get("status")=="reachable" or b.get("status")=="reachable"
        links={}
        for source in (a.get("candidate_events",[]),b.get("links",[])):
            for row in source:
                if row.get("source_url"):links[row["source_url"]]=row
        result[key]={"availability":"reachable" if reachable else "unavailable",
            "http_status":a.get("status","not_checked"),
            "browser_status":b.get("status","not_checked"),
            "discovered_links":len(links),
            "candidate_events":list(links.values())[:50],
            "publication_allowed":False}
    return {"checked_at":datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "total":len(sites),"reachable":sum(r["availability"]=="reachable" for r in result.values()),
            "candidate_links":sum(r["discovered_links"] for r in result.values()),
            "published":0,"platforms":result}
def main():
    def load(path,default):
        try:return json.loads((ROOT/"app"/path).read_text(encoding="utf-8"))
        except (OSError,ValueError):return default
    output=aggregate(load("auction-platforms.json",[]),
                     load("auction-platform-diagnostics.json",{}),
                     load("auction-browser-diagnostics.json",{}))
    (ROOT/"app/auction-discovery-combined.json").write_text(
        json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"16-site discovery: {output['reachable']}/{output['total']} accessible, "
          f"{output['candidate_links']} unverified links")
if __name__=="__main__":main()
