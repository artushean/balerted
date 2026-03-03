# Local Momentum Stock Alert Scanner (Windows + Python)

A lightweight, local-only scanner for semi-professional retail momentum workflows.

## What it does

- Runs every **30 minutes** during U.S. market hours (**9:30 AM–4:00 PM ET**, weekdays).
- Monitors **75–150 large-cap U.S. stocks** (default list is a broad S&P 500 subset).
- Uses free Yahoo data via `yfinance` with **batched downloads**.
- Sends **one consolidated email per cycle** using SMTP (Gmail App Password supported).
- Includes anti-spam de-duplication so the same stock/category is alerted once per day.
- Logs all alerts to CSV.

> Informational only. Not investment advice.

## Signals included per stock

- Current price
- Daily % move (vs today's open)
- 30-minute % move (vs previous 30-minute candle)
- Dollar move
- 30-day average volume and volume multiplier
- MA context: 20D / 50D (above or below)
- RSI(14) with overbought/oversold flags
- ATR(14), ATR%, and move-vs-ATR comparison
- 52-week high/low, distance from 52W high, and 52W range position
- Relative strength vs SPY (stock daily % minus SPY daily %)
- Intraday positioning (near high / near low)

## Alert logic

A stock is considered only when one or more triggers fire:
- Daily move >= ±5%
- 30-minute move >= ±3%
- Volume >= 2x average
- Within 2% of 52-week high
- RSI extreme (>70 or <30)

Quality filter (at least one required):
- Volume >= 1.5x average
- Above 50D MA (bullish)
- Below 50D MA (bearish)

Noise reduction score (default `>= 3`):
- +2 daily >= 5%
- +1 30m >= 3%
- +1 volume >= 2x
- +1 above 50D MA
- +1 near 52W high

## Setup

```bash
pip install -r requirements.txt
copy .env.example .env
```

Fill `.env` values (especially Gmail SMTP + App Password), then run:

```bash
python -m stock_alerts.main
```

## Windows usage

Run from a persistent shell or Task Scheduler (at logon/startup) so it stays local on your machine.
