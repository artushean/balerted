# Full-Stack Stock Momentum Scanner

Local momentum intelligence app with:
- **Backend**: FastAPI + yfinance + pandas/numpy + ta + APScheduler
- **Frontend**: static HTML/CSS/JS (GitHub Pages compatible)
- **Alerts**: SMTP emails and CSV logging
- **Watchlist layer**: custom symbols with lower score threshold

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn stock_alerts.main:app --reload
```

Open http://127.0.0.1:8000

## Files

- `medium_cap.txt`, `large_cap.txt`: stock universe files (combined at runtime).
- `watchlist.json`: watchlist storage.
- `latest_data.json`: latest scan payload for dashboard/API.
- `alerts_log.csv`: append-only alert history.

## API

- `GET /api/latest`
- `GET /api/watchlist`
- `POST /api/watchlist/add` body: `{ "symbol": "AAPL", "note": "Earnings soon" }`
- `POST /api/watchlist/remove` body: `{ "symbol": "AAPL" }`
- `POST /api/scan` manual trigger

## Scheduler & alerts

- Runs every 15 minutes (configurable by `CHECK_INTERVAL_MINUTES`)
- Restricted to US market hours (9:30–16:00 ET) for scheduled scans
- Deduplicates same-symbol alerts per trading day
- Email subject format:
  - `Momentum Alert – X Market Signals | Y Watchlist Triggers`

## Environment variables

```env
ALERT_EMAIL_TO=ayoseph815@protonmail.com
ALERT_EMAIL_FROM=you@example.com
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USERNAME=you@example.com
SMTP_PASSWORD=app-password
SMTP_USE_TLS=true
CHECK_INTERVAL_MINUTES=15
```
