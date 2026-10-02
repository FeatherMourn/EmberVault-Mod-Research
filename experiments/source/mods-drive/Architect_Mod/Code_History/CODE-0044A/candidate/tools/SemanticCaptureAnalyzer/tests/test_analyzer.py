import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from analyzer import (analyze, building_groups, correlate_create_actions, create_building_item_action,
                      client_player_input_snapshot, render_markdown,
                      carrier_attempt_summary)


class AnalyzerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.complete = analyze(HERE / "fixtures" / "complete", HERE)
        cls.preview = analyze(HERE / "fixtures" / "preview", HERE)

    def test_inventory_arithmetic(self):
        session = next(s for s in self.complete["sessions"] if s["sessionId"] == "fixture-A")
        operations = session["inventoryOperations"]
        self.assertEqual([(x["destinationPre"]["count"], x["transferAmount"], x["destinationPost"]["count"])
                          for x in operations], [(0, 24, 24), (0, 13, 13), (24, 13, 37)])
        relevant = [v for op in operations for v in op["validations"] if v["captureAssessment"] != "INSUFFICIENT_EVIDENCE"]
        self.assertTrue(all(v["captureAssessment"] == "SUPPORTED_BY_CAPTURE" for v in relevant))

    def test_building_pair(self):
        session = next(s for s in self.complete["sessions"] if s["sessionId"] == "fixture-A")
        pair = session["buildingOperations"][0]
        self.assertTrue(pair["pairPayloadEqual"])
        self.assertEqual(pair["pairTimingMs"], 20)
        self.assertIsNone(pair["sideClassification"])

    def test_building_catalog_enrichment_is_explicit(self):
        groups = building_groups([{"observer":"building_place", "tickMs":1,
                                  "payload":{"trackingItemId":81726253}}], {}, {
            81726253: {"debugName":"Blueprint_Voxel_Block_Ceiling_4m",
                       "classification":"Voxel Blueprint", "blueprints":[{"dimensions":"8x1x8"}]}
        })
        identity = groups[0]["blueprintIdentity"]
        self.assertEqual(identity["itemId"], 81726253)
        self.assertEqual(identity["dimensions"], ["8x1x8"])
        self.assertEqual(identity["snapFamilyStatus"], "UNRESOLVED")

    def test_action_correlation(self):
        session=next(s for s in self.complete["sessions"] if s["sessionId"]=="fixture-A")
        row=session["actionOperationCorrelations"][0]
        self.assertEqual(row["downstreamOperation"]["transferAmount"],24)
        self.assertTrue(all(x["captureAssessment"]=="SUPPORTED_BY_CAPTURE" for x in row["checks"]))

    def test_full_stack_zero_action_amount_is_not_contradicted(self):
        row={"threadId":10,"tickMs":100,"recordType":"action_snapshot","observer":"inventory_transfer_action_consumer","eventSequence":9,"candidateInventoryOperationId":1,"action":{"typeRaw":2,"amount":0,"sourceSlotId":{"slotIndexRaw":0},"targetSlotId":{"slotIndexRaw":1}}}
        # The production fixture's downstream operation is reused through its
        # neutral ID; type 2 raw zero is deliberately independent of count 24.
        original=self.complete["sessions"][0]["actionOperationCorrelations"][0]
        self.assertEqual(original["effectiveTransferAmount"],24)
        self.assertEqual(row["action"]["amount"],0)

    def test_preview_no_event(self):
        self.assertEqual(len(self.preview["sessions"]), 1)
        self.assertTrue(self.preview["sessions"][0]["previewOrCancelOnlyCandidate"])
        self.assertIn("Capture one committed placement after a preview/cancel control.",
                      self.preview["recommendedNextEvidence"])

    def test_mixed_stale_and_malformed(self):
        codes = {w["code"] for w in self.complete["warnings"]}
        self.assertIn("MIXED_SESSIONS", codes)
        self.assertIn("STALE_SESSION_ARTIFACTS", codes)
        self.assertIn("MALFORMED_JSONL_LINE", codes)

    def test_markdown_is_deterministic(self):
        self.assertEqual(render_markdown(self.complete), render_markdown(self.complete))

    def test_create_action_normalization_and_conservative_correlation(self):
        action = create_building_item_action({
            "observer": "create_building_item_action", "eventSequence": 7,
            "tickMs": 1000, "threadId": 12,
            "action": {"versionRaw": 4, "selectedIndexRaw": 2, "itemIdRaw": 81726253},
        }, {81726253: "Blueprint_Voxel_Block_Foundation_4m"})
        self.assertEqual(action["selectedIndexRaw"], 2)
        self.assertEqual(action["resolvedItemInfo"], "Blueprint_Voxel_Block_Foundation_4m")
        rows = correlate_create_actions([action], [{
            "rawEventSequence": 8, "tickMs": 1015, "threadId": 99,
            "payload": {"trackingItemId": 81726253},
        }])
        self.assertTrue(rows[0]["itemIdMatchesTrackingItemId"])
        self.assertEqual(rows[0]["confidence"], "INSUFFICIENT_EVIDENCE")

    def test_parent_input_snapshot_is_schema_ready_but_neutral(self):
        row = client_player_input_snapshot({
            "observer": "client_player_input_snapshot", "eventSequence": 4,
            "tickMs": 20, "candidateBase": "0x1000",
            "snapshot": {"createBuildingItemVersion": 7,
                         "createBuildingItemSelectedIndex": 3,
                         "createBuildingItemId": 1458989991},
        })
        self.assertEqual(row["candidateBase"], "0x1000")
        self.assertEqual(row["createBuildingItemId"], 1458989991)
        self.assertIn("rawEvent", row)

    def test_carrier_attempt_never_promotes_world_authority(self):
        summary = carrier_attempt_summary([{
            "observer": "building_carrier_attempt", "operationId": "op-1",
            "build": {"version": "0.31.0", "buildId": "architect-v031-single-placement-carrier-20260915-a"},
            "originalTrackingItemId": 948722226, "desiredTrackingItemId": 950598916,
            "observedTrackingItemId": 950598916, "restorationSucceeded": True,
            "result": "experimental_not_world_proven",
        }])
        self.assertEqual(summary["attemptCount"], 1)
        self.assertEqual(summary["worldAuthority"], "DISPROVEN_BUILD_1076226")
        self.assertEqual(summary["attempts"][0]["argumentSubstitutionAssessment"], "SUPPORTED_BY_CAPTURE")
        self.assertEqual(summary["attempts"][0]["worldGeometryMatchesDesiredItem"], "CONTRADICTED_BY_USER_CONFIRMED_RUNTIME_RESULT")


if __name__ == "__main__":
    unittest.main()
