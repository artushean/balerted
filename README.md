# Stock Momentum Scanner

Serverless momentum scanner that runs in GitHub Actions and publishes a static dashboard.

## What it does

- Scans up to ~500 symbols from the configured S&P universe file (`stock-scanner/sp500_symbols.txt`).
- Detects 3% momentum moves (1-day or latest 15m bar).
- Ranks signals with a 0-100 momentum score.
- Sends SMTP email alerts for qualifying signals.
- Publishes a modern static dashboard in `docs/` and `stock-scanner/docs/`.
- Auto-runs every 30 minutes via GitHub Actions.

## Serverless run path

- Workflow: `.github/workflows/update_data.yml`
- Scanner entrypoint: `stock-scanner/main.py`
- Scanner JSON output: `stock-scanner/docs/latest_data.json`
- GitHub Pages mirror JSON: `docs/latest_data.json`

## Required GitHub secrets

- `SMTP_HOST`
- `SMTP_PORT`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `ALERT_EMAIL_FROM`
- `ALERT_EMAIL_TO`

## Quick local checks

```bash
python -m compileall stock-scanner
python -m http.server 8000 --directory docs
```
