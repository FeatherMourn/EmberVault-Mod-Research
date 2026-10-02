"""Safe, offline builder/furnishing catalog utilities."""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class CatalogItem:
    item_id: int
    name: str
    category: str
    ingredients: dict[str, int]
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class BuildPlan:
    name: str
    item_quantities: dict[int, int]

    def materials(self, catalog: "BuilderCatalog") -> dict[str, int]:
        by_id = {item.item_id: item for item in catalog.items}
        selected: list[CatalogItem] = []
        for item_id, quantity in self.item_quantities.items():
            if item_id not in by_id or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
                raise ValueError(f"Invalid build-plan item or quantity: {item_id}")
            selected.extend([by_id[item_id]] * quantity)
        return catalog.material_totals(selected)

    def item_breakdown(self, catalog: "BuilderCatalog") -> list[dict[str, Any]]:
        """Return resolved plan lines with per-line material totals.

        This is intentionally an offline explanation layer: it never implies
        that the loader can place or craft anything in the live game.
        """
        by_id = {item.item_id: item for item in catalog.items}
        breakdown: list[dict[str, Any]] = []
        for item_id, quantity in self.item_quantities.items():
            if item_id not in by_id or not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
                raise ValueError(f"Invalid build-plan item or quantity: {item_id}")
            item = by_id[item_id]
            breakdown.append({
                "item_id": item.item_id,
                "name": item.name,
                "category": item.category,
                "quantity": quantity,
                "materials": {key: int(value) * quantity for key, value in sorted(item.ingredients.items())},
            })
        return breakdown

    def shortages(self, catalog: "BuilderCatalog", available: dict[str, int]) -> dict[str, int]:
        """Return only the additional materials needed for this plan."""
        if not isinstance(available, dict):
            raise ValueError("available materials must be an object.")
        required = self.materials(catalog)
        shortages: dict[str, int] = {}
        for material, amount in required.items():
            held = available.get(material, 0)
            if not isinstance(held, int) or held < 0:
                raise ValueError(f"Available quantity must be a non-negative integer: {material}")
            if amount > held:
                shortages[material] = amount - held
        return shortages

    def to_dict(self) -> dict[str, Any]:
        return {"schema_version": 1, "name": self.name, "item_quantities": self.item_quantities}

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "BuildPlan":
        if not isinstance(payload, dict) or not str(payload.get("name", "")).strip():
            raise ValueError("Build plan requires a name.")
        if payload.get("schema_version", 1) != 1:
            raise ValueError("Unsupported build plan schema version.")
        quantities = payload.get("item_quantities")
        if not isinstance(quantities, dict):
            raise ValueError("Build plan requires item_quantities.")
        normalized = {}
        for key, value in quantities.items():
            item_id = int(key)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise ValueError(f"Invalid quantity for item {item_id}.")
            normalized[item_id] = value
        return cls(str(payload["name"]).strip(), normalized)


