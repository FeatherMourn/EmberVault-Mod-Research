import tempfile
import unittest
from pathlib import Path

from tools.audit_documentation import audit


class DocumentationAuditTests(unittest.TestCase):
    def test_audit_reports_missing_documents(self):
        with tempfile.TemporaryDirectory() as td:
            result = audit(Path(td))
            self.assertFalse(result["valid"])
            self.assertGreater(result["required_count"], result["present_count"])
            self.assertIn("user_guide", result["missing"])

    def test_audit_accepts_complete_document_set(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            for relative in (
                "docs/USER_GUIDE.md", "docs/MOD_AUTHOR_GUIDE.md", "docs/BLENDERTOOLS_GUIDE.md", "docs/BEGINNER_CONTENT_WIZARD_GUIDE.md",
                "docs/MOD_INSTALLATION_GUIDE.md", "docs/SAVE_BACKUP_GUIDE.md", "docs/EML_API_GUIDE.md",
                "docs/CLONE_AND_PATCH_GUIDE.md", "docs/VISUAL_SUBSTITUTION_GUIDE.md",
                "docs/TUNING_GUIDE.md", "docs/BUILDER_GUIDE.md", "docs/RESEARCH_PROBE_GUIDE.md", "docs/RESEARCH_LAB_GUIDE.md",
                "docs/WORLD_GENERATION_RESEARCH_GUIDE.md",
                "docs/RECOVERY_GUIDE.md", "docs/UPDATE_MIGRATION_GUIDE.md",
                "research/CAPABILITY_LIMITATIONS_REPORT_20260927.md", "docs/SECURITY_AND_SAFETY_POLICY.md",
                "docs/TROUBLESHOOTING_GUIDE.md",
                "docs/CURRENT_SOURCE_RELEASE_VERIFICATION_20260929.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# placeholder\n", encoding="utf-8")
            self.assertTrue(audit(root)["valid"])

    def test_visual_session_runbook_preserves_building_context_gate(self):
        path = Path(__file__).parents[1] / "research" / "VISUAL_SUBSTITUTION_SESSION_CHECKLIST_20260928.md"
        text = path.read_text(encoding="utf-8")
        self.assertIn("accessible player", text)
        self.assertIn("UiBuildingMenu", text)
        self.assertIn("not as catalog or visual-substitution proof", text)


if __name__ == "__main__":
    unittest.main()
