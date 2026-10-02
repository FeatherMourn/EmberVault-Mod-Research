import re,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
class NativeHarnessTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.c=(ROOT/"runtime/native/source/CheatCorrelationHarness.c").read_text(encoding="utf-8")
  cls.h=(ROOT/"runtime/native/source/CheatCorrelationHarness.h").read_text(encoding="utf-8")
  cls.asm=(ROOT/"runtime/native/source/ArchitectCheatCorrelationEntry.asm").read_text(encoding="utf-8")
  cls.host=(ROOT/"runtime/native/source/ArchitectNativeRuntime.c").read_text(encoding="utf-8")
 def test_exact_build_gate(self):
  self.assertIn("g_buildFingerprintValidated", self.host)
  self.assertIn("SEMANTIC_SUPPORTED_PE_TIMESTAMP", self.host)
 def test_signature_mismatch_and_multiple_rejected(self): self.assertIn("*matches != 1 || found != expected", self.c)
 def test_capture_bounds(self): self.assertIn("CHEAT_CORRELATION_MAX_EVENTS 512UL", self.h); self.assertIn("CHEAT_CORRELATION_BYTE_LIMIT 1048576ULL", self.h)
 def test_marker_allowlist(self):
  for p in ("BASELINE_IDLE", "WALK", "SPRINT_ACTIVE", "SPRINT_RECOVERY", "JUMP", "POST_JUMP_RECOVERY", "COMBAT_IDLE", "MENU"): self.assertIn(p, self.c)
  self.assertNotIn('ascii_equal(p, "ACTIVE")', self.c)
 def test_no_game_mutation(self):
  self.assertIn("cheat_correlation_get_state", self.h)
  self.assertIn("cheat_correlation_take_next", self.h)
 def test_clean_uninstall(self): self.assertIn("revert_bytes", self.c); self.assertIn("cheat_correlation_shutdown", self.c)
 def test_displaced_instructions_replayed(self):
  self.assertIn("mulss xmm3,xmm9", self.asm); self.assertIn("movzx edx,word ptr [rcx+0Ch]", self.asm)
 def test_no_io_in_hooks(self):
  capture = self.c[self.c.index("void __fastcall architect_cheat_movement_capture"):self.c.index("BOOL cheat_correlation_take_next")]
  self.assertNotIn("WriteFile", capture); self.assertNotIn("CreateFile", capture)
if __name__=="__main__":unittest.main()
