import os
import asyncio
from playwright.async_api import async_playwright, TimeoutError

LOGIN_URL = "https://chatgpt.com/auth/login?next=/codex"

async def login_to_codex(email: str, password: str) -> None:
    """Attempt to log into the Codex site using Playwright.

    The function navigates to the login page, fills the email and password
    fields, and submits the form. It prints whether the login appears
    successful or not. The actual login is expected to fail when invalid
    credentials are supplied, but this function exercises the DOM flow.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await page.goto(LOGIN_URL)

        try:
            await page.wait_for_selector('input[name="email"]', timeout=30000)
        except TimeoutError:
            print("Login form not found; perhaps blocked by challenge page.")
            await browser.close()
            return

        await page.fill('input[name="email"]', email)
        await page.fill('input[name="password"]', password)
        await page.click('button[type="submit"]')

        try:
            await page.wait_for_url("https://chatgpt.com/codex", timeout=30000)
            print("Login appeared successful")
        except TimeoutError:
            # An error message is expected with invalid credentials.
            error_text = await page.text_content('div[role="alert"]')
            if error_text:
                print(error_text.strip())
            else:
                print("Login failed or was redirected elsewhere.")

        await browser.close()

if __name__ == "__main__":
    email = os.environ.get("CODEX_EMAIL", "user@example.com")
    password = os.environ.get("CODEX_PASSWORD", "not-a-real-password")
    asyncio.run(login_to_codex(email, password))
