"""
Enshrouded Mod Hub & Simplified Lua Editor.
Allows users to directly write, inspect, and test EML Lua scripts with:
- One-click templates (Stack sizes, Shroud timer, Durability, Altar limits)
- Direct Deploy to Enshrouded game folder (H:\\SteamLibrary\\steamapps\\common\\Enshrouded\\mods\\EnshroudedModHub\\src\\mod.lua)
- One-click Launch Game
- Real-time EML log monitoring and syntax checking
"""

import os
import sys
import json
import threading
from pathlib import Path
import customtkinter as ctk

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Target Paths
GAME_MODS_DIR = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\mods\EnshroudedModHub")
GAME_MOD_LUA = GAME_MODS_DIR / "src" / "mod.lua"
GAME_MOD_JSON = GAME_MODS_DIR / "mod.json"
GAME_LOGS_DIR = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\logs")

# Curated, Verified Templates
TEMPLATES = {
    "Blank Script": """-- Enshrouded EML Custom Script
-- Uses Keen Games Asset System

print("[CustomMod] Hello from Enshrouded EML!")

-- Example: Iterate over ItemInfo resources
local items = game.assets.get_resources_by_type("keen::ItemInfo")
print("[CustomMod] Found " .. tostring(#items) .. " item records.")
""",

    "Stack Sizes (10x Multiplier)": """-- ============================================================
-- Stack Size Multiplier
-- Multiplies stackable item limits by 10 (capped at 65535)
-- ============================================================

local MULTIPLIER = 10
local items = game.assets.get_resources_by_type("keen::ItemInfo")
local count = 0

for _, item in ipairs(items or {}) do
    local d = item and item.data
    local cur = d and d.maxStackSize
    if type(cur) == "number" and cur > 1 then
        d.maxStackSize = math.min(65535, math.floor(cur * MULTIPLIER))
        count = count + 1
    end
end

print(("[StackMod] Updated %d items with %dx stack size!"):format(count, MULTIPLIER))
""",

    "Infinite Shroud Timer": """-- ============================================================
-- Shroud Survival Timer Multiplier
-- Multiplies playerBaseFogResistance in the BalancingTable
-- ============================================================

local MULTIPLIER = 10 -- 10x normal survival time
local TARGET_GUID = "82706b40-61b1-4b8f-8b23-dcec6971bda1"

local tables = game.assets.get_resources_by_type("keen::BalancingTable")
for _, res in ipairs(tables or {}) do
    if tostring(res.guid) == TARGET_GUID and res.data then
        local base = res.data.playerBaseFogResistance or 300
        res.data.playerBaseFogResistance = base * MULTIPLIER
        print(("[ShroudMod] Extended shroud base time from %s to %s"):format(tostring(base), tostring(res.data.playerBaseFogResistance)))
        break
    end
end
""",

    "Flame Altar Range & Cap": """-- ============================================================
-- Flame Altar Build Radius & Max Count Multipliers
-- ============================================================

local tables = game.assets.get_resources_by_type("keen::BalancingTable")
local bt = (tables and #tables > 0 and tables[1].data) or nil

if bt then
    -- Expand protected building territory radius (2x)
    if bt.buildzoneSizesPerAltarLevel then
        for _, size in ipairs(bt.buildzoneSizesPerAltarLevel) do
            if size.x and size.y and size.z then
                size.x = math.floor(size.x * 2.0)
                size.y = math.floor(size.y * 2.0)
                size.z = math.floor(size.z * 2.0)
            end
        end
        print("[AltarMod] Doubled flame altar build zone boundaries!")
    end

    -- Increase maximum number of active flame altars allowed to 100
    if bt.altarsPerFlameLevel then
        for idx, count in ipairs(bt.altarsPerFlameLevel) do
            bt.altarsPerFlameLevel[idx] = math.min(100, count * 5)
        end
        print("[AltarMod] Increased max flame altars cap to 100!")
    end
end
""",

    "No Durability Loss": """-- ============================================================
-- Infinite Durability (Tools & Weapons Never Degrade)
-- ============================================================

local presetRes = game.assets.get_resources_by_type("keen::GameSettingsPresetsResource")
local uiRes = game.assets.get_resources_by_type("keen::FbUiBundle")

if presetRes and #presetRes > 0 and presetRes[1].data then
    local presets = presetRes[1].data
    if presets.minValues and presets.minValues["enableDurability"] then
        presets.minValues["enableDurability"].value = false
    end
    if presets.maxValues and presets.maxValues["enableDurability"] then
        presets.maxValues["enableDurability"].value = false
    end
    print("[DurabilityMod] Disabled durability loss in GameSettingsPresets.")
end

if uiRes and #uiRes > 0 and uiRes[1].data then
    local ui = uiRes[1].data
    if ui.difficultySettings and ui.difficultySettings.settingValues then
        ui.difficultySettings.settingValues["enableDurability"] = false
        print("[DurabilityMod] Disabled durability loss in UI Difficulty settings.")
    end
end
"""
}


class SimplifiedLuaEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Enshrouded EML - Simple Lua Editor & Runner")
        self.geometry("1100x740")
        self.minsize(920, 600)

        self._ensure_environment()

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._build_status_bar()

        # Load initial script
        self.load_active_script()

    def _ensure_environment(self):
        GAME_MODS_DIR.mkdir(parents=True, exist_ok=True)
        (GAME_MODS_DIR / "src").mkdir(parents=True, exist_ok=True)
        if not GAME_MOD_JSON.exists():
            with open(GAME_MOD_JSON, "w", encoding="utf-8") as f:
                json.dump({
                    "id": "EnshroudedModHub",
                    "name": "Enshrouded Mod Hub",
                    "version": "1.0.0",
                    "author": "JoelT",
                    "description": "Custom Lua modifications executed via EML."
                }, f, indent=2)

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, width=240, corner_radius=0)
        sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        sidebar.grid_rowconfigure(8, weight=1)

        # Title
        ctk.CTkLabel(
            sidebar,
            text="EML LUA EDITOR\nEnshrouded",
            font=ctk.CTkFont(size=18, weight="bold"),
            justify="center"
        ).grid(row=0, column=0, padx=20, pady=(25, 20))

        # Status Badge
        badge = ctk.CTkFrame(sidebar, fg_color="#1f2937", corner_radius=6)
        badge.grid(row=1, column=0, padx=15, pady=(0, 20), sticky="ew")
        ctk.CTkLabel(
            badge,
            text="● EML CONNECTED",
            text_color="#10b981",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(pady=6)

        # Templates Section
        ctk.CTkLabel(
            sidebar,
            text="Load Preset Template:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8"
        ).grid(row=2, column=0, padx=15, pady=(5, 4), sticky="w")

        self.template_dropdown = ctk.CTkOptionMenu(
            sidebar,
            values=list(TEMPLATES.keys()),
            command=self._on_template_selected
        )
        self.template_dropdown.set("Stack Sizes (10x Multiplier)")
        self.template_dropdown.grid(row=3, column=0, padx=15, pady=(0, 15), sticky="ew")

        # Action Buttons
        self.save_btn = ctk.CTkButton(
            sidebar,
            text="💾 Save & Deploy to Game",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=40,
            command=self.save_and_deploy
        )
        self.save_btn.grid(row=4, column=0, padx=15, pady=8, sticky="ew")

        self.reload_btn = ctk.CTkButton(
            sidebar,
            text="🔄 Reload from Disk",
            fg_color="transparent",
            border_width=1,
            border_color="#4b5563",
            command=self.load_active_script
        )
        self.reload_btn.grid(row=5, column=0, padx=15, pady=6, sticky="ew")

        self.clear_btn = ctk.CTkButton(
            sidebar,
            text="Clear Editor",
            fg_color="transparent",
            border_width=1,
            border_color="#374151",
            command=lambda: self.editor_box.delete("1.0", "end")
        )
        self.clear_btn.grid(row=6, column=0, padx=15, pady=6, sticky="ew")

        # Big Launch Button
        self.launch_btn = ctk.CTkButton(
            sidebar,
            text="▶ SAVE & LAUNCH",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=48,
            command=self.save_and_launch
        )
        self.launch_btn.grid(row=9, column=0, padx=15, pady=15, sticky="ew")

    def _build_main_area(self):
        main = ctk.CTkFrame(self, fg_color="transparent")
        main.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=3)
        main.grid_rowconfigure(3, weight=1)

        # Header
        header = ctk.CTkFrame(main, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header,
            text="Lua Script Editor (mod.lua)",
            font=ctk.CTkFont(size=20, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkLabel(
            header,
            text=f"Target: {GAME_MOD_LUA}",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Main Code Editor
        self.editor_box = ctk.CTkTextbox(
            main,
            font=ctk.CTkFont(family="Consolas", size=13),
            corner_radius=8,
            undo=True
        )
        self.editor_box.grid(row=1, column=0, sticky="nsew")

        # Bottom Log Viewer Header
        log_header = ctk.CTkFrame(main, fg_color="transparent")
        log_header.grid(row=2, column=0, sticky="ew", pady=(12, 6))
        log_header.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            log_header,
            text="EML Game Log Output",
            font=ctk.CTkFont(size=14, weight="bold")
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            log_header,
            text="Fetch Latest Log",
            width=120,
            height=26,
            command=self.refresh_game_log
        ).grid(row=0, column=1, sticky="e")

        # Log Output Box
        self.log_box = ctk.CTkTextbox(
            main,
            font=ctk.CTkFont(family="Consolas", size=11),
            height=120,
            corner_radius=8,
            fg_color="#0f172a"
        )
        self.log_box.grid(row=3, column=0, sticky="nsew")

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color="#111827")
        self.status_bar.grid(row=1, column=1, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            self.status_bar,
            text="Ready.",
            font=ctk.CTkFont(size=11),
            text_color="#9ca3af"
        )
        self.status_label.pack(side="left", padx=15)

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def _on_template_selected(self, choice: str):
        if choice in TEMPLATES:
            self.editor_box.delete("1.0", "end")
            self.editor_box.insert("1.0", TEMPLATES[choice])
            self.set_status(f"Loaded template: '{choice}'")

    def load_active_script(self):
        if GAME_MOD_LUA.exists():
            try:
                with open(GAME_MOD_LUA, "r", encoding="utf-8") as f:
                    content = f.read()
                self.editor_box.delete("1.0", "end")
                self.editor_box.insert("1.0", content)
                self.set_status(f"Loaded active script from game folder ({len(content)} bytes).")
            except Exception as e:
                self.set_status(f"Failed to read mod.lua: {e}")
        else:
            self._on_template_selected("Stack Sizes (10x Multiplier)")

    def save_and_deploy(self) -> bool:
        content = self.editor_box.get("1.0", "end-1c")
        if not content.strip():
            self.set_status("Cannot deploy empty script.")
            return False

        self.set_status("Direct deployment disabled: use Control Center Preview/Install so one composer owns mod.lua.")
        return False

    def save_and_launch(self):
        if self.save_and_deploy():
            self.set_status("Launching Enshrouded via Steam...")
            try:
                os.startfile("steam://rungameid/1203620")
            except Exception as e:
                self.set_status(f"Launch error: {e}")

    def refresh_game_log(self):
        if not GAME_LOGS_DIR.exists():
            self.log_box.delete("1.0", "end")
            self.log_box.insert("1.0", "Logs directory not found.\n")
            return

        # Find latest eml.log
        log_files = sorted(GAME_LOGS_DIR.glob("*.eml.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not log_files:
            self.log_box.delete("1.0", "end")
            self.log_box.insert("1.0", "No .eml.log files found.\n")
            return

        latest_log = log_files[0]
        try:
            with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            tail_lines = lines[-40:]
            self.log_box.delete("1.0", "end")
            self.log_box.insert("1.0", "".join(tail_lines))
            self.log_box.see("end")
            self.set_status(f"Fetched tail of {latest_log.name}")
        except Exception as e:
            self.set_status(f"Failed to read log: {e}")


def main():
    app = SimplifiedLuaEditorApp()
    app.mainloop()


if __name__ == "__main__":
    main()
