from __future__ import annotations

import logging
import time

from .alerts import AlertEngine
from .config import load_settings
from .data_provider import YahooFinanceProvider
from .emailer import EmailAlerter


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
    )


def run() -> None:
    configure_logging()
    settings = load_settings()

    provider = YahooFinanceProvider()
    alert_engine = AlertEngine(
        daily_move_threshold_pct=settings.daily_move_threshold_pct,
        short_window_minutes=settings.short_window_minutes,
        short_move_threshold_pct=settings.short_move_threshold_pct,
    )
    emailer = EmailAlerter(settings=settings)

    interval_seconds = settings.check_interval_minutes * 60

    logging.info("Starting stock alert monitor for %d symbols.", len(settings.symbols))

    while True:
        for symbol in settings.symbols:
            try:
                snapshot = provider.get_snapshot(symbol)
                events = alert_engine.evaluate(snapshot)
                for event in events:
                    logging.info("Alert triggered for %s: %s", event.symbol, event.details)
                    emailer.send_alert(event)
            except Exception as exc:  # noqa: BLE001
                logging.exception("Error processing %s: %s", symbol, exc)

        logging.info("Sleeping for %d minutes.", settings.check_interval_minutes)
        time.sleep(interval_seconds)


if __name__ == "__main__":
    run()
