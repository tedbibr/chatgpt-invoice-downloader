import os
import re
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from config import START_DATE, CHATGPT_EMAIL

# Where to save downloaded invoices (same folder as main.py)
INVOICES_DIR = "invoices"


def parse_start_date(date_str):
    """Convert START_DATE string like '2026/01/01' to a datetime object."""
    return datetime.strptime(date_str, "%Y/%m/%d")


def extract_date_from_text(text):
    """
    Tries to find a date in a string. Handles two formats:
      - 'Jan 1, 2026' / 'January 1, 2026'  (Gmail emails)
      - '12 Feb 2026'                        (Stripe billing portal)
    Returns a datetime object or None if no date found.
    """
    # Format 1: "Mon DD, YYYY" — e.g. "Feb 12, 2026"
    match = re.search(r'(\w+ \d{1,2}, \d{4})', text)
    if match:
        for fmt in ["%b %d, %Y", "%B %d, %Y"]:
            try:
                return datetime.strptime(match.group(1), fmt)
            except ValueError:
                continue
    # Format 2: "DD Mon YYYY" — e.g. "12 Feb 2026" (Stripe)
    match = re.search(r'(\d{1,2} \w+ \d{4})', text)
    if match:
        for fmt in ["%d %b %Y", "%d %B %Y"]:
            try:
                return datetime.strptime(match.group(1), fmt)
            except ValueError:
                continue
    return None


def make_month_folder(year, month):
    """
    Creates and returns the path for a monthly invoice folder.
    e.g. invoices/2026-01/
    """
    folder_name = f"{year:04d}-{month:02d}"
    path = os.path.join(INVOICES_DIR, folder_name)
    os.makedirs(path, exist_ok=True)
    return path


