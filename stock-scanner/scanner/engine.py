from __future__ import annotations

from datetime import datetime, timezone

from .breakout import breakout_20d, breakout_52w, distance_to_52w_high
from .data_fetcher import DataFetcher, load_symbols
from .indicators import atr, moving_average, pct_change, rsi, volume_multiple
from .relative_strength import five_day_change, relative_strength
from .scoring import conviction_from_score, score_signal
from .sector import fetch_sector_momentum


class ScanEngine:
    def __init__(self, large_cap_path: str, medium_cap_path: str, watchlist_path: str | None = None) -> None:
        self.large_cap_path = large_cap_path
        self.medium_cap_path = medium_cap_path
        self.watchlist_path = watchlist_path
        self.fetcher = DataFetcher()

    def run(self) -> dict:
        symbols, watchlist = load_symbols(self.large_cap_path, self.medium_cap_path, self.watchlist_path)
        spy = self.fetcher.fetch_spy_5d()
        spy_5d = five_day_change(spy["Close"]) if not spy.empty else 0.0

        alerts: list[dict] = []

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
                vol_mult = volume_multiple(float(intraday["Volume"].sum()), avg30)
                dist_52 = distance_to_52w_high(price, highs)
                above_50ma = price > ma50 if ma50 == ma50 else False

                score = score_signal(daily_pct, pct_15m, is_20, is_52, vol_mult, rel, above_50ma)
                conviction = conviction_from_score(score)

                if score < 3 and symbol not in watchlist:
                    continue

                alerts.append(
                    {
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
                        "score": score,
                        "watchlist": symbol in watchlist,
                    }
                )
            except Exception:
                continue

        alerts.sort(key=lambda x: (x["conviction"] != "Extreme", -x["score"], -x["daily_pct"]))

        return {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "total_alerts": len(alerts),
            "alerts": alerts,
            "sector_momentum": fetch_sector_momentum(),
        }
