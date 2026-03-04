from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    alert_email_from: str
    alert_email_to: str
    scheduler_minutes: int
    latest_data_path: Path
    watchlist_path: Path
    alerts_log_path: Path
    medium_cap_file: Path
    large_cap_file: Path


def _parse_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings() -> Settings:
    load_dotenv()
    base = Path(os.getenv("DATA_DIR", ".")).resolve()
    return Settings(
        smtp_host=os.getenv("SMTP_HOST", ""),
        smtp_port=int(os.getenv("SMTP_PORT", "587")),
        smtp_username=os.getenv("SMTP_USERNAME", ""),
        smtp_password=os.getenv("SMTP_PASSWORD", ""),
        smtp_use_tls=_parse_bool(os.getenv("SMTP_USE_TLS"), True),
        alert_email_from=os.getenv("ALERT_EMAIL_FROM", ""),
        alert_email_to=os.getenv("ALERT_EMAIL_TO", "ayoseph815@protonmail.com"),
        scheduler_minutes=int(os.getenv("CHECK_INTERVAL_MINUTES", "15")),
        latest_data_path=base / "latest_data.json",
        watchlist_path=base / "watchlist.json",
        alerts_log_path=base / "alerts_log.csv",
        medium_cap_file=base / "medium_cap.txt",
        large_cap_file=base / "large_cap.txt",
    )
