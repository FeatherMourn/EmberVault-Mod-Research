import unittest

from construction_sdk.models import Coordinate
from kinetic_works import KineticComponent, KineticNetwork, NetworkState
from kinetic_works.engine import Belt


class KineticTests(unittest.TestCase):
    def test_network_runs_with_available_power(self):
        network = KineticNetwork("test")
        network.add_component(KineticComponent("wheel", "power_source", power_generated=10))
        network.add_component(KineticComponent("saw", "machine", stress_required=4, ratio=2))
        network.connect("wheel", "saw")
        self.assertEqual(network.simulate(), NetworkState.RUNNING)
        self.assertEqual(network.output_speed, 2)

    def test_overload_and_emergency_stop(self):
        network = KineticNetwork("test")
        network.add_component(KineticComponent("wheel", "power_source", power_generated=2))
        network.add_component(KineticComponent("drill", "machine", stress_required=3))
        self.assertEqual(network.simulate(), NetworkState.OVERLOADED)
        network.emergency_stop()
        self.assertEqual(network.state, NetworkState.STOPPED)
        self.assertEqual(network.output_speed, 0)

    def test_belt_moves_items(self):
        belt = Belt("belt", [(0, 0, 0), (1, 0, 0)], capacity=2)
        belt.add_item("ore")
        belt.start()
        self.assertEqual(belt.move_one(), "ore")
        self.assertIsNone(belt.move_one())

    def test_network_exports_shared_blueprint(self):
        network = KineticNetwork("factory")
        network.add_component(KineticComponent("wheel", "power_source", power_generated=10))
        network.add_component(KineticComponent("saw", "machine", stress_required=2))
        blueprint = network.to_blueprint(
            {"wheel": Coordinate(4, 0, 4), "saw": Coordinate(5, 0, 4)},
            {"power_source": "generator", "machine": "sawbench"},
        )
        self.assertEqual(blueprint.source_type, "kinetic_works")
        self.assertEqual(len(blueprint.pieces), 2)
        self.assertEqual(blueprint.pieces[1].properties["network_id"], "factory")

    def test_belt_exports_path_blueprint(self):
        belt = Belt("ore_line", [(4, 0, 4), (5, 0, 4), (6, 0, 4)], capacity=12)
        blueprint = belt.to_blueprint("belt_resource", "iron")
        self.assertEqual(blueprint.source_type, "kinetic_works")
        self.assertEqual(len(blueprint.pieces), 3)
        self.assertEqual(blueprint.metadata["capacity"], 12)


if __name__ == "__main__":
    unittest.main()
