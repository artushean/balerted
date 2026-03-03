from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PriceSnapshot:
    symbol: str
    current_price: float
    previous_close: float


class YahooFinanceProvider:
    """Fetches quote info from Yahoo Finance."""

    def get_snapshot(self, symbol: str) -> PriceSnapshot:
        try:
            import yfinance as yf
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "yfinance is not installed. Run: pip install -r requirements.txt"
            ) from exc

        ticker = yf.Ticker(symbol)
        info = ticker.fast_info

        current = float(info["last_price"])
        previous_close = float(info["previous_close"])

        return PriceSnapshot(symbol=symbol, current_price=current, previous_close=previous_close)
