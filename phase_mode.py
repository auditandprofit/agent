"""Phase mode entry point for the Codex agent.

This thin wrapper exists so external tooling can invoke the headless
Codex loop using a stable module name.
"""

from codex_loop import main

if __name__ == "__main__":
    main()
