import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]


class PlayerObserverScaffoldTests(unittest.TestCase):
    def test_profile_has_no_guessed_observation_rvas(self):
        text = (ROOT / "runtime/native/source/PlayerBuildProfile.h").read_text(encoding="utf-8")
        for name in ("LOCAL_PLAYER", "HEALTH", "STAMINA", "MANA"):
            self.assertRegex(text, rf"PLAYER_PROFILE_{name}_OBSERVER_RVA\s+0ULL")
        self.assertIn("PLAYER_PROFILE_RUNTIME_PROBE_READY 0", text)

    def test_every_player_classification_is_unsolved(self):
        text = (ROOT / "runtime/native/source/PlayerBuildProfile.h").read_text(encoding="utf-8")
        statuses = re.findall(r'PLAYER_PROFILE_(?:LOCAL_PLAYER|HEALTH|STAMINA|MANA)_STATUS\s+"([A-Z_0-9]+)"', text)
        self.assertEqual(statuses, ["UNSOLVED"] * 4)

    def test_f7_registers_read_only_inspect_and_keeps_mutations_disabled(self):
        text = (ROOT / "runtime/ArchitectRuntime.ps1").read_text(encoding="utf-8")
        self.assertRegex(text, r'action = "player\.inspect";[^\r\n]+state = "read_only"')
        self.assertRegex(text, r'action = "player\.health\.fill";[^\r\n]+state = "unsupported"')
        self.assertRegex(text, r'action = "player\.stamina\.fill";[^\r\n]+state = "unsupported"')

    def test_native_schema_is_atomic_and_null_until_evidence(self):
        text = (ROOT / "runtime/native/source/ArchitectNativeRuntime.c").read_text(encoding="utf-8")
        self.assertIn(r'L"\\player_state.json"', text)
        self.assertIn("write_all(g_playerStatePath,json,p)", text)
        self.assertIn('\\"candidateEntityId\\": null', text)
        self.assertIn('\\"current\\": null', text)

    def test_player_gate_reuses_canonical_validation_after_signature_check(self):
        text = (ROOT / "runtime/native/source/ArchitectNativeRuntime.c").read_text(encoding="utf-8")
        install = text.index("if (install_building_place_hook())")
        initialize = text.index("player_observer_initialize(")
        self.assertGreater(initialize, install)
        gate = text[initialize:initialize + 400]
        self.assertIn("g_buildFingerprintValidated", gate)
        self.assertIn("g_buildingPlaceSignatureMatches == 1", gate)
        self.assertIn("g_hostPeTimestamp == SEMANTIC_SUPPORTED_PE_TIMESTAMP", gate)
        self.assertIn("g_imageSize == SEMANTIC_SUPPORTED_IMAGE_SIZE", gate)


if __name__ == "__main__":
    unittest.main()
