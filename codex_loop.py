import argparse
import asyncio
from typing import Optional

from playwright.async_api import async_playwright


CODEx_URL = "https://chatgpt.com/codex"


def orchestrator_llm(prompt: str) -> str:
    """Placeholder for an orchestrator LLM.

    In a full implementation this function would call an LLM to determine the
    next action based on the provided prompt. For now it simply echoes the
    prompt to demonstrate the flow.
    """
    return f"Echo: {prompt}"


async def ask_codex(question: str) -> str:
    """Send a question to the Codex site and return the last response text."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(CODEx_URL)

        # Wait for the text area to be available and submit the question
        textarea_selector = "textarea"
        await page.wait_for_selector(textarea_selector)
        await page.fill(textarea_selector, question)
        await page.keyboard.press("Enter")

        # Wait for a response to appear in the DOM
        response_selector = "div.markdown"  # selector for chat response text
        await page.wait_for_selector(response_selector, timeout=60000)
        content = await page.locator(response_selector).last.inner_text()

        await browser.close()
        return content


async def run(goal: str, cycles: int) -> None:
    """Run the orchestrator/agent loop for a given number of cycles."""
    query: Optional[str] = goal
    for idx in range(1, cycles + 1):
        if query is None:
            break
        result = await ask_codex(query)
        print(f"Cycle {idx} result:\n{result}\n")
        query = orchestrator_llm(result)


def main() -> None:
    parser = argparse.ArgumentParser(description="Codex headless loop prototype")
    parser.add_argument("goal", help="Initial user goal or question")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run")
    args = parser.parse_args()
    asyncio.run(run(args.goal, args.cycles))


if __name__ == "__main__":
    main()
