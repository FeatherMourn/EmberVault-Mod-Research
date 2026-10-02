"""Source-file and directory discovery.

The tool needs to locate ``types.lua``, ``base.lua``, the KFC resource roots,
and an output directory. Locations can be overridden with environment
variables; otherwise sensible defaults for the current development machine are
used.

Environment overrides
---------------------
* ``ENSHROUDED_TYPES_LUA``
* ``ENSHROUDED_BASE_LUA``
* ``ENSHROUDED_KFC_DIR``
* ``LUA_CONFIG_LAB_OUTPUT``
* ``LUA_CONFIG_LAB_PROJECT``
"""

from __future__ import annotations

import os

# Default install / evidence locations (documented, not hard requirements).
_DEFAULT_GAME_CACHE = r"H:\SteamLibrary\steamapps\common\Enshrouded\.cache\lua"
_DEFAULT_KFC_DIR = (
    r"H:\enshroudedresearch\Enshrouded Mods-20260918T044156Z-1-001"
    r"\Enshrouded Mods\ENSHROUDED KFC FILES"
)


def project_dir() -> str:
    return os.environ.get(
        "LUA_CONFIG_LAB_PROJECT",
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    )


def types_lua_path() -> str:
    return os.environ.get(
        "ENSHROUDED_TYPES_LUA",
        os.path.join(_DEFAULT_GAME_CACHE, "types.lua"),
    )


def base_lua_path() -> str:
    return os.environ.get(
        "ENSHROUDED_BASE_LUA",
        os.path.join(_DEFAULT_GAME_CACHE, "base.lua"),
    )


def kfc_dir() -> str:
    return os.environ.get("ENSHROUDED_KFC_DIR", _DEFAULT_KFC_DIR)


def output_dir() -> str:
    return os.environ.get(
        "LUA_CONFIG_LAB_OUTPUT",
        os.path.join(project_dir(), "output"),
    )


def cache_dir() -> str:
    return os.path.join(project_dir(), ".lab_cache")


def results_dir() -> str:
    return os.path.join(project_dir(), "results")
