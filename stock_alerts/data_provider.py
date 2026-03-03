from __future__ import annotations

from dataclasses import dataclass

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd


@dataclass(frozen=True)
class SymbolMetrics:
    symbol: str
    current_price: float
    daily_pct: float
    intraday_30m_pct: float
    dollar_change: float
    avg_volume_30d: float
    current_volume: float
    volume_multiplier: float
    ma20: float
    ma50: float
    above_ma20: bool
    above_ma50: bool
    rsi14: float
    atr14: float
    atr_pct: float
    daily_move_vs_atr_ratio: float
    high_52w: float
    low_52w: float
    distance_from_52w_high_pct: float
    range_position_52w_pct: float
    relative_strength_vs_spy_pct: float
    intraday_near_high: bool
    intraday_near_low: bool


class YahooFinanceProvider:
    """Fetches stock metrics from Yahoo Finance using batched downloads."""

    def fetch_metrics(self, symbols: list[str]) -> dict[str, SymbolMetrics]:
        try:
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("yfinance is not installed. Run: pip install -r requirements.txt") from exc

        all_symbols = sorted(set([*symbols, "SPY"]))
        daily = yf.download(
            tickers=all_symbols,
            period="18mo",
            interval="1d",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )
        intraday = yf.download(
            tickers=all_symbols,
            period="5d",
            interval="30m",
            group_by="ticker",
            auto_adjust=False,
            progress=False,
            threads=True,
        )

        spy_daily_pct = self._daily_pct(self._ticker_frame(intraday, "SPY"))
        results: dict[str, SymbolMetrics] = {}
        for symbol in symbols:
            dframe = self._ticker_frame(daily, symbol)
            iframe = self._ticker_frame(intraday, symbol)
            if dframe.empty or iframe.empty:
                continue
            metric = self._build_metrics(symbol, dframe, iframe, spy_daily_pct)
            if metric:
                results[symbol] = metric
        return results

    def _build_metrics(
        self,
        symbol: str,
        dframe: "pd.DataFrame",
        iframe: "pd.DataFrame",
        spy_daily_pct: float,
    ) -> SymbolMetrics | None:
        import pandas as pd

        dframe = dframe.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        iframe = iframe.dropna(subset=["Open", "High", "Low", "Close", "Volume"])
        if len(dframe) < 60 or len(iframe) < 2:
            return None

        last_row = iframe.iloc[-1]
        current_price = float(last_row["Close"])

        today = iframe.index[-1].date()
        today_intraday = iframe[iframe.index.date == today]
        if today_intraday.empty:
            return None

        open_price = float(today_intraday.iloc[0]["Open"])
        prev_30m_close = float(iframe.iloc[-2]["Close"])
        daily_pct = self._percent_change(current_price, open_price)
        intraday_30m_pct = self._percent_change(current_price, prev_30m_close)
        dollar_change = current_price - open_price

        current_volume = float(today_intraday["Volume"].sum())
        avg_volume_30d = float(dframe["Volume"].tail(30).mean())
        volume_multiplier = current_volume / avg_volume_30d if avg_volume_30d else 0.0

        closes = dframe["Close"]
        ma20 = float(closes.tail(20).mean())
        ma50 = float(closes.tail(50).mean())

        rsi14 = self._rsi(closes, period=14)
        atr14 = self._atr(dframe, period=14)
        atr_pct = (atr14 / current_price) * 100 if current_price else 0.0
        daily_move_vs_atr_ratio = abs(daily_pct) / atr_pct if atr_pct else 0.0

        trailing = dframe.tail(252)
        high_52w = float(trailing["High"].max())
        low_52w = float(trailing["Low"].min())
        distance_from_52w_high_pct = self._percent_change(current_price, high_52w)
        range_span = high_52w - low_52w
        range_position_52w_pct = ((current_price - low_52w) / range_span) * 100 if range_span else 0.0

        day_high = float(today_intraday["High"].max())
        day_low = float(today_intraday["Low"].min())
        intraday_near_high = day_high > 0 and ((day_high - current_price) / day_high) * 100 <= 1
        intraday_near_low = current_price > 0 and ((current_price - day_low) / current_price) * 100 <= 1

        relative_strength = daily_pct - spy_daily_pct

        return SymbolMetrics(
            symbol=symbol,
            current_price=current_price,
            daily_pct=daily_pct,
            intraday_30m_pct=intraday_30m_pct,
            dollar_change=dollar_change,
            avg_volume_30d=avg_volume_30d,
            current_volume=current_volume,
            volume_multiplier=volume_multiplier,
            ma20=ma20,
            ma50=ma50,
            above_ma20=current_price >= ma20,
            above_ma50=current_price >= ma50,
            rsi14=rsi14,
            atr14=atr14,
            atr_pct=atr_pct,
            daily_move_vs_atr_ratio=daily_move_vs_atr_ratio,
            high_52w=high_52w,
            low_52w=low_52w,
            distance_from_52w_high_pct=distance_from_52w_high_pct,
            range_position_52w_pct=range_position_52w_pct,
            relative_strength_vs_spy_pct=relative_strength,
            intraday_near_high=intraday_near_high,
            intraday_near_low=intraday_near_low,
        )

    @staticmethod
    def _ticker_frame(frame: "pd.DataFrame", symbol: str) -> "pd.DataFrame":
        import pandas as pd
        if frame.empty:
            return pd.DataFrame()
        if isinstance(frame.columns, pd.MultiIndex):
            if symbol not in frame.columns.levels[0]:
                return pd.DataFrame()
            out = frame[symbol].copy()
        else:
            out = frame.copy()
        out = out.sort_index()
        out.index = pd.to_datetime(out.index)
        return out

    @staticmethod
    def _percent_change(current: float, base: float) -> float:
        if not base:
            return 0.0
        return ((current - base) / base) * 100

    def _daily_pct(self, iframe: "pd.DataFrame") -> float:
        if iframe.empty or len(iframe) < 2:
            return 0.0
        today = iframe.index[-1].date()
        day_slice = iframe[iframe.index.date == today]
        if day_slice.empty:
            return 0.0
        open_price = float(day_slice.iloc[0]["Open"])
        current = float(day_slice.iloc[-1]["Close"])
        return self._percent_change(current, open_price)

    @staticmethod
    def _rsi(series: "pd.Series", period: int = 14) -> float:
        import pandas as pd
        delta = series.diff()
        gain = delta.clip(lower=0).rolling(period).mean()
        loss = (-delta.clip(upper=0)).rolling(period).mean()
        rs = gain / loss.replace(0, pd.NA)
        rsi = 100 - (100 / (1 + rs))
        value = rsi.iloc[-1]
        return float(value) if pd.notna(value) else 50.0

    @staticmethod
    def _atr(dframe: "pd.DataFrame", period: int = 14) -> float:
        import pandas as pd
        prev_close = dframe["Close"].shift(1)
        tr = pd.concat(
            [
                dframe["High"] - dframe["Low"],
                (dframe["High"] - prev_close).abs(),
                (dframe["Low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)
        atr = tr.rolling(period).mean().iloc[-1]
        return float(atr) if pd.notna(atr) else 0.0
