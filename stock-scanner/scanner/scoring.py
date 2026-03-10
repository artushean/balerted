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
    score += _clamp((daily_pct - 1.0) / 6.0, 0.0, 1.0) * 45
    score += _clamp((pct_15m - 0.2) / 2.8, 0.0, 1.0) * 15
    score += _clamp((vol_mult - 1.0) / 2.0, 0.0, 1.0) * 15
    score += _clamp((rel_strength + 1.0) / 6.0, 0.0, 1.0) * 15

    if is_20d_breakout:
        score += 4
    if is_52w_breakout:
        score += 4
    if above_50ma:
        score += 2

    return int(round(_clamp(score, 0.0, 100.0)))


def score_multi_signal(signal_hits: dict[str, bool], signal_weights: dict[str, int]) -> int:
    """Returns a multi-signal conviction score with bonus for confluence."""

    base = sum(signal_weights.get(name, 0) for name, active in signal_hits.items() if active)
    active_count = sum(1 for active in signal_hits.values() if active)
    confluence_bonus = max(0, active_count - 1) * 4
    return int(round(_clamp(base + confluence_bonus, 0.0, 100.0)))


def conviction_from_score(score: int) -> str:
    if score >= 85:
        return "Extreme"
    if score >= 70:
        return "High"
    if score >= 55:
        return "Medium"
    return "Low"
