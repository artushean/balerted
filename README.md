# Local Stock Alert System (Windows + Python)

This project runs a **local stock price alert service** that:

- Monitors large-cap U.S. stocks (default set from the S&P 500)
- Checks prices every **30 minutes**
- Sends **email alerts**
- Triggers alerts for:
  - 📈 **±5% daily move** (vs previous close)
  - ⚡ **≥10% short-period move** (default: over 2 hours)

It uses **free/low-cost data** from Yahoo Finance via `yfinance` and runs on your own Windows machine (no hosting required).

## 1) Requirements

- Python 3.10+
- Internet access for market data
- SMTP email account (Gmail, Outlook, etc.)

Install dependencies:

```bash
pip install -r requirements.txt
```

## 2) Configure

Copy and edit env file:

```bash
copy .env.example .env
```

Set values in `.env`:

- `ALERT_EMAIL_TO`: recipient email
- `ALERT_EMAIL_FROM`: sender email
- `SMTP_HOST`, `SMTP_PORT`, `SMTP_USERNAME`, `SMTP_PASSWORD`
- Optionally tune:
  - `CHECK_INTERVAL_MINUTES` (default `30`)
  - `DAILY_MOVE_THRESHOLD_PCT` (default `5`)
  - `SHORT_WINDOW_MINUTES` (default `120`)
  - `SHORT_MOVE_THRESHOLD_PCT` (default `10`)

## 3) Run

```bash
python -m stock_alerts.main
```

Run in a persistent PowerShell window, or create a Windows Task Scheduler task to start it at logon.

## 4) Notes

- Data is best-effort and delayed depending on exchange/data availability.
- To avoid noisy alerts, the app deduplicates alerts for the same symbol/type/window in memory.
- If the process restarts, dedup state resets.

## 5) Quick Windows Task Scheduler setup

1. Open **Task Scheduler** → **Create Task**.
2. Trigger: *At log on* (or on startup).
3. Action: `Start a program`.
   - Program/script: `python`
   - Add arguments: `-m stock_alerts.main`
   - Start in: path to this repo.
4. Save.

