#!/usr/bin/env python3
"""Run TextLands CLI without installation."""

import sys
from pathlib import Path

# Add the cli directory to path
sys.path.insert(0, str(Path(__file__).parent))

from textlands_cli.main import app

if __name__ == "__main__":
    app()
