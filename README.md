# ChatGPT Invoice Downloader

A Python script that automatically logs into ChatGPT, navigates to the Stripe billing portal, and downloads your ChatGPT Plus invoice PDFs into organised monthly folders.

## What it does

- Opens a visible browser window and logs into ChatGPT
- Navigates to your billing portal on Stripe
- Downloads ChatGPT Plus invoice PDFs
- Saves them into organised monthly folders like `invoices/2026-01/`
- Skips invoices already downloaded — safe to run every month

## Folder structure

```
invoices/
├── 2026-01/
│   └── ChatGPT_2026-01.pdf
└── 2026-02/
    └── ChatGPT_2026-02.pdf
```

## Requirements

- Python 3.8+
- A ChatGPT Plus subscription
- Chromium (installed automatically in the setup step below)

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

Open `config.py` and fill in your details:

```python
START_DATE = "2026/01/01"       # only download invoices from this date onwards
CHATGPT_EMAIL = "you@example.com"
```

> **Note:** `config.py` is listed in `.gitignore` — your email is never uploaded to GitHub.

## Usage

```bash
python3 main.py
```

A browser window will open automatically. The script fills in your email and submits it. OpenAI then sends a **verification code to your inbox** — enter it in the browser when prompted. Once logged in, the script navigates to your billing portal and downloads all invoices automatically.

## Example output

```
=== ChatGPT Invoice Downloader ===
Will download invoices from 2026/01/01 onwards.

Opening ChatGPT login page...
Filling in email address...

============================================================
ACTION REQUIRED: Check your email for a verification code
and enter it in the browser window.

The script will continue automatically once you are logged in.
You have 3 minutes.
============================================================

Login successful!
Navigating to subscription settings...
Opening Account tab...
Opening billing portal...
Reached billing portal: https://pay.openai.com/...

Looking for invoices...
Found 3 invoice link(s).

  Downloading invoice for 2026-02...
  Saved: invoices/2026-02/ChatGPT_2026-02.pdf
  Downloading invoice for 2026-01...
  Saved: invoices/2026-01/ChatGPT_2026-01.pdf
  Skipping 2025-12 (before START_DATE)

=== Done! Downloaded 2 ChatGPT invoice(s). ===
```

## ⚠️ Language note

The script uses English button labels to navigate the ChatGPT interface (`Account`, `Manage`, `Download`). If your ChatGPT is set to a different language, these selectors may not work. You can either:
- Set your ChatGPT interface language to English in settings, or
- Update the button labels in `main.py` to match your language

## Security

- Your email is stored **only on your computer** in `config.py`
- The browser runs visibly so you can see everything happening
- `config.py` and `invoices/` are excluded from Git via `.gitignore`

## Contributing

Pull requests welcome!
