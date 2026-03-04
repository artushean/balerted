from __future__ import annotations

from .indicators import pct_change


def five_day_change(close_series) -> float:
    if len(close_series) < 6:
        return 0.0
    return pct_change(float(close_series.iloc[-1]), float(close_series.iloc[-6]))


def relative_strength(stock_5d: float, spy_5d: float) -> float:
    return stock_5d - spy_5d
