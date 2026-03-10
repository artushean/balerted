from __future__ import annotations

from datetime import datetime, timezone

from .breakout import breakout_20d, breakout_52w, distance_to_52w_high
from .data_fetcher import DataFetcher, load_symbols
from .indicators import atr, moving_average, pct_change, rsi, volume_multiple
from .relative_strength import five_day_change, relative_strength
from .scoring import conviction_from_score, score_multi_signal, score_signal
from .sector import fetch_sector_momentum
from .signals import evaluate_signals
from .signals.core import SIGNAL_WEIGHTS


MOMENTUM_MOVE_THRESHOLD = 3.0


class ScanEngine:
    def __init__(
        self,
        large_cap_path: str,
        medium_cap_path: str,
        watchlist_path: str | None = None,
        sp500_path: str | None = None,
    ) -> None:
        self.large_cap_path = large_cap_path
        self.medium_cap_path = medium_cap_path
        self.watchlist_path = watchlist_path
        self.sp500_path = sp500_path
        self.fetcher = DataFetcher()

    def run(self) -> dict:
        symbols, watchlist = load_symbols(
            self.large_cap_path,
            self.medium_cap_path,
            self.watchlist_path,
            sp500_path=self.sp500_path,
            max_symbols=500,
        )
        spy = self.fetcher.fetch_spy_5d()
        spy_5d = five_day_change(spy["Close"]) if not spy.empty else 0.0

        alerts: list[dict] = []
        signal_buckets: dict[str, list[dict]] = {name: [] for name in SIGNAL_WEIGHTS}

        for symbol in symbols:
            data = self.fetcher.fetch_symbol(symbol)
            if data is None:
                continue

            try:
                intraday = data.intraday_15m
                daily = data.daily_6m
                close = daily["Close"]
                highs = daily["High"]
                volume = daily["Volume"]

                if len(intraday) < 2 or len(daily) < 60:
                    continue

                price = float(intraday["Close"].iloc[-1])
                daily_pct = pct_change(float(intraday["Close"].iloc[-1]), float(intraday["Open"].iloc[0]))
                pct_15m = pct_change(float(intraday["Close"].iloc[-1]), float(intraday["Close"].iloc[-2]))
                stock_5d = five_day_change(data.daily_5d["Close"])
                rel = relative_strength(stock_5d, spy_5d)
                ma50 = moving_average(close, 50)
                rsi14 = rsi(close, 14)
                atr14 = atr(daily, 14)
                is_20 = breakout_20d(price, highs)
                is_52 = breakout_52w(price, highs)
                avg30 = float(volume.tail(30).mean()) if len(volume) >= 30 else 0.0
                current_volume = float(intraday["Volume"].sum())
                vol_mult = volume_multiple(current_volume, avg30)
                dist_52 = distance_to_52w_high(price, highs)
                above_50ma = price > ma50 if ma50 == ma50 else False

                momentum_score = score_signal(daily_pct, pct_15m, is_20, is_52, vol_mult, rel, above_50ma)

                signal_hits = evaluate_signals(
                    price=price,
                    daily_pct=daily_pct,
                    close=close,
                    highs=highs,
                    volume=volume,
                    current_volume=current_volume,
                    info=data.info,
                    insider_transactions=data.insider_transactions,
                    earnings_date=data.earnings_date,
                )
                multi_signal_score = score_multi_signal(signal_hits, SIGNAL_WEIGHTS)
                conviction_score = min(100, momentum_score + multi_signal_score)
                conviction = conviction_from_score(conviction_score)

                has_3pct_momentum = daily_pct >= MOMENTUM_MOVE_THRESHOLD or pct_15m >= MOMENTUM_MOVE_THRESHOLD
                has_any_signal = any(signal_hits.values())
                if ((not has_3pct_momentum and symbol not in watchlist) or momentum_score < 40) and not has_any_signal:
                    continue

                active_categories = [name for name, active in signal_hits.items() if active]
                alert = {
                    "symbol": symbol,
                    "price": round(price, 2),
                    "daily_pct": round(daily_pct, 2),
                    "15m_pct": round(pct_15m, 2),
                    "stock_5d": round(stock_5d, 2),
                    "spy_5d": round(spy_5d, 2),
                    "relative_strength": round(rel, 2),
                    "volume_mult": round(vol_mult, 2),
                    "rsi": round(rsi14, 2),
                    "atr": round(atr14, 2),
                    "breakout_20d": is_20,
                    "breakout_52w": is_52,
                    "distance_to_52w_high": round(dist_52, 2),
                    "conviction": conviction,
                    "score": conviction_score,
                    "momentum_score": momentum_score,
                    "multi_signal_score": multi_signal_score,
                    "conviction_score": conviction_score,
                    "watchlist": symbol in watchlist,
                    "signal_categories": active_categories,
                    "signal_hits": signal_hits,
                }
                alerts.append(alert)

                for category in active_categories:
                    signal_buckets[category].append(
                        {
                            "symbol": symbol,
                            "price": round(price, 2),
                            "daily_pct": round(daily_pct, 2),
                            "volume_mult": round(vol_mult, 2),
                            "conviction_score": conviction_score,
                            "momentum_score": momentum_score,
                            "multi_signal_score": multi_signal_score,
                        }
                    )
            except Exception:
                continue

        alerts.sort(key=lambda x: -x["conviction_score"])
        for key in signal_buckets:
            signal_buckets[key].sort(key=lambda x: -x["conviction_score"])

        return {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_alerts": len(alerts),
            "scan_universe": len(symbols),
            "momentum_threshold_pct": MOMENTUM_MOVE_THRESHOLD,
            "alerts": alerts,
            "signals": signal_buckets,
            "sector_momentum": fetch_sector_momentum(),
        }
