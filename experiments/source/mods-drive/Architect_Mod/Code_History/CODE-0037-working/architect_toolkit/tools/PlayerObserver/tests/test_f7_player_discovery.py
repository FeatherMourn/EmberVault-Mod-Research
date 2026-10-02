import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "runtime" / "ArchitectRuntime.ps1"


class F7PlayerDiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = RUNTIME.read_text(encoding="utf-8")

    def test_discovery_commands_are_read_only(self):
        for action in ("begin", "mark", "end"):
            self.assertRegex(
                self.text,
                rf'action = "player\.discovery\.{action}";[^\r\n]+state = "read_only"',
            )

    def test_marker_allowlist_is_complete_and_bounded(self):
        match = re.search(r"\$playerDiscoveryPhases = @\((.*?)\)", self.text, re.S)
        self.assertIsNotNone(match)
        phases = re.findall(r'"([A-Z_]+)"', match.group(1))
        self.assertEqual(
            phases,
            [
                "BASELINE", "SPRINT_ACTIVE", "SPRINT_RECOVERY", "MANA_SPEND",
                "MANA_RECOVERY", "DAMAGE", "HEAL", "INVENTORY", "FAST_TRAVEL",
                "POST_TRAVEL",
            ],
        )
        self.assertIn('$script:playerDiscoveryPhases -notcontains $phase', self.text)
        self.assertIn('state = "invalid_marker"', self.text)

    def test_native_handoff_is_atomic_and_read_only(self):
        self.assertIn('player_discovery_command.json', self.text)
        self.assertIn('Write-AtomicUtf8Json -LiteralPath $playerDiscoveryCommandFile', self.text)
        self.assertIn('readOnly = $true', self.text)
        self.assertNotRegex(self.text, r'player\.discovery\.(?:set|fill|max|infinite)')

    def test_research_ui_does_not_enable_player_mutations(self):
        self.assertIn('action = "player.discovery.begin"', self.text)
        self.assertIn('action = "player.discovery.end"', self.text)
        self.assertIn('action = "player.discovery.mark"', self.text)
        self.assertRegex(self.text, r'action = "player\.stamina\.fill";[^\r\n]+state = "unsupported"')


if __name__ == "__main__":
    unittest.main()
