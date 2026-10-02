"""
Enshrouded Master Item Catalog & Transmutation Database.
Contains verified item IDs, friendly formatted names, categories, and fast indexing
for inventory item transmutation and spawning.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any

# Primary source path to extracted build catalog
CATALOG_JSON_PATH = Path(__file__).parent.parent / "bridge" / "create_building_item_static_map.json"
ARCHITECT_CATALOG_PATH = Path(__file__).parent.parent.parent / "Architect_Mod" / "Code_History" / "CODE-0037-working" / "architect_toolkit" / "bridge" / "build_catalog.json"
CACHE_JSON_PATH = Path(__file__).parent / "items_cache.json"

# Curated High-Priority Popular Items for Instant One-Click Spawning
POPULAR_ITEMS = [
    {"id": 3087876, "name": "Greater Mana Potion (T5)", "category": "Consumables", "default_stack": 50},
    {"id": 3087875, "name": "Greater Health Potion (T5)", "category": "Consumables", "default_stack": 50},
    {"id": 2045610, "name": "Shroud Survival Flask", "category": "Consumables", "default_stack": 20},
    {"id": 1400201, "name": "Runes (Upgrade Currency)", "category": "Materials", "default_stack": 5000},
    {"id": 1001101, "name": "Flintstone Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1001102, "name": "Rough Stone Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1001103, "name": "Castle Wall Stone Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1001104, "name": "Weathered Stone Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1001105, "name": "Refined Stone Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1001201, "name": "Wood Planks Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1001202, "name": "Palm Wood Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1001301, "name": "Luminescent Blue Block", "category": "Building Blocks", "default_stack": 1000},
    {"id": 1200101, "name": "Iron Ore", "category": "Materials", "default_stack": 500},
    {"id": 1200102, "name": "Copper Ore", "category": "Materials", "default_stack": 500},
    {"id": 1200103, "name": "Tin Ore", "category": "Materials", "default_stack": 500},
    {"id": 1200104, "name": "Obsidian Ore", "category": "Materials", "default_stack": 500},
    {"id": 1200105, "name": "Lapis Lazuli", "category": "Materials", "default_stack": 500},
    {"id": 1200201, "name": "Iron Bar", "category": "Materials", "default_stack": 500},
    {"id": 1200202, "name": "Copper Bar", "category": "Materials", "default_stack": 500},
    {"id": 1200203, "name": "Bronze Bar", "category": "Materials", "default_stack": 500},
    {"id": 1200301, "name": "Metal Scraps", "category": "Materials", "default_stack": 500},
    {"id": 1200401, "name": "Shroud Wood", "category": "Materials", "default_stack": 500},
    {"id": 1200402, "name": "Hardwood", "category": "Materials", "default_stack": 500},
    {"id": 1200501, "name": "Fabric / Linen", "category": "Materials", "default_stack": 500},
    {"id": 1200502, "name": "Leather", "category": "Materials", "default_stack": 500},
    {"id": 1200503, "name": "Padding", "category": "Materials", "default_stack": 500},
    {"id": 1300101, "name": "Ghost Glider", "category": "Equipment", "default_stack": 1},
    {"id": 1300201, "name": "Extraordinary Grappling Hook", "category": "Equipment", "default_stack": 1},
    {"id": 3372205, "name": "Archmage Battle Robes (T5)", "category": "Equipment", "default_stack": 1},
    {"id": 3372206, "name": "Radiant Paladin Chestplate (T5)", "category": "Equipment", "default_stack": 1},
    {"id": 3372207, "name": "Eagle Eye Assassin Tunic (T5)", "category": "Equipment", "default_stack": 1},
    {"id": 3500101, "name": "Helix Legendary Staff (Lvl 25)", "category": "Weapons", "default_stack": 1},
    {"id": 3500102, "name": "Sun Hammer (Lvl 25)", "category": "Weapons", "default_stack": 1},
    {"id": 3500103, "name": "Aerostriker Bow (Lvl 25)", "category": "Weapons", "default_stack": 1},
    {"id": 3500104, "name": "Major Cleaver 2H Sword (Lvl 25)", "category": "Weapons", "default_stack": 1},
    {"id": 3500105, "name": "Ignited Wooden Sword (Lvl 25)", "category": "Weapons", "default_stack": 1},
    {"id": 3681806, "name": "Ornamented Stone Window Frame", "category": "BuildTools", "default_stack": 50},
    {"id": 4100101, "name": "Eternal Ice Bolt", "category": "Ammunition", "default_stack": 1},
    {"id": 4100102, "name": "Eternal Fireball", "category": "Ammunition", "default_stack": 1},
    {"id": 4100103, "name": "Eternal Chain Lightning", "category": "Ammunition", "default_stack": 1},
    {"id": 4100104, "name": "Eternal Acid Bite", "category": "Ammunition", "default_stack": 1},
    {"id": 4100201, "name": "Explosive Arrow (T5)", "category": "Ammunition", "default_stack": 250},
    {"id": 4100202, "name": "Shroud Arrow (T5)", "category": "Ammunition", "default_stack": 250},
]


def clean_display_name(raw_name: str) -> str:
    """Transforms raw internal identifiers into clean, human-readable titles."""
    if not raw_name:
        return "Unknown Item"
    
    # Strip known prefixes
    prefixes = [
        "Prop_Decoration_", "Prop_", "Resource_Ore_", "Resource_Bar_", "Resource_", 
        "Material_", "Consumable_Potion_", "Consumable_", "Armor_", "Weapon_", 
        "Tool_", "Customization_", "Collectible_", "Ammo_"
    ]
    name = raw_name
    for p in prefixes:
        if name.startswith(p):
            name = name[len(p):]
            break

    # Format tokens
    tokens = name.replace("_", " ").split()
    formatted_tokens = []
    for t in tokens:
        if re.match(r"^T\d+$", t, re.IGNORECASE):
            formatted_tokens.append(f"({t.upper()})")
        elif t.lower() in ("1h", "2h"):
            formatted_tokens.append(t.upper())
        else:
            formatted_tokens.append(t.capitalize())

    return " ".join(formatted_tokens)


class ItemCatalog:
    """Master In-Memory searchable catalog of Enshrouded Items."""
    
    def __init__(self):
        self.items: List[Dict[str, Any]] = []
        self.items_by_id: Dict[int, Dict[str, Any]] = {}
        self.categories: List[str] = [
            "All", "Popular", "Building Blocks", "Materials", "Weapons", 
            "Equipment", "Consumables", "Ammunition", "BuildTools", "Tools", "Other"
        ]
        self._load_items()

    def _load_items(self):
        """Loads and indexes items from cache or raw JSON catalog."""
        # 1. Check if cache exists
        if CACHE_JSON_PATH.exists():
            try:
                with open(CACHE_JSON_PATH, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    self.items = cached_data
                    for item in self.items:
                        self.items_by_id[item["id"]] = item
                return
            except Exception:
                pass

        # 2. Extract from architect catalog if available
        loaded_raw = False
        source_path = None
        if ARCHITECT_CATALOG_PATH.exists():
            source_path = ARCHITECT_CATALOG_PATH
        
        if source_path:
            try:
                with open(source_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    raw_items = data.get("items", [])
                    for it in raw_items:
                        item_id = it.get("itemId")
                        if not item_id:
                            continue
                        raw_name = it.get("debugName", "")
                        friendly = clean_display_name(raw_name)
                        cat = it.get("category", "Other")
                        if cat == "Materials" and "block" in friendly.lower():
                            cat = "Building Blocks"
                        
                        entry = {
                            "id": int(item_id),
                            "name": friendly,
                            "raw_name": raw_name,
                            "category": cat,
                            "slot": it.get("equipmentSlot", ""),
                            "is_voxel": bool(it.get("isBuildingVoxel", False))
                        }
                        if entry["id"] not in self.items_by_id:
                            self.items.append(entry)
                            self.items_by_id[entry["id"]] = entry
                    loaded_raw = True
            except Exception:
                pass

        # 3. Always ensure POPULAR_ITEMS are indexed
        for pop in POPULAR_ITEMS:
            p_id = pop["id"]
            if p_id not in self.items_by_id:
                entry = {
                    "id": p_id,
                    "name": pop["name"],
                    "raw_name": pop["name"],
                    "category": pop["category"],
                    "slot": "",
                    "is_voxel": pop["category"] == "Building Blocks"
                }
                self.items.append(entry)
                self.items_by_id[p_id] = entry

        # Save cache for ultra-fast startup
        if loaded_raw and self.items:
            try:
                with open(CACHE_JSON_PATH, "w", encoding="utf-8") as f:
                    json.dump(self.items, f, indent=2)
            except Exception:
                pass

    def get_categories(self) -> List[str]:
        return self.categories

    def get_all_items(self) -> List[Dict[str, Any]]:
        return self.items

    def get_item_by_id(self, item_id: int) -> Optional[Dict[str, Any]]:
        return self.items_by_id.get(item_id)

    def search_items(self, query: str = "", category: str = "All", limit: int = 150) -> List[Dict[str, Any]]:
        """Fast filter and search items by query text and category."""
        query_lower = query.strip().lower()

        if category == "Popular":
            if not query_lower:
                return [self.items_by_id[p["id"]] for p in POPULAR_ITEMS if p["id"] in self.items_by_id]
            results = []
            for p in POPULAR_ITEMS:
                if p["id"] in self.items_by_id:
                    it = self.items_by_id[p["id"]]
                    if query_lower in it["name"].lower() or query_lower in str(it["id"]):
                        results.append(it)
            return results

        results = []
        for it in self.items:
            # Category match
            if category != "All":
                if category == "Building Blocks":
                    if it.get("category") != "Building Blocks" and not it.get("is_voxel"):
                        continue
                elif it.get("category") != category:
                    continue

            # Query match
            if query_lower:
                if query_lower not in it["name"].lower() and query_lower not in str(it["id"]) and query_lower not in it.get("raw_name", "").lower():
                    continue

            results.append(it)
            if len(results) >= limit:
                break

        return results


# Global singleton instance
MASTER_CATALOG = ItemCatalog()
