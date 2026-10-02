"""Verify the dependency-free public site and its privacy boundary."""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def validate() -> None:
    required_assets = ("index.html", "site.css", "site.js", "embervault-catalog.json", "content/community.json")
    missing = [name for name in required_assets if not (ROOT / name).is_file()]
    if missing:
        raise ValueError(f"Missing public site assets: {', '.join(missing)}")
    catalog = json.loads((ROOT / "embervault-catalog.json").read_text(encoding="utf-8"))
    if "profile_id" in json.dumps(catalog) or "local_path" in json.dumps(catalog) or "evidence_text" in json.dumps(catalog):
        raise ValueError("Public catalog contains a private field")
    community = json.loads((ROOT / "schemas" / "community.schema.json").read_text(encoding="utf-8"))
    if set(community["properties"]) != {"user", "submission", "forum_thread", "shared_project", "moderation_action"}:
        raise ValueError("Community schema is incomplete")
    community_data = json.loads((ROOT / "content" / "community.json").read_text(encoding="utf-8"))
    for project in community_data.get("projects", []):
        if project.get("visibility") != "public" or project.get("status") != "published":
            raise ValueError("Unpublished project entered the public community snapshot")
    for thread in community_data.get("threads", []):
        if thread.get("status") not in {"open", "locked", "archived"}:
            raise ValueError("Hidden community thread entered the public snapshot")
    public_text = json.dumps(community_data)
    if any(token in public_text for token in ("password", "session_token", "backup_path", "local_path")):
        raise ValueError("Community snapshot contains private data")
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    if "site.js" not in html or "embervault-catalog.json" not in (ROOT / "site.js").read_text(encoding="utf-8"):
        raise ValueError("Public site is not wired to the reviewed catalog")


if __name__ == "__main__":
    validate()
    print("Public site verification passed")
