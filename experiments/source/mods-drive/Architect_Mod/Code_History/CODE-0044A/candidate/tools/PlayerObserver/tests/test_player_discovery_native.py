import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HARNESS_H = ROOT / "runtime/native/source/PlayerDiscoveryHarness.h"
HARNESS_C = ROOT / "runtime/native/source/PlayerDiscoveryHarness.c"
NATIVE = ROOT / "runtime/native/source/ArchitectNativeRuntime.c"


class PlayerDiscoveryNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.header = HARNESS_H.read_text(encoding="utf-8")
        cls.impl = HARNESS_C.read_text(encoding="utf-8")
        cls.native = NATIVE.read_text(encoding="utf-8")

    def test_build_gate_is_canonical_and_exact(self):
        gate = re.search(r"player_discovery_initialize\((.*?)\);", self.native, re.S)
        self.assertIsNotNone(gate)
        for condition in (
            "g_buildFingerprintValidated",
            "g_buildingPlaceSignatureMatches == 1",
            "g_hostPeTimestamp == SEMANTIC_SUPPORTED_PE_TIMESTAMP",
            "g_imageSize == SEMANTIC_SUPPORTED_IMAGE_SIZE",
        ):
            self.assertIn(condition, gate.group(1))

    def test_capture_limits_are_hard_bounded(self):
        self.assertIn("PLAYER_DISCOVERY_TOTAL_CAPACITY 512UL", self.header)
        self.assertIn("PLAYER_DISCOVERY_PER_PROBE_CAPACITY 128UL", self.header)
        self.assertIn("PLAYER_DISCOVERY_CAPTURE_BYTE_LIMIT (1024UL * 1024UL)", self.header)
        self.assertIn("g_playerDiscoveryProbeCounts[probe]>=PLAYER_DISCOVERY_PER_PROBE_CAPACITY", self.impl)
        self.assertIn("g_playerDiscovery.eventCount>=PLAYER_DISCOVERY_TOTAL_CAPACITY", self.impl)
        self.assertIn("size+len>PLAYER_DISCOVERY_CAPTURE_BYTE_LIMIT", self.native)

    def test_unsupported_build_cannot_record_or_begin(self):
        self.assertIn("if(!g_playerDiscovery.buildSupported||g_playerDiscovery.active)", self.impl)
        self.assertIn("if(!input||!g_playerDiscovery.buildSupported||!g_playerDiscovery.active)", self.impl)

    def test_marker_allowlist_and_unknown_rejection(self):
        for phase in ("BASELINE", "SPRINT_ACTIVE", "SPRINT_RECOVERY", "MANA_SPEND", "MANA_RECOVERY", "DAMAGE", "HEAL", "INVENTORY", "FAST_TRAVEL", "POST_TRAVEL"):
            self.assertIn(f'"{phase}"', self.impl)
        self.assertIn('"Unknown discovery phase rejected."', self.impl)

    def test_clean_shutdown_and_no_player_probe_install(self):
        self.assertIn("player_discovery_shutdown(GetTickCount64())", self.native)
        self.assertIn("installedProbes\\\": []", self.native)
        self.assertNotRegex(self.impl, r"VirtualProtect|write_process|WriteProcessMemory")


if __name__ == "__main__":
    unittest.main()