def main():
    start_dt = parse_start_date(START_DATE)

    print("=== ChatGPT Invoice Downloader ===")
    print(f"Will download invoices from {START_DATE} onwards.")
    print()

    with sync_playwright() as p:
        # Open a VISIBLE browser so you can see what's happening
        # slow_mo=500 adds a 500ms pause between actions (looks more human-like)
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()

        # ── STEP 1: Navigate to login page ───────────────────────────
        print("Opening ChatGPT login page...")
        page.goto("https://chatgpt.com/auth/login", wait_until="domcontentloaded")
        page.wait_for_timeout(2000)

        # Click "Log in" if the landing screen shows it (some regions/accounts show it)
        try:
            page.locator("a[href*='log-in'], button:has-text('Log in')").first.click(timeout=5_000)
            page.wait_for_timeout(2000)
        except PlaywrightTimeoutError:
            pass  # Already on login form

        # ── STEP 2: Fill in email ─────────────────────────────────────
        print("Filling in email address...")
        try:
            page.locator('input[name="username"], input[type="email"]').first.fill(CHATGPT_EMAIL, timeout=10_000)
            page.click('button[type="submit"]')
            page.wait_for_timeout(1500)
        except PlaywrightTimeoutError:
            print("WARNING: Could not find email field. Please fill it manually in the browser.")

        # ── STEP 3: Wait for user to enter verification code ─────────
        print()
        print("=" * 60)
        print("ACTION REQUIRED: Check your email for a verification code")
        print("and enter it in the browser window.")
        print()
        print("The script will continue automatically once you are logged in.")
        print("You have 3 minutes.")
        print("=" * 60)
        print()

        # Wait until the browser lands on the main ChatGPT page
        try:
            page.wait_for_url("https://chatgpt.com/**", timeout=180_000)
            print("Login successful!")
        except PlaywrightTimeoutError:
            print("ERROR: Timed out waiting for login. Please try again.")
            browser.close()
            return

        # ── STEP 5: Navigate to billing settings ─────────────────────
        print()
        print("Navigating to subscription settings...")
        # #settings in the URL tells ChatGPT's JavaScript to open the settings modal
        page.goto("https://chatgpt.com/settings#settings", wait_until="domcontentloaded")
        page.wait_for_timeout(3000)

        # Click the "Account" tab inside the settings modal
        print("Opening Account tab...")
        try:
            page.locator("button:has-text('Account'), [role='tab']:has-text('Account')").first.click(timeout=10_000)
            page.wait_for_timeout(2000)
        except PlaywrightTimeoutError:
            print("ERROR: Could not find Account tab in settings.")
            print("The browser window is open - please check what you see on screen.")
            browser.close()
            return

        # There are two "Manage" buttons on the Account tab:
        #   - First: next to "ChatGPT Plus"  → manages plan
        #   - Last:  next to "Payment"        → opens Stripe billing portal with invoices
        print("Opening billing portal...")
        stripe_page = None
        try:
            with context.expect_page(timeout=5_000) as new_page_info:
                page.locator("button:has-text('Manage')").nth(1).click(timeout=10_000)
            stripe_page = new_page_info.value
            stripe_page.wait_for_load_state("domcontentloaded")
            stripe_page.wait_for_timeout(500)
            print(f"Reached billing portal: {stripe_page.url}")
        except PlaywrightTimeoutError:
            # Stripe tab may have opened after the timeout — scan all open pages
            page.wait_for_timeout(2000)  # Give the tab a moment to appear
            for p in context.pages:
                if "stripe" in p.url or "billing" in p.url or "openai" in p.url.lower():
                    stripe_page = p
                    stripe_page.wait_for_load_state("domcontentloaded")
                    print(f"Reached billing portal (late): {stripe_page.url}")
                    break

        if stripe_page is None:
            print("ERROR: Could not open billing portal.")
            print("Make sure you have an active ChatGPT Plus subscription.")
            browser.close()
            return

        # ── STEP 6: Find invoices on the Stripe portal ────────────────
        print()
        print("Looking for invoices...")

        try:
            stripe_page.wait_for_selector("a[href*='invoice'], a[href*='receipt']", timeout=15_000)
        except PlaywrightTimeoutError:
            print("ERROR: No invoices found on the billing page.")
            print(f"Current URL: {stripe_page.url}")
            browser.close()
            return

        invoice_links = stripe_page.locator("a[href*='invoice'], a[href*='receipt']").all()
        print(f"Found {len(invoice_links)} invoice link(s).")
        print()

        downloaded = 0

        for link in invoice_links:
            # The invoice row text contains the date, e.g. "12 Feb 2026  US$20.00  Paid"
            row_text = link.inner_text()

            # Extract the invoice date from the row text
            invoice_date = extract_date_from_text(row_text)

            if invoice_date is None:
                print(f"  Warning: could not read date from: {row_text[:60]!r}")
                continue

            # Skip invoices before START_DATE
            if invoice_date < start_dt:
                print(f"  Skipping {invoice_date.strftime('%Y-%m')} (before START_DATE)")
                continue

            # Build the file path
            year = invoice_date.year
            month = invoice_date.month
            folder = make_month_folder(year, month)
            file_path = os.path.join(folder, f"ChatGPT_{year:04d}-{month:02d}.pdf")

            # Skip if already downloaded
            if os.path.exists(file_path):
                print(f"  Already exists, skipping: {file_path}")
                continue

            # ── Download the PDF ─────────────────────────────────────
            print(f"  Downloading invoice for {year:04d}-{month:02d}...")

            try:
                # Click invoice row → opens Stripe invoice detail page in new tab
                with context.expect_page(timeout=15_000) as invoice_tab_info:
                    link.click()
                invoice_tab = invoice_tab_info.value
                invoice_tab.wait_for_load_state("domcontentloaded")
                invoice_tab.wait_for_timeout(500)

                # On the Stripe invoice page, click the Download button to get the PDF
                with invoice_tab.expect_download(timeout=15_000) as dl_info:
                    invoice_tab.locator(
                        "a:has-text('Download'), button:has-text('Download')"
                    ).first.click(timeout=10_000)
                dl_info.value.save_as(file_path)
                print(f"  Saved: {file_path}")
                downloaded += 1
                invoice_tab.close()
            except Exception as e:
                print(f"  ERROR downloading {year:04d}-{month:02d}: {e}")

        print()
        print(f"=== Done! Downloaded {downloaded} ChatGPT invoice(s). ===")
        print(f"Check the '{INVOICES_DIR}/' folder for your invoices.")

        browser.close()


if __name__ == "__main__":
    main()
