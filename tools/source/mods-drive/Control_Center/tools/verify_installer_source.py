"""Verify that installer source references current user-facing documents."""
from __future__ import annotations
import argparse, json
from pathlib import Path
REQUIRED=["USER_GUIDE.md","MOD_AUTHOR_GUIDE.md","BEGINNER_CONTENT_WIZARD_GUIDE.md","MOD_INSTALLATION_GUIDE.md","SAVE_BACKUP_GUIDE.md","EML_API_GUIDE.md","CLONE_AND_PATCH_GUIDE.md","VISUAL_SUBSTITUTION_GUIDE.md","TUNING_GUIDE.md","BUILDER_GUIDE.md","WORLD_GENERATION_RESEARCH_GUIDE.md","RESEARCH_PROBE_GUIDE.md","RECOVERY_GUIDE.md","UPDATE_MIGRATION_GUIDE.md","TROUBLESHOOTING_GUIDE.md","SECURITY_AND_SAFETY_POLICY.md","CAPABILITY_LIMITATIONS_REPORT_20260927.md","CURRENT_SOURCE_RELEASE_VERIFICATION_20260929.md"]
REQUIRED.insert(2, "BLENDERTOOLS_GUIDE.md")
REQUIRED.insert(14, "RESEARCH_LAB_GUIDE.md")
def verify(path: Path)->dict:
    try: text=Path(path).read_text(encoding="utf-8")
    except OSError as exc: return {"schema":"control_center.installer_source_verification.v1","valid":False,"errors":[str(exc)]}
    missing=[name for name in REQUIRED if name not in text]
    return {"schema":"control_center.installer_source_verification.v1","valid":not missing,"required_count":len(REQUIRED),"required":REQUIRED,"missing":missing}
def main()->int:
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("source",type=Path); args=parser.parse_args(); result=verify(args.source); print(json.dumps(result,indent=2)); return 0 if result["valid"] else 1
if __name__=="__main__": raise SystemExit(main())
