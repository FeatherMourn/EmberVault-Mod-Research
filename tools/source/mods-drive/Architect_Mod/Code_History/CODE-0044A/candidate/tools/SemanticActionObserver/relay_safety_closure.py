"""Pure bounded publication/matching model for CODE-0005E tests.

This is a deterministic harness model, not a game/runtime hook implementation.
"""
from dataclasses import dataclass

@dataclass
class RelayRecord:
    generation: int; buffer: int; rbp: int; entry_rsp: int; thread: int = 1

class RelaySlots:
    def __init__(self, count=8):
        if count <= 0 or count & (count-1): raise ValueError("power-of-two slot count required")
        self.count=count; self.slots=[None]*count; self.next=0; self.consumed=set(); self.dropped=0
    def publish(self, buffer, rbp, entry_rsp, thread=1):
        gen=(self.next+1) & ((1<<64)-1); self.next=gen; idx=gen & (self.count-1)
        self.slots[idx]=RelayRecord(gen,buffer,rbp,entry_rsp,thread); return gen
    def candidates(self): return [x for x in self.slots if x is not None]

def match(slots: RelaySlots, *, current_rbp, current_entry_rsp, current_return,
          module_base, stack_identity, current_stack_identity, marker=True,
          buffer_readable=True, field38_readable=True, field78_readable=True,
          multiple_policy="reject"):
    valid=[]
    for rec in slots.candidates():
        if rec.generation in slots.consumed or not rec.generation: continue
        if not rec.buffer or not rec.rbp or not rec.entry_rsp: continue
        if rec.buffer != rec.rbp-0x30 or rec.entry_rsp != rec.rbp-0x108: continue
        if current_return != module_base+0x280F8B or not marker: continue
        if stack_identity != current_stack_identity: continue
        if not (buffer_readable and field38_readable and field78_readable): continue
        valid.append(rec)
    if len(valid) != 1: return None
    rec=valid[0]
    # Consume is unique in this model; stale reuse cannot be accepted.
    if rec.generation in slots.consumed: return None
    slots.consumed.add(rec.generation)
    return rec

class OneShotLifecycle:
    """Synthetic lifecycle state machine; no executable/game target access."""
    def __init__(self): self.state="idle"; self.installed=False; self.accepted=False
    def install(self, expected_ok=True, in_range=True):
        if self.installed or not expected_ok or not in_range: return False
        self.installed=True; self.state="armed"; return True
    def accept(self):
        if not self.installed or self.state != "armed": return False
        self.accepted=True; self.state="complete"; return True
    def timeout(self):
        if not self.installed: return False
        self.state="timeout"; return True
    def uninstall(self):
        if not self.installed: return False
        self.installed=False; self.state="idle"; return True
