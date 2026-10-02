"""Deterministic CODE-0004 affine/domain safety tests."""
import unittest

from tools.SemanticActionObserver.scan_placement_computed_destination_arithmetic_static import (
    AffineExpr, recover_loop_domain, safe_multiply, sign_extend, solve_target_overlap,
    zero_extend,
)


class ComputedDestinationArithmeticTests(unittest.TestCase):
    def test_lea_base_index_scale_displacement(self):
        e = AffineExpr(const=8).add(AffineExpr.var("i").scale(8))
        self.assertEqual(e.text(), "8 + 8*i")

    def test_chained_lea_add_shl(self):
        e = AffineExpr.var("i").scale(2).scale(8).add(16)
        self.assertEqual(e.text(), "16 + 16*i")

    def test_imul_constant(self):
        self.assertEqual(safe_multiply(AffineExpr.var("k"), 16).text(), "16*k")

    def test_zero_extend_index(self):
        e = zero_extend(AffineExpr.var("eax", width=32), 64)
        self.assertEqual(e.width, 64)
        self.assertFalse(e.signed)

    def test_signed_movsxd_index(self):
        e = sign_extend(AffineExpr.var("ecx", width=32), 64)
        self.assertTrue(e.signed)
        self.assertEqual(e.width, 64)

    def test_simple_induction_recovery(self):
        d = recover_loop_domain(0, 1, 8)
        self.assertEqual(d["domain"], [0, 7])
        self.assertEqual(d["step"], 1)

    def test_unsigned_loop_bound(self):
        self.assertEqual(recover_loop_domain(0, 1, 4, unsigned=True)["signedness"], "unsigned")

    def test_signed_loop_bound(self):
        self.assertEqual(recover_loop_domain(-2, 2, 4, unsigned=False)["signedness"], "signed")

    def test_stride_congruence_cannot_hit(self):
        e = AffineExpr(const=0).add(AffineExpr.var("k").scale(16))
        result = solve_target_overlap(e, {"k": range(0, 4)}, (8, 16), 8)
        self.assertEqual(result["classification"], "CANNOT_HIT_TARGET")
        self.assertTrue(result["proof"])

    def test_exact_target_witness(self):
        e = AffineExpr(const=8).add(AffineExpr.var("k").scale(8))
        result = solve_target_overlap(e, {"k": range(0, 8)}, (56, 64), 8)
        self.assertEqual(result["classification"], "CAN_HIT_TARGET")
        self.assertEqual(result["witnesses"][0]["destinationOffset"], 56)

    def test_write_width_overlap_start_differs(self):
        e = AffineExpr(const=52)
        result = solve_target_overlap(e, {}, (56, 64), 8)
        self.assertEqual(result["classification"], "CAN_HIT_TARGET")

    def test_correlated_variables_not_independent_intervals(self):
        e = AffineExpr.var("a").add(AffineExpr.var("j"))
        result = solve_target_overlap(e, {"a": range(0, 4), "j": range(0, 4)}, (6, 7), 1,
                                       constraints=lambda v: v["j"] < v["a"])
        self.assertEqual(result["classification"], "CANNOT_HIT_TARGET")

    def test_ambiguous_merge_is_unresolved(self):
        e = AffineExpr(terms={"<width-mismatch>": 1}, wrapped=True)
        result = solve_target_overlap(e, {"x": range(0, 2)}, (0, 1), 1)
        self.assertEqual(result["classification"], "UNRESOLVED_WRAPAROUND")

    def test_non_affine_variable_product_stops(self):
        self.assertIsNone(safe_multiply(AffineExpr.var("x"), AffineExpr.var("y")))

    def test_wraparound_sensitive_arithmetic(self):
        e = AffineExpr.var("x", width=32).truncate(16)
        result = solve_target_overlap(e, {"x": range(0, 2)}, (0, 1), 1)
        self.assertEqual(result["classification"], "UNRESOLVED_WRAPAROUND")

    def test_variable_size_with_proven_destination(self):
        dest = AffineExpr(const=8)
        size = AffineExpr.var("n").scale(8)
        self.assertEqual(dest.text(), "8")
        self.assertEqual(size.text(), "8*n")

    def test_known_size_unresolved_destination(self):
        unresolved = AffineExpr(terms={"unknown": 1}, wrapped=True)
        self.assertTrue(unresolved.wrapped)

    def test_parent_callsite_domains_are_separate(self):
        a = recover_loop_domain(0, 1, 3)
        b = recover_loop_domain(0, 1, 7)
        self.assertNotEqual(a["domain"], b["domain"])

    def test_can_hit_does_not_promote_last_writer(self):
        result = solve_target_overlap(AffineExpr(const=56), {}, (56, 64), 8)
        last_proven_writer = None
        self.assertEqual(result["classification"], "CAN_HIT_TARGET")
        self.assertIsNone(last_proven_writer)


if __name__ == "__main__":
    unittest.main()
