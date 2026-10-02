import unittest
from tools.GameSettingsMapper.recover_descriptor_callbacks import build

class DescriptorCallbackRecoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.result=build()
    def test_exact_build_and_exact_target_scope(self):
        self.assertEqual(self.result['build']['revision'],1076226)
        self.assertEqual({2703,3410},{d['reflectionIndex'] for d in self.result['descriptors']})
        self.assertIn('exact reflection indices',self.result['method']['scope'])
    def test_descriptor_bounds_and_identity_validate(self):
        expected={2703:('0x198F520','0x198F5D0','0x9919D92D'),3410:('0x18CBCA0','0x18CBD50','0x81B10CBB')}
        for d in self.result['descriptors']:
            start,end,h=expected[d['reflectionIndex']];self.assertEqual((d['objectStartRva'],d['objectEndRva']),(start,end));self.assertEqual(d['objectSize'],0xB0);self.assertEqual(d['validation']['internalHash'],h);self.assertTrue(d['validation']['matchesExpected'])
    def test_every_owned_pointer_is_relocated_and_non_code(self):
        for d in self.result['descriptors']:
            self.assertTrue(d['ownedRelocations']);self.assertEqual(d['ownedCodePointerCount'],0);self.assertFalse(d['callbackCandidates'])
            self.assertTrue(all(p['relocationType']=='IMAGE_REL_BASED_DIR64' for p in d['ownedRelocations']))
            self.assertTrue(all(p['classification']!='code' for p in d['ownedRelocations']))
    def test_no_hook_or_mutation_convergence(self):
        self.assertEqual(self.result['conclusion'],'NO_DESCRIPTOR_CONVERGENCE');self.assertFalse(self.result['safeObserveHookJustified']);self.assertIsNone(self.result['dispatchBoundary']);self.assertIsNone(self.result['readbackBoundary']);self.assertTrue(self.result['mutationBlocked'])

if __name__=='__main__':unittest.main()
