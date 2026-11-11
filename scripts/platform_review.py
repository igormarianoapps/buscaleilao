"""Review queue for the 16 auction sites. Never produces public events."""
import json
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def build(triage,now=None):
    now=now or datetime.now(timezone.utc)
    result=[]
    for ident,site in sorted(triage.get("platforms",{}).items()):
        recorded=0
        for c in site.get("candidates",[]):
            if c.get("url_kind") in ("individual_lot_not_auction","generic_category_not_auction"):
                continue
            if c.get("category_hint")=="non_vehicle":
                continue
            if recorded>=8:break
            result.append({
                "platform_id":ident,"title":c.get("title",""),
                "source_url":c.get("source_url",""),"category_hint":c.get("category_hint"),
                "date_hint":c.get("date_hint"),
                "state_hint":c.get("state_hint_verified_from_event"),
                "status":"pending_manual_or_adapter_validation",
                "review_reasons":c.get("review_reasons",[]),
                "next_step":"Check first-party event status, exact date, vehicle lots, actual state and authorized auctioneer; never auto-publish this research lead"})
            recorded+=1
    return {"generated_at":now.isoformat(timespec="seconds"),
            "candidates_count":len(result),"events_automatically_published":0,
            "items":result}
def main():
    p=json.loads((ROOT/"app/platform-triage.json").read_text(encoding="utf-8"))
    report=build(p)
    (ROOT/"app/platform-review-queue.json").write_text(
        json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Platform review: {report['candidates_count']} event candidates, 0 published")
if __name__=="__main__":main()
