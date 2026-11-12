"""Compare independent collector runs for duplicates and unexpected churn.

Identity stability alone is insufficient: a multi-state auction can gain or
lose a state while preserving the same event ID.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def fingerprint(rows):
    """Build a sorted representation of each auction including all associated UFs."""
    groups={}
    for row in rows:
        key=(row.get("organizer"),row.get("event_id") or row.get("id"))
        info=groups.setdefault(key,{"states":set(),"details":set()})
        if row.get("state"):
            info["states"].add(row["state"])
        info["states"].update(row.get("states") or [])
        info["details"].add((
            row.get("auction_date"),row.get("auction_time"),
            row.get("source_url"),row.get("event_url")
        ))
    return {k:(tuple(sorted(v["states"])),tuple(sorted(
        (tuple("" if x is None else str(x) for x in fields) for fields in v["details"])
    ))) for k,v in groups.items()}

def compare(first,second):
    a=first.get("events",[])
    b=second.get("events",[])
    old=fingerprint(a)
    new=fingerprint(b)
    ids=[x.get("id") for x in b]
    duplicate_ids=len(ids)-len(set(ids))
    common=old.keys() & new.keys()
    changed_states=sorted(str(k) for k in common if old[k][0]!=new[k][0])
    changed_details=sorted(str(k) for k in common if old[k][1]!=new[k][1])
    return {"first_unique":len(old),"second_unique":len(new),
            "first_rows":len(a),"second_rows":len(b),
            "added":sorted(str(x) for x in new.keys()-old.keys()),
            "removed":sorted(str(x) for x in old.keys()-new.keys()),
            "changed_state_membership":changed_states,
            "changed_event_details":changed_details,
            "duplicate_ids":duplicate_ids,
            "stable":old==new and duplicate_ids==0}

def main():
    if len(sys.argv)!=3:raise SystemExit("usage: compare_collections.py BEFORE.json AFTER.json")
    before=json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    after=json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    report=compare(before,after)
    (ROOT/"app/collection-consistency.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Collection consistency:",report)
    if report["duplicate_ids"]:
        raise SystemExit("second collection produced duplicate IDs")
if __name__=="__main__":main()
