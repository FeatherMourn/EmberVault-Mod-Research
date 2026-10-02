"""Custom localization catalog creation with deterministic keys and fallback."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


LANGUAGE_RE = re.compile(r"^[a-z]{2}(?:-[A-Z]{2})?$")


@dataclass(frozen=True)
class LocalizationIssue:
    severity: str
    key: str
    message: str


@dataclass(frozen=True)
class LocalizationCatalog:
    namespace: str
    default_language: str
    entries: dict[str, dict[str, str]]
    issues: tuple[LocalizationIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    def resolve(self, key: str, language: str) -> str | None:
        values = self.entries.get(key, {})
        requested = LocalizationService.normalize_language(language)
        candidates = [requested]
        if "-" in requested:
            candidates.append(requested.split("-", 1)[0])
        for candidate in candidates:
            if candidate in values:
                return values[candidate]
        if "-" in requested:
            base = requested.split("-", 1)[0]
            for available in sorted(values):
                if available.startswith(base + "-"):
                    return values[available]
        default = LocalizationService.normalize_language(self.default_language)
        if default in values:
            return values[default]
        return next(iter(values.values()), None)


class LocalizationService:
    """Build catalogs without claiming that runtime localization injection is verified."""

    def build(self, namespace: str, entries: dict[str, dict[str, str]], default_language: str = "en") -> LocalizationCatalog:
        issues: list[LocalizationIssue] = []
        try:
            from .content_identity import ContentIdentityService
            namespace = ContentIdentityService.validate_namespace(namespace)
        except ValueError as exc:
            issues.append(LocalizationIssue("error", "", str(exc)))
            namespace = str(namespace).strip().lower()
        default_language = self.normalize_language(default_language)
        if not LANGUAGE_RE.fullmatch(default_language):
            issues.append(LocalizationIssue("error", "", f"Invalid default language: {default_language}"))
        normalized: dict[str, dict[str, str]] = {}
        for raw_key, raw_values in entries.items():
            key = f"{namespace}.{self._slug(raw_key)}"
            if key in normalized:
                issues.append(LocalizationIssue("error", key, "Localization key collides with another entry after slugging."))
                continue
            if not isinstance(raw_values, dict) or not raw_values:
                issues.append(LocalizationIssue("error", key, "Localization entry must contain at least one language."))
                continue
            normalized[key] = {}
            for language, value in raw_values.items():
                normalized_language = self.normalize_language(language)
                if not LANGUAGE_RE.fullmatch(normalized_language):
                    issues.append(LocalizationIssue("error", key, f"Invalid language code: {language}"))
                elif not isinstance(value, str) or not value.strip():
                    issues.append(LocalizationIssue("error", key, f"Empty translation for {normalized_language}."))
                elif normalized_language in normalized[key]:
                    issues.append(LocalizationIssue("error", key, f"Duplicate language after normalization: {normalized_language}"))
                else:
                    normalized[key][normalized_language] = value
            if default_language not in normalized[key]:
                issues.append(LocalizationIssue("warning", key, f"Missing default-language translation: {default_language}"))
        return LocalizationCatalog(namespace, default_language, normalized, tuple(issues))

    @classmethod
    def validate_payload(cls, payload: Any) -> tuple[LocalizationIssue, ...]:
        """Validate a saved catalog without changing or writing the payload."""
        issues: list[LocalizationIssue] = []
        if not isinstance(payload, dict) or payload.get("schema") != "control_center.localization.v1":
            return (LocalizationIssue("error", "", "Unsupported localization schema."),)
        namespace = payload.get("namespace")
        try:
            from .content_identity import ContentIdentityService
            ContentIdentityService.validate_namespace(str(namespace))
        except ValueError as exc:
            issues.append(LocalizationIssue("error", "", str(exc)))
        default_language = cls.normalize_language(payload.get("default_language", ""))
        if not LANGUAGE_RE.fullmatch(default_language):
            issues.append(LocalizationIssue("error", "", f"Invalid default language: {payload.get('default_language')}"))
        entries = payload.get("entries")
        if not isinstance(entries, dict):
            issues.append(LocalizationIssue("error", "", "Localization payload requires an entries object."))
            return tuple(issues)
        namespace_prefix = f"{str(namespace).strip().lower()}."
        for key, values in entries.items():
            if not isinstance(key, str) or not key.strip():
                issues.append(LocalizationIssue("error", str(key), "Localization key cannot be empty."))
                continue
            if not key.casefold().startswith(namespace_prefix.casefold()):
                issues.append(LocalizationIssue("error", key, f"Localization key must belong to namespace {namespace}."))
                continue
            if not isinstance(values, dict) or not values:
                issues.append(LocalizationIssue("error", key, "Localization entry must contain at least one language."))
                continue
            seen: set[str] = set()
            for language, value in values.items():
                normalized_language = cls.normalize_language(language)
                if not LANGUAGE_RE.fullmatch(normalized_language):
                    issues.append(LocalizationIssue("error", key, f"Invalid language code: {language}"))
                if normalized_language in seen:
                    issues.append(LocalizationIssue("error", key, f"Duplicate language after normalization: {normalized_language}"))
                if not isinstance(value, str) or not value.strip():
                    issues.append(LocalizationIssue("error", key, f"Empty translation for {language}."))
                seen.add(normalized_language)
        return tuple(issues)

    @classmethod
    def load(cls, path: Path) -> LocalizationCatalog:
        """Load and validate a saved catalog before it enters a build.

        This is deliberately a payload operation: it does not claim that the
        current game build consumes newly-created localization resources.
        """
        try:
            payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        except (OSError, ValueError) as exc:
            raise ValueError(f"Unable to read localization catalog: {exc}") from exc
        issues = list(cls.validate_payload(payload))
        if any(issue.severity == "error" for issue in issues):
            raise ValueError("Invalid localization catalog: " + "; ".join(issue.message for issue in issues))
        namespace = str(payload["namespace"]).strip().lower()
        default_language = cls.normalize_language(payload["default_language"])
        entries = {
            str(key): {cls.normalize_language(language): str(value) for language, value in values.items()}
            for key, values in payload["entries"].items()
        }
        return LocalizationCatalog(namespace, default_language, entries, tuple(issues))

    @staticmethod
    def validate_runtime_evidence(entry: Any) -> tuple[str, ...]:
        """Reject promotion claims without explicit game-facing evidence."""
        if not isinstance(entry, dict):
            return ("Localization runtime evidence must be an object.",)
        issues: list[str] = []
        if entry.get("schema") != "control_center.localization_probe_result.v1":
            issues.append("runtime evidence schema is unsupported")
        if not str(entry.get("build", "")).strip():
            issues.append("runtime evidence requires a build")
        if not str(entry.get("status", "")).strip():
            issues.append("runtime evidence requires a status")
        if not isinstance(entry.get("ui_consumption_verified"), bool):
            issues.append("ui_consumption_verified must be boolean")
        if not isinstance(entry.get("promotion_ready"), bool):
            issues.append("promotion_ready must be boolean")
        if entry.get("promotion_ready"):
            if not entry.get("ui_consumption_verified"):
                issues.append("promotion_ready requires ui_consumption_verified=true")
            if not str(entry.get("visual_evidence", "")).strip():
                issues.append("promotion_ready requires visual_evidence")
        if entry.get("ui_consumption_verified") and not str(entry.get("visual_evidence", "")).strip():
            issues.append("ui_consumption_verified requires visual_evidence")
        return tuple(issues)

    @staticmethod
    def normalize_language(language: Any) -> str:
        value = str(language).strip()
        if "-" in value:
            base, region = value.split("-", 1)
            return f"{base.lower()}-{region.upper()}"
        return value.lower()

    def save(self, catalog: LocalizationCatalog, path: Path) -> None:
        payload: dict[str, Any] = {
            "schema": "control_center.localization.v1",
            "namespace": catalog.namespace,
            "default_language": catalog.default_language,
            "feature_state": "research-only",
            "entries": catalog.entries,
        }
        temporary = Path(path).with_suffix(Path(path).suffix + ".tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        temporary.replace(path)

    def save_lua_payload(self, catalog: LocalizationCatalog, path: Path) -> None:
        """Export a deterministic Lua payload for localization-capable loaders."""
        def quote(value: str) -> str:
            return json.dumps(value, ensure_ascii=False)
        lines = ["-- Generated by Enshrouded Control Center.", "-- Payload only: registration requires a loader localization capability.", "return {"]
        for key in sorted(catalog.entries):
            lines.append(f"  [{quote(key)}] = {{")
            for language in sorted(catalog.entries[key]):
                lines.append(f"    [{quote(language)}] = {quote(catalog.entries[key][language])},")
            lines.append("  },")
        lines.append("}\n")
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text("\n".join(lines), encoding="utf-8")
        temporary.replace(destination)

    @staticmethod
    def _slug(value: str) -> str:
        value = re.sub(r"[^a-zA-Z0-9]+", "_", str(value).strip()).strip("_").lower()
        return value or "unnamed"