class BuilderCatalog:
    """Search and planning only; never writes game state."""

    def __init__(self, items: Iterable[CatalogItem] = ()):
        self.items = tuple(items)
        self.favorites: set[int] = set()

    def set_favorite(self, item_id: int, enabled: bool = True) -> None:
        if not any(item.item_id == item_id for item in self.items):
            raise KeyError(f"Unknown catalog item: {item_id}")
        if enabled:
            self.favorites.add(item_id)
        else:
            self.favorites.discard(item_id)

    def favorite_items(self) -> list[CatalogItem]:
        return [item for item in self.items if item.item_id in self.favorites]

    def add_items(self, records: Iterable[dict[str, Any]]) -> int:
        """Add valid, non-duplicate planning entries without touching game data."""
        existing = {item.item_id for item in self.items}
        additions = self.from_records(record for record in records if isinstance(record, dict) and record.get("id") not in existing)
        if additions.items:
            self.items = tuple((*self.items, *additions.items))
        return len(additions.items)

    @staticmethod
    def discover_control_center_projects(root: Path) -> list[dict[str, Any]]:
        """Discover locally generated projects as planning-only catalog entries."""
        records: list[dict[str, Any]] = []
        for manifest_path in sorted(Path(root).rglob("mod.json")):
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                identity = manifest.get("identity", {})
                item_id = identity.get("numeric_id") if isinstance(identity, dict) else None
                if isinstance(item_id, int) and not isinstance(item_id, bool) and item_id > 0 and str(manifest.get("name", "")).strip():
                    records.append({
                        "id": item_id,
                        "name": manifest["name"],
                        "category": "Custom furniture",
                        "ingredients": {},
                        "tags": ["custom", "research-only"],
                    })
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                continue
        return records

    def build_plan(self, name: str, item_quantities: dict[int, int]) -> BuildPlan:
        if not str(name).strip():
            raise ValueError("Build plan name is required.")
        for item_id, quantity in item_quantities.items():
            if not any(item.item_id == item_id for item in self.items):
                raise KeyError(f"Unknown catalog item: {item_id}")
            if not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0:
                raise ValueError(f"Quantity must be positive: {item_id}")
        return BuildPlan(str(name).strip(), dict(item_quantities))

    def save_build_plan(self, plan: BuildPlan, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(plan.to_dict(), indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    def load_build_plan(self, path: Path) -> BuildPlan:
        plan = BuildPlan.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))
        for item_id in plan.item_quantities:
            if not any(item.item_id == item_id for item in self.items):
                raise KeyError(f"Unknown catalog item in saved plan: {item_id}")
        return plan

    def save_favorites(self, path: Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps({"schema_version": 1, "favorite_item_ids": sorted(self.favorites)}, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    def load_favorites(self, path: Path) -> None:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(payload, dict) and payload.get("schema_version", 1) != 1:
            raise ValueError("Unsupported favorites schema version.")
        ids = payload.get("favorite_item_ids", []) if isinstance(payload, dict) else []
        known = {item.item_id for item in self.items}
        self.favorites = {item_id for item_id in ids if item_id in known and isinstance(item_id, int)}

    @classmethod
    def from_records(cls, records: Iterable[dict[str, Any]]) -> "BuilderCatalog":
        items: list[CatalogItem] = []
        seen_ids: set[int] = set()
        for record in records:
            if not isinstance(record, dict):
                continue
            item_id = record.get("item_id", record.get("id"))
            name = record.get("name", record.get("debug_name", ""))
            if not isinstance(item_id, int) or isinstance(item_id, bool) or item_id <= 0 or item_id in seen_ids or not str(name).strip():
                continue
            ingredients = record.get("ingredients", record.get("resources", {}))
            if not isinstance(ingredients, dict):
                ingredients = {}
            normalized_ingredients = {
                str(key): value for key, value in ingredients.items()
                if isinstance(key, str) and key.strip() and isinstance(value, int)
                and not isinstance(value, bool) and value > 0
            }
            seen_ids.add(item_id)
            items.append(CatalogItem(
                item_id, str(name), str(record.get("category", "Uncategorized")),
                normalized_ingredients,
                tuple(str(tag) for tag in record.get("tags", []) if isinstance(tag, str)),
            ))
        return cls(items)

    @classmethod
    def from_json_file(cls, path: Path) -> "BuilderCatalog":
        payload = json.loads(Path(path).read_text(encoding="utf-8-sig"))
        records = payload.get("items", payload) if isinstance(payload, dict) else payload
        if not isinstance(records, list):
            raise ValueError("Builder catalog JSON must contain an array or an items array.")
        return cls.from_records(records)

    def search(self, query: str = "", category: str | None = None,
               tags: set[str] | None = None) -> list[CatalogItem]:
        needle = query.casefold().strip()
        required = {tag.casefold() for tag in (tags or set())}
        return [
            item for item in self.items
            if (not needle or needle in item.name.casefold() or needle in str(item.item_id))
            and (category is None or item.category == category)
            and required.issubset({tag.casefold() for tag in item.tags})
        ]

    def recommend(self, *, category: str | None = None,
                  tags: set[str] | None = None, limit: int = 12) -> list[CatalogItem]:
        """Return deterministic building-set recommendations offline."""
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError("limit must be a positive integer.")
        wanted = {str(tag).casefold() for tag in (tags or set())}
        has_filter = category is not None or bool(wanted) or bool(self.favorites)
        scored: list[tuple[int, int, CatalogItem]] = []
        for index, item in enumerate(self.items):
            item_tags = {tag.casefold() for tag in item.tags}
            score = 1 if not has_filter else 0
            score += 100 if category is not None and item.category == category else 0
            score += 10 * len(wanted.intersection(item_tags))
            score += 1 if item.item_id in self.favorites else 0
            scored.append((score, -index, item))
        scored.sort(key=lambda value: (value[0], value[1]), reverse=True)
        return [item for score, _, item in scored if score > 0][:limit]

    @staticmethod
    def material_totals(items: Iterable[CatalogItem], quantity: int = 1) -> dict[str, int]:
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("quantity must be a positive integer.")
        totals: dict[str, int] = {}
        for item in items:
            for material, amount in item.ingredients.items():
                totals[material] = totals.get(material, 0) + int(amount) * quantity
        return dict(sorted(totals.items()))

    @staticmethod
    def manifest_metadata() -> dict[str, Any]:
        return {
            "feature": "builder_catalog",
            "state": "verified-offline",
            "runtime_mutation": False,
        }
