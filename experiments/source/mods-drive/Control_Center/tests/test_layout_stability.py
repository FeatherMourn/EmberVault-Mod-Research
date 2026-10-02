import unittest
from types import SimpleNamespace
from gui.control_center import ControlCenter, RIGHT_PANEL_BREAKPOINT

class FakeWidget:
    def __init__(self, width):
        self.width = width; self._right_visible = True; self._resize_child_count = 0; self._resize_transition_count = 0; self.trace = []
        self.right = SimpleNamespace(grid=lambda **kwargs: None, grid_remove=lambda: None)
    def winfo_width(self): return self.width
    def grid_columnconfigure(self, *_args, **_kwargs): pass
    def _trace_resize(self, event=None, **extra): self.trace.append(extra)
    def _responsive_layout(self, event=None): return ControlCenter._responsive_layout(self, event)

class LayoutStabilityTests(unittest.TestCase):
    def test_descendant_configure_is_ignored(self):
        root=FakeWidget(1920); root._responsive_layout(SimpleNamespace(widget=object(),width=900)); self.assertTrue(root._right_visible); self.assertEqual(root._resize_transition_count,0); self.assertEqual(root._resize_child_count,1)
    def test_root_crossing_breakpoint_changes_state_once(self):
        root=FakeWidget(1920); root._responsive_layout(SimpleNamespace(widget=root,width=1920)); root.width=RIGHT_PANEL_BREAKPOINT-1; root._responsive_layout(SimpleNamespace(widget=root,width=1479)); self.assertFalse(root._right_visible); self.assertEqual(root._resize_transition_count,1); root._responsive_layout(SimpleNamespace(widget=root,width=1479)); self.assertEqual(root._resize_transition_count,1); root.width=RIGHT_PANEL_BREAKPOINT; root._responsive_layout(SimpleNamespace(widget=root,width=1480)); self.assertTrue(root._right_visible); self.assertEqual(root._resize_transition_count,2)
    def test_rapid_root_events_do_not_create_transition_storm(self):
        root=FakeWidget(1600)
        for width in [1600,1599,1601,1600,1602,1598]*20: root.width=width; root._responsive_layout(SimpleNamespace(widget=root,width=width))
        self.assertEqual(root._resize_transition_count,0)

if __name__ == '__main__': unittest.main()
