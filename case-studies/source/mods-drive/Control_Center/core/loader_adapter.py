"""Stable Control Center adapter for EML capability and fork provenance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .api_capabilities import CapabilityRegistry


@dataclass(frozen=True)
class LoaderIdentity:
    backend: str
    version: str | None
    upstream_commit: str | None
    fork_label: str | None


@dataclass(frozen=True)
class LoaderCompatibility:
    identity: LoaderIdentity
    capabilities: frozenset[str]
    missing: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def compatible(self) -> bool:
        return not self.missing


class EmlCompatibilityAdapter:
    """Normalize EML/fork metadata without assuming a replacement backend."""

    def __init__(self, identity: LoaderIdentity | None = None) -> None:
        self.identity = identity or LoaderIdentity("EML", None, None, None)
        self.registry = CapabilityRegistry()

    def inspect(self, available: Iterable[str], required: Iterable[str] = ()) -> LoaderCompatibility:
        raw = {str(value).strip() for value in available if str(value).strip()}
        normalized = frozenset(self.registry.normalize(raw))
        required_names = [str(value).strip() for value in required if str(value).strip()]
        missing = tuple(self.registry.missing(required_names, set(normalized)))
        warnings: list[str] = []
        if self.identity.backend.upper() != "EML":
            warnings.append(f"Unexpected loader backend: {self.identity.backend}")
        if self.identity.fork_label and not self.identity.upstream_commit:
            warnings.append("Fork label is present without an upstream commit.")
        if "assets.register_resource" in normalized and "assets.create_resource" in raw:
            warnings.append("register_resource is being provided through a legacy create_resource alias.")
        return LoaderCompatibility(self.identity, normalized, missing, tuple(warnings))

    @staticmethod
    def manifest(identity: LoaderIdentity, capabilities: Iterable[str]) -> dict[str, object]:
        return {
            "schema": "control_center.loader_provenance.v1",
            "backend": identity.backend,
            "version": identity.version,
            "upstream_commit": identity.upstream_commit,
            "fork_label": identity.fork_label,
            "capabilities": sorted({str(value).strip() for value in capabilities if str(value).strip()}),
        }
