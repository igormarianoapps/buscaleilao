"""Track verified collection runs for MVP P0.2 (not test-only executions).

The workflow invokes this only after feed publication and optional steps.
The history is a progress ledger, not proof that a GitHub Actions run
finished successfully: the final job conclusion must still be checked.
"""
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/"app"
HISTORY=ROOT/"collection-history.json"

def parse_stamp(text):
    value=datetime.fromisoformat(text.replace("Z","+00:00"))
    if value.tzinfo is None:
        raise ValueError("Timezone required")
    return value.astimezone(timezone.utc)

def build_history(existing, report, run_id, attempt, now=None):
    now=now or datetime.now(timezone.utc)
    checked=parse_stamp(report["checked_at"])
    if not timedelta(0)<=now-checked<=timedelta(hours=2):
        raise ValueError("Current collection report is missing or stale")
    if not isinstance(run_id,str) or not run_id.isdigit():
        raise ValueError("Real GitHub Actions run ID required")
    if not isinstance(attempt,str) or not attempt.isdigit():
        raise ValueError("Real GitHub Actions attempt required")
    if not isinstance(report.get("unique_events"),int) or report["unique_events"]<1:
        raise ValueError("Invalid event count")
    rows=[r for r in existing.get("runs",[]) if isinstance(r,dict)]
    key=(run_id,attempt)
    rows=[r for r in rows if (str(r.get("run_id")),str(r.get("attempt"))) != key]
    rows.append({
        "run_id":run_id,
        "attempt":int(attempt),
        "checked_at":report["checked_at"],
        "unique_events":report["unique_events"],
        "states_with_events":len(report.get("states_with_events",[])),
        "curated_success":report.get("curated_success"),
        "curated_failure":report.get("curated_failure"),
        "recorded_at":now.isoformat(timespec="seconds"),
        "status":"reached_final_recording_step"
    })
    rows.sort(key=lambda row:row["checked_at"])
    rows=rows[-20:]
    consecutive=0
    previous=None
    for row in rows:
        when=parse_stamp(row["checked_at"])
        if previous is None or timedelta(0)<when-previous<=timedelta(hours=24):
            consecutive+=1
        else:
            consecutive=1
        previous=when
    return {
        "note":"Runner reached final recording step; verify each GitHub Actions run conclusion=success before marking P0.2 done.",
        "consecutive_recorded_runs":consecutive,
        "requires_confirmed_workflow_success":True,
        "runs":rows
    }

def main():
    report=json.loads((ROOT/"collection-report.json").read_text(encoding="utf-8"))
    try:
        existing=json.loads(HISTORY.read_text(encoding="utf-8"))
    except (OSError,ValueError):
        existing={}
    result=build_history(existing,report,os.environ.get("GITHUB_RUN_ID",""),
                         os.environ.get("GITHUB_RUN_ATTEMPT",""),datetime.now(timezone.utc))
    HISTORY.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Collection history: {result['consecutive_recorded_runs']} recorded consecutive runs; GitHub conclusions must be verified")

if __name__=="__main__":
    main()
