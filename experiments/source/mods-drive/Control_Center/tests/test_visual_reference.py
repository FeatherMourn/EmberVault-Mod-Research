import unittest

from core.visual_reference import VisualReferenceEvidence


class VisualReferenceEvidenceTests(unittest.TestCase):
    def _report(self):
        return {
            "schema": "control_center.visual_reference_probe_session.v1",
            "probe_id": "probe",
            "build": "1076226",
            "donor_item_guid": "donor",
            "clone_item_id": 1,
            "replacement_render_model_guid": "model",
            "assignment_accepted": True,
            "donor_preservation_checked": True,
            "registry_mutation": False,
            "panic_observed": False,
            "placed_object_render_verified": False,
            "state": "experimental",
        }

    def test_accepts_clone_only_boundary(self):
        self.assertEqual(VisualReferenceEvidence.validate_report(self._report()), ())

    def test_rejects_unproven_render_claim(self):
        report = self._report()
        report["placed_object_render_verified"] = True
        self.assertIn("visual_evidence", " ".join(VisualReferenceEvidence.validate_report(report)))

    def test_rejects_registry_mutation(self):
        report = self._report()
        report["registry_mutation"] = True
        self.assertIn("registry_mutation must be false", VisualReferenceEvidence.validate_report(report))

    def test_accepts_registered_boundary_without_render_claim(self):
        report = {
            "schema": "control_center.registered_visual_substitution_session.v1",
            "probe_id": "registered", "build": "1076226",
            "replacement_render_model_guid": "model", "placed_entity_reference": "entity",
            "clone_item_id": 1, "clone_recipe_id": 2,
            "visual_assignment_accepted": True, "clone_discovered": True,
            "item_registered": True, "recipe_registered": True, "ui_set_cloned": True,
            "panic_observed": False, "placed_object_visual_verified": False,
            "state": "experimental",
        }
        self.assertEqual(VisualReferenceEvidence.validate_registered_report(report), ())

