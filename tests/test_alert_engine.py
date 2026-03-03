from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timezone

from stock_alerts.alerts import AlertEngine
from stock_alerts.data_provider import SymbolMetrics


def sample_metrics(**overrides: float | bool | str) -> SymbolMetrics:
    base = dict(
        symbol="AAPL",
        current_price=105.0,
        daily_pct=6.0,
        intraday_30m_pct=3.2,
        dollar_change=5.0,
        avg_volume_30d=1_000_000.0,
        current_volume=2_200_000.0,
        volume_multiplier=2.2,
        ma20=100.0,
        ma50=99.0,
        above_ma20=True,
        above_ma50=True,
        rsi14=72.0,
        atr14=2.0,
        atr_pct=1.9,
        daily_move_vs_atr_ratio=3.15,
        high_52w=107.0,
        low_52w=70.0,
        distance_from_52w_high_pct=-1.9,
        range_position_52w_pct=94.0,
        relative_strength_vs_spy_pct=3.5,
        intraday_near_high=True,
        intraday_near_low=False,
    )
    base.update(overrides)
    return SymbolMetrics(**base)


class AlertEngineTests(unittest.TestCase):
    def test_alert_triggers_once_per_category_per_day(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            engine = AlertEngine(5, 3, 2, 1.5, 3, 3, f"{td}/alerts.csv")
            now = datetime(2025, 1, 1, tzinfo=timezone.utc)
            metrics = {"AAPL": sample_metrics()}

            first = engine.evaluate(metrics, now=now)
            second = engine.evaluate(metrics, now=now)

            self.assertEqual(len(first), 1)
            self.assertEqual(second, [])

    def test_quality_filter_blocks_weak_signal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            engine = AlertEngine(5, 3, 2, 1.5, 3, 3, f"{td}/alerts.csv")
            weak = sample_metrics(
                daily_pct=5.5,
                intraday_30m_pct=3.5,
                volume_multiplier=1.2,
                above_ma50=False,
                distance_from_52w_high_pct=-5.0,
            )
            alerts = engine.evaluate({"AAPL": weak}, now=datetime(2025, 1, 1, tzinfo=timezone.utc))
            self.assertEqual(alerts, [])


if __name__ == "__main__":
    unittest.main()
