import unittest
from tools.SemanticActionObserver.scan_parent_call_relay_correlation_static import build, EXE

class ParentCallRelayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.m = build(EXE)
    def test_call_and_target(self):
        s=self.m['site']; self.assertEqual(s['originalBytes'],'E8 D3 54 65 00'); self.assertTrue(s['targetMatchesExpected']); self.assertEqual(s['decodedTargetRva'],'0x8D5CA0')
    def test_return_and_no_call(self):
        r=self.m['relay']; self.assertEqual(r['patchWidth'],5); self.assertFalse(r['callsFromRelay']); self.assertFalse(r['modifiesReturnAddress']); self.assertEqual(self.m['site']['returnRva'],'0x2807CD')
    def test_register_contract(self):
        p=self.m['relay']['preserves'];
        for x in ('rcx','rdx','r8','r9','rax','rsp','rbp','rbx','rsi','rdi','r12','r15'): self.assertIn(x,p)
    def test_correlation_fail_closed(self):
        c=self.m['correlation']; self.assertFalse(c['requiresNewGameHook']); self.assertEqual(c['status'],'CORRELATION_UNPROVEN'); self.assertFalse(self.m['runtimeEligibility']['installNow'])
    def test_write_check_not_immutability(self): self.assertEqual(self.m['boundedWriteBetweenConsumers']['status'],'NO_STATIC_WRITE_FOUND_IN_BOUNDED_PATH')

if __name__=='__main__': unittest.main()
