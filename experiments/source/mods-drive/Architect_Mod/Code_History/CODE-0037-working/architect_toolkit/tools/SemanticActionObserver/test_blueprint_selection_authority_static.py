import unittest

import capstone

from tools.SemanticActionObserver.scan_blueprint_selection_authority_static import (
    build_basic_blocks,
    reaching_definitions,
)


class BlueprintSelectionSliceTests(unittest.TestCase):
    def decode(self, encoded: str):
        decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        decoder.detail = True
        return list(decoder.disasm(bytes.fromhex(encoded), 0x1000))

    def test_unique_register_and_memory_base_definitions(self):
        instructions = self.decode("48 8B D8 44 8B 03 E8 00 00 00 00 C3")
        cfg = build_basic_blocks(instructions)
        r8 = reaching_definitions(instructions, cfg, "r8")
        rbx = reaching_definitions(instructions, cfg, "rbx")
        self.assertEqual(r8[2], {1})
        self.assertEqual(rbx[1], {0})

    def test_ambiguous_control_flow_merge_stays_ambiguous(self):
        instructions = self.decode("85 C0 74 04 89 CB EB 02 89 D3 44 8B 03 C3")
        cfg = build_basic_blocks(instructions)
        rbx = reaching_definitions(instructions, cfg, "rbx")
        read_index = next(i for i, ins in enumerate(instructions) if ins.address == 0x100A)
        self.assertEqual(len(rbx[read_index]), 2)


if __name__ == "__main__":
    unittest.main()
