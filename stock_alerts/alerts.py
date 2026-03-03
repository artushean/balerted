from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .data_provider import SymbolMetrics

EASTERN = ZoneInfo("America/New_York")


@dataclass(frozen=True)
class AlertRecord:
    symbol: str
    categories: tuple[str, ...]
    score: int
    tag: str
    triggered_at: datetime
    metrics: SymbolMetrics


class AlertEngine:
    def __init__(
        self,
        daily_move_threshold_pct: float,
        intraday_move_threshold_pct: float,
        high_volume_threshold: float,
        quality_volume_threshold: float,
        relative_strength_threshold_pct: float,
        score_threshold: int,
        csv_log_path: str,
    ) -> None:
        self.daily_move_threshold_pct = daily_move_threshold_pct
        self.intraday_move_threshold_pct = intraday_move_threshold_pct
        self.high_volume_threshold = high_volume_threshold
        self.quality_volume_threshold = quality_volume_threshold
        self.relative_strength_threshold_pct = relative_strength_threshold_pct
        self.score_threshold = score_threshold
        self.csv_log_path = Path(csv_log_path)

        self._sent_categories: set[tuple[date, str, str]] = set()
        self._last_reset_day: date | None = None

    def reset_for_new_day_if_needed(self, now_et: datetime) -> None:
        market_day = now_et.date()
        if self._last_reset_day is None:
            self._last_reset_day = market_day
            return
        if market_day != self._last_reset_day:
            self._sent_categories.clear()
            self._last_reset_day = market_day

    def evaluate(self, metrics_by_symbol: dict[str, SymbolMetrics], now: datetime | None = None) -> list[AlertRecord]:
        now_utc = now or datetime.now(timezone.utc)
        day_key = now_utc.astimezone(EASTERN).date()
        alerts: list[AlertRecord] = []

        for symbol, metrics in metrics_by_symbol.items():
            categories = self._triggered_categories(metrics)
            if not categories:
                continue
            if not self._passes_quality_filter(metrics):
                continue

            score = self._score(metrics)
            if score < self.score_threshold:
                continue

            unsent = [c for c in categories if (day_key, symbol, c) not in self._sent_categories]
            if not unsent:
                continue

            for category in unsent:
                self._sent_categories.add((day_key, symbol, category))

            record = AlertRecord(
                symbol=symbol,
                categories=tuple(unsent),
                score=score,
                tag=self._build_tag(metrics),
                triggered_at=now_utc,
                metrics=metrics,
            )
            alerts.append(record)
            self._append_csv(record)

        return alerts

    def _triggered_categories(self, metrics: SymbolMetrics) -> list[str]:
        categories: list[str] = []
        if abs(metrics.daily_pct) >= self.daily_move_threshold_pct:
            categories.append("daily_move")
        if abs(metrics.intraday_30m_pct) >= self.intraday_move_threshold_pct:
            categories.append("intraday_30m")
        if metrics.volume_multiplier >= self.high_volume_threshold:
            categories.append("volume_surge")
        if metrics.distance_from_52w_high_pct >= -2:
            categories.append("near_52w_high")
        if metrics.rsi14 > 70 or metrics.rsi14 < 30:
            categories.append("rsi_extreme")
        return categories

    def _passes_quality_filter(self, metrics: SymbolMetrics) -> bool:
        bullish = metrics.daily_pct >= 0
        bearish = metrics.daily_pct < 0
        return (
            metrics.volume_multiplier >= self.quality_volume_threshold
            or (bullish and metrics.above_ma50)
            or (bearish and not metrics.above_ma50)
        )

    def _score(self, metrics: SymbolMetrics) -> int:
        score = 0
        if abs(metrics.daily_pct) >= self.daily_move_threshold_pct:
            score += 2
        if abs(metrics.intraday_30m_pct) >= self.intraday_move_threshold_pct:
            score += 1
        if metrics.volume_multiplier >= self.high_volume_threshold:
            score += 1
        if metrics.above_ma50:
            score += 1
        if metrics.distance_from_52w_high_pct >= -2:
            score += 1
        return score

    def _build_tag(self, metrics: SymbolMetrics) -> str:
        if metrics.daily_pct > 0 and metrics.volume_multiplier >= 2 and metrics.above_ma50:
            return "Strong Bullish Momentum"
        if abs(metrics.daily_move_vs_atr_ratio) >= 1.5:
            return "Volatility Expansion"
        if metrics.distance_from_52w_high_pct >= -2 and metrics.above_ma20:
            return "Breakout Watch"
        if metrics.daily_pct < 0 and metrics.rsi14 < 30:
            return "Weak Structure – Oversold"
        return "Momentum Watch"

    def _append_csv(self, record: AlertRecord) -> None:
        self.csv_log_path.parent.mkdir(parents=True, exist_ok=True)
        is_new = not self.csv_log_path.exists()
        with self.csv_log_path.open("a", newline="", encoding="utf-8") as fp:
            writer = csv.writer(fp)
            if is_new:
                writer.writerow(
                    [
                        "timestamp_utc",
                        "symbol",
                        "alert_type",
                        "daily_pct",
                        "volume_multiplier",
                        "rsi14",
                        "distance_from_52w_high_pct",
                    ]
                )
            writer.writerow(
                [
                    record.triggered_at.isoformat(),
                    record.symbol,
                    "|".join(record.categories),
                    f"{record.metrics.daily_pct:.2f}",
                    f"{record.metrics.volume_multiplier:.2f}",
                    f"{record.metrics.rsi14:.2f}",
                    f"{record.metrics.distance_from_52w_high_pct:.2f}",
                ]
            )
