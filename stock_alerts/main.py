from __future__ import annotations

import logging
import time
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo

from .alerts import AlertEngine
from .config import load_settings
from .data_provider import YahooFinanceProvider
from .emailer import EmailAlerter

EASTERN = ZoneInfo("America/New_York")


def configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")


def _is_market_hours(now_et: datetime) -> bool:
    if now_et.weekday() >= 5:
        return False
    return dt_time(9, 30) <= now_et.time() <= dt_time(16, 0)


def run() -> None:
    configure_logging()
    settings = load_settings()

    provider = YahooFinanceProvider()
    alert_engine = AlertEngine(
        daily_move_threshold_pct=settings.daily_move_threshold_pct,
        intraday_move_threshold_pct=settings.intraday_move_threshold_pct,
        high_volume_threshold=settings.high_volume_threshold,
        quality_volume_threshold=settings.quality_volume_threshold,
        relative_strength_threshold_pct=settings.relative_strength_threshold_pct,
        score_threshold=settings.score_threshold,
        csv_log_path=settings.csv_log_path,
    )
    emailer = EmailAlerter(settings=settings)

    interval_seconds = settings.check_interval_minutes * 60
    logging.info("Starting local momentum scanner for %d symbols.", len(settings.symbols))

    while True:
        now_et = datetime.now(EASTERN)
        alert_engine.reset_for_new_day_if_needed(now_et)

        if _is_market_hours(now_et):
            try:
                metrics = provider.fetch_metrics(settings.symbols)
                alerts = alert_engine.evaluate(metrics)
                if alerts:
                    emailer.send_consolidated_alert(alerts)
                    logging.info("Sent consolidated digest with %d triggered symbols.", len(alerts))
                else:
                    logging.info("No qualifying alerts this cycle.")
            except Exception as exc:  # noqa: BLE001
                logging.exception("Cycle failed: %s", exc)
        else:
            logging.info("Outside U.S. market hours (ET). Waiting for next cycle.")

        time.sleep(interval_seconds)


if __name__ == "__main__":
    run()
