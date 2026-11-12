"""Compare independent collector runs for duplicates and unexpected churn.

A small change in live auctions is expected and reported, never silently
rewritten as zero. Feed validation remains responsible for URL approval.
"""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def compare(first,second):
    a=first.get("events",[])
    b=second.get("events",[])
    def identity(row):return (row.get("organizer"),row.get("event_id") or row.get("id"))
    old={identity(x) for x in a}
    new={identity(x) for x in b}
    ids=[x.get("id") for x in b]
    duplicate_ids=len(ids)-len(set(ids))
    return {"first_unique":len(old),"second_unique":len(new),
            "added":sorted(str(x) for x in new-old),
            "removed":sorted(str(x) for x in old-new),
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
