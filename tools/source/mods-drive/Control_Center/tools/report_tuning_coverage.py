"""Report reflected tuning-family coverage by Control Center modules."""
from __future__ import annotations
import argparse, json
from pathlib import Path

PRIORITY = {
    "Building and blueprints": 1,
    "Building and materials": 1,
    "Crafting and recipes": 1,
    "Items and equipment": 1,
    "Game rules and difficulty": 1,
    "Loot and rewards": 2,
    "Loot and fishing": 2,
    "Enemies and combat": 2,
    "Skills and progression": 2,
    "Balance and progression": 2,
    "Inventory and starter loadout": 2,
    "Knowledge and map": 3,
    "Buffs and attributes": 3,
    "Terrain and mining": 3,
    "Time": 3,
    "Fog and atmosphere": 3,
    "Weather and environment": 3,
    "Temperature and environment": 3,
    "Water and environment": 3,
    "Camera": 4,
    "Workshops and production": 2,
}

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inventory", type=Path)
    p.add_argument("modules", type=Path)
    p.add_argument("--output", type=Path, help="also write the complete report to a JSON file")
    args = p.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding="utf-8-sig"))
    covered = {}
    setting_count = 0
    for manifest_path in sorted(args.modules.glob("*/module.json")):
        data = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        settings = data.get("settings", [])
        setting_count += len(settings) if isinstance(settings, list) else 0
        for resource in data.get("target_kfc_resources", []):
            covered.setdefault(resource, []).append({
                "module": data.get("id", manifest_path.parent.name),
                "feature_state": data.get("feature_state", "unclassified"),
                "settings": len(settings) if isinstance(settings, list) else 0,
            })
    families = []
    for family in inventory.get("families", []):
        name = family.get("family", "")
        qualified = [item.get("name") for item in family.get("reflected_types", [])]
        matches = covered.get(name, []) + [covered.get(item, []) for item in qualified]
        matches = [item for group in matches for item in (group if isinstance(group, list) else [])]
        families.append({
            "family": name,
            "category": family.get("category"),
            "reflected_types": qualified,
            "state": "covered" if matches else "uncovered",
            "modules": sorted({item["module"] for item in matches}),
            "feature_states": sorted({item["feature_state"] for item in matches}),
            "priority": PRIORITY.get(family.get("category"), 4),
        })
    uncovered = [item for item in families if item["state"] == "uncovered"]
    queue = sorted(uncovered, key=lambda item: (item["priority"], item["category"] or "", item["family"]))
    report = {
        "schema": "control_center.tuning_coverage.v1",
        "build": inventory.get("build"),
        "inventory_family_count": len(families),
        "covered_family_count": sum(item["state"] == "covered" for item in families),
        "uncovered_family_count": sum(item["state"] == "uncovered" for item in families),
        "module_count": len(list(args.modules.glob("*/module.json"))),
        "user_setting_count": setting_count,
        "families": families,
        "research_queue": [
            {
                "family": item["family"],
                "category": item["category"],
                "priority": item["priority"],
                "reason": "user-facing tuning family; validate one donor/resource at a time"
                if item["priority"] <= 2 else
                "secondary tuning family; validate after priority 1-2 coverage",
            }
            for item in queue
        ],
    }
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0

if __name__ == "__main__": raise SystemExit(main())
