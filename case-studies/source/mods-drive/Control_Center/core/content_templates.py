"""Research-gated starter manifests for supported content families."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .content_classes import ContentClassService


class ContentTemplateError(ValueError):
    pass


class ContentTemplateService:
    """Generate project-local metadata only; never touches the game install."""

    def __init__(self) -> None:
        self.classes = ContentClassService()

    def build(self, content_class: str, namespace: str, name: str, output: Path | None = None) -> dict[str, Any]:
        profile = self.classes.profile(content_class)
        namespace = self._slug(namespace, "namespace")
        name = str(name).strip()
        if not name:
            raise ContentTemplateError("Content name is required.")
        template: dict[str, Any] = {
            "schema": "control_center.content_template.v1",
            "namespace": namespace,
            "name": name,
            "content_class": profile.name,
            "feature_state": "research-only" if profile.status != "verified" else "experimental",
            "verification_boundary": profile.status,
            "required_resource_types": list(profile.required_resource_types),
            "donor_metadata": {},
            "donor_validation": [],
            "assets": [],
            "localization": {"required": True, "status": "research-only"},
        }
        if output is not None:
            output = Path(output)
            output.parent.mkdir(parents=True, exist_ok=True)
            temporary = output.with_suffix(output.suffix + ".tmp")
            temporary.write_text(json.dumps(template, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            temporary.replace(output)
        return template

    @staticmethod
    def _slug(value: str, label: str) -> str:
        result = re.sub(r"[^a-zA-Z0-9_-]+", "_", str(value).strip()).strip("_").lower()
        if not result:
            raise ContentTemplateError(f"{label} is required.")
        return result[:64]
