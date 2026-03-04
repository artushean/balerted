# Stock Momentum Scanner

This repo now supports two modes:

- **Serverless GitHub mode (MVP):** `stock-scanner/` runs from GitHub Actions, writes JSON for static UI, and can send SMTP alerts.
- **Legacy local prototype:** `stock_alerts/` + `frontend/` can still run against local API for development.

## Frontend integration

`frontend/app.js` is now integrated for both environments:

1. **Serverless mode:** reads `./latest_data.json` (written by workflow from `stock-scanner/docs/latest_data.json`).
2. **Local mode fallback:** if static JSON is unavailable, it falls back to `/api/latest`.

So yes — FE is integrated with the new scanner output and still backward-compatible.

## Serverless run path

- Workflow: `.github/workflows/update_data.yml`
- Scanner entrypoint: `stock-scanner/main.py`
- Scanner JSON output: `stock-scanner/docs/latest_data.json`
- FE JSON mirror for root static frontend: `frontend/latest_data.json`

## Quick local checks

```bash
python -m compileall stock-scanner
python -m http.server 8000 --directory frontend
```
