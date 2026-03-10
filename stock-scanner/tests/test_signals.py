from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from datetime import datetime, timedelta

import pandas as pd

from scanner.scoring import score_multi_signal
from scanner.signals.core import (
    SIGNAL_WEIGHTS,
    detect_earnings_winner,
    detect_high_revenue_growth,
    detect_rsi_oversold_reversal,
    detect_short_squeeze_candidate,
    detect_small_cap_momentum,
    detect_top_mover,
    detect_unusual_volume,
    evaluate_signals,
)


def test_detect_top_mover_and_unusual_volume():
    volume = pd.Series([100] * 50)
    assert detect_top_mover(5.1)
    assert detect_unusual_volume(260, volume)


def test_detect_fundamental_signals():
    assert detect_high_revenue_growth({"revenueGrowth": 0.25})
    assert detect_small_cap_momentum(5.2, {"marketCap": 1_500_000_000})
    assert detect_short_squeeze_candidate(4.2, True, {"shortPercentOfFloat": 0.2})


def test_detect_earnings_winner_and_rsi_reversal():
    earnings = datetime.utcnow() - timedelta(days=1)
    assert detect_earnings_winner(6.5, True, earnings)

    closes = pd.Series([100] * 20 + [95, 90, 85, 82, 80, 79, 78, 82, 86, 90])
    assert detect_rsi_oversold_reversal(closes)


def test_evaluate_signals_and_scoring_confluence():
    closes = pd.Series([100] * 45 + [96, 94, 92, 90, 92, 95, 98])
    highs = pd.Series([100] * 252)
    volume = pd.Series([100] * 50)

    hits = evaluate_signals(
        price=101,
        daily_pct=6.2,
        close=closes,
        highs=highs,
        volume=volume,
        current_volume=300,
        info={"marketCap": 1_000_000_000, "revenueGrowth": 0.30, "shortPercentOfFloat": 0.21},
        insider_transactions=pd.DataFrame({"Shares": [1000]}),
        earnings_date=datetime.utcnow() - timedelta(days=1),
    )

    assert hits["top_movers"]
    assert hits["breakouts"]
    assert hits["unusual_volume"]
    assert hits["insider_buying"]

    score = score_multi_signal(hits, SIGNAL_WEIGHTS)
    assert score > 0
