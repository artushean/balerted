from __future__ import annotations

import csv
import json
import logging
import smtplib
from dataclasses import dataclass
from datetime import datetime, time
from email.message import EmailMessage
from pathlib import Path

from zoneinfo import ZoneInfo

from .config import Settings

ET = ZoneInfo("America/New_York")


@dataclass
class WatchItem:
    symbol: str
    note: str = ""


class MomentumScanner:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._daily_alert_memory: set[tuple[str, str]] = set()
        self._ensure_files()

    def _ensure_files(self) -> None:
        if not self.settings.watchlist_path.exists():
            self.settings.watchlist_path.write_text('[\n  {"symbol": "AAPL", "note": "Earnings soon"}\n]\n')
        if not self.settings.latest_data_path.exists():
            self.settings.latest_data_path.write_text("[]\n")
        if not self.settings.alerts_log_path.exists():
            with self.settings.alerts_log_path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp",
                    "symbol",
                    "daily_pct",
                    "15m_pct",
                    "volume_mult",
                    "rsi",
                    "atr_ratio",
                    "score",
                    "watchlist_flag",
                ])

    def in_market_hours(self, now: datetime | None = None) -> bool:
        t = (now or datetime.now(ET)).astimezone(ET)
        return t.weekday() < 5 and time(9, 30) <= t.time() <= time(16, 0)

    def _load_symbols(self) -> list[str]:
        def read_file(path: Path) -> list[str]:
            if not path.exists():
                return []
            return [line.strip().upper() for line in path.read_text().splitlines() if line.strip()]

        symbols = sorted(set(read_file(self.settings.medium_cap_file) + read_file(self.settings.large_cap_file)))
        return symbols[:150]

    def get_watchlist(self) -> list[WatchItem]:
        raw = json.loads(self.settings.watchlist_path.read_text() or "[]")
        return [WatchItem(symbol=item["symbol"].upper(), note=item.get("note", "")) for item in raw]

    def save_watchlist(self, items: list[WatchItem]) -> None:
        serial = [{"symbol": w.symbol.upper(), "note": w.note} for w in items]
        self.settings.watchlist_path.write_text(json.dumps(serial, indent=2) + "\n")

    def add_watch(self, symbol: str, note: str = "") -> list[WatchItem]:
        items = self.get_watchlist()
        s = symbol.upper().strip()
        if s and s not in {w.symbol for w in items}:
            items.append(WatchItem(symbol=s, note=note.strip()))
        self.save_watchlist(items)
        return items

    def remove_watch(self, symbol: str) -> list[WatchItem]:
        s = symbol.upper().strip()
        items = [w for w in self.get_watchlist() if w.symbol != s]
        self.save_watchlist(items)
        return items

    def latest(self) -> list[dict]:
        return json.loads(self.settings.latest_data_path.read_text() or "[]")

    def run_scan(self, force: bool = False) -> list[dict]:
        import pandas as pd
        import yfinance as yf
        from ta.momentum import RSIIndicator
        from ta.volatility import AverageTrueRange
        if not force and not self.in_market_hours():
            logging.info("Skipping scan outside market hours")
            return self.latest()

        symbols = self._load_symbols()
        if not symbols:
            logging.warning("No symbols loaded from medium_cap.txt and large_cap.txt")
            return []

        tickers = symbols + ["SPY"]
        daily = yf.download(" ".join(tickers), period="6mo", interval="1d", group_by="ticker", auto_adjust=False, progress=False)
        intra = yf.download(" ".join(tickers), period="2d", interval="15m", group_by="ticker", auto_adjust=False, progress=False)

        watch = {w.symbol: w.note for w in self.get_watchlist()}
        rows: list[dict] = []
        today_key = datetime.now(ET).date().isoformat()
        market_alerts: list[dict] = []
        watch_alerts: list[dict] = []

        spy_close = self._series(daily, "SPY", "Close").dropna()
        spy_return_20 = float((spy_close.iloc[-1] / spy_close.iloc[-20] - 1) * 100) if len(spy_close) >= 20 else 0.0

        yf_tickers = yf.Tickers(" ".join(symbols)).tickers

        for symbol in symbols:
            try:
                d = daily[symbol] if isinstance(daily.columns, pd.MultiIndex) else daily
                i = intra[symbol] if isinstance(intra.columns, pd.MultiIndex) else intra
                if d.empty or i.empty:
                    continue
                d = d.dropna()
                i = i.dropna()
                if len(d) < 60 or len(i) < 3:
                    continue

                close = d["Close"]
                high = d["High"]
                low = d["Low"]
                vol = d["Volume"]

                price = float(i["Close"].iloc[-1])
                open_today = float(i["Open"].iloc[-1])
                daily_pct = (price / open_today - 1) * 100 if open_today else 0.0
                pct_15m = (float(i["Close"].iloc[-1]) / float(i["Close"].iloc[-2]) - 1) * 100
                ma20 = float(close.tail(20).mean())
                ma50 = float(close.tail(50).mean())
                rsi = float(RSIIndicator(close=close, window=14).rsi().iloc[-1])
                atr = float(AverageTrueRange(high=high, low=low, close=close, window=14).average_true_range().iloc[-1])
                atr_ratio = daily_pct / (atr / price * 100) if atr > 0 and price > 0 else 0.0
                avg_vol30 = float(vol.tail(30).mean())
                volume_mult = float(i["Volume"].iloc[-1] / avg_vol30) if avg_vol30 > 0 else 0.0
                high_52w = float(high.tail(252).max())
                low_52w = float(low.tail(252).min())
                dist_52h = ((high_52w - price) / high_52w) * 100 if high_52w else 0.0
                sym_return_20 = float((close.iloc[-1] / close.iloc[-20] - 1) * 100)
                rel_strength = sym_return_20 - spy_return_20
                intraday_high = float(i["High"].tail(26).max())
                intraday_low = float(i["Low"].tail(26).min())
                intraday_pos = (price - intraday_low) / (intraday_high - intraday_low) if intraday_high > intraday_low else 0.5

                finfo = yf_tickers[symbol].fast_info
                mcap = float(finfo.get("market_cap") or 0)
                if mcap <= 10_000_000_000 or avg_vol30 <= 5_000_000:
                    continue

                score = 0
                score += 2 if abs(daily_pct) >= 5 else 0
                score += 1 if abs(pct_15m) >= 3 else 0
                score += 1 if volume_mult >= 2 else 0
                score += 1 if price > ma50 else 0
                score += 1 if dist_52h <= 2 else 0

                primary = abs(daily_pct) >= 5 or abs(pct_15m) >= 3 or volume_mult >= 2 or dist_52h <= 2
                is_watch = symbol in watch
                alert_threshold = 2 if is_watch else 3
                should_alert = primary and score >= alert_threshold

                row = {
                    "symbol": symbol,
                    "price": round(price, 2),
                    "daily_pct": round(daily_pct, 2),
                    "15m_pct": round(pct_15m, 2),
                    "ma20": round(ma20, 2),
                    "ma50": round(ma50, 2),
                    "rsi": round(rsi, 2),
                    "atr": round(atr, 2),
                    "atr_ratio": round(atr_ratio, 2),
                    "avg_volume_30d": int(avg_vol30),
                    "volume_mult": round(volume_mult, 2),
                    "high_52w": round(high_52w, 2),
                    "low_52w": round(low_52w, 2),
                    "distance_from_52w_high": round(dist_52h, 2),
                    "relative_strength_vs_spy": round(rel_strength, 2),
                    "intraday_position": round(intraday_pos, 2),
                    "score": score,
                    "watchlist": is_watch,
                    "watch_note": watch.get(symbol, ""),
                }
                rows.append(row)

                if should_alert and (symbol, today_key) not in self._daily_alert_memory:
                    self._daily_alert_memory.add((symbol, today_key))
                    (watch_alerts if is_watch else market_alerts).append(row)
                    self._append_alert_log(row)
            except Exception as exc:  # noqa: BLE001
                logging.exception("scan failure for %s: %s", symbol, exc)

        rows.sort(key=lambda x: (not x["watchlist"], -x["score"], -abs(x["daily_pct"])))
        self.settings.latest_data_path.write_text(json.dumps(rows, indent=2) + "\n")

        if market_alerts or watch_alerts:
            self._send_email(market_alerts, watch_alerts)

        return rows

    @staticmethod
    def _series(frame, symbol: str, field: str):
        if isinstance(frame.columns, pd.MultiIndex):
            return frame[symbol][field]
        return frame[field]

    def _append_alert_log(self, row: dict) -> None:
        with self.settings.alerts_log_path.open("a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.utcnow().isoformat(),
                row["symbol"],
                row["daily_pct"],
                row["15m_pct"],
                row["volume_mult"],
                row["rsi"],
                row["atr_ratio"],
                row["score"],
                row["watchlist"],
            ])

    def _send_email(self, market_alerts: list[dict], watch_alerts: list[dict]) -> None:
        if not self.settings.smtp_host or not self.settings.alert_email_from:
            logging.warning("SMTP not configured; skipping email alerts")
            return

        msg = EmailMessage()
        msg["From"] = self.settings.alert_email_from
        msg["To"] = self.settings.alert_email_to
        msg["Subject"] = (
            f"Momentum Alert – {len(market_alerts)} Market Signals | {len(watch_alerts)} Watchlist Triggers"
        )

        def lines(items: list[dict]) -> list[str]:
            out: list[str] = []
            for r in items:
                out.append(
                    f"{r['symbol']}: score={r['score']} daily={r['daily_pct']}% 15m={r['15m_pct']}% volx={r['volume_mult']} rsi={r['rsi']}"
                )
            return out or ["None"]

        body = [
            "Watchlist Triggers",
            "-------------------",
            *lines(watch_alerts),
            "",
            "Market Signals",
            "--------------",
            *lines(market_alerts),
        ]
        msg.set_content("\n".join(body))

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=20) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(msg)
