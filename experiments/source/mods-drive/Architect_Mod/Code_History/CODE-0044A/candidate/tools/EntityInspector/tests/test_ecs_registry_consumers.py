import copy,json,unittest
from pathlib import Path
from tools.EntityInspector.recover_ecs_registry_consumers import derive_registry_base,recognize_indexed_lookup,classify_membership,hook_eligible

ROOT=Path(__file__).resolve().parents[3]

class EcsRegistryConsumerTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((ROOT/"bridge/entity_cursor_system_map.json").read_text(encoding="utf-8"))
 def test_registry_base_derivation(self):self.assertEqual(derive_registry_base(((2670,0x1817920),(2842,0x1817E80))),0x18125B0)
 def test_false_registry_base_rejection(self):self.assertIsNone(derive_registry_base(((2670,0x1817920),(2842,0x1817E88))))
 def test_indexed_lookup_recognition(self):self.assertTrue(recognize_indexed_lookup({"rooted_registry","entry_width_8","caller_key_32","returns_descriptor"}))
 def test_incomplete_lookup_rejection(self):self.assertFalse(recognize_indexed_lookup({"entry_width_8","caller_key_32"}))
 def test_typed_membership_and_unrelated_integer(self):
  self.assertEqual(classify_membership("ecs_query"),"TYPED_MEMBERSHIP_ONLY")
  self.assertEqual(classify_membership("integer_literal"),"TYPE_METADATA_ONLY")
 def test_system_query_and_callback_ownership(self):
  self.assertEqual(classify_membership("ecs_system",True),"TYPED_CALLBACK_OWNED")
  self.assertEqual(classify_membership("generated_type_metadata_collection",True),"TYPE_METADATA_ONLY")
 def test_generic_path_rejection_and_type_identity(self):
  self.assertEqual(self.data["conclusion"],"GENERIC_REGISTRY_CONSUMER_ONLY")
  self.assertFalse(self.data["typeIdentityPreservedToCallback"])
  self.assertEqual(self.data["typedSystemCandidates"],[])
 def test_hook_gating(self):
  self.assertTrue(hook_eligible(True,True,True,True,True,True,True))
  self.assertFalse(hook_eligible(True,False,True,True,True,True,True))
  self.assertFalse(self.data["hookEligibility"]["strongObserveCandidate"])
 def test_deterministic_membership_order(self):
  got=[(x["reflectionIndex"],x["slotRva"]) for x in self.data["typeMemberships"]]
  self.assertEqual(got,sorted(got,key=lambda x:(x[0],int(x[1],16))))

if __name__=="__main__":unittest.main()
