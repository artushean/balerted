from __future__ import annotations

import smtplib
from email.message import EmailMessage

from .alerts import AlertRecord
from .config import Settings


class EmailAlerter:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def send_consolidated_alert(self, alerts: list[AlertRecord]) -> None:
        if not alerts:
            return
        self._validate_email_config()

        msg = EmailMessage()
        msg["From"] = self.settings.alert_email_from
        msg["To"] = self.settings.alert_email_to
        msg["Subject"] = f"Momentum Scanner Digest ({len(alerts)} symbols)"

        lines = [
            "Semi-Professional Momentum Scanner (Informational only, not investment advice)",
            "",
        ]
        for record in sorted(alerts, key=lambda r: r.score, reverse=True):
            m = record.metrics
            rsi_condition = "Overbought" if m.rsi14 > 70 else "Oversold" if m.rsi14 < 30 else "Neutral"
            vol_condition = "Strong" if m.volume_multiplier >= 2.5 else "Elevated" if m.volume_multiplier >= 1.8 else "Normal"
            rs_flag = "Strong Outperformance" if m.relative_strength_vs_spy_pct >= self.settings.relative_strength_threshold_pct else "Inline"
            intraday_pos = "Near High" if m.intraday_near_high else "Near Low" if m.intraday_near_low else "Mid-Range"
            lines.extend(
                [
                    f"=== {record.symbol} | {record.tag} ===",
                    f"Triggers: {', '.join(record.categories)} | Score: {record.score}",
                    f"Price: ${m.current_price:.2f} | Daily: {m.daily_pct:+.2f}% (${m.dollar_change:+.2f}) | 30m: {m.intraday_30m_pct:+.2f}%",
                    f"Volume: {m.current_volume:,.0f} vs 30D Avg {m.avg_volume_30d:,.0f} ({m.volume_multiplier:.2f}x, {vol_condition})",
                    f"MA Context: 20D {m.ma20:.2f} ({'above' if m.above_ma20 else 'below'}), 50D {m.ma50:.2f} ({'above' if m.above_ma50 else 'below'})",
                    f"RSI(14): {m.rsi14:.1f} ({rsi_condition}) | ATR(14): {m.atr14:.2f} ({m.atr_pct:.2f}% of price) | Move/ATR%: {m.daily_move_vs_atr_ratio:.2f}x",
                    f"Rel Strength vs SPY: {m.relative_strength_vs_spy_pct:+.2f}% ({rs_flag})",
                    f"52W: High {m.high_52w:.2f}, Low {m.low_52w:.2f}, Dist from High {m.distance_from_52w_high_pct:+.2f}%, Range Pos {m.range_position_52w_pct:.1f}%",
                    f"Intraday Positioning: {intraday_pos}",
                    "",
                ]
            )

        msg.set_content("\n".join(lines))

        with smtplib.SMTP(self.settings.smtp_host, self.settings.smtp_port, timeout=20) as smtp:
            if self.settings.smtp_use_tls:
                smtp.starttls()
            if self.settings.smtp_username:
                smtp.login(self.settings.smtp_username, self.settings.smtp_password)
            smtp.send_message(msg)

    def _validate_email_config(self) -> None:
        required = [self.settings.alert_email_to, self.settings.alert_email_from, self.settings.smtp_host]
        if not all(required):
            raise ValueError("Missing email config. Set ALERT_EMAIL_TO, ALERT_EMAIL_FROM, and SMTP_HOST in .env")
