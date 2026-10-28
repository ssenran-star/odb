#!/usr/bin/env python3
"""Send the seekdb context to MiniMax and apply the returned edit.

Reads MINIMAX_API_KEY from the environment. With --dry-run, writes the exact
request body and does not call the API or modify the sample.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sddctx.cli import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main(["edit", *sys.argv[1:]]))
