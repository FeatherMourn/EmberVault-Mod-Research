import importlib.util, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
SPEC=importlib.util.spec_from_file_location("sprint",ROOT/"tools"/"CheatSprint"/"analyze_candidates.py")
MOD=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MOD)
class CheatSprintTests(unittest.TestCase):
 def test_every_candidate_is_fail_closed(self):
  self.assertGreaterEqual(len(MOD.CANDIDATES),6)
 def test_no_raw_address_target(self):
  for row in MOD.CANDIDATES:self.assertNotIn("address",row[0].lower())
 def test_current_executable_evidence(self):
  exe=ROOT.parents[1]/"enshrouded.exe"
  if not exe.exists():self.skipTest("game executable unavailable")
  result=MOD.analyze(exe);self.assertTrue(result["build"]["exactMatch"])
  self.assertEqual("NO_SAFE_MUTATION_CANDIDATE_FOUND",result["primaryResult"])
  for c in result["candidates"]:
   if c["signature"]:
    self.assertEqual(1,c["matchCount"],c["feature"]);self.assertTrue(c["signatureAtExpectedRva"],c["feature"])
    self.assertEqual("CURRENT_BUILD_STATIC_CANDIDATE",c["evidenceStatus"])
  self.assertFalse(result["runtimeBehaviorChanged"])
if __name__=="__main__":unittest.main()
