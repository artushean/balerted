from __future__ import annotations

from .indicators import pct_change


def _to_float(v):
    """Convert pandas scalar/Series to float safely."""
    try:
        return float(v)
    except TypeError:
        return float(v.iloc[0])


def five_day_change(close_series) -> float:
    if len(close_series) < 6:
        return 0.0

    latest = _to_float(close_series.iloc[-1])
    past = _to_float(close_series.iloc[-6])

    return pct_change(latest, past)


def relative_strength(stock_5d: float, spy_5d: float) -> float:
    return stock_5d - spy_5d
