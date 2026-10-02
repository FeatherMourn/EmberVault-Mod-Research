import unittest

import capstone

from tools.SemanticActionObserver.scan_placement_helper_buffer_field_provenance_static import (
    analyze_helper_instructions,
    select_last_unique_writer,
    source_provenance,
)


class PlacementHelperBufferFieldProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.decoder = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
        self.decoder.detail = True

    def decode(self, encoded):
        return list(self.decoder.disasm(bytes.fromhex(encoded), 0x1000))

    def test_direct_exact_store_to_output_plus_38(self):
        report = analyze_helper_instructions(self.decode("48 8B FA 48 89 7F 38 C3"), 0x9000)
        row = next(row for row in report["writes"] if row["destinationOffset"] == "0x38")
        self.assertTrue(row["exactTargetHit38"])
        self.assertEqual(row["writeWidth"], 8)

    def test_direct_exact_store_to_output_plus_78(self):
        report = analyze_helper_instructions(self.decode("48 8B FA 48 89 7F 78 C3"), 0x9000)
        row = next(row for row in report["writes"] if row["destinationOffset"] == "0x78")
        self.assertTrue(row["exactTargetHit78"])

    def test_wider_fixed_store_overlaps_target(self):
        report = analyze_helper_instructions(self.decode("48 8B FA 48 89 7F 34 C3"), 0x9000)
        row = next(row for row in report["writes"] if row["destinationOffset"] == "0x34")
        self.assertTrue(row["overlapsTarget38"])
        self.assertFalse(row["exactTargetHit38"])

    def test_lea_alias_followed_by_field_store(self):
        report = analyze_helper_instructions(self.decode("48 8B FA 48 8D 4F 38 48 89 19 C3"), 0x9000)
        row = next(row for row in report["writes"] if row["destinationOffset"] == "0x38")
        self.assertEqual(row["evidenceStatus"], "PROVEN_STATIC")

    def test_forwarded_output_pointer_into_direct_nested_callee(self):
        report = analyze_helper_instructions(self.decode("48 8B FA 48 8D 4F 38 E8 F4 FF FF FF C3"), 0x9000)
        nested = report["nestedDirectCallees"][0]
        self.assertTrue(nested["directCallEvidence"])
        self.assertEqual(nested["outputPointerArguments"]["RCX"], "output+0x38")

    def test_call_order_overwrite_selects_later_proven_writer(self):
        report = analyze_helper_instructions(self.decode("48 8B FA 48 89 7F 38 48 89 57 38 C3"), 0x9000)
        writes = [row for row in report["fixedFieldWrites"] if row["overlapsTarget38"]]
        self.assertEqual(len(writes), 2)
        self.assertEqual(select_last_unique_writer([writes[-1]])["instructionRva"], writes[-1]["instructionRva"])

    def test_branch_dependent_writers_remain_unresolved_at_merge(self):
        report = analyze_helper_instructions(self.decode("48 8B FA 85 C0 74 04 48 89 7F 38 EB 04 48 89 57 38 C3"), 0x9000)
        writes = [row for row in report["fixedFieldWrites"] if row["overlapsTarget38"]]
        self.assertEqual(len(writes), 2)
        self.assertIsNone(select_last_unique_writer(writes, ambiguous=True))

    def test_source_provenance_object_field_load(self):
        ins = self.decode("8B 41 1C")[0]
        source = source_provenance(ins)
        self.assertEqual(source["baseRegister"], "RCX")
        self.assertEqual(source["fieldOffset"], "0x1C")
        self.assertEqual(source["status"], "PROVEN_STATIC")

    def test_source_provenance_reduces_to_incoming_argument(self):
        ins = self.decode("8B C1")[0]
        source = source_provenance(ins)
        self.assertEqual(source["terminalSource"], "incoming register or alias")
        self.assertEqual(source["status"], "INFERRED")

    def test_opaque_call_is_safe_stop(self):
        report = analyze_helper_instructions(self.decode("E8 FB FF FF FF C3"), 0x9000)
        self.assertEqual(report["writes"], [])
        self.assertEqual(report["nestedDirectCallees"], [])
        self.assertNotEqual(report["outputBufferArgument"]["status"], "PROVEN_STATIC")


if __name__ == "__main__":
    unittest.main()
