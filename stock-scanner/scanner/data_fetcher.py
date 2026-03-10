from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd
import yfinance as yf


@dataclass
class StockData:
    symbol: str
    intraday_15m: pd.DataFrame
    daily_6m: pd.DataFrame
    daily_5d: pd.DataFrame
    info: dict
    insider_transactions: pd.DataFrame | None
    earnings_date: datetime | None


class DataFetcher:
    """Fetches market data with fault tolerance for batch scans."""

    def fetch_spy_5d(self) -> pd.DataFrame:
        return yf.download("SPY", period="10d", interval="1d", progress=False, auto_adjust=False)

    def fetch_symbol(self, symbol: str) -> StockData | None:
        try:
            ticker = yf.Ticker(symbol)
            intraday = yf.download(symbol, period="1d", interval="15m", progress=False, auto_adjust=False)
            daily_6m = yf.download(symbol, period="6mo", interval="1d", progress=False, auto_adjust=False)
            daily_5d = yf.download(symbol, period="10d", interval="1d", progress=False, auto_adjust=False)
            info = ticker.info or {}
            insider_transactions = ticker.insider_transactions
            earnings_date = _extract_earnings_date(ticker.calendar)
        except Exception:
            return None

        if intraday.empty or daily_6m.empty or daily_5d.empty:
            return None

        return StockData(
            symbol=symbol,
            intraday_15m=intraday,
            daily_6m=daily_6m,
            daily_5d=daily_5d,
            info=info,
            insider_transactions=insider_transactions,
            earnings_date=earnings_date,
        )


def _extract_earnings_date(calendar: pd.DataFrame | dict | None) -> datetime | None:
    if calendar is None:
        return None

    if isinstance(calendar, dict):
        candidate = calendar.get("Earnings Date")
        if isinstance(candidate, list) and candidate:
            candidate = candidate[0]
        if isinstance(candidate, pd.Timestamp):
            return candidate.to_pydatetime()
        if isinstance(candidate, datetime):
            return candidate
        return None

    if isinstance(calendar, pd.DataFrame) and not calendar.empty:
        first_value = calendar.iloc[0, 0]
        if isinstance(first_value, pd.Timestamp):
            return first_value.to_pydatetime()
        if isinstance(first_value, datetime):
            return first_value

    return None


def load_symbols(
    large_cap_path: str,
    medium_cap_path: str,
    watchlist_path: str | None = None,
    sp500_path: str | None = None,
    max_symbols: int = 500,
) -> tuple[list[str], set[str]]:
    def read_lines(path: str | None) -> list[str]:
        if not path:
            return []
        with open(path, "r", encoding="utf-8") as f:
            return [line.strip().upper() for line in f if line.strip()]

    base_symbols = read_lines(sp500_path) if sp500_path else []
    if not base_symbols:
        base_symbols = read_lines(large_cap_path) + read_lines(medium_cap_path)

    symbols = set(base_symbols[:max_symbols])
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
