from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .data_provider import PriceSnapshot


@dataclass(frozen=True)
class AlertEvent:
    symbol: str
    alert_type: str
    percent_move: float
    details: str
    triggered_at: datetime


class AlertEngine:
    def __init__(
        self,
        daily_move_threshold_pct: float,
        short_window_minutes: int,
        short_move_threshold_pct: float,
    ) -> None:
        self.daily_move_threshold_pct = daily_move_threshold_pct
        self.short_window_minutes = short_window_minutes
        self.short_move_threshold_pct = short_move_threshold_pct

        self._history: dict[str, list[tuple[datetime, float]]] = defaultdict(list)
        self._sent_keys: set[tuple[str, str, str]] = set()

    def evaluate(self, snapshot: PriceSnapshot, now: datetime | None = None) -> list[AlertEvent]:
        timestamp = now or datetime.now(timezone.utc)
        symbol = snapshot.symbol

        self._history[symbol].append((timestamp, snapshot.current_price))
        self._prune_history(symbol=symbol, now=timestamp)

        events: list[AlertEvent] = []

        daily_pct = self._percent_change(snapshot.current_price, snapshot.previous_close)
        if abs(daily_pct) >= self.daily_move_threshold_pct:
            key = (symbol, "daily", self._daily_direction_key(daily_pct))
            if key not in self._sent_keys:
                events.append(
                    AlertEvent(
                        symbol=symbol,
                        alert_type="daily_move",
                        percent_move=daily_pct,
                        details=f"Daily move reached {daily_pct:+.2f}% vs previous close.",
                        triggered_at=timestamp,
                    )
                )
                self._sent_keys.add(key)

        short_pct = self._short_window_percent_move(symbol=symbol)
        if short_pct is not None and abs(short_pct) >= self.short_move_threshold_pct:
            direction = "up" if short_pct > 0 else "down"
            key = (symbol, "short", direction)
            if key not in self._sent_keys:
                events.append(
                    AlertEvent(
                        symbol=symbol,
                        alert_type="short_move",
                        percent_move=short_pct,
                        details=(
                            f"Short-window move reached {short_pct:+.2f}% over "
                            f"{self.short_window_minutes} minutes."
                        ),
                        triggered_at=timestamp,
                    )
                )
                self._sent_keys.add(key)

        return events

    @staticmethod
    def _percent_change(current: float, base: float) -> float:
        if base == 0:
            return 0.0
        return ((current - base) / base) * 100

    def _short_window_percent_move(self, symbol: str) -> float | None:
        history = self._history.get(symbol, [])
        if len(history) < 2:
            return None
        first_price = history[0][1]
        last_price = history[-1][1]
        return self._percent_change(last_price, first_price)

    def _prune_history(self, symbol: str, now: datetime) -> None:
        cutoff = now - timedelta(minutes=self.short_window_minutes)
        self._history[symbol] = [(ts, price) for ts, price in self._history[symbol] if ts >= cutoff]

    @staticmethod
    def _daily_direction_key(move_pct: float) -> str:
        return "up" if move_pct > 0 else "down"
