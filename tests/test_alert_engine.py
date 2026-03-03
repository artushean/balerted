from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from stock_alerts.alerts import AlertEngine
from stock_alerts.data_provider import PriceSnapshot


class AlertEngineTests(unittest.TestCase):
    def test_daily_threshold_triggers_once_per_direction(self) -> None:
        engine = AlertEngine(
            daily_move_threshold_pct=5,
            short_window_minutes=120,
            short_move_threshold_pct=10,
        )
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)

        snap1 = PriceSnapshot(symbol="AAPL", current_price=106, previous_close=100)
        events1 = engine.evaluate(snap1, now=now)
        self.assertEqual(len(events1), 1)
        self.assertEqual(events1[0].alert_type, "daily_move")

        snap2 = PriceSnapshot(symbol="AAPL", current_price=107, previous_close=100)
        events2 = engine.evaluate(snap2, now=now + timedelta(minutes=30))
        self.assertEqual(events2, [])

    def test_short_window_threshold_triggers(self) -> None:
        engine = AlertEngine(
            daily_move_threshold_pct=50,
            short_window_minutes=120,
            short_move_threshold_pct=10,
        )
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)

        first = PriceSnapshot(symbol="MSFT", current_price=100, previous_close=100)
        second = PriceSnapshot(symbol="MSFT", current_price=111, previous_close=100)

        self.assertEqual(engine.evaluate(first, now=now), [])
        events = engine.evaluate(second, now=now + timedelta(minutes=90))

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].alert_type, "short_move")
        self.assertGreaterEqual(events[0].percent_move, 10)


if __name__ == "__main__":
    unittest.main()
