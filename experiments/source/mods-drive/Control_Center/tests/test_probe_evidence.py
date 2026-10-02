import tempfile
import unittest
from pathlib import Path

from core.probe_evidence import inspect_probe


class ProbeEvidenceTests(unittest.TestCase):
    def test_stale_log_is_never_reported_as_success(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text("[CC-MINIMAL-CLONE:x] CLONED_ITEM|1\n", encoding="utf-8")
            self.assertEqual(inspect_probe(path, "x", path.stat().st_mtime)["status"], "stale_log")

    def test_freshness_mode_requires_a_baseline(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text("[CC-MINIMAL-CLONE:x] CLONED_ITEM|1\n", encoding="utf-8")
            self.assertEqual(inspect_probe(path, "x", require_fresh=True)["status"], "freshness_baseline_required")

    def test_classifies_clone_registration(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text("[CC-MINIMAL-CLONE:x] DONOR|true\n[CC-MINIMAL-CLONE:x] REGISTER|true|table\n[CC-MINIMAL-CLONE:x] CLONED_ITEM|1\n", encoding="utf-8")
            self.assertEqual(inspect_probe(path, "x")["status"], "clone_registered")

    def test_classifies_custom_furniture_prefix_without_promoting_visual_proof(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-CHAIR-CLONE] DISCOVERED_CLONE|true\n"
                "[CC-CHAIR-CLONE] REGISTERED|itemId=3987657001|recipeId=3987657002\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "[CC-CHAIR-CLONE]")["status"], "furniture_clone_registered")

    def test_classifies_actor_sequence_identity_clone(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ACTOR-SEQUENCE-CLONE:x] DONOR_PRESERVED|true\n"
                "[CC-ACTOR-SEQUENCE-CLONE:x] PARITY|sequences=true|events=true|types=true\n"
                "[CC-ACTOR-SEQUENCE-CLONE:x] RESULT|identity_clone_registered\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "x")["status"], "actor_sequence_identity_clone_registered")

    def test_distinguishes_registry_growth_from_index_lookup(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-REGISTRY-CLONE:x] REGISTRY|3520->3521\n"
                "[CC-REGISTRY-CLONE:x] INDEX_LOOKUP|false\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "x")["status"], "registry_grew_lookup_unverified")

    def test_metadata_probe_without_fresh_log_is_not_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text("[CC-RESOURCE-METADATA:x] API|assets=table\n", encoding="utf-8")
            self.assertEqual(inspect_probe(path, "x", path.stat().st_mtime)["status"], "stale_log")

    def test_classifies_metadata_api_surface(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-RESOURCE-METADATA:x] API|assets=table|metadata=function\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "x")["status"], "metadata_api_exposed")

    def test_extracts_clean_message_from_structured_eml_json(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                '{"fields":{"message":"[CC-RESOURCE-METADATA:x] API|assets=table|metadata=function"}}\n',
                encoding="utf-8",
            )
            result = inspect_probe(path, "x")
            self.assertEqual(result["events"], ["API|assets=table|metadata=function"])

    def test_classifies_metadata_enumeration(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-RESOURCE-METADATA:x] API|metadata=function\n"
                "[CC-RESOURCE-METADATA:x] MATCH|guid|part=0\n"
                "[CC-RESOURCE-METADATA:x] COUNT|3609\n"
                "[CC-RESOURCE-METADATA:x] RESULT|true\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "x")["status"], "metadata_enumeration_verified")

    def test_classifies_metadata_enumeration_without_match(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-RESOURCE-METADATA:x] API|metadata=function\n"
                "[CC-RESOURCE-METADATA:x] COUNT|1\n"
                "[CC-RESOURCE-METADATA:x] RESULT|false\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "x")["status"], "metadata_enumeration_verified")

    def test_classifies_enemy_arsenal_enumeration(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-ARSENAL-ENUM] API|resources=function\n"
                "[CC-ENEMY-ARSENAL-ENUM] RESULT|ok=true|type=keen::enemy::EnemyArsenalRegistryResource\n"
                "[CC-ENEMY-ARSENAL-ENUM] COUNT|1\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "enemy_arsenal_enumeration_probe_1076226")["status"], "metadata_enumeration_verified")

    def test_classifies_enemy_arsenal_payload_read(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-ARSENAL-READ:enemy_arsenal_payload_read_probe_1076226] API|resources=function\n"
                "[CC-ENEMY-ARSENAL-READ:enemy_arsenal_payload_read_probe_1076226] DATA|ok=true|type=userdata\n"
                "[CC-ENEMY-ARSENAL-READ:enemy_arsenal_payload_read_probe_1076226] FIELD|arsenal_1|key=attacks|type=userdata\n"
                "[CC-ENEMY-ARSENAL-READ:enemy_arsenal_payload_read_probe_1076226] ARSENAL_COUNT|170\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "enemy_arsenal_payload_read_probe_1076226")["status"], "payload_read_verified")

    def test_classifies_enemy_arsenal_graph_entry_read(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-ARSENAL-GRAPH:enemy_arsenal_graph_entry_probe_1076226] DATA|ok=true|type=userdata\n"
                "[CC-ENEMY-ARSENAL-GRAPH:enemy_arsenal_graph_entry_probe_1076226] FIELD|attacks|key=commands|type=userdata\n"
                "[CC-ENEMY-ARSENAL-GRAPH:enemy_arsenal_graph_entry_probe_1076226] FIELD_COUNT|attacks|ok=true|count=6\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "enemy_arsenal_graph_entry_probe_1076226")["status"], "graph_entry_read_verified")

    def test_classifies_enemy_arsenal_dependency_identity_read(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-ARSENAL-DEPS:enemy_arsenal_dependency_probe_1076226] RESULT|ok=true\n"
                "[CC-ENEMY-ARSENAL-DEPS:enemy_arsenal_dependency_probe_1076226] FIRST|attacks|ok=true|type=userdata\n"
                "[CC-ENEMY-ARSENAL-DEPS:enemy_arsenal_dependency_probe_1076226] VALUE|attacks.description|ok=true|type=userdata|text={\\\"actionSequence\\\":\\\"a837f190-d163-4ef5-a48e-3ea7caac7296\\\"}\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "enemy_arsenal_dependency_probe_1076226")["status"], "dependency_identity_read_verified")

    def test_classifies_enemy_arsenal_sequence_graph_boundary(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-ARSENAL-SEQ:enemy_arsenal_sequence_probe_1076226] RESULT|ok=true\n"
                "[CC-ENEMY-ARSENAL-SEQ:enemy_arsenal_sequence_probe_1076226] ATTACK|ok=true|type=userdata\n"
                "[CC-ENEMY-ARSENAL-SEQ:enemy_arsenal_sequence_probe_1076226] FIRST|attack.actions|ok=true|type=nil\n"
                "[CC-ENEMY-ARSENAL-SEQ:enemy_arsenal_sequence_probe_1076226] BEHAVIOR|ok=true|type=userdata\n"
                "[CC-ENEMY-ARSENAL-SEQ:enemy_arsenal_sequence_probe_1076226] FIRST|behavior.actions|ok=true|type=userdata\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "enemy_arsenal_sequence_probe_1076226")["status"], "sequence_graph_boundary_verified")

    def test_classifies_mapped_variant_boundary_observation(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-BEHAVIOR-ACTION:enemy_behavior_action_probe_1076226] RESULT|ok=true\n"
                "[CC-ENEMY-BEHAVIOR-ACTION:enemy_behavior_action_probe_1076226] FIRST|behavior.actions|ok=true|type=userdata\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "enemy_behavior_action_probe_1076226")["status"], "mapped_variant_boundary_observed")

    def test_classifies_helper_probe_without_readback_as_inconclusive(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-BEHAVIOR-HELPER:enemy_behavior_helper_probe_1076226] RESULT|ok=true\n",
                encoding="utf-8",
            )
            self.assertEqual(inspect_probe(path, "enemy_behavior_helper_probe_1076226")["status"], "helper_probe_inconclusive")

    def test_classifies_attack_donor_scan(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ENEMY-ARSENAL-SCAN:enemy_arsenal_attack_scan_probe_1076226] "
                "SUMMARY|arsenals=170|attacks=73|populated=24\n",
                encoding="utf-8",
            )
            self.assertEqual(
                inspect_probe(path, "enemy_arsenal_attack_scan_probe_1076226")["status"],
                "attack_donor_scan_verified",
            )

    def test_classifies_empty_action_sequence_resource_family(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ACTION-SEQUENCE-RESOURCE:enemy_action_sequence_resource_probe_1076226] "
                "RESULT|ok=true|type=table\n"
                "[CC-ACTION-SEQUENCE-RESOURCE:enemy_action_sequence_resource_probe_1076226] COUNT|0\n",
                encoding="utf-8",
            )
            self.assertEqual(
                inspect_probe(path, "enemy_action_sequence_resource_probe_1076226")["status"],
                "action_sequence_resource_empty",
            )

    def test_classifies_action_sequence_resource_inventory(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-ACTION-SEQUENCE-RESOURCE:enemy_action_sequence_resource_probe_1076226] "
                "RESOURCE|key=1|data_ok=true|type=userdata\n"
                "[CC-ACTION-SEQUENCE-RESOURCE:enemy_action_sequence_resource_probe_1076226] COUNT|2202\n",
                encoding="utf-8",
            )
            self.assertEqual(
                inspect_probe(path, "enemy_action_sequence_resource_probe_1076226")["status"],
                "action_sequence_resource_inventory_verified",
            )

    def test_prefers_live_journal_attachment_over_insert_status(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "latest.eml.log"
            path.write_text(
                "[CC-JOURNAL-CLONE:x] RESULT|journal_registry_clone_insert_verified\n"
                "[CC-JOURNAL-CLONE:x] RESULT|journal_live_attachment_runtime_verified\n",
                encoding="utf-8",
            )
            self.assertEqual(
                inspect_probe(path, "x")["status"],
                "journal_live_attachment_runtime_verified",
            )


if __name__ == "__main__":
    unittest.main()
