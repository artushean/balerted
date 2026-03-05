from __future__ import annotations


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def score_signal(
    daily_pct: float,
    pct_15m: float,
    is_20d_breakout: bool,
    is_52w_breakout: bool,
    vol_mult: float,
    rel_strength: float,
    above_50ma: bool,
) -> int:
    """Returns a 0-100 momentum score."""

    score = 0.0

    # 45 points from 1-day momentum centered around 3% threshold.
    score += _clamp((daily_pct - 1.0) / 6.0, 0.0, 1.0) * 45

    # 15 points from latest 15m acceleration.
    score += _clamp((pct_15m - 0.2) / 2.8, 0.0, 1.0) * 15

    # 15 points from volume confirmation.
    score += _clamp((vol_mult - 1.0) / 2.0, 0.0, 1.0) * 15

    # 15 points from relative strength vs SPY.
    score += _clamp((rel_strength + 1.0) / 6.0, 0.0, 1.0) * 15

    # Structure and trend quality.
    if is_20d_breakout:
        score += 4
    if is_52w_breakout:
        score += 4
    if above_50ma:
        score += 2

    return int(round(_clamp(score, 0.0, 100.0)))


def conviction_from_score(score: int) -> str:
    if score >= 85:
        return "Extreme"
    if score >= 70:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"
