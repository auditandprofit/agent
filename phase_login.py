"""Phase login entry point for the Codex agent.

This thin wrapper exists so external tooling can invoke the Codex login using a
stable module name.
"""

from codex_login import main

if __name__ == "__main__":
    main()
