from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from construction_sdk.models import Blueprint, Coordinate, Piece


class NetworkState(str, Enum):
    DESIGNED = "designed"
    RUNNING = "running"
    OVERLOADED = "overloaded"
    STOPPED = "stopped"


@dataclass(frozen=True)
class KineticComponent:
    component_id: str
    component_type: str
    power_generated: float = 0.0
    stress_required: float = 0.0
    ratio: float = 1.0


@dataclass
class KineticNetwork:
    network_id: str
    components: dict[str, KineticComponent] = field(default_factory=dict)
    connections: list[tuple[str, str]] = field(default_factory=list)
    state: NetworkState = NetworkState.DESIGNED
    available_power: float = 0.0
    used_stress: float = 0.0
    output_speed: float = 0.0

    def add_component(self, component: KineticComponent) -> None:
        if component.component_id in self.components:
            raise ValueError(f"duplicate component: {component.component_id}")
        if component.ratio <= 0:
            raise ValueError("component ratio must be positive")
        self.components[component.component_id] = component

    def connect(self, source: str, target: str) -> None:
        if source not in self.components or target not in self.components:
            raise ValueError("both connected components must exist")
        if source == target:
            raise ValueError("component cannot connect to itself")
        connection = (source, target)
        if connection not in self.connections:
            self.connections.append(connection)

    def simulate(self, base_speed: float = 1.0) -> NetworkState:
        self.available_power = sum(c.power_generated for c in self.components.values())
        self.used_stress = sum(c.stress_required for c in self.components.values())
        ratios = [c.ratio for c in self.components.values() if c.ratio != 1.0]
        ratio = ratios[-1] if ratios else 1.0
        self.output_speed = base_speed * ratio
        if self.used_stress > self.available_power and self.available_power >= 0:
            self.state = NetworkState.OVERLOADED
        else:
            self.state = NetworkState.RUNNING
        return self.state

    def emergency_stop(self) -> None:
        self.state = NetworkState.STOPPED
        self.output_speed = 0.0

    def restart(self, base_speed: float = 1.0) -> NetworkState:
        if self.state != NetworkState.STOPPED:
            raise ValueError("network must be stopped before restart")
        return self.simulate(base_speed)

    def to_blueprint(self, layout: dict[str, Coordinate], resource_by_type: dict[str, str],
                     name: str | None = None) -> Blueprint:
        """Export a validated machine layout through the shared Blueprint contract."""
        missing = set(self.components) - set(layout)
        if missing:
            raise ValueError(f"missing layout positions: {sorted(missing)}")
        pieces = []
        for component_id, component in self.components.items():
            if component.component_type not in resource_by_type:
                raise ValueError(f"missing resource for component type: {component.component_type}")
            pieces.append(Piece(layout[component_id], resource_by_type[component.component_type],
                                component.component_type,
                                properties={"network_id": self.network_id, "component_id": component_id,
                                            "ratio": component.ratio}))
        anchor = min((piece.position for piece in pieces), default=Coordinate(0, 0, 0))
        return Blueprint(name or self.network_id, pieces, source_type="kinetic_works", anchor=anchor,
                         metadata={"network_id": self.network_id, "connections": [list(edge) for edge in self.connections]})


@dataclass
class Belt:
    belt_id: str
    path: list[tuple[int, int, int]]
    capacity: int = 8
    items: list[str] = field(default_factory=list)
    running: bool = False

    def start(self) -> None:
        if len(self.items) > self.capacity:
            raise ValueError("belt exceeds capacity")
        self.running = True

    def stop(self) -> None:
        self.running = False

    def add_item(self, item: str) -> None:
        if len(self.items) >= self.capacity:
            raise ValueError("belt is full")
        self.items.append(item)

    def move_one(self) -> str | None:
        if not self.running or not self.items:
            return None
        return self.items.pop(0)

    def to_blueprint(self, resource_id: str = "kinetic:belt", material_id: str = "default") -> Blueprint:
        """Export the belt path as a shared blueprint."""
        positions = [Coordinate(*point) for point in self.path]
        anchor = min(positions, default=Coordinate(0, 0, 0))
        pieces = [Piece(position, resource_id, material_id,
                        properties={"belt_id": self.belt_id, "capacity": self.capacity,
                                    "path_index": index})
                  for index, position in enumerate(positions)]
        return Blueprint(self.belt_id, pieces, source_type="kinetic_works", anchor=anchor,
                         metadata={"belt_id": self.belt_id, "capacity": self.capacity,
                                   "running": self.running})
