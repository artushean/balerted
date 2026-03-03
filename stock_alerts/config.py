from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_SYMBOLS = [
    "AAPL",
    "MSFT",
    "AMZN",
    "GOOGL",
    "META",
    "NVDA",
    "BRK-B",
    "JPM",
    "V",
    "UNH",
    "XOM",
    "PG",
    "MA",
    "HD",
    "COST",
    "LLY",
    "AVGO",
    "MRK",
    "PEP",
    "KO",
]


@dataclass(frozen=True)
class Settings:
    symbols: list[str]
    check_interval_minutes: int
    daily_move_threshold_pct: float
    short_window_minutes: int
    short_move_threshold_pct: float
    alert_email_to: str
    alert_email_from: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    load_dotenv()

    raw_symbols = os.getenv("SYMBOLS", "").strip()
    if raw_symbols:
        symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
    else:
        symbols = DEFAULT_SYMBOLS

    return Settings(
        symbols=symbols,
        check_interval_minutes=int(os.getenv("CHECK_INTERVAL_MINUTES", "30")),
        daily_move_threshold_pct=float(os.getenv("DAILY_MOVE_THRESHOLD_PCT", "5")),
        short_window_minutes=int(os.getenv("SHORT_WINDOW_MINUTES", "120")),
        short_move_threshold_pct=float(os.getenv("SHORT_MOVE_THRESHOLD_PCT", "10")),
        alert_email_to=os.getenv("ALERT_EMAIL_TO", ""),
        alert_email_from=os.getenv("ALERT_EMAIL_FROM", ""),
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_use_tls=_parse_bool(os.getenv("SMTP_USE_TLS"), default=True),
    )
