"""Provenance recording.

Every exported mod carries a provenance record so that after an Enshrouded
update we know exactly which ``types.lua`` / ``base.lua`` / profile produced it.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from typing import Dict, Optional

from .. import __version__
from .profile import Profile, profile_hash


def sha256_file(path: str) -> Optional[str]:
    if not path or not os.path.isfile(path):
        return None
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def build_provenance(
    profile: Profile,
    generated_lua: str,
    types_lua_path: Optional[str] = None,
    base_lua_path: Optional[str] = None,
    game_build: Optional[str] = None,
) -> Dict:
    """Assemble a provenance record for an export."""
    record = {
        "tool": "Architect Lua Config Lab",
        "tool_version": __version__,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_name": profile.name,
        "profile_hash": profile_hash(profile),
        "types_lua_sha256": sha256_file(types_lua_path),
        "base_lua_sha256": sha256_file(base_lua_path),
        "game_build": game_build or profile.game_build or None,
        "generated_lua_sha256": sha256_text(generated_lua),
    }
    return record
