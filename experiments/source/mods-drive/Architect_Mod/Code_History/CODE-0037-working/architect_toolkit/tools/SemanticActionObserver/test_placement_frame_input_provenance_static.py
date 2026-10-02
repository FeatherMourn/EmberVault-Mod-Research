import unittest

import capstone

from tools.SemanticActionObserver.scan_placement_frame_input_provenance_static import (
    build_basic_blocks,
    classify_frame_location,
    classify_incoming_register,
    frame_slot_events,
    preserve_caller_callsite_separation,
    reaching_memory_definitions,
    simulate_prologue,
    stack_slot_reads,
)


class PlacementFrameInputProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        self.decoder.detail = True
        self.frame = {
            "rbpOffsetFromEntry": -0x100,
            "rspOffsetFromEntry": -0x200,
            "pushes": [{"rspOffsetAfterFromEntry": -8}, {"rspOffsetAfterFromEntry": -16}],
        }

    def decode(self, encoded):
        return list(self.decoder.disasm(bytes.fromhex(encoded), 0x1000))

    def test_rbp_rsp_normalization_from_synthetic_prologue(self):
        ins = self.decode("55 41 57 48 8D 6C 24 E0 48 81 EC 80 00 00 00")
        model = simulate_prologue(ins)
        self.assertEqual(model["rbpOffsetFromEntry"], -0x30)
        self.assertEqual(model["rspOffsetFromEntry"], -0x90)
        slot = classify_frame_location(8, model)
        self.assertEqual(slot["classification"], "FUNCTION_LOCAL_STACK_SLOT")
        self.assertEqual(slot["entryRspOffset"], -0x28)

    def test_direct_frame_slot_store_and_load(self):
        ins = self.decode("48 89 4D 08 48 8B 45 08 C3")
        cfg = build_basic_blocks(ins)
        events = frame_slot_events(ins, self.frame, 8)
        reads = stack_slot_reads(ins, 8, self.frame)
        self.assertEqual([row["instructionIndex"] for row in events], [0])
        self.assertEqual(events[0]["mustWrite"], True)
        self.assertEqual([row["instructionRva"] for row in reads], ["0x1004"])

    def test_lea_alias_followed_by_indirect_store_and_load(self):
        ins = self.decode("48 8D 4D 08 48 89 19 48 8B 01 C3")
        events = frame_slot_events(ins, self.frame, 8)
        reads = stack_slot_reads(ins, 8, self.frame)
        self.assertTrue(any(row["instructionIndex"] == 1 and row["kind"] == "DIRECT_FRAME_STORE" for row in events))
        self.assertTrue(any(row["instructionRva"] == "0x1007" for row in reads))

    def test_unique_predecessor_definition_after_merge(self):
        # Both branch paths converge before the only full-width store.
        ins = self.decode("85 C0 74 03 90 EB 01 90 48 89 4D 08 48 8B 45 08 C3")
        cfg = build_basic_blocks(ins)
        events = frame_slot_events(ins, self.frame, 8)
        read_index = next(i for i, row in enumerate(ins) if row.address == 0x100C)
        defs = reaching_memory_definitions(ins, cfg, events)[read_index]
        self.assertEqual(defs, {5})

    def test_ambiguous_branch_merge_remains_ambiguous(self):
        ins = self.decode("85 C0 74 06 48 89 4D 08 EB 04 48 89 55 08 48 8B 45 08 C3")
        cfg = build_basic_blocks(ins)
        events = frame_slot_events(ins, self.frame, 8)
        read_index = next(i for i, row in enumerate(ins) if row.address == 0x100E)
        defs = reaching_memory_definitions(ins, cfg, events)[read_index]
        self.assertEqual(len(defs), 2)

    def test_incoming_argument_mapping_requires_frame_and_callsite_evidence(self):
        model = {"rbpOffsetFromEntry": -0x100, "rspOffsetFromEntry": -0x200,
                 "pushes": [{"rspOffsetAfterFromEntry": -16}]}
        unresolved = classify_frame_location(0x128, model)
        self.assertEqual(unresolved["classification"], "UNRESOLVED_FRAME_RELATIVE_LOCATION")
        proven = classify_frame_location(0x128, model, {"proven": True, "callsiteRva": "0x2222"})
        self.assertEqual(proven["classification"], "INCOMING_STACK_ARGUMENT")
        self.assertEqual(proven["argumentIndex"], 5)
        self.assertEqual(classify_incoming_register("rcx", None)["status"], "UNSOLVED")
        self.assertEqual(classify_incoming_register("rcx", {"proven": True})["status"], "PROVEN_STATIC")

    def test_multiple_direct_callers_remain_separate(self):
        rows = [
            {"callsiteRva": "0x3000", "callerFunctionStartRva": "0x2000", "argumentSource": "RCX"},
            {"callsiteRva": "0x1000", "callerFunctionStartRva": "0x0800", "argumentSource": "RDX"},
        ]
        result = preserve_caller_callsite_separation(rows)
        self.assertEqual([row["callsiteRva"] for row in result], ["0x1000", "0x3000"])
        self.assertEqual(len({row["callsiteRva"] for row in result}), 2)
        self.assertEqual([row["argumentSource"] for row in result], ["RDX", "RCX"])

    def test_unknown_helper_call_is_a_safe_stop_not_a_guessed_definition(self):
        ins = self.decode("48 8D 4D 08 E8 00 00 00 00 48 8B 45 08 C3")
        cfg = build_basic_blocks(ins)
        events = frame_slot_events(ins, self.frame, 8)
        call_event = next(row for row in events if row["kind"] == "UNKNOWN_CALL_MAY_WRITE_EXACT_SLOT")
        self.assertEqual(call_event["mustWrite"], False)
        self.assertEqual(call_event["evidenceStatus"], "UNSOLVED_OPAQUE_CALL_CLOBBER")
        read_index = next(i for i, row in enumerate(ins) if row.address == 0x1009)
        defs = reaching_memory_definitions(ins, cfg, events)[read_index]
        self.assertEqual(defs, {1})
        self.assertNotEqual(call_event["evidenceStatus"], "PROVEN_STATIC")


if __name__ == "__main__":
    unittest.main()
