from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .alerts import AlertEvent
from .config import Settings


class EmailAlerter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_alert(self, event: AlertEvent) -> None:
        self._validate_email_config()

        msg = EmailMessage()
        msg["From"] = self.settings.alert_email_from
        msg["To"] = self.settings.alert_email_to
        msg["Subject"] = f"Stock Alert: {event.symbol} {event.alert_type} {event.percent_move:+.2f}%"
        msg.set_content(
            "\n".join(
                [
                    f"Symbol: {event.symbol}",
                    f"Alert type: {event.alert_type}",
                    f"Move: {event.percent_move:+.2f}%",
                    f"Details: {event.details}",
                    f"Time (UTC): {event.triggered_at.isoformat()}",
                ]
            )
        )

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=20) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(msg)

    def _validate_email_config(self) -> None:
        required = [
            self.settings.alert_email_to,
            self.settings.alert_email_from,
            self.settings.smtp_host,
        ]
        if not all(required):
            raise ValueError(
                "Missing email config. Set ALERT_EMAIL_TO, ALERT_EMAIL_FROM, and SMTP_HOST in .env"
            )
