import re
import json
import os

ct_files = [
    r'h:/enshroudedresearch/Enshrouded Mods-20260918T044156Z-1-001/Enshrouded Mods/Incoming/2026-09-17/INC-0010/Enshrouded Building Companion Water Update WIP V2.CT',
    r'h:/enshroudedresearch/Enshrouded Mods-20260918T044156Z-1-001/Enshrouded Mods/Incoming/2026-09-17/INC-0010/enshrouded_1013216.CT',
    r'h:/enshroudedresearch/Enshrouded Mods-20260918T044156Z-1-001/Enshrouded Mods/Incoming/2026-09-17/INC-0010/enshrouded.CT'
]

raw_items = {}

for path in ct_files:
    if not os.path.exists(path):
        continue
    try:
        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            for m in re.finditer(r'\["([^"]+)"\]\s*=\s*"([^"]+)"', content):
                name, val = m.group(1).strip(), m.group(2).strip()
                if not name.startswith("Teleport_"):
                    raw_items[name] = val
    except Exception as e:
        print(f"Error reading {path}: {e}")

def clean_display_name(raw_name):
    s = raw_name
    if s.startswith("_"):
        s = s[1:]
    parts = s.split("_")
    # Clean up prefixes
    clean_parts = []
    for p in parts:
        if p in ["Prop", "Item", "Equip", "Weapon", "Armor", "Consumable", "Mat", "Deco", "LootPickup"]:
            continue
        clean_parts.append(p)
    if not clean_parts:
        clean_parts = parts
    # Add spaces between PascalCase words
    res = " ".join(clean_parts)
    res = re.sub(r'([a-z])([A-Z])', r'\1 \2', res)
    return res.strip()

def categorize_item(name):
    n = name.lower()
    if any(k in n for k in ["sword", "axe", "hammer", "mace", "bow", "wand", "staff", "dagger", "shield", "weapon", "arrow"]):
        return "Weapons & Shields"
    elif any(k in n for k in ["armor", "helmet", "chest", "boots", "gloves", "pants", "trousers", "hood", "robe", "ring", "amulet"]):
        return "Armor & Apparel"
    elif any(k in n for k in ["block", "roof", "wall", "floor", "stairs", "pillar", "door", "window", "fence", "gate"]):
        return "Building & Architecture"
    elif any(k in n for k in ["potion", "food", "meat", "berry", "mushroom", "bandage", "elixir", "water", "tea"]):
        return "Consumables & Food"
    elif any(k in n for k in ["ore", "ingot", "wood", "log", "stone", "clay", "fiber", "resin", "flax", "leather", "fabric", "cloth", "seed", "spore", "shroud_core", "runes"]):
        return "Crafting Resources"
    elif any(k in n for k in ["bed", "chair", "table", "chest", "light", "torch", "lantern", "candle", "banner", "deco", "carpet", "statue", "trophy", "furnace", "workbench"]):
        return "Furniture & Decor"
    elif any(k in n for k in ["glider", "grappling", "pickaxe", "axe", "rake", "hammer"]):
        return "Tools & Exploration"
    else:
        return "World & Miscellaneous"

codex_list = []
for raw_name, byte_val in raw_items.items():
    cat = categorize_item(raw_name)
    disp = clean_display_name(raw_name)
    
    # Hash or integer ID
    int_id = 0
    try:
        # If byte_val is hex string of 32 bytes (GUID)
        tokens = byte_val.split()
        if len(tokens) >= 4:
            b0 = int(tokens[0], 16)
            b1 = int(tokens[1], 16)
            b2 = int(tokens[2], 16)
            b3 = int(tokens[3], 16)
            int_id = b0 | (b1 << 8) | (b2 << 16) | (b3 << 24)
    except:
        pass
    
    if int_id == 0:
        int_id = abs(hash(raw_name)) % 2147483647

    item_obj = {
        "id": raw_name,
        "name": disp,
        "category": cat,
        "tags": [cat.lower().replace("&", "").replace("  ", " "), raw_name.lower()],
        "itemId": int_id,
        "developerView": {
            "internalName": raw_name,
            "guid": byte_val,
            "hash": f"0x{int_id:08X}",
            "resourceType": "ItemTemplate",
            "command": f"item.give {raw_name} 1"
        }
    }
    codex_list.append(item_obj)

print(f"Total structured items generated: {len(codex_list)}")
target_file = r'H:/SteamLibrary/steamapps/common/Enshrouded/mods/architect_toolkit/runtime/codex_database.json'
with open(target_file, 'w', encoding='utf-8') as f:
    json.dump(codex_list, f, indent=2)
print(f"Saved to {target_file}")
