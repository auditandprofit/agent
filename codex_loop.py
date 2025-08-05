import argparse
import asyncio
from dataclasses import dataclass
from typing import List, Optional

from playwright.async_api import async_playwright, TimeoutError

from openai_utils import openai_configure_api, openai_generate_response


CODEx_URL = "https://chatgpt.com/codex"


@dataclass
class HistoryEntry:
    """Container for a single Codex interaction."""

    request: str
    response: str
    summary: str


def summarize_response(request: str, response: str) -> str:
    """Summarize Codex's response for compact history."""

    messages = [
        {
            "role": "system",
            "content": "You condense Codex responses into brief summaries.",
        },
        {
            "role": "user",
            "content": f"Request:\n{request}\n\nResponse:\n{response}\n\nSummary:",
        },
    ]
    resp = openai_generate_response(messages, functions=[])
    return resp.choices[0].message.content or ""


def generate_next_step(goal: str, history: List[HistoryEntry]) -> Optional[str]:
    """Ask the LLM for the next Codex request based on accumulated history."""

    history_lines = [f"Initial goal: {goal}"]
    for entry in history:
        history_lines.append(
            f"Request: {entry.request}\nResponse: {entry.response}\nSummary: {entry.summary}"
        )

    messages = [
        {
            "role": "system",
            "content": (
                "You plan the next step for Codex."
                " Given the user's goal and history, respond with the next request."
                " Reply with DONE if no further steps are required."
            ),
        },
        {"role": "user", "content": "\n\n".join(history_lines)},
    ]

    resp = openai_generate_response(messages, functions=[])
    content = resp.choices[0].message.content
    if content and content.strip().upper().startswith("DONE"):
        return None
    return content.strip() if content else None


async def ask_codex(question: str, gui: bool = False) -> str:
    """Send a question to the Codex site and return the last response text."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=not gui)
        page = await browser.new_page()
        await page.goto(CODEx_URL)

        # Wait for the text area to be available and submit the question
        textarea_selector = "textarea"
        try:
            await page.wait_for_selector(textarea_selector, timeout=30000)
        except TimeoutError:
            if gui:
                print(
                    "Text area not found; a challenge page may be present."
                    "\nResolve it in the browser window, then press Enter here to continue."
                )
                await asyncio.get_running_loop().run_in_executor(
                    None, input, "Press Enter to resume..."
                )
                await page.wait_for_selector(textarea_selector, timeout=30000)
            else:
                await browser.close()
                raise
        await page.fill(textarea_selector, question)
        await page.keyboard.press("Enter")

        # Wait for a response to appear in the DOM
        response_selector = "div.markdown"  # selector for chat response text
        await page.wait_for_selector(response_selector, timeout=60000)
        content = await page.locator(response_selector).last.inner_text()

        await browser.close()
        return content


async def run(goal: str, cycles: int, gui: bool = False) -> None:
    """Run the orchestrator/agent loop for a given number of cycles."""

    history: List[HistoryEntry] = []
    query = generate_next_step(goal, history)

    for idx in range(1, cycles + 1):
        if query is None:
            print("No further steps generated.")
            break
        response = await ask_codex(query, gui=gui)
        summary = summarize_response(query, response)
        history.append(HistoryEntry(query, response, summary))
        print(
            f"Cycle {idx}\nRequest: {query}\nResponse: {response}\nSummary: {summary}\n"
        )
        query = generate_next_step(goal, history)


def main() -> None:
    parser = argparse.ArgumentParser(description="Codex headless loop prototype")
    parser.add_argument("goal", help="Initial user goal or question")
    parser.add_argument("--cycles", type=int, default=1, help="Number of cycles to run")
    parser.add_argument(
        "--gui", action="store_true", help="Open a visible browser and pause for manual steps"
    )
    args = parser.parse_args()
    openai_configure_api()
    asyncio.run(run(args.goal, args.cycles, gui=args.gui))


if __name__ == "__main__":
    main()
