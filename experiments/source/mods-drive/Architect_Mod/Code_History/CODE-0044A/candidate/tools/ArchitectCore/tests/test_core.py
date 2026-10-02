import json
import unittest
from pathlib import Path

from tools.ArchitectCore.contracts import validate_capability_map, validate_feature_graph
from tools.ArchitectCore.query import ArchitectCoreQuery
from tools.ArchitectCore.target import ArchitectTargetObservation, TargetProvenance

ROOT = Path(__file__).resolve().parents[3]


class ArchitectCoreTests(unittest.TestCase):
    def setUp(self):
        self.capabilities = json.loads((ROOT / "bridge/vanilla_capability_map.json").read_text(encoding="utf-8"))
        self.graph = json.loads((ROOT / "bridge/feature_dependency_graph.json").read_text(encoding="utf-8"))

    def test_maps_validate(self):
        validate_capability_map(self.capabilities)
        validate_feature_graph(self.graph, self.capabilities)

    def test_queries(self):
        query = ArchitectCoreQuery(self.capabilities, self.graph)
        self.assertTrue(query.proven())
        self.assertTrue(query.features_blocked_by("build.resolve_runtime_blueprint"))

    def test_duplicate_capability_and_invalid_status_rejected(self):
        bad = json.loads(json.dumps(self.capabilities))
        bad["adapters"][0]["capabilities"].append(bad["adapters"][0]["capabilities"][0])
        with self.assertRaises(ValueError): validate_capability_map(bad)
        bad = json.loads(json.dumps(self.capabilities)); bad["adapters"][0]["capabilities"][0]["status"] = "BOGUS"
        with self.assertRaises(ValueError): validate_capability_map(bad)
        bad = json.loads(json.dumps(self.capabilities)); bad["adapters"][0]["capabilities"][0]["dependencies"] = ["missing"]
        with self.assertRaises(ValueError): validate_capability_map(bad)

    def test_unknown_reference_and_cycle_rejected(self):
        bad = json.loads(json.dumps(self.capabilities)); bad["features"] = [{"id": "x", "requiredCapabilities": ["missing"]}]
        with self.assertRaises(ValueError): validate_capability_map(bad)
        badg = json.loads(json.dumps(self.graph)); badg["features"][0]["dependsOnFeatures"] = [badg["features"][0]["id"]]
        with self.assertRaises(ValueError): validate_feature_graph(badg, self.capabilities)
        bad_caps = json.loads(json.dumps(self.capabilities)); bad_caps["adapters"][0]["capabilities"][0]["status"] = "DISPROVEN"
        badg = json.loads(json.dumps(self.graph)); badg["features"] = [{"id":"x", "requiredCapabilities":[bad_caps["adapters"][0]["capabilities"][0]["id"]], "dependsOnFeatures":[]}]
        with self.assertRaises(ValueError): validate_feature_graph(badg, bad_caps)

    def test_target_observation_is_optional_and_provenance_bearing(self):
        unknown = ArchitectTargetObservation.unknown()
        self.assertEqual(unknown.kind, "unknown")
        self.assertEqual(unknown.to_dict()["provenance"][0]["status"], "UNKNOWN")
        observed = ArchitectTargetObservation(
            target_id="candidate-1", kind="building", entity_identity={"entityId": 42}, confidence=0.8,
            provenance=(TargetProvenance("static-test", "INFERRED", "shape only", "0x1234", "cursor.target"),),
        )
        self.assertEqual(observed.to_dict()["entityIdentity"]["entityId"], 42)
        self.assertEqual(observed.to_dict()["targetId"], "candidate-1")
        with self.assertRaises(ValueError): ArchitectTargetObservation(confidence=1.1)
        with self.assertRaises(ValueError): TargetProvenance("", "UNKNOWN", "missing source")


if __name__ == "__main__": unittest.main()
