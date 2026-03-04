from __future__ import annotations


def score_signal(
    daily_pct: float,
    pct_15m: float,
    is_20d_breakout: bool,
    is_52w_breakout: bool,
    vol_mult: float,
    rel_strength: float,
    above_50ma: bool,
) -> int:
    score = 0
    score += 2 if daily_pct >= 5 else 0
    score += 1 if pct_15m >= 3 else 0
    score += 2 if is_20d_breakout else 0
    score += 3 if is_52w_breakout else 0
    score += 1 if vol_mult >= 2 else 0
    score += 2 if rel_strength > 3 else 0
    score -= 1 if rel_strength < -3 else 0
    score += 1 if above_50ma else 0
    return score


def conviction_from_score(score: int) -> str:
    if score >= 6:
        return "Extreme"
    if score >= 4:
        return "High"
    if score >= 3:
        return "Medium"
    return "Low"
