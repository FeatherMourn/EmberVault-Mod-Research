import threading, unittest
from tools.SemanticActionObserver.relay_safety_closure import RelaySlots, match, OneShotLifecycle

class RelaySafetyTests(unittest.TestCase):
    def good(self, slots, gen=None):
        return match(slots, current_rbp=0x2000, current_entry_rsp=0x1EF8,
                     current_return=0x140000000+0x280F8B, module_base=0x140000000,
                     stack_identity='S', current_stack_identity='S')
    def test_two_producers_different_tuples_no_false_accept(self):
        s=RelaySlots(8); barrier=threading.Barrier(2)
        def p(i): barrier.wait(); s.publish(0x1d0+i*0x100,0x2000+i*0x100,0x1ef8+i*0x100,thread=i)
        ts=[threading.Thread(target=p,args=(i,)) for i in (1,2)]
        [t.start() for t in ts]; [t.join() for t in ts]
        self.assertIsNone(self.good(s))
    def test_nested_and_stale_rejected(self):
        s=RelaySlots(); s.publish(0x1fd0,0x2000,0x1ef8); g=s.publish(0x2fd0,0x3000,0x2ef8)
        self.assertIsNone(self.good(s)); s.slots[g & 7]=s.slots[g & 7] # explicit stale presentation
        self.assertIsNone(self.good(s))
    def test_single_candidate_consumed_once(self):
        s=RelaySlots(); s.publish(0x1fd0,0x2000,0x1ef8)
        self.assertIsNotNone(self.good(s)); self.assertIsNone(self.good(s))
    def test_cross_stack_and_marker_fail(self):
        s=RelaySlots(); s.publish(0x1fd0,0x2000,0x1ef8)
        self.assertIsNone(match(s,current_rbp=0x2000,current_entry_rsp=0x1ef8,current_return=1,module_base=0x140000000,stack_identity='A',current_stack_identity='B'))
    def test_multiple_structural_candidates_reject(self):
        s=RelaySlots(); s.publish(0x1fd0,0x2000,0x1ef8); s.publish(0x1fd1,0x2001,0x1ef9)
        self.assertIsNone(self.good(s))
    def test_zero_candidates_reject(self): self.assertIsNone(self.good(RelaySlots()))
    def test_generation_wrap_is_nonzero_and_bounded(self):
        s=RelaySlots(); s.next=(1<<64)-2; g=s.publish(1,0x31,1); self.assertEqual(g,(1<<64)-1); g=s.publish(2,0x32,2); self.assertEqual(g,0) # zero is rejected by matcher
    def test_lifecycle_install_timeout_uninstall(self):
        l=OneShotLifecycle(); self.assertTrue(l.install()); self.assertFalse(l.install()); self.assertTrue(l.timeout()); self.assertTrue(l.uninstall()); self.assertEqual(l.state,"idle")

if __name__=='__main__': unittest.main()
