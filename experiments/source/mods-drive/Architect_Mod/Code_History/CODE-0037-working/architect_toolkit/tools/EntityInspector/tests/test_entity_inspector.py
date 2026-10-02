import json,re,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

class EntityInspectorTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  from tools.EntityInspector.analyze_entity_targeting import analyze
  cls.report=analyze()
  cls.registry=json.loads((ROOT/"runtime/admin_action_registry.json").read_text(encoding="utf-8"))
  cls.native=(ROOT/"runtime/native/source/EntityInspector.c").read_text(encoding="utf-8")
  cls.host=(ROOT/"runtime/native/source/ArchitectNativeRuntime.c").read_text(encoding="utf-8")
  cls.ps=(ROOT/"runtime/ArchitectRuntime.ps1").read_text(encoding="utf-8")
 def test_build_rejection_and_exact_profile(self):
  self.assertTrue(self.report["build"]["supported"])
  profile=(ROOT/"runtime/native/source/EntityBuildProfile.h").read_text()
  self.assertIn(self.report["build"]["sha256"],profile)
  self.assertIn("ENTITY_PROFILE_PE_TIMESTAMP 0x6A4236C8",profile)
 def test_signature_mismatch_and_duplicate_fail_closed(self):
  self.assertEqual(self.report["selectedVanillaPath"]["signature"],None)
  self.assertFalse(self.report["hookSafety"]["exactSignature"])
  self.assertFalse(self.report["hookSafety"]["uniqueMatch"])
  self.assertFalse(self.report["hookSafety"]["install"])
 def test_invalid_pointer_and_identity_rejected(self):
  self.assertIn("zero probes installed",self.native)
  self.assertNotIn("ReadProcessMemory",self.native)
  self.assertEqual(self.report["resultLayout"]["entityId"],None)
 def test_bounds_and_null_target(self):
  self.assertEqual(self.report["captureBounds"],{"records":64,"bytes":262144})
  self.assertIn("ENTITY_CAPTURE_CAPACITY 64",(ROOT/"runtime/native/source/EntityInspector.h").read_text())
  self.assertEqual(self.report["resultLayout"]["classification"] if "classification" in self.report["resultLayout"] else "UNKNOWN","UNKNOWN")
 def test_registry_and_command_routing(self):
  actions={a["commandId"]:a for a in self.registry["actions"]}
  for command in ("entity.inspect","entity.capture.begin","entity.capture.mark","entity.capture.end","entity.inspect.clear"):
   self.assertIn(command,actions);self.assertTrue(actions[command]["enabled"]);self.assertEqual(actions[command]["risk"],"read_only")
   self.assertIn(command,self.ps)
 def test_zero_mutation_commands_and_shutdown(self):
  self.assertEqual(self.report["mutationCommands"],[])
  self.assertIn("entity_inspector_shutdown(GetTickCount64())",self.host)
  self.assertIn("write_entity_state();",self.host)
 def test_existing_observers_preserved(self):
  for token in ("PlayerObserver.c","PlayerDiscoveryHarness.c","GameSettingsObserver.c","SemanticActionObserver.c"):
   self.assertIn(token,self.host)

if __name__=="__main__":unittest.main()
