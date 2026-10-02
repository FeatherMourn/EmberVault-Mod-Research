"""Shared test helpers."""

from __future__ import annotations

import os
import unittest

from architect_lua_config_lab.config import (
    base_lua_path,
    cache_dir,
    kfc_dir,
    types_lua_path,
)
from architect_lua_config_lab.core.lab import Lab

import tempfile


def types_lua_exists() -> bool:
    return os.path.isfile(types_lua_path())


def make_lab() -> Lab:
    lab = Lab(
        types_lua_path=types_lua_path(),
        base_lua_path=base_lua_path(),
        kfc_dir=kfc_dir(),
        cache_dir=tempfile.mkdtemp(prefix="lab_cache_"),
    )
    lab.load()
    return lab


def require_types_lua(testcase: unittest.TestCase) -> bool:
    if not types_lua_exists():
        testcase.skipTest("types.lua not available at %r" % types_lua_path())
        return False
    return True
