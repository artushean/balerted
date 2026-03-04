from __future__ import annotations

import pandas as pd


def pct_change(current: float, previous: float) -> float:
    if not previous:
        return 0.0
    return ((current / previous) - 1.0) * 100.0


def moving_average(series: pd.Series, window: int) -> float:
    if len(series) < window:
        return float("nan")
    return float(series.tail(window).mean())


def rsi(series: pd.Series, window: int = 14) -> float:
    if len(series) < window + 1:
        return 50.0
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(window=window).mean()
    loss = (-delta.clip(upper=0)).rolling(window=window).mean()
    rs = gain / loss.replace(0, pd.NA)
    value = 100 - (100 / (1 + rs))
    latest = value.iloc[-1]
    return float(latest) if pd.notna(latest) else 50.0


def atr(df: pd.DataFrame, window: int = 14) -> float:
    if len(df) < window + 1:
        return 0.0
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high - low), (high - prev_close).abs(), (low - prev_close).abs()], axis=1).max(axis=1)
    return float(tr.rolling(window=window).mean().iloc[-1])


def volume_multiple(today_volume: float, avg_volume: float) -> float:
    if not avg_volume:
        return 0.0
    return today_volume / avg_volume
