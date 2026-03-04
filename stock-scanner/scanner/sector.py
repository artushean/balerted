from __future__ import annotations

import yfinance as yf

from .relative_strength import five_day_change

SECTOR_ETFS = ["XLK", "XLF", "XLI", "XLE", "XLV", "XLY", "XLP", "XLB", "XLU", "XLRE", "XLC"]


def fetch_sector_momentum() -> list[dict]:
    rows: list[dict] = []
    for etf in SECTOR_ETFS:
        try:
            data = yf.download(etf, period="10d", interval="1d", progress=False, auto_adjust=False)
            if data.empty:
                continue
            weekly_pct = five_day_change(data["Close"])
            rows.append({"sector": etf, "weekly_pct": round(weekly_pct, 2)})
        except Exception:
            continue
    return sorted(rows, key=lambda x: x["weekly_pct"], reverse=True)
