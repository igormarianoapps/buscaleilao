"""BuscaLeilão MVP: events-first API, without any fabricated auctions."""
import os
import sqlite3
from datetime import date
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse

DB_PATH = Path(os.environ.get("DATABASE_PATH", "data/auctions.sqlite3"))
app = FastAPI(title="BuscaLeilão", version="0.1.0")


def get_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS auctions (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, state TEXT NOT NULL,
        city TEXT NOT NULL, auction_date TEXT NOT NULL, auction_time TEXT,
        vehicle_count INTEGER, organizer TEXT NOT NULL, source_url TEXT NOT NULL,
        source_type TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'scheduled',
        last_checked_at TEXT)""")
    return db


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/auctions")
def auctions(state: str | None = Query(default=None, min_length=2, max_length=2),
             day: date | None = None):
    filters = ["status = 'scheduled'", "auction_date >= :today"]
    params = {"today": date.today().isoformat()}
    if state:
        filters.append("state = :state")
        params["state"] = state.upper()
    if day:
        filters.append("auction_date = :day")
        params["day"] = day.isoformat()
    with get_db() as db:
        rows = db.execute("SELECT * FROM auctions WHERE " + " AND ".join(filters) +
                          " ORDER BY auction_date, auction_time, city", params).fetchall()
    return {"count": len(rows), "auctions": [dict(row) for row in rows]}


@app.get("/")
def home():
    return FileResponse(Path(__file__).with_name("index.html"))
