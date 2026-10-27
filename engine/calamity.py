#!/usr/bin/env python3
"""Entry point of the Calamity engine.

    python3 engine/calamity.py <command> [options]     (Linux, macOS)
    python engine/calamity.py <command> [options]      (Windows; or: py -3 ...)

Run with --help for the list of commands.
"""
import os
import sys

if sys.version_info < (3, 9):
    sys.stderr.write("error: Calamity needs Python 3.9 or newer (this is %d.%d).\n" % sys.version_info[:2])
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__" and sys.argv[1:] == ["guard", "tool"]:
    # The key guard runs before every Read, Grep, Glob and shell call: answer it without loading the CLI.
    from cal.guard import hook_main  # noqa: E402

    sys.exit(hook_main())

from cal.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
