"""
Module Manager & Compiler for Enshrouded Control Center.
Handles discovery, validation, profile saving, and Lua script generation.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from .installer import LuaComposer
from .live_config import LiveConfigService
from .platform_services import feature_state

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

# Fail-closed deployment policy. A module is eligible only when every one of
# its settings has an explicit KFC/reflection field mapping. This prevents
# experimental/custom-content code from being emitted just because it exists
# in a profile.
VERIFIED_MODULES = {
    "loot_and_chests",
    "music_and_instruments",
    "progression_balancing",
    "survival_qol",
    "terraforming_and_mining",
}
KNOWN_UNVERIFIED_MODULES = {
    "actor_scaling_proportions",
    "architect_companion",
    "buffs_and_status",
    "building_and_architecture",
    "crafting_and_recipes",
    "custom_alchemy_and_potions",
    "custom_art_and_paintings",
    "custom_building_materials",
    "custom_color_palettes",
    "custom_farming_and_botany",
    "custom_furniture",
    "custom_gliders_and_hooks",
    "custom_hair_and_beards",
    "custom_music_and_midi",
    "custom_pets_and_npcs",
    "custom_spells_and_magic",
    "custom_weapons_and_armor",
    "environment_time_weather",
    "inventory_and_items",
    "knowledge_and_map",
    "skills_and_perks",
    "starter_loadout",
}


class ModuleManager:
    def __init__(self, base_dir: Path):
        self.base_dir = Path(base_dir)
        self.modules_dir = self.base_dir / "modules"
        self.config_file = self.base_dir / "profiles" / "active_profile.json"
        self.live_ipc_file = self.base_dir / "runtime" / "live_config.json"
        
        # Steam Enshrouded game installation target
        self.game_mods_dir = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\mods\EnshroudedModHub")
        
        self.modules: Dict[str, Dict[str, Any]] = {}
        self.active_config: Dict[str, Any] = {"enabled_modules": {}, "module_settings": {}}
        
        self._ensure_directories()
        self.discover_modules()
        self.load_profile()

    def _ensure_directories(self):
        (self.base_dir / "modules").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "profiles").mkdir(parents=True, exist_ok=True)
        (self.base_dir / "runtime").mkdir(parents=True, exist_ok=True)

    def discover_modules(self) -> Dict[str, Dict[str, Any]]:
        """Scans the /modules folder for valid module.json files."""
        self.modules.clear()
        if not self.modules_dir.exists():
            return self.modules

        for entry in self.modules_dir.iterdir():
            if entry.is_dir():
                manifest_path = entry / "module.json"
                if manifest_path.exists():
                    try:
                        with open(manifest_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            mod_id = data.get("id", entry.name)
                            data["_path"] = str(entry)
                            self.modules[mod_id] = data
                            logging.info(f"Loaded module: {data.get('name', mod_id)} v{data.get('version', '0.0')}")
                    except Exception as e:
                        logging.error(f"Failed to parse manifest for {entry.name}: {e}")
        return self.modules

    def _is_verified_module(self, mod_id: str) -> bool:
        manifest = self.modules.get(mod_id, {})
        if feature_state(manifest) in {"research-only", "disabled"}:
            return False
        # Unknown IDs are allowed for isolated test/extension modules; the
        # fail-closed restriction applies to the shipped Control Center set.
        return mod_id not in KNOWN_UNVERIFIED_MODULES or mod_id in VERIFIED_MODULES

    def _enforce_verified_tuning_policy(self) -> bool:
        """Disable custom/unmapped modules in the active profile."""
        changed = False
        enabled = self.active_config.setdefault("enabled_modules", {})
        for mod_id in self.modules:
            if not self._is_verified_module(mod_id) and enabled.get(mod_id, False):
                enabled[mod_id] = False
                changed = True
        return changed

    def load_profile(self):
        """Loads enabled modules and user settings from the active profile."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.active_config = json.load(f)
            except Exception as e:
                logging.error(f"Failed to read profile: {e}")
                self._init_default_profile()
                return

            # Merge any newly discovered modules
            modified = False
            if "enabled_modules" not in self.active_config:
                self.active_config["enabled_modules"] = {}
                modified = True
            if "module_settings" not in self.active_config:
                self.active_config["module_settings"] = {}
                modified = True

            for mod_id, mod in self.modules.items():
                if mod_id not in self.active_config["enabled_modules"]:
                    self.active_config["enabled_modules"][mod_id] = True
                    modified = True
                if mod_id not in self.active_config["module_settings"]:
                    self.active_config["module_settings"][mod_id] = {}
                    modified = True
                for s in mod.get("settings", []):
                    k = s["key"]
                    if k not in self.active_config["module_settings"][mod_id]:
                        self.active_config["module_settings"][mod_id][k] = s.get("default")
                        modified = True

            modified = self._enforce_verified_tuning_policy() or modified

            if modified:
                self.save_profile()
        else:
            self._init_default_profile()

    def _init_default_profile(self):
        self.active_config = {"enabled_modules": {}, "module_settings": {}}
        for mod_id, mod in self.modules.items():
            self.active_config["enabled_modules"][mod_id] = self._is_verified_module(mod_id)
            self.active_config["module_settings"][mod_id] = {}
            for s in mod.get("settings", []):
                self.active_config["module_settings"][mod_id][s["key"]] = s.get("default")
        self.save_profile()

    def reset_to_defaults(self):
        """Resets all module toggles and slider settings to their vanilla/default values."""
        self.active_config = {"enabled_modules": {}, "module_settings": {}}
        for mod_id, mod in self.modules.items():
            self.active_config["enabled_modules"][mod_id] = self._is_verified_module(mod_id)
            self.active_config["module_settings"][mod_id] = {}
            for s in mod.get("settings", []):
                self.active_config["module_settings"][mod_id][s["key"]] = s.get("default")
        self.save_profile()
        self.compile_master_lua()

    def save_profile(self):
        """Saves current state to profile JSON."""
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self.active_config, f, indent=2)

    def update_setting(self, mod_id: str, key: str, value: Any, is_dynamic: bool = False):
        """Updates a setting value and writes to live IPC file if dynamic."""
        if mod_id not in self.active_config["module_settings"]:
            self.active_config["module_settings"][mod_id] = {}
        self.active_config["module_settings"][mod_id][key] = value
        self.save_profile()

        # If it's a dynamic setting, update the live IPC bridge file for in-game immediate sync!
        if is_dynamic:
            self.push_live_update()

    def set_module_enabled(self, mod_id: str, enabled: bool):
        if enabled and not self._is_verified_module(mod_id):
            logging.warning("Blocked unverified/custom tuning module: %s", mod_id)
            enabled = False
        self.active_config["enabled_modules"][mod_id] = enabled
        self.save_profile()

    def push_live_update(self):
        """Writes active dynamic settings to live_config.json for in-game Lua watcher."""
        LiveConfigService().write(self.live_ipc_file, self.modules, self.active_config)

    def _to_lua_value(self, val: Any) -> str:
        if isinstance(val, bool):
            return "true" if val else "false"
        elif isinstance(val, (int, float)):
            return str(val)
        elif isinstance(val, str):
            return '"' + val.replace('\\', '\\\\').replace('"', '\\"') + '"'
        elif isinstance(val, dict):
            parts = []
            for k, v in val.items():
                parts.append(f'["{k}"] = {self._to_lua_value(v)}')
            return "{" + ", ".join(parts) + "}"
        elif isinstance(val, (list, tuple)):
            parts = [self._to_lua_value(v) for v in val]
            return "{" + ", ".join(parts) + "}"
        return "nil"

    def compile_master_lua(self) -> str:
        """
        Generates the fault-tolerant master Lua script that EML executes on game launch.
        Each module is wrapped in a pcall() so one error will never crash the game.
        """
        # Composition is centralized so GUI/editor paths cannot race by writing
        # different versions of mod.lua. Deployment is exclusively handled by
        # InstallerService; this method only updates the local preview artifact.
        content = LuaComposer(self.base_dir).compose(self.modules, self.active_config)
        output_path = self.base_dir / "runtime" / "master_loader.lua"
        output_path.write_text(content, encoding="utf-8")
        logging.info(f"Compiled master Lua loader: {output_path}")
        return str(output_path)

        lua_configs = self._to_lua_value(self.active_config["module_settings"])
        lines = [
            "-- Generated by Enshrouded Control Center Brain",
            "-- DO NOT EDIT DIRECTLY",
            "",
            "local Brain = {",
            "    Modules = {},",
            f"    Configs = {lua_configs},",
            "    Context = {",
            "        Log = function(msg) print('[ModBrain] ' .. tostring(msg)) end,",
            "        LogWarn = function(msg) print('[ModBrain WARN] ' .. tostring(msg)) end,",
            "        LogError = function(msg) print('[ModBrain ERROR] ' .. tostring(msg)) end,",
            "        GetResources = function(typeName)",
            "            if game and game.assets and game.assets.get_resources_by_type then",
            "                return game.assets.get_resources_by_type(typeName) or {}",
            "            end",
            "            return {}",
            "        end,",
            "        SetPlayerAttribute = function(k, v) if _G.Player then _G.Player[k] = v end end,",
            "        SetGlobalRule = function(k, v) if _G.GameRules then _G.GameRules[k] = v end end",
            "    }",
            "}",
            ""
        ]

        for mod_id, mod in self.modules.items():
            if not self.active_config["enabled_modules"].get(mod_id, False):
                continue

            entrypoint = Path(mod["_path"]) / mod.get("entrypoint", "patch.lua")
            if not entrypoint.exists():
                continue

            lines.append(f"-- ===================== Module: {mod_id} =====================")
            lines.append("local ok, err = pcall(function()")
            lines.append(f'    Brain.Context.Log("Booting module: {mod_id}")')
            
            with open(entrypoint, "r", encoding="utf-8") as ef:
                code = ef.read()
                # Wrap inside closure
                lines.append("    local modFunc = function()")
                for code_line in code.splitlines():
                    lines.append("        " + code_line)
                lines.append("    end")
                lines.append(f"    local instance = modFunc()")
                lines.append(f"    if instance and instance.OnInit then")
                lines.append(f"        instance.OnInit(Brain.Configs['{mod_id}'] or {{}}, Brain.Context)")
                lines.append("    end")
                lines.append(f"    Brain.Modules['{mod_id}'] = instance")

            lines.append("end)")
            lines.append("if not ok then")
            lines.append(f'    Brain.Context.LogError("Module {mod_id} failed safely: " .. tostring(err))')
            lines.append("end")
            lines.append("")

        output_path = self.base_dir / "runtime" / "master_loader.lua"
        content = "\n".join(lines)
        with open(output_path, "w", encoding="utf-8") as out:
            out.write(content)
        logging.info(f"Compiled master Lua loader: {output_path}")

        # Deploy directly to Enshrouded game mod directory if it exists
        if self.game_mods_dir.exists():
            game_src_dir = self.game_mods_dir / "src"
            game_src_dir.mkdir(parents=True, exist_ok=True)
            game_mod_lua = game_src_dir / "mod.lua"
            with open(game_mod_lua, "w", encoding="utf-8") as out:
                out.write(content)
            logging.info(f"Deployed mod to game directory: {game_mod_lua}")

        return str(output_path)


if __name__ == "__main__":
    hub = ModuleManager(Path(__file__).parent.parent)
    hub.compile_master_lua()
    hub.push_live_update()
    print("Module Manager initialized successfully!")
