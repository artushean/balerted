from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


DEFAULT_SYMBOLS = [
    "AAPL","MSFT","AMZN","GOOGL","GOOG","META","NVDA","TSLA","BRK-B","UNH",
    "JNJ","JPM","V","PG","XOM","MA","HD","CVX","MRK","ABBV",
    "PEP","AVGO","KO","COST","ADBE","WMT","BAC","MCD","CSCO","CRM",
    "ACN","PFE","ABT","LIN","TMO","DHR","NFLX","DIS","TXN","AMD",
    "INTC","CMCSA","ORCL","QCOM","NKE","UPS","PM","HON","UNP","MS",
    "LOW","SBUX","GS","CAT","AMAT","IBM","GE","INTU","BKNG","ISRG",
    "SPGI","BLK","RTX","GILD","LMT","ELV","MDLZ","PLD","AXP","DE",
    "ADP","TJX","SYK","VRTX","MMC","CB","SO","SCHW","C","MU",
    "TMUS","CI","FISV","BDX","ZTS","MO","CSX","CL","EQIX","APD",
]


@dataclass(frozen=True)
class Settings:
    symbols: list[str]
    check_interval_minutes: int
    daily_move_threshold_pct: float
    intraday_move_threshold_pct: float
    high_volume_threshold: float
    quality_volume_threshold: float
    relative_strength_threshold_pct: float
    score_threshold: int
    alert_email_to: str
    alert_email_from: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    csv_log_path: str


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    load_dotenv()

    raw_symbols = os.getenv("SYMBOLS", "").strip()
    symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()] if raw_symbols else DEFAULT_SYMBOLS

    return Settings(
        symbols=symbols,
        check_interval_minutes=int(os.getenv("CHECK_INTERVAL_MINUTES", "30")),
        daily_move_threshold_pct=float(os.getenv("DAILY_MOVE_THRESHOLD_PCT", "5")),
        intraday_move_threshold_pct=float(os.getenv("INTRADAY_30M_MOVE_THRESHOLD_PCT", "3")),
        high_volume_threshold=float(os.getenv("HIGH_VOLUME_THRESHOLD", "2")),
        quality_volume_threshold=float(os.getenv("QUALITY_VOLUME_THRESHOLD", "1.5")),
        relative_strength_threshold_pct=float(os.getenv("RELATIVE_STRENGTH_THRESHOLD_PCT", "3")),
        score_threshold=int(os.getenv("MIN_ALERT_SCORE", "3")),
        alert_email_to=os.getenv("ALERT_EMAIL_TO", ""),
        alert_email_from=os.getenv("ALERT_EMAIL_FROM", ""),
        smtp_host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_use_tls=_parse_bool(os.getenv("SMTP_USE_TLS"), default=True),
        csv_log_path=os.getenv("CSV_LOG_PATH", "logs/alerts.csv"),
    )
