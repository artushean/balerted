from __future__ import annotations

import pandas as pd


def breakout_20d(price: float, highs: pd.Series) -> bool:
    if len(highs) < 20:
        return False
    prior_20_high = float(highs.tail(20).iloc[:-1].max())
    return price >= prior_20_high


def breakout_52w(price: float, highs: pd.Series) -> bool:
    if len(highs) < 252:
        return False
    prior_52w_high = float(highs.tail(252).iloc[:-1].max())
    return price >= prior_52w_high


def distance_to_52w_high(price: float, highs: pd.Series) -> float:
    if highs.empty:
        return 0.0
    high_52w = float(highs.tail(252).max())
    if not high_52w:
        return 0.0
    return ((high_52w - price) / high_52w) * 100
