from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import pandas as pd
import yfinance as yf


@dataclass
class StockData:
    symbol: str
    intraday_15m: pd.DataFrame
    daily_6m: pd.DataFrame
    daily_5d: pd.DataFrame


class DataFetcher:
    """Fetches market data with fault tolerance for batch scans."""

    def fetch_spy_5d(self) -> pd.DataFrame:
        return yf.download("SPY", period="10d", interval="1d", progress=False, auto_adjust=False)

    def fetch_symbol(self, symbol: str) -> StockData | None:
        try:
            intraday = yf.download(symbol, period="1d", interval="15m", progress=False, auto_adjust=False)
            daily_6m = yf.download(symbol, period="6mo", interval="1d", progress=False, auto_adjust=False)
            daily_5d = yf.download(symbol, period="10d", interval="1d", progress=False, auto_adjust=False)
        except Exception:
            return None

        if intraday.empty or daily_6m.empty or daily_5d.empty:
            return None

        return StockData(symbol=symbol, intraday_15m=intraday, daily_6m=daily_6m, daily_5d=daily_5d)


def load_symbols(large_cap_path: str, medium_cap_path: str, watchlist_path: str | None = None) -> tuple[list[str], set[str]]:
    def read_lines(path: str) -> list[str]:
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip().upper() for line in f if line.strip()]

    symbols = set(read_lines(large_cap_path) + read_lines(medium_cap_path))
    watchlist: set[str] = set()

    if watchlist_path:
        try:
            import json

            with open(watchlist_path, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    if isinstance(item, str):
                        watchlist.add(item.upper())
                    elif isinstance(item, dict) and item.get("symbol"):
                        watchlist.add(str(item["symbol"]).upper())
        except Exception:
            pass

    return sorted(symbols), watchlist
