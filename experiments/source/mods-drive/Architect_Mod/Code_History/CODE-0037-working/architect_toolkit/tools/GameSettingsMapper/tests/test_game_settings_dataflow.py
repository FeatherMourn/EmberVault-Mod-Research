import json, unittest
from pathlib import Path
from tools.GameSettingsMapper.analyze_game_settings_dataflow import build

ROOT=Path(__file__).resolve().parents[3]

class GameSettingsDataFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.result=build()
    def test_exact_build_and_bounded_offline_method(self):
        self.assertTrue(self.result['build']['sha256'].startswith('AF2F5A1227911D8A'))
        self.assertFalse(self.result['method']['runtimeAccess']); self.assertFalse(self.result['method']['arbitraryMemoryScan'])
        self.assertEqual(self.result['method']['descriptorPointerDepth'],3)
    def test_all_required_registration_families_are_anchored(self):
        self.assertEqual({2702,2703,2784,3410,4311},{a['typeIndex'] for a in self.result['registrationAnchors']})
        self.assertTrue(self.result['descriptorPointerEdges'])
    def test_candidate_schema_and_no_speculative_hook(self):
        required={'candidateId','rva','functionEndRva','callers','callees','dataReferences','likelySide','relationshipReasons','contradictions','classification','uniqueSignature','overwrittenBytesUnderstood','runtimeHookEligibility'}
        self.assertTrue(self.result['candidates'])
        for c in self.result['candidates']:
            self.assertFalse(required-set(c)); self.assertEqual(c['runtimeHookEligibility'],'NO'); self.assertFalse(c['overwrittenBytesUnderstood'])
    def test_write_and_readback_do_not_converge(self):
        c=self.result['convergence'];self.assertEqual(c['result'],'NO_STATIC_CONVERGENCE');self.assertFalse(c['safeObserveHookJustified']);self.assertFalse(c['dispatchCandidateIds']);self.assertFalse(c['readbackCandidateIds'])
    def test_comparable_actions_remain_layout_only(self):
        rows=self.result['comparableVersionedActions'];self.assertGreater(len(rows),20)
        self.assertTrue(any(x['actionVersionField']=='consumedAdminChangeGameSettingsAction' and x['offset']=='0xC4' for x in rows))
        self.assertTrue(all(x['serverConsumer']=='UNSOLVED' for x in rows))

if __name__=='__main__':unittest.main()
