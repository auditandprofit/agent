import os
import asyncio
import argparse
from playwright.async_api import async_playwright, TimeoutError

LOGIN_URL = "https://chatgpt.com/auth/login?next=/codex"

async def login_to_codex(email: str, password: str, gui: bool = False) -> None:
    """Attempt to log into the Codex site using Playwright.

    The function navigates to the login page, fills the email and password
    fields, and submits the form. In ``gui`` mode the browser window is
    visible and, if a challenge page (e.g. Cloudflare) is encountered,
    the routine pauses and allows the user to intervene manually before
    resuming.
    """

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not gui)
        context = await browser.new_context(ignore_https_errors=True)
        page = await context.new_page()
        await page.goto(LOGIN_URL)

        try:
            await page.wait_for_selector('input[name="email"]', timeout=30000)
        except TimeoutError:
            if gui:
                print(
                    "Login form not found; a challenge page may be present."
                    "\nResolve it in the browser window, then press Enter here to continue."
                )
                await asyncio.get_running_loop().run_in_executor(
                    None, input, "Press Enter to resume..."
                )
                try:
                    await page.wait_for_selector('input[name="email"]', timeout=30000)
                except TimeoutError:
                    print("Login form still not found. Aborting.")
                    await browser.close()
                    return
            else:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Log into Codex using Playwright")
    parser.add_argument(
        "--gui", action="store_true", help="Open a visible browser and pause for manual steps"
    )
    args = parser.parse_args()

    email = os.environ.get("CODEX_EMAIL", "user@example.com")
    password = os.environ.get("CODEX_PASSWORD", "not-a-real-password")

    asyncio.run(login_to_codex(email, password, gui=args.gui))


if __name__ == "__main__":
    main()

