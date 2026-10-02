"""Offline Architect Core contracts and capability-map queries.

This package deliberately has no Enshrouded/process/runtime dependencies.  It
validates architecture evidence and dependency data only.
"""

from .contracts import VALID_STATUSES, load_capability_map, validate_capability_map
from .query import ArchitectCoreQuery
from .target import ArchitectTargetObservation, TargetProvenance, TargetKind, new_unknown_observation

__all__ = ["VALID_STATUSES", "load_capability_map", "validate_capability_map", "ArchitectCoreQuery",
           "ArchitectTargetObservation", "TargetProvenance", "TargetKind", "new_unknown_observation"]
