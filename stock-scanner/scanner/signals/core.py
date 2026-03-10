from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..breakout import breakout_52w
from ..indicators import rsi

TOP_MOVER_THRESHOLD = 4.5
UNUSUAL_VOLUME_THRESHOLD = 2.5
SHORT_INTEREST_THRESHOLD = 0.15
EARNINGS_WINNER_THRESHOLD = 6.0
REVENUE_GROWTH_THRESHOLD = 0.20
SMALL_CAP_THRESHOLD = 2_000_000_000
SMALL_CAP_MOMENTUM_THRESHOLD = 5.0

SIGNAL_WEIGHTS = {
    "top_movers": 8,
    "breakouts": 8,
    "unusual_volume": 10,
    "insider_buying": 9,
    "short_squeeze": 10,
    "earnings_winners": 9,
    "high_revenue_growth": 7,
    "institutional_buying": 8,
    "rsi_reversals": 6,
    "small_cap_momentum": 8,
}


def detect_top_mover(daily_pct: float, threshold: float = TOP_MOVER_THRESHOLD) -> bool:
    return abs(daily_pct) >= threshold


def detect_52_week_breakout(price: float, highs: pd.Series) -> bool:
    return breakout_52w(price, highs)


def detect_unusual_volume(current_volume: float, volume: pd.Series, threshold: float = UNUSUAL_VOLUME_THRESHOLD) -> bool:
    avg20 = float(volume.tail(20).mean()) if len(volume) >= 20 else 0.0
    avg50 = float(volume.tail(50).mean()) if len(volume) >= 50 else 0.0
    base = max(avg20, avg50)
    if base <= 0:
        return False
    return (current_volume / base) >= threshold


def detect_insider_buying(insider_transactions: pd.DataFrame | None) -> bool:
    if insider_transactions is None or insider_transactions.empty:
        return False

    frame = insider_transactions.copy()
    cols = {c.lower(): c for c in frame.columns}
    shares_col = cols.get("shares") or cols.get("shares traded")
    text_col = cols.get("text") or cols.get("transaction")

    if shares_col and shares_col in frame:
        positive = pd.to_numeric(frame[shares_col], errors="coerce").fillna(0) > 0
        if positive.any():
            return True

    if text_col and text_col in frame:
        return frame[text_col].astype(str).str.contains("buy", case=False, na=False).any()

    return False


def detect_short_squeeze_candidate(daily_pct: float, unusual_volume: bool, info: dict) -> bool:
    short_interest = float(info.get("shortPercentOfFloat") or info.get("shortRatio") or 0.0)
    return short_interest >= SHORT_INTEREST_THRESHOLD and daily_pct > 0 and unusual_volume


def detect_earnings_winner(daily_pct: float, unusual_volume: bool, earnings_date: datetime | None) -> bool:
    if not earnings_date:
        return False
    days_since_earnings = abs((datetime.utcnow().date() - earnings_date.date()).days)
    return days_since_earnings <= 3 and daily_pct >= EARNINGS_WINNER_THRESHOLD and unusual_volume


def detect_high_revenue_growth(info: dict, threshold: float = REVENUE_GROWTH_THRESHOLD) -> bool:
    growth = info.get("revenueGrowth")
    if growth is None:
        return False
    try:
        return float(growth) >= threshold
    except (TypeError, ValueError):
        return False


def detect_institutional_buying(daily_pct: float, unusual_volume: bool, close: pd.Series) -> bool:
    if close.empty:
        return False
    ma20 = float(close.tail(20).mean()) if len(close) >= 20 else float(close.mean())
    return daily_pct >= 3.0 and unusual_volume and float(close.iloc[-1]) >= ma20


def detect_rsi_oversold_reversal(close: pd.Series) -> bool:
    if len(close) < 20:
        return False
    prev_rsi = rsi(close.iloc[:-1], 14)
    curr_rsi = rsi(close, 14)
    if prev_rsi != prev_rsi or curr_rsi != curr_rsi:
        return False
    return prev_rsi < 30 <= curr_rsi


def detect_small_cap_momentum(daily_pct: float, info: dict) -> bool:
    market_cap = info.get("marketCap")
    if market_cap is None:
        return False
    try:
        return float(market_cap) < SMALL_CAP_THRESHOLD and daily_pct >= SMALL_CAP_MOMENTUM_THRESHOLD
    except (TypeError, ValueError):
        return False


def evaluate_signals(
    *,
    price: float,
    daily_pct: float,
    close: pd.Series,
    highs: pd.Series,
    volume: pd.Series,
    current_volume: float,
    info: dict,
    insider_transactions: pd.DataFrame | None,
    earnings_date: datetime | None,
) -> dict[str, bool]:
    unusual_volume = detect_unusual_volume(current_volume, volume)

    return {
        "top_movers": detect_top_mover(daily_pct),
        "breakouts": detect_52_week_breakout(price, highs),
        "unusual_volume": unusual_volume,
        "insider_buying": detect_insider_buying(insider_transactions),
        "short_squeeze": detect_short_squeeze_candidate(daily_pct, unusual_volume, info),
        "earnings_winners": detect_earnings_winner(daily_pct, unusual_volume, earnings_date),
        "high_revenue_growth": detect_high_revenue_growth(info),
        "institutional_buying": detect_institutional_buying(daily_pct, unusual_volume, close),
        "rsi_reversals": detect_rsi_oversold_reversal(close),
        "small_cap_momentum": detect_small_cap_momentum(daily_pct, info),
    }
