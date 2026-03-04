from __future__ import annotations

import json
import os
import smtplib
from email.message import EmailMessage
from pathlib import Path

from scanner.engine import ScanEngine

BASE = Path(__file__).resolve().parent
OUTPUT_FILE = BASE / "docs" / "latest_data.json"


def send_email_if_needed(payload: dict) -> None:
    alerts = payload.get("alerts", [])
    if not alerts:
        return

    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))

    if not all([email_user, email_password, smtp_server]):
        return

    msg = EmailMessage()
    msg["Subject"] = f"Stock Momentum Alerts: {len(alerts)} signal(s)"
    msg["From"] = email_user
    msg["To"] = "ayoseph815@protonmail.com"

    lines = ["Momentum scanner detected qualifying symbols:\n"]
    for item in alerts:
        breakout = []
        if item.get("breakout_52w"):
            breakout.append("52-week breakout")
        if item.get("breakout_20d"):
            breakout.append("20-day breakout")
        breakout_txt = ", ".join(breakout) if breakout else "no breakout"

        lines.append(
            f"- {item['symbol']} | conviction={item['conviction']} | score={item['score']} | "
            f"RS={item['relative_strength']}% | {breakout_txt}"
        )

    lines.append("\nGenerated automatically. This message is informational and not investment advice.")
    msg.set_content("\n".join(lines))

    with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
        server.starttls()
        server.login(email_user, email_password)
        server.send_message(msg)


def main() -> None:
    engine = ScanEngine(
        large_cap_path=str(BASE / "large_cap.txt"),
        medium_cap_path=str(BASE / "medium_cap.txt"),
        watchlist_path=str(BASE / "watchlist.json"),
    )
    payload = engine.run()
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    send_email_if_needed(payload)


if __name__ == "__main__":
    main()
