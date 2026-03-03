# Local Stock Alert System (Beginner-Friendly Guide)

This project is a **small background program** that watches stock prices and sends you an email when a big move happens.

> ✅ Important: This system is **command-line only**. There is **no front-end (web page or app UI)** to install or use.

---

## What this system does

It repeatedly checks a list of stock symbols (like `AAPL`, `MSFT`, `NVDA`) and sends an email alert when:

- A stock moves up/down by at least **5%** vs previous close (default).
- A stock moves by at least **10%** inside a short window, default **2 hours**.

By default, checks run every **30 minutes**.

---

## Before you begin (non-technical checklist)

You need:

1. **A Windows computer** (guide below is Windows-first).
2. **Internet access** (for stock data).
3. **An email account** you can send from (Gmail/Outlook/etc.).
4. **Python 3.10 or newer** installed.

---

## Step-by-step setup from zero

## 1) Install Python (if not already installed)

1. Open your browser.
2. Go to: https://www.python.org/downloads/
3. Download the latest Python 3 release.
4. Run the installer.
5. On the first installer screen, **check the box**: `Add Python to PATH`.
6. Click **Install Now**.

### Verify Python installed

1. Open **Command Prompt**:
   - Press `Windows` key
   - Type `cmd`
   - Press Enter
2. Run:

```bash
python --version
```

You should see something like `Python 3.10.x` or newer.

If not, close and reopen Command Prompt and try again.

---

## 2) Open this project folder in Command Prompt

If your project is in `C:\Users\YourName\Downloads\balerted`, do:

```bash
cd C:\Users\YourName\Downloads\balerted
```

Tip: In Windows File Explorer, you can click the folder path bar, type `cmd`, and press Enter. It opens Command Prompt in that folder.

---

## 3) Install required Python packages

In the project folder, run:

```bash
pip install -r requirements.txt
```

This installs everything the alert system needs.

---

## 4) Create your configuration file

This system reads settings from a file named `.env`.

### Create `.env` from template

In Command Prompt (inside project folder):

```bash
copy .env.example .env
```

Now open `.env` in Notepad:

```bash
notepad .env
```

---

## 5) Fill out `.env` values

Update these lines in `.env`:

- `ALERT_EMAIL_TO` → the email that should receive alerts.
- `ALERT_EMAIL_FROM` → the sender email.
- `SMTP_HOST` → your email provider SMTP server.
- `SMTP_PORT` → usually `587` for TLS.
- `SMTP_USERNAME` → login username (often your email address).
- `SMTP_PASSWORD` → your email password or app password.
- `SMTP_USE_TLS` → usually `true`.

### Optional tuning values

- `SYMBOLS` → comma-separated list like `AAPL,MSFT,NVDA`.
  - Leave blank to use default list.
- `CHECK_INTERVAL_MINUTES` → how often to check (default `30`).
- `DAILY_MOVE_THRESHOLD_PCT` → daily move threshold percent (default `5`).
- `SHORT_WINDOW_MINUTES` → short window in minutes (default `120`).
- `SHORT_MOVE_THRESHOLD_PCT` → short-window threshold percent (default `10`).

Save and close Notepad.

---

## 6) Run the system

In Command Prompt (project folder):

```bash
python -m stock_alerts.main
```

You should see logs saying it started and how many symbols it is monitoring.

Keep this window open while the system runs.

---

## 7) Confirm it is working

What to look for:

- Startup message like: `Starting stock alert monitor...`
- Repeating messages about sleeping/check intervals.
- If a threshold is hit, it sends an email alert.

If no alert happens quickly, that can be normal (market may not have crossed thresholds yet).

---

## 8) Stop the system

In the same Command Prompt window, press:

`Ctrl + C`

---

## 9) Auto-start on Windows login (optional)

Use Task Scheduler so it starts automatically.

1. Open **Task Scheduler**.
2. Click **Create Task**.
3. In **General** tab:
   - Name: `Stock Alerts`
4. In **Triggers** tab:
   - New → Begin the task: `At log on`
5. In **Actions** tab:
   - New → Action: `Start a program`
   - Program/script: `python`
   - Add arguments: `-m stock_alerts.main`
   - Start in: full path to this project folder
6. Save task.

Now it can launch automatically when you sign in.

---

## Email provider tips (common issue)

Some providers block direct SMTP password login unless you enable app passwords.

- **Gmail**: Usually requires 2FA + App Password.
- **Outlook/Office365**: May require SMTP AUTH enabled.

If login fails, check your provider's SMTP help page.

---

## Troubleshooting (plain language)

### `python` is not recognized

Python is not on PATH.

- Reinstall Python and check `Add Python to PATH`.
- Or restart terminal after install.

### `pip` is not recognized

Try:

```bash
python -m pip install -r requirements.txt
```

### Not receiving emails

Check `.env` values carefully:

- SMTP host/port are correct.
- Username/password are correct.
- Sender account allows SMTP/app passwords.
- Recipient email is valid.

### Program runs but no alerts

Could be normal. It only alerts when thresholds are crossed.

To test faster, temporarily lower thresholds in `.env` (for example, 1–2%).

---

## Full first-run command list (copy/paste)

Use these commands in order from Command Prompt:

```bash
cd C:\path\to\balerted
pip install -r requirements.txt
copy .env.example .env
notepad .env
python -m stock_alerts.main
```

---

## Security note

Your `.env` file contains sensitive credentials (email password).

- Do not share it.
- Do not post it publicly.
- Keep this project folder private on your computer.

