# ChatGPT Invoice Downloader

> Since OpenAI still doesn't email invoices automatically, this script does it for you.

Automatically logs into ChatGPT, downloads your invoice PDFs from the Stripe billing portal, and saves them into organised monthly folders — with one manual step (entering a verification code).

Works with **ChatGPT Plus** and **ChatGPT Teams**.

## What it does

- Opens a browser, fills in your email, and waits for you to enter the verification code
- Navigates to your Stripe billing portal automatically
- Downloads all invoice PDFs since your chosen start date
- Saves them into monthly folders like `invoices/2026-01/`
- Skips invoices already downloaded — safe to run every month

```
invoices/
├── 2026-01/
│   └── ChatGPT_2026-01.pdf
└── 2026-02/
    └── ChatGPT_2026-02.pdf
```

## Requirements

- Python 3.8+
- A ChatGPT Plus or Teams subscription
- macOS, Windows, or Linux

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/tedbibr/chatgpt-invoice-downloader.git
cd chatgpt-invoice-downloader
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
playwright install chromium
```

> `playwright install chromium` downloads a ~160MB browser used for automation. This is a one-time step.

### 3. Configure your account

```bash
cp config.example.py config.py
```

Open `config.py` and fill in two things:

```python
START_DATE = "2026/01/01"         # only download invoices from this date onwards
CHATGPT_EMAIL = "you@example.com" # your ChatGPT login email
```

> `config.py` is listed in `.gitignore` — your email is never uploaded to GitHub.

## Usage

```bash
python3 main.py
```

A browser window opens automatically. The script fills in your email and submits it. OpenAI sends a **verification code to your inbox** — enter it in the browser. Once logged in, everything else is automatic.

## Example output

```
=== ChatGPT Invoice Downloader ===
Will download invoices from 2026/01/01 onwards.

Opening ChatGPT login page...
Filling in email address...

============================================================
ACTION REQUIRED: Check your email for a verification code
and enter it in the browser window.

The script continues automatically once you are logged in.
You have 3 minutes.
============================================================

Login successful!
Navigating to subscription settings...
Opening billing portal...

Looking for invoices...
Found 3 invoice link(s).

  Downloading invoice for 2026-02...
  Saved: invoices/2026-02/ChatGPT_2026-02.pdf
  Downloading invoice for 2026-01...
  Saved: invoices/2026-01/ChatGPT_2026-01.pdf
  Skipping 2025-12 (before START_DATE)

=== Done! Downloaded 2 ChatGPT invoice(s). ===
```

## Scheduling

Because OpenAI requires a verification code on each login, the script can't run fully unattended. You can still schedule it as a monthly reminder — it will open the browser automatically and wait for you to enter the code.

To schedule it, use your OS's built-in scheduler:

- **macOS** — `launchd` (via a `.plist` file in `~/Library/LaunchAgents/`)
- **Linux** — `cron` (`crontab -e`)
- **Windows** — Task Scheduler

## Language note

The script uses English button labels to navigate the ChatGPT interface (`Account`, `Manage`, `Download`). If your ChatGPT is set to a different language, either:
- Switch your ChatGPT interface language to English in settings, or
- Update the button labels in `main.py` to match your language

## Security

- Your email is stored **only on your computer** in `config.py`
- The browser runs visibly so you can see exactly what's happening at all times
- `config.py` and `invoices/` are excluded from Git via `.gitignore`

## Contributing

Pull requests welcome!
