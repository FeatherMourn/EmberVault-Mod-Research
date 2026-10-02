"""Convenience launcher: ``python run.py`` (or ``python run.py gui``)."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from architect_lua_config_lab.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
