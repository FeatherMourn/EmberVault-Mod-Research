"""Inventory required user-facing documentation and fail closed on omissions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED = {
    "user_guide": "docs/USER_GUIDE.md",
    "mod_author_guide": "docs/MOD_AUTHOR_GUIDE.md",
    "blendertools_guide": "docs/BLENDERTOOLS_GUIDE.md",
    "beginner_content_wizard_guide": "docs/BEGINNER_CONTENT_WIZARD_GUIDE.md",
    "mod_installation_guide": "docs/MOD_INSTALLATION_GUIDE.md",
    "save_backup_guide": "docs/SAVE_BACKUP_GUIDE.md",
    "eml_api_guide": "docs/EML_API_GUIDE.md",
    "clone_patch_guide": "docs/CLONE_AND_PATCH_GUIDE.md",
    "visual_substitution_guide": "docs/VISUAL_SUBSTITUTION_GUIDE.md",
    "tuning_guide": "docs/TUNING_GUIDE.md",
    "builder_guide": "docs/BUILDER_GUIDE.md",
    "world_generation_research_guide": "docs/WORLD_GENERATION_RESEARCH_GUIDE.md",
    "research_probe_guide": "docs/RESEARCH_PROBE_GUIDE.md",
    "research_lab_guide": "docs/RESEARCH_LAB_GUIDE.md",
    "recovery_guide": "docs/RECOVERY_GUIDE.md",
    "update_migration_guide": "docs/UPDATE_MIGRATION_GUIDE.md",
    "capability_report": "research/CAPABILITY_LIMITATIONS_REPORT_20260927.md",
    "security_safety_policy": "docs/SECURITY_AND_SAFETY_POLICY.md",
    "troubleshooting_guide": "docs/TROUBLESHOOTING_GUIDE.md",
    "current_source_release_verification": "docs/CURRENT_SOURCE_RELEASE_VERIFICATION_20260929.md",
}


def audit(root: Path) -> dict:
    root = Path(root).resolve()
    files = {key: (root / relative).is_file() for key, relative in REQUIRED.items()}
    missing = [key for key, present in files.items() if not present]
    return {
        "schema": "control_center.documentation_audit.v1",
        "valid": not missing,
        "required_count": len(REQUIRED),
        "present_count": sum(files.values()),
        "files": {key: {"path": REQUIRED[key], "present": present} for key, present in files.items()},
        "missing": missing,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
