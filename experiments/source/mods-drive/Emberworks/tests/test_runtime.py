import unittest

from construction_sdk import (Coordinate, Piece, RuntimeCapabilityError, RuntimeReport,
                               SimulatedAdapter, SimulatedWorld, UnavailableRuntimeAdapter)


class RuntimeContractTests(unittest.TestCase):
    def test_simulated_adapter_matches_runtime_boundary(self):
        world = SimulatedWorld()
        adapter = SimulatedAdapter(world)
        piece = Piece(Coordinate(1, 2, 3), "wall", "stone")
        self.assertTrue(adapter.place(piece))
        self.assertEqual(adapter.inspect(piece.position), piece)
        self.assertTrue(adapter.remove(piece.position))
        self.assertIsNone(adapter.inspect(piece.position))

    def test_report_tracks_latest_evidence(self):
        report = RuntimeReport("simulated")
        report.record("single_piece_placement", "verified", "simulated adapter")
        report.record("live_capture", "probe_required", "no live adapter")
        self.assertEqual(report.status("single_piece_placement"), "verified")
        self.assertEqual(report.status("live_capture"), "probe_required")
        self.assertEqual(report.status("unknown"), "unverified")

    def test_probe_export_maps_only_what_it_proves(self):
        report = RuntimeReport.from_probe_export({
            "probe": "emberworks_worldwright",
            "state": "capabilities_observed",
            "detail": "read-only API inventory",
        }, game_build="test-build")
        self.assertEqual(report.status("eml_mod_loading"), "verified")
        self.assertEqual(report.status("runtime_probe"), "verified")
        self.assertEqual(report.status("world_capture"), "unverified")
        self.assertEqual(report.status("construction_mutation"), "unverified")

    def test_unavailable_runtime_adapter_fails_explicitly(self):
        adapter = UnavailableRuntimeAdapter()
        with self.assertRaises(RuntimeCapabilityError):
            adapter.player_position()
        with self.assertRaises(RuntimeCapabilityError):
            adapter.place(Piece(Coordinate(0, 0, 0), "wall"))

    def test_report_requires_verified_capability(self):
        report = RuntimeReport("eml")
        report.record("read_only_asset_probe", "verified", "asset evidence")
        report.require_verified("read_only_asset_probe")
        with self.assertRaises(RuntimeCapabilityError):
            report.require_verified("construction_mutation")


if __name__ == "__main__":
    unittest.main()
