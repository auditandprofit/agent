# Headless Codex Prototype

Prototype exploring a loop between a planning LLM and the ChatGPT Codex site using a headless browser.

## Setup

```bash
pip install -r requirements.txt
playwright install
```

## Usage

```bash
python codex_loop.py "What is the capital of France?" --cycles 1
```

To interact with the browser during intermediate steps (e.g. solving a
challenge page), run the scripts with the `--gui` flag. This opens a visible
browser window and pauses execution so you can complete any required steps
before the automation resumes.

Example:

```bash
python codex_login.py --gui
python codex_loop.py "What is the capital of France?" --cycles 1 --gui
```

The script performs the following cycle:

1. The LLM planner generates the next request for Codex using the user goal and interaction history.
2. The request is sent to `https://chatgpt.com/codex` using a headless browser.
3. The Codex response is summarised and appended to the history.
4. The updated history is provided to the planner to determine the next step.

The number of cycles can be configured via the `--cycles` flag.
