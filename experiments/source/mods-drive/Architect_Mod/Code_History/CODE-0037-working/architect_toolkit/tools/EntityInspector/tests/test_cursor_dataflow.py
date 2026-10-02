import json,unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]

class CursorDataFlowTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((ROOT/"bridge/cursor_target_dataflow.json").read_text(encoding="utf-8"))
 def test_exact_build_gate(self):
  self.assertTrue(self.data["build"]["supported"])
  self.assertEqual(self.data["build"]["sha256"],"AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781")
 def test_exact_two_field_scope(self):
  self.assertEqual(self.data["scope"]["fields"],["CursorSelectObjectAction.selectedObjectId +0x08","ClientCursor.previousSelectedEntityId +0xC0"])
  self.assertEqual([(x["reflectionIndex"],x["offset"]) for x in self.data["targets"]],[(2670,"0x8"),(2842,"0xC0")])
 def test_registry_derivation_is_correlated(self):
  self.assertEqual(self.data["primaryReflectionRegistry"]["baseRva"],"0x18125B0")
  self.assertTrue(self.data["primaryReflectionRegistry"]["validatedByBothTargets"])
 def test_no_false_displacement_promotion(self):
  result=self.data["result"]
  self.assertIsNone(result["selectedObjectIdProducer"]);self.assertIsNone(result["selectedObjectIdConsumer"])
  self.assertIsNone(result["previousSelectedEntityIdWriter"]);self.assertIsNone(result["previousSelectedEntityIdReader"])
  self.assertEqual(result["conclusion"],"NO_CURSOR_DATAFLOW_CONVERGENCE")
 def test_runtime_untouched_and_no_hook(self):
  self.assertEqual(self.data["descriptorRootedFunctions"],[])
  self.assertEqual(self.data["safety"],{"customRaycast":False,"hookInstalled":False,"mutation":False,"pointerScan":False,"runtimeChanged":False})

if __name__=="__main__":unittest.main()
