"""Calendar date for auctions presented in Brazil.

All collector date cutoffs match the app's America/Sao_Paulo display
timezone instead of the runner's UTC date. UTC is retained for timestamps.
"""
from datetime import datetime
from zoneinfo import ZoneInfo

BRAZIL_TIMEZONE=ZoneInfo("America/Sao_Paulo")

def auction_today(now=None):
    """Return the current calendar day in Brasília, also for UTC-aware input."""
    if now is None:
        now=datetime.now(BRAZIL_TIMEZONE)
    if now.tzinfo is None:
        raise ValueError("auction_today requires a timezone-aware datetime")
    return now.astimezone(BRAZIL_TIMEZONE).date()
