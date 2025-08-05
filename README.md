# Headless Codex Prototype

Prototype exploring a loop between a placeholder "orchestrator" and the ChatGPT Codex site using a headless browser.

## Setup

```bash
pip install -r requirements.txt
playwright install
```

## Usage

```bash
python codex_loop.py "What is the capital of France?" --cycles 1
```

The script performs the following simplified cycle:

1. The orchestrator generates a question (currently a stub).
2. The question is sent to `https://chatgpt.com/codex` using a headless browser.
3. The response is extracted from the DOM and printed.
4. The response is fed back into the orchestrator for the next cycle.

The number of cycles can be configured via the `--cycles` flag. LLM integration is left as a TODO.
