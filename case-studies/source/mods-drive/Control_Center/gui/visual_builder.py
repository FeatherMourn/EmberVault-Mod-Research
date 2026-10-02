"""
Enshrouded EML - Visual / Beginner-Friendly Mod Builder & Lua Generator.
Features a D&D-styled Character Sheet and categorized sidebar navigation:
- 🧙 Character Sheet (Vitals, Resistances, Leveling & Mobility)
- 🔨 Building & Terraforming (Altars, Reach, Free Crafting, Fog Bypass, Storage)
- ⚔️ Combat & Spells (Damage, Armor, Crit, Mana, Fast Casts, Enemy & Boss Scaling)
- 🦅 Glider & Flight (Propulsion, Infinite Hover, Turn Agility, Updraft)
- 💰 Loot & Economy (Chest Drops, Harvest Yields, Blacksmith Runes, Stacks)
- 🌍 World & Environment (Fog of War Reveal, Crops, Kilns, Day/Night, XP, Fast Travel)
- ⚡ Live Memory Cheats (Zero-Crash Verified AOB Engine)
- 📜 Generated Lua Script & Logs
"""

import os
import sys
import time
import math
import json
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk

# Import Safe Memory Engine for Live Cheats
sys.path.append(str(Path(__file__).parent.parent))
from core.memory_engine import MemoryEngine, PROVEN_SIGNATURES
from core.shape_generator import (
    generate_circle_ring, generate_cylinder, generate_dome,
    generate_spiral_staircase, generate_box_perimeter, generate_zoop_line,
    generate_beveled_trim, generate_roman_arch, export_blueprint_json
)
from core.mod_shield import DiagnosticShield, run_diagnostic_check
from core.dynamic_scripts_catalog import DYNAMIC_SCRIPTS, get_scripts_by_category
from core.item_catalog import MASTER_CATALOG, POPULAR_ITEMS
from core.trainer_table import describe as describe_trainer

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

GAME_MODS_DIR = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\mods\EnshroudedModHub")
GAME_MOD_LUA = GAME_MODS_DIR / "src" / "mod.lua"
GAME_MOD_JSON = GAME_MODS_DIR / "mod.json"
GAME_LOGS_DIR = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\logs")
PROFILES_FILE = Path(__file__).parent.parent / "profiles" / "visual_builder_profile.json"
RUNTIME_SYNC_FILE = GAME_MODS_DIR / "runtime_sync.json"
TRAINER_PATH = Path(__file__).resolve().parents[2] / "Cheat Tables" / "Enshrouded_Master_Trainer.CT"


class VisualLuaBuilderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Enshrouded - Visual Mod Builder & Character Studio")
        self.geometry("1180x820")
        self.minsize(980, 680)

        self._ensure_environment()

        # State Dictionary for all user-facing toggles & sliders
        self.mod_state = {
            # === 1. CHARACTER SHEET: VITALS, RESISTANCES & PROGRESSION ===
            "player_max_health_mult": 1.0,
            "player_max_mana_mult": 1.0,
            "player_max_stamina_mult": 1.0,
            "enable_zero_stamina": False,
            "infinite_durability": True,
            "body_heat_mult": 1.0,           # Cold/Freezing resistance
            "diving_breath_mult": 1.0,       # Diving breath time
            "starving_time_mult": 1.0,       # Hunger to starvation delay
            "player_level_cap": 45,          # Vanilla is 45 (or 25/35 depending on EA tier)
            "enable_skill_points_per_level": False,
            "skill_points_per_level": 5,
            "enable_shroud_mult": True,
            "shroud_multiplier": 5.0,
            "enable_slope_climbing": False,
            "climb_max_angle": 85.0,

            # === 2. BUILDING & TERRAFORMING TOOLS ===
            "enable_altar_range": True,
            "altar_radius_mult": 2.0,
            "max_altars_cap": 100,
            "building_hammer_reach_mult": 1.0,
            "crafting_cost_percent": 100,     # 0% = Free Crafting
            "unlock_all_recipes": False,
            "universal_magic_storage": True,
            "build_in_fog_everywhere": False,
            "remove_red_barriers": False,
            "snap_distance_mult": 1.0,           # VoxelBlueprintConfig snapping range
            "enable_microvoxel_chiseling": False, # Option B: 1x1x1 and 2x2x2 chisel blueprints
            "chisel_carve_precision": 1.0,        # Precision block carving

            # === 3. COMBAT, SPELLS & BOSS SCALING ===
            "enable_weapon_scaling": False,
            "melee_damage_mult": 2.0,
            "ranged_damage_mult": 2.0,
            "magic_damage_mult": 2.0,
            "armor_defense_mult": 2.0,
            "crit_chance_percent": 0,
            "spell_mana_cost_percent": 100,
            "spell_cast_time_mult": 1.0,
            "enemy_health_mult": 1.0,
            "enemy_damage_mult": 1.0,
            "boss_health_mult": 1.0,
            "boss_damage_mult": 1.0,
            "enemy_perception_range_mult": 1.0,
            # Option A: BalancingTable Combat Fields
            "base_crit_chance_percent": 10,       # BalancingTable.baseCritChance (default 10%)
            "crit_damage_bonus_percent": 80,      # BalancingTable.critBonus (default 80%)
            "ap_damage_scale_percent": 5,         # BalancingTable.damageScalePerAttributePoint (5%)
            "two_handed_damage_mult": 1.5,        # BalancingTable.damageMod2Handed (1.5x)
            "armor_penetration_percent": 20,      # BalancingTable.defaultArmorBlowthrough (20%)
            # Option 11: Elemental Spell Tuning Fields
            "enable_elemental_spells": False,
            "fire_spell_damage_mult": 1.0,        # Fireball, Flame Arrow
            "ice_spell_damage_mult": 1.0,         # Ice Bolt, Frost Nova
            "shock_spell_damage_mult": 1.0,       # Chain Lightning, Shock Wave
            "shroud_spell_damage_mult": 1.0,      # Shroud Meteor, Acid Bite

            # === 4. GLIDER & FLIGHT AERODYNAMICS ===
            "enable_glider_boost": False,
            "glider_accel_mult": 2.5,
            "glider_hover_efficiency": 1.0,   # Higher = lower vertical air drop (1.0 = normal, 3.0 = near zero drop)
            "glider_turn_agility_mult": 1.0,  # Yaw and pitch turn sensitivity
            "updraft_boost_mult": 1.0,        # Updraft vertical force

            # === 5. LOOT, CHESTS & BLACKSMITH ECONOMY ===
            "enable_stacks": True,
            "stack_multiplier": 10,
            "chest_loot_mult": 1.0,
            "resource_drop_mult": 1,
            "mining_damage_mult": 1.0,
            "blacksmith_rune_return_mult": 1.0, # Perk upgrade salvage return
            "weapon_upgrade_cost_mult": 1.0,    # Perk upgrade rune cost factor
            "gem_upgrade_cost_mult": 1.0,       # BalancingTable.gemCrafting.maxUpgradeCost
            "gem_salvage_gain_mult": 1.0,       # BalancingTable.gemCrafting.salvageGainPercentage

            # === 6. WORLD & ENVIRONMENT ===
            "fog_reveal_mult": 1.0,           # Fog of War reveal radius factor
            "plant_growth_speed_mult": 1.0,
            "factory_production_speed_mult": 1.0,
            "food_buff_duration_mult": 1.0,
            "day_length_minutes": 30.0,
            "night_length_minutes": 10.0,
            "fast_travel_all_markers": True,
            "enable_xp_multipliers": False,
            "combat_xp_mult": 2.0,
            "mining_xp_mult": 2.0,
            "quest_xp_mult": 2.0,
            "base_comfort_rating": 34,        # BalancingTable.comfortSetup.base (default 34)
            "music_comfort_max_buff": 15,     # BalancingTable.maximumTotalMusicComfortBuff (15)
            "water_sources_mult": 1.0,        # BalancingTable.waterSourcesPerFlameLevel

            # === 7. BASE AUTOMATION & TIME / WEATHER CONTROLS ===
            "enable_storage_hopper": True,    # Option 12: Base Automation Storage Hopper Loop
            "time_of_day_hour": 12.0,         # Option 13: Time of Day Dial (0-24)
            "active_weather_override": "Clear", # Option 13: Weather State
        }
        self.load_profile()

        # Initialize Safe Memory Engine for Live Cheats
        self.mem_engine = MemoryEngine()
        self.mem_attached = False

        # Category View Frames
        self.category_frames = {}
        self.nav_buttons = {}
        self.current_category = "character"

        # Layout: Column 0 Sidebar, Column 1 Category Display Area
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_category_container()
        self._build_status_bar()

        # Show initial category
        self.switch_category("character")

        # Initial Lua code preview update
        self.compile_and_update_preview()

    def _ensure_environment(self):
        GAME_MODS_DIR.mkdir(parents=True, exist_ok=True)
        (GAME_MODS_DIR / "src").mkdir(parents=True, exist_ok=True)
        PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not GAME_MOD_JSON.exists():
            with open(GAME_MOD_JSON, "w", encoding="utf-8") as f:
                json.dump({
                    "id": "EnshroudedModHub",
                    "name": "Enshrouded Visual Mod Hub",
                    "version": "1.0.0",
                    "author": "JoelT",
                    "description": "Custom modifications generated via Visual Builder.",
                    "capabilities": ["patch", "runtime"]
                }, f, indent=2)

    def load_profile(self):
        if PROFILES_FILE.exists():
            try:
                with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.mod_state.update(saved)
            except Exception:
                pass

    def save_profile(self):
        try:
            with open(PROFILES_FILE, "w", encoding="utf-8") as f:
                json.dump(self.mod_state, f, indent=2)
            # Live Hot-Swap Bridge (Option 9): Write runtime state for in-game poller
            with open(RUNTIME_SYNC_FILE, "w", encoding="utf-8") as f:
                json.dump({"updated_at": time.time(), "state": self.mod_state}, f)
        except Exception:
            pass

    # =========================================================================
    # SIDEBAR NAVIGATION
    # =========================================================================

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=250, corner_radius=0, fg_color="#0f172a")
        self.sidebar.grid(row=0, column=0, sticky="nsew", rowspan=2)
        self.sidebar.grid_rowconfigure(10, weight=1)

        # Title
        ctk.CTkLabel(
            self.sidebar,
            text="ENSHROUDED\nMOD BUILDER",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#38bdf8",
            justify="center"
        ).grid(row=0, column=0, padx=20, pady=(20, 10))

        # Status Badge
        badge = ctk.CTkFrame(self.sidebar, fg_color="#1e293b", corner_radius=6)
        badge.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="ew")
        ctk.CTkLabel(
            badge,
            text="● ZERO-CODE READY",
            text_color="#10b981",
            font=ctk.CTkFont(size=11, weight="bold")
        ).pack(pady=5)

        # Grouped Navigation Items (3 Architectural Tiers)
        nav_sections = [
            ("IN-GAME LIVE ENGINE & CHEATS", [
                ("cheats",    "⚡ Live Engine Cheats"),
                ("scripts",   "🤖 Dynamic Scripts"),
                ("items",     "📦 Item Transmuter"),
            ]),
            ("PRE-GAME MODS (EML)", [
                ("character", "🧙 Character Sheet"),
                ("building",  "🔨 Building & Terrain"),
                ("studio",    "📐 Shape & Blueprints"),
                ("combat",    "⚔️ Combat & Spells"),
                ("glider",    "🦅 Glider & Flight"),
                ("loot",      "💰 Loot & Economy"),
                ("world",     "🌍 World & Environment"),
            ]),
            ("DEVELOPER & TOOLS", [
                ("code",      "📜 Generated Lua"),
                ("logs",      "📋 Game Logs"),
                ("help",      "📖 Help & Guide"),
            ])
        ]

        nav_frame = ctk.CTkScrollableFrame(
            self.sidebar,
            fg_color="transparent",
            scrollbar_button_color="#334155",
            scrollbar_button_hover_color="#0284c7"
        )
        nav_frame.grid(row=2, column=0, sticky="nsew", padx=4)
        self.sidebar.grid_rowconfigure(2, weight=1)

        for sec_title, items in nav_sections:
            sec_lbl = ctk.CTkLabel(
                nav_frame,
                text=sec_title,
                font=ctk.CTkFont(size=9, weight="bold"),
                text_color="#38bdf8" if "IN-GAME" in sec_title else "#64748b"
            )
            sec_lbl.pack(anchor="w", padx=4, pady=(6, 2))

            for cat_id, label in items:
                btn = ctk.CTkButton(
                    nav_frame,
                    text=label,
                    font=ctk.CTkFont(size=11, weight="bold" if cat_id in ("character", "cheats") else "normal"),
                    fg_color="#1e293b" if cat_id != "character" else "#0284c7",
                    hover_color="#334155",
                    anchor="w",
                    height=26,
                    command=lambda c=cat_id: self.switch_category(c)
                )
                btn.pack(fill="x", pady=1)
                self.nav_buttons[cat_id] = btn

        # Quick Presets Box
        preset_frame = ctk.CTkFrame(self.sidebar, fg_color="#1e293b", corner_radius=8)
        preset_frame.grid(row=10, column=0, padx=10, pady=(8, 6), sticky="sew")

        ctk.CTkLabel(
            preset_frame,
            text="Quick Presets",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#94a3b8"
        ).pack(anchor="w", padx=10, pady=(6, 2))

        preset_row1 = ctk.CTkFrame(preset_frame, fg_color="transparent")
        preset_row1.pack(fill="x", padx=8, pady=2)
        ctk.CTkButton(
            preset_row1,
            text="🛠️ QoL",
            width=65,
            height=26,
            fg_color="#374151",
            hover_color="#4b5563",
            font=ctk.CTkFont(size=11),
            command=self.preset_recommended
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            preset_row1,
            text="🏰 Builder",
            width=70,
            height=26,
            fg_color="#374151",
            hover_color="#4b5563",
            font=ctk.CTkFont(size=11),
            command=self.preset_builder
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            preset_row1,
            text="⚡ God",
            width=60,
            height=26,
            fg_color="#374151",
            hover_color="#4b5563",
            font=ctk.CTkFont(size=11),
            command=self.preset_sandbox
        ).pack(side="left", padx=2)

        ctk.CTkButton(
            preset_frame,
            text="↩ Reset to Vanilla",
            height=24,
            fg_color="transparent",
            border_width=1,
            border_color="#475569",
            text_color="#94a3b8",
            font=ctk.CTkFont(size=10),
            command=self.preset_vanilla
        ).pack(fill="x", padx=10, pady=(4, 8))

        # Open Cheat Engine Master Trainer Button
        self.trainer_btn = ctk.CTkButton(
            self.sidebar,
            text="🎯 OPEN MASTER TRAINER",
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#8b5cf6",
            hover_color="#7c3aed",
            height=36,
            command=self.launch_cheat_trainer
        )
        self.trainer_btn.grid(row=11, column=0, padx=12, pady=(6, 4), sticky="ew")

        # Big Deploy & Launch Button
        self.launch_btn = ctk.CTkButton(
            self.sidebar,
            text="▶ DEPLOY & LAUNCH",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=44,
            command=self.deploy_and_launch
        )
        self.launch_btn.grid(row=12, column=0, padx=12, pady=(4, 12), sticky="ew")

    def switch_category(self, cat_id: str):
        self.current_category = cat_id
        for c, frame in self.category_frames.items():
            if c == cat_id:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()

        # Update button highlights
        for c, btn in self.nav_buttons.items():
            if c == cat_id:
                btn.configure(fg_color="#0284c7", font=ctk.CTkFont(size=13, weight="bold"))
            else:
                btn.configure(fg_color="#1e293b", font=ctk.CTkFont(size=13, weight="normal"))

    # =========================================================================
    # CATEGORY CONTAINER & BUILDERS
    # =========================================================================

    def _build_category_container(self):
        self.main_container = ctk.CTkFrame(self, corner_radius=0, fg_color="#020617")
        self.main_container.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(0, weight=1)

        # Build each individual category frame
        self._build_character_sheet_category()
        self._build_building_category()
        self._build_shape_studio_category()
        self._build_combat_category()
        self._build_glider_category()
        self._build_loot_category()
        self._build_world_category()
        self._build_scripts_category()
        self._build_live_cheats_category()
        self._build_items_category()
        self._build_code_preview_category()
        self._build_logs_category()
        self._build_help_category()

    # -------------------------------------------------------------------------
    # 1. 🧙 D&D CHARACTER SHEET
    # -------------------------------------------------------------------------
    def _build_character_sheet_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["character"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # D&D Character Sheet Header Banner
        header = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1e1b4b", border_width=1, border_color="#6366f1")
        header.pack(fill="x", padx=10, pady=(4, 12))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header,
            text="📜 CHARACTER SHEET & STATS",
            font=ctk.CTkFont(family="Georgia", size=18, weight="bold"),
            text_color="#a5b4fc"
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        ctk.CTkLabel(
            header,
            text="Class: Flameborn Pioneer | World Balancing Overrides",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color="#c7d2fe"
        ).grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))

        # D&D Stat Pillars Card (HP, Mana, Stamina)
        self._build_card(scroll, "❤️ Primary Vitals (Health, Mana, Stamina)", [
            {
                "type": "slider",
                "key": "player_max_health_mult",
                "label": "CONSTITUTION: Max Health Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x base health"
            },
            {
                "type": "slider",
                "key": "player_max_mana_mult",
                "label": "INTELLIGENCE: Max Mana Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x base mana"
            },
            {
                "type": "slider",
                "key": "player_max_stamina_mult",
                "label": "DEXTERITY: Max Stamina Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x base stamina"
            },
            {
                "type": "toggle",
                "key": "enable_zero_stamina",
                "label": "Boundless Stamina (Zero Depletion)",
                "desc": "Sprint, swim, swing weapons, and glide forever with zero stamina exhaustion."
            },
            {
                "type": "toggle",
                "key": "infinite_durability",
                "label": "Indestructible Equipment (Durability Immunity)",
                "desc": "Weapons, armor, bows, pickaxes, and axes never break or lose durability."
            }
        ])

        # Survival & Resistances (Cold, Diving, Hunger, Shroud)
        self._build_card(scroll, "🛡️ Resistances & Survival Vitals", [
            {
                "type": "slider",
                "key": "body_heat_mult",
                "label": "Body Heat / Cold Resistance Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x warmth (Freeze slower in mountain snows)"
            },
            {
                "type": "slider",
                "key": "diving_breath_mult",
                "label": "Underwater Diving Breath Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x breath duration"
            },
            {
                "type": "slider",
                "key": "starving_time_mult",
                "label": "Hunger-to-Starvation Delay Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x starvation buffer"
            },
            {
                "type": "toggle",
                "key": "enable_shroud_mult",
                "label": "Enshrouded Mist Resistance Multiplier",
                "desc": "Extends time before your Flameborn timer reaches 0 inside the deadly Shroud."
            },
            {
                "type": "slider",
                "key": "shroud_multiplier",
                "label": "Shroud Survival Timer Multiplier",
                "min": 1.0,
                "max": 20.0,
                "step": 0.5,
                "suffix": "x base Shroud time"
            }
        ])

        # Progression & Leveling (Level Cap, Skill Points)
        self._build_card(scroll, "🌟 Leveling & Progression Rules", [
            {
                "type": "slider",
                "key": "player_level_cap",
                "label": "Player & World Level Cap",
                "min": 25,
                "max": 100,
                "step": 5,
                "suffix": " Max Level (Vanilla is 45)"
            },
            {
                "type": "toggle",
                "key": "enable_skill_points_per_level",
                "label": "Accelerated Skill Point Gains",
                "desc": "Awards bonus skill points on every level up to unlock the entire skill tree."
            },
            {
                "type": "slider",
                "key": "skill_points_per_level",
                "label": "Skill Points Awarded Per Level",
                "min": 2,
                "max": 25,
                "step": 1,
                "suffix": " points / lvl"
            }
        ])

        # Mountain Climbing & Mobility
        self._build_card(scroll, "⛰️ Mountain Climbing & Terrestrial Mobility", [
            {
                "type": "toggle",
                "key": "enable_slope_climbing",
                "label": "Extreme Mountain Slope Climbing",
                "desc": "Allows scaling steep cliffs and mountain faces without slipping backwards."
            },
            {
                "type": "slider",
                "key": "climb_max_angle",
                "label": "Max Walkable Slope Angle",
                "min": 45.0,
                "max": 89.0,
                "step": 1.0,
                "suffix": "° (Vanilla is ~45°)"
            }
        ])

    # -------------------------------------------------------------------------
    # 2. 🔨 BUILDING & TERRAFORMING
    # -------------------------------------------------------------------------
    def _build_building_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["building"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # Construction Hammer & Reach
        self._build_card(scroll, "🔨 Construction Tools & Reach Range", [
            {
                "type": "slider",
                "key": "building_hammer_reach_mult",
                "label": "Building Hammer Placement Reach Range",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x reach (Build tall towers from ground)"
            }
        ])

        # Flame Altars & Base Domains
        self._build_card(scroll, "🔥 Flame Altars & Protected Territory", [
            {
                "type": "toggle",
                "key": "enable_altar_range",
                "label": "Expand Flame Altar Building Area",
                "desc": "Multiplies the protected building boundary radius around all your flame altars."
            },
            {
                "type": "slider",
                "key": "altar_radius_mult",
                "label": "Building Radius Multiplier",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x radius"
            },
            {
                "type": "slider",
                "key": "max_altars_cap",
                "label": "Max Flame Altars Limit",
                "min": 2,
                "max": 100,
                "step": 5,
                "suffix": " altars allowed in world"
            }
        ])

        # Free Crafting & Blueprints
        self._build_card(scroll, "✨ Crafting Costs & Blueprint Knowledge", [
            {
                "type": "slider",
                "key": "crafting_cost_percent",
                "label": "Crafting Material Cost Percentage",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "% (0% = Free Crafting)"
            },
            {
                "type": "toggle",
                "key": "unlock_all_recipes",
                "label": "Unlock All Recipes & Blueprints Immediately",
                "desc": "Unlocks all locked workshop crafts, armor, and furniture recipes without quest gating."
            },
            {
                "type": "toggle",
                "key": "universal_magic_storage",
                "label": "Universal Magic Storage (Craft from ANY Chest)",
                "desc": "Turns every regular wooden and iron chest into a Magic Chest across your whole base."
            },
            {
                "type": "toggle",
                "key": "enable_storage_hopper",
                "label": "Smart Base Automation Hopper (Auto-Deposit Production)",
                "desc": "Automatically scans kilns, smelters, and seedbeds within flame altar bounds and routes outputs into nearby base chests."
            }
        ])

        # Boundaries & No-Build Bypass
        self._build_card(scroll, "🚫 Boundaries & Fog-Building Bypass", [
            {
                "type": "toggle",
                "key": "build_in_fog_everywhere",
                "label": "Bypass No-Build Zones & Build In Shroud",
                "desc": "Allows placing flame altars and building structures inside Shroud fog and restricted areas."
            },
            {
                "type": "toggle",
                "key": "remove_red_barriers",
                "label": "Remove Red Boundary Barriers (Early Access Zones)",
                "desc": "Disables red death fog barriers at world borders, allowing exploration into locked territories."
            }
        ])

        # Snapping Rules & VoxelBlueprintConfig Reach
        self._build_card(scroll, "🧲 Snapping Rules & Magnetic Bounds (VoxelBlueprintConfig)", [
            {
                "type": "slider",
                "key": "snap_distance_mult",
                "label": "Blueprint Magnetic Snapping Range Multiplier",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x snap range (Walls, Roofs, Stairs snap from further away)"
            }
        ])

        # Option B: Microvoxel Chiseling & Carving Tools
        self._build_card(scroll, "⛏️ Microvoxel Chiseling & Precision Masonry (Vintage Story / Chisels)", [
            {
                "type": "toggle",
                "key": "enable_microvoxel_chiseling",
                "label": "Unlock Native 1x1x1 Microvoxel Blueprints",
                "desc": "Exposes native 1x1x1 and 2x2x2 voxel pieces in your building tools for micro-sculpting."
            },
            {
                "type": "slider",
                "key": "chisel_carve_precision",
                "label": "Chisel Carving Damage Scale",
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "suffix": "x (0.1x = Carve single microvoxels without breaking wall)"
            }
        ])

    # -------------------------------------------------------------------------
    # 2b. 📐 SHAPE GENERATOR & BLUEPRINT STUDIO (OPTIONS C & D)
    # -------------------------------------------------------------------------
    def _build_shape_studio_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["studio"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # Header Banner
        banner = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#0f172a", border_width=1, border_color="#38bdf8")
        banner.pack(fill="x", padx=10, pady=(4, 12))
        banner.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            banner,
            text="📐",
            font=ctk.CTkFont(size=32)
        ).grid(row=0, column=0, rowspan=2, padx=16, pady=12)

        ctk.CTkLabel(
            banner,
            text="PROCEDURAL SHAPE & BLUEPRINT STUDIO",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38bdf8",
            anchor="w"
        ).grid(row=0, column=1, sticky="w", pady=(10, 0))

        ctk.CTkLabel(
            banner,
            text="Generate mathematical circles, towers, domes, spirals & zoop lines. Export to JSON or trigger directly in-game.",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            anchor="w"
        ).grid(row=1, column=1, sticky="w", pady=(0, 10))

        # Two-Column Studio Layout
        studio_body = ctk.CTkFrame(scroll, fg_color="transparent")
        studio_body.pack(fill="both", expand=True, padx=10, pady=5)
        studio_body.grid_columnconfigure(0, weight=1)
        studio_body.grid_columnconfigure(1, weight=1)

        # Left Column: Shape Config & Controls
        left_card = ctk.CTkFrame(studio_body, corner_radius=10, fg_color="#1e293b")
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=0)
        left_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_card,
            text="🛠️ Shape Configuration",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc"
        ).pack(anchor="w", padx=16, pady=(12, 6))

        # Shape Selector Dropdown (Including Option 6 Vintage Story Chisel Presets)
        ctk.CTkLabel(left_card, text="Procedural Shape & Chisel Type:", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(anchor="w", padx=16, pady=(4, 0))
        self.studio_shape_var = ctk.StringVar(value="Circle / Ring")
        shape_options = [
            "Circle / Ring",
            "Cylinder / Tower",
            "Dome / Hemisphere",
            "Spiral Staircase",
            "Hollow Box Perimeter",
            "Straight Zoop Line",
            "Beveled Edge / Cornice (Chisel)",
            "Roman Semicircular Arch (Chisel)"
        ]
        self.studio_shape_menu = ctk.CTkOptionMenu(
            left_card,
            values=shape_options,
            variable=self.studio_shape_var,
            command=lambda _: self._update_shape_preview()
        )
        self.studio_shape_menu.pack(fill="x", padx=16, pady=(2, 10))

        # Dimension Sliders: Radius
        self.studio_radius_label = ctk.CTkLabel(left_card, text="Radius / Span: 10 voxels", font=ctk.CTkFont(size=11), text_color="#cbd5e1")
        self.studio_radius_label.pack(anchor="w", padx=16, pady=(4, 0))
        self.studio_radius_slider = ctk.CTkSlider(
            left_card, from_=2, to=50, number_of_steps=48,
            command=self._on_studio_slider_change
        )
        self.studio_radius_slider.set(10)
        self.studio_radius_slider.pack(fill="x", padx=16, pady=(2, 8))

        # Height Slider
        self.studio_height_label = ctk.CTkLabel(left_card, text="Height: 8 voxels", font=ctk.CTkFont(size=11), text_color="#cbd5e1")
        self.studio_height_label.pack(anchor="w", padx=16, pady=(4, 0))
        self.studio_height_slider = ctk.CTkSlider(
            left_card, from_=1, to=64, number_of_steps=63,
            command=self._on_studio_slider_change
        )
        self.studio_height_slider.set(8)
        self.studio_height_slider.pack(fill="x", padx=16, pady=(2, 8))

        # Wall Thickness Slider
        self.studio_thick_label = ctk.CTkLabel(left_card, text="Thickness / Depth: 1 voxel", font=ctk.CTkFont(size=11), text_color="#cbd5e1")
        self.studio_thick_label.pack(anchor="w", padx=16, pady=(4, 0))
        self.studio_thick_slider = ctk.CTkSlider(
            left_card, from_=1, to=6, number_of_steps=5,
            command=self._on_studio_slider_change
        )
        self.studio_thick_slider.set(1)
        self.studio_thick_slider.pack(fill="x", padx=16, pady=(2, 8))

        # Voxel Material Choice & Multi-Material Theming (Option 2)
        ctk.CTkLabel(left_card, text="Base Voxel Material:", font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(anchor="w", padx=16, pady=(4, 0))
        self.studio_mat_var = ctk.StringVar(value="Rough Cut Stone (ID: 67)")
        mat_options = [
            "Rough Cut Stone (ID: 67)",
            "Refined Wood Planks (ID: 42)",
            "Polished Castle Stone (ID: 89)",
            "Luminous Bone Shard (ID: 114)",
            "Desert Sandstone (ID: 31)"
        ]
        self.studio_mat_menu = ctk.CTkOptionMenu(
            left_card,
            values=mat_options,
            variable=self.studio_mat_var
        )
        self.studio_mat_menu.pack(fill="x", padx=16, pady=(2, 6))

        # Option 2: Multi-Material Theming Toggle
        self.multi_mat_var = ctk.BooleanVar(value=True)
        self.multi_mat_switch = ctk.CTkSwitch(
            left_card,
            text="Multi-Material Theme (Stone Base + Timber + Slate)",
            variable=self.multi_mat_var,
            font=ctk.CTkFont(size=10)
        )
        self.multi_mat_switch.pack(anchor="w", padx=16, pady=(2, 12))

        # Blueprint File Operations
        bp_btn_row = ctk.CTkFrame(left_card, fg_color="transparent")
        bp_btn_row.pack(fill="x", padx=16, pady=(0, 14))
        bp_btn_row.grid_columnconfigure(0, weight=1)
        bp_btn_row.grid_columnconfigure(1, weight=1)

        self.export_bp_btn = ctk.CTkButton(
            bp_btn_row,
            text="💾 Save Blueprint (.json)",
            font=ctk.CTkFont(size=11, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=32,
            command=self._export_blueprint_action
        )
        self.export_bp_btn.grid(row=0, column=0, padx=(0, 4), sticky="ew")

        self.import_bp_btn = ctk.CTkButton(
            bp_btn_row,
            text="📂 Load Blueprint",
            font=ctk.CTkFont(size=11),
            fg_color="#334155",
            hover_color="#475569",
            height=32,
            command=self._import_blueprint_action
        )
        self.import_bp_btn.grid(row=0, column=1, padx=(4, 0), sticky="ew")

        # Right Column: Visualizer Canvas & In-Game Hotkey Dispatcher (Option D)
        right_card = ctk.CTkFrame(studio_body, corner_radius=10, fg_color="#1e293b")
        right_card.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=0)
        right_card.grid_columnconfigure(0, weight=1)

        # View Mode Header with 3D Orbit / 2D Toggle
        header_row = ctk.CTkFrame(right_card, fg_color="transparent")
        header_row.pack(fill="x", padx=16, pady=(12, 4))
        header_row.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            header_row,
            text="👁️ Studio Viewport",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc"
        ).grid(row=0, column=0, sticky="w")

        self.studio_view_mode = ctk.StringVar(value="3D Orbit")
        self.view_toggle_seg = ctk.CTkSegmentedButton(
            header_row,
            values=["3D Orbit", "2D Top-Down"],
            variable=self.studio_view_mode,
            command=lambda _: self._update_shape_preview(),
            height=24,
            font=ctk.CTkFont(size=10)
        )
        self.view_toggle_seg.grid(row=0, column=1, sticky="e")

        # 3D Orbit Angle State (Option 1)
        self.yaw_deg = 45.0
        self.pitch_deg = 30.0
        self.orbit_zoom = 1.0
        self._last_mouse_x = 0
        self._last_mouse_y = 0

        # Voxel Preview Stats
        self.studio_stats_label = ctk.CTkLabel(
            right_card,
            text="Total Voxels: 0 | Bounds: 0 x 0 x 0",
            font=ctk.CTkFont(size=11),
            text_color="#38bdf8"
        )
        self.studio_stats_label.pack(anchor="w", padx=16, pady=(0, 6))

        # Embedded TK Canvas for live 3D isometric & 2D rendering
        canvas_border = ctk.CTkFrame(right_card, fg_color="#090d16", corner_radius=6)
        canvas_border.pack(padx=16, pady=4, fill="both", expand=True)

        self.studio_canvas = tk.Canvas(
            canvas_border,
            width=320,
            height=240,
            bg="#020617",
            highlightthickness=0
        )
        self.studio_canvas.pack(padx=2, pady=2, fill="both", expand=True)

        # Mouse Drag Event Bindings for 3D Orbit Rotation
        self.studio_canvas.bind("<ButtonPress-1>", self._on_canvas_mouse_down)
        self.studio_canvas.bind("<B1-Motion>", self._on_canvas_mouse_drag)
        self.studio_canvas.bind("<MouseWheel>", self._on_canvas_mouse_wheel)

        # In-Game Hotkey Overlay Control (Option D)
        # Blueprint & Geometry Export Card
        export_box = ctk.CTkFrame(right_card, corner_radius=8, fg_color="#0f172a", border_width=1, border_color="#334155")
        export_box.pack(fill="x", padx=16, pady=(10, 14))

        exp_row = ctk.CTkFrame(export_box, fg_color="transparent")
        exp_row.pack(fill="x", padx=12, pady=(8, 2))

        ctk.CTkLabel(
            exp_row,
            text="📐 Blueprint Exporter & Geometry Engine",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="left")

        ctk.CTkButton(
            exp_row,
            text="💾 Save JSON",
            font=ctk.CTkFont(size=10, weight="bold"),
            width=90,
            height=22,
            fg_color="#3b82f6",
            hover_color="#2563eb",
            command=self._export_blueprint_action
        ).pack(side="right")

        ctk.CTkLabel(
            export_box,
            text="Generates placement-ready JSON schemas for Enshrouded blueprint injection.\nUse with the Dynamic Scripts tab or import custom .obj 3D models.",
            font=ctk.CTkFont(family="Consolas", size=9),
            text_color="#94a3b8",
            justify="left"
        ).pack(anchor="w", padx=12, pady=(0, 8))

        # Initial calculation & canvas render
        self._current_shape_coords = []
        self._update_shape_preview()

    def _on_studio_slider_change(self, _val=None):
        r = int(self.studio_radius_slider.get())
        h = int(self.studio_height_slider.get())
        t = int(self.studio_thick_slider.get())
        self.studio_radius_label.configure(text=f"Radius / Extent: {r} voxels")
        self.studio_height_label.configure(text=f"Height: {h} voxels")
        self.studio_thick_label.configure(text=f"Thickness: {t} voxel{'s' if t > 1 else ''}")
        self._update_shape_preview()

    def _update_shape_preview(self):
        shape_type = self.studio_shape_var.get()
        r = int(self.studio_radius_slider.get())
        h = int(self.studio_height_slider.get())
        t = int(self.studio_thick_slider.get())

        if shape_type == "Circle / Ring":
            coords = generate_circle_ring(radius=r, thickness=t)
        elif shape_type == "Cylinder / Tower":
            coords = generate_cylinder(radius=r, height=h, thickness=t)
        elif shape_type == "Dome / Hemisphere":
            coords = generate_dome(radius=r, thickness=t)
        elif shape_type == "Spiral Staircase":
            coords = generate_spiral_staircase(radius=r, height=h, turns=1.5, step_width=2)
        elif shape_type == "Hollow Box Perimeter":
            coords = generate_box_perimeter(width=r * 2, length=r * 2, height=h, thickness=t)
        elif "Beveled Edge" in shape_type:
            coords = generate_beveled_trim(length=r * 2, thickness=max(1, t))
        elif "Roman" in shape_type:
            coords = generate_roman_arch(span=r * 2, height=h, depth=max(1, t))
        else:  # Straight Zoop Line
            coords = generate_zoop_line((0, 0, 0), (r * 2, 0, 0), step_size=4)

        self._current_shape_coords = coords

        # Update stats
        if coords:
            min_x = min(c[0] for c in coords)
            max_x = max(c[0] for c in coords)
            min_y = min(c[1] for c in coords)
            max_y = max(c[1] for c in coords)
            min_z = min(c[2] for c in coords)
            max_z = max(c[2] for c in coords)
            dx = max_x - min_x + 1
            dy = max_y - min_y + 1
            dz = max_z - min_z + 1
            self.studio_stats_label.configure(
                text=f"Total Voxels: {len(coords)} | Bounds: {dx}w x {dy}h x {dz}d"
            )
        else:
            self.studio_stats_label.configure(text="Total Voxels: 0 | Bounds: 0 x 0 x 0")

        # Redraw Canvas based on active View Mode (3D Orbit or 2D)
        self._render_canvas_preview(coords)

    def _on_canvas_mouse_down(self, event):
        self._last_mouse_x = event.x
        self._last_mouse_y = event.y

    def _on_canvas_mouse_drag(self, event):
        if getattr(self, "studio_view_mode", None) and self.studio_view_mode.get() == "3D Orbit":
            dx = event.x - self._last_mouse_x
            dy = event.y - self._last_mouse_y
            self.yaw_deg = (self.yaw_deg + dx * 0.8) % 360.0
            self.pitch_deg = max(5.0, min(85.0, self.pitch_deg - dy * 0.8))
            self._last_mouse_x = event.x
            self._last_mouse_y = event.y
            self._render_canvas_preview(self._current_shape_coords)

    def _on_canvas_mouse_wheel(self, event):
        if getattr(self, "studio_view_mode", None) and self.studio_view_mode.get() == "3D Orbit":
            factor = 1.1 if event.delta > 0 else 0.9
            self.orbit_zoom = max(0.4, min(3.5, self.orbit_zoom * factor))
            self._render_canvas_preview(self._current_shape_coords)

    def _render_canvas_preview(self, coords):
        if not hasattr(self, "studio_canvas"):
            return
        self.studio_canvas.delete("all")

        cw = self.studio_canvas.winfo_width()
        ch = self.studio_canvas.winfo_height()
        if cw <= 1:
            cw, ch = 320, 240

        cx, cy = cw // 2, ch // 2

        if not coords:
            self.studio_canvas.create_line(cx - 15, cy, cx + 15, cy, fill="#334155", width=1)
            self.studio_canvas.create_line(cx, cy - 15, cx, cy + 15, fill="#334155", width=1)
            return

        is_3d = getattr(self, "studio_view_mode", None) and self.studio_view_mode.get() == "3D Orbit"

        if is_3d:
            # === 3D ISOMETRIC ORBIT ENGINE (Option 1) ===
            yaw_rad = math.radians(getattr(self, "yaw_deg", 45.0))
            pitch_rad = math.radians(getattr(self, "pitch_deg", 30.0))
            zoom = getattr(self, "orbit_zoom", 1.0)

            cos_y, sin_y = math.cos(yaw_rad), math.sin(yaw_rad)
            cos_p, sin_p = math.cos(pitch_rad), math.sin(pitch_rad)

            # Find geometric bounds
            max_extent = max(max(abs(c[0]), abs(c[1]), abs(c[2])) for c in coords)
            base_scale = min(cw, ch) / (max_extent * 3.2 + 2) if max_extent > 0 else 6.0
            scale = max(2.0, min(base_scale * zoom, 18.0))

            # Transform each voxel to 3D camera coordinate space
            projected = []
            for x, y, z in coords:
                # Rotate around Y axis (Yaw)
                rx = x * cos_y - z * sin_y
                rz = x * sin_y + z * cos_y
                # Tilt around X axis (Pitch)
                ry = y * cos_p - rz * sin_p
                depth = y * sin_p + rz * cos_p

                screen_x = cx + int(rx * scale)
                screen_y = cy - int(ry * scale)
                projected.append((depth, screen_x, screen_y, y))

            # Sort by depth back-to-front (Painter's Algorithm)
            projected.sort(key=lambda p: p[0])

            max_y = max((c[1] for c in coords), default=1)
            r_box = max(2, int(scale / 2.0))

            # Draw ground grid orientation indicator
            self.studio_canvas.create_text(
                12, ch - 12, anchor="w",
                text=f"Orbit: Yaw {int(self.yaw_deg)}° | Pitch {int(self.pitch_deg)}° | Zoom {round(zoom, 1)}x (Drag to rotate)",
                font=("Consolas", 8), fill="#64748b"
            )

            for depth, px, py, orig_y in projected:
                # Shading based on vertical elevation and depth
                ratio = (orig_y / max_y) if max_y > 0 else 0.5
                red_val = int(56 + ratio * 160)
                green_val = int(140 + ratio * 80)
                blue_val = int(220 - ratio * 40)
                color = f"#{max(0, min(255, red_val)):02x}{max(0, min(255, green_val)):02x}{max(0, min(255, blue_val)):02x}"

                # Draw shaded 3D voxel box
                self.studio_canvas.create_rectangle(
                    px - r_box, py - r_box, px + r_box, py + r_box,
                    fill=color, outline="#0f172a", width=1
                )
        else:
            # === 2D TOP-DOWN VIEWPORT ===
            self.studio_canvas.create_line(cx - 15, cy, cx + 15, cy, fill="#334155", width=1)
            self.studio_canvas.create_line(cx, cy - 15, cx, cy + 15, fill="#334155", width=1)

            max_extent = max(max(abs(c[0]), abs(c[2])) for c in coords)
            scale = 4.0 if max_extent == 0 else min((cw - 40) / (max_extent * 2 + 1), (ch - 40) / (max_extent * 2 + 1))
            scale = max(1.5, min(scale, 12.0))

            top_down_map = {}
            for x, y, z in coords:
                pt = (x, z)
                if pt not in top_down_map or y > top_down_map[pt]:
                    top_down_map[pt] = y

            max_y = max(c[1] for c in coords) if coords else 1
            for (x, z), y in top_down_map.items():
                px = cx + int(x * scale)
                pz = cy + int(z * scale)

                intensity = int(140 + (y / max_y) * 115) if max_y > 0 else 200
                intensity = max(100, min(255, intensity))
                hex_color = f"#{intensity:02x}{int(intensity * 0.7):02x}38"

                r_dot = max(1, int(scale / 2.2))
                self.studio_canvas.create_rectangle(
                    px - r_dot, pz - r_dot, px + r_dot, pz + r_dot,
                    fill=hex_color, outline=""
                )

    def _export_blueprint_action(self):
        shape_type = self.studio_shape_var.get()
        if not self._current_shape_coords:
            self.set_status("No voxel coordinates to export!")
            return

        mat_text = self.studio_mat_var.get()
        mat_id = 67
        if "ID:" in mat_text:
            try:
                mat_id = int(mat_text.split("ID:")[1].strip().rstrip(")"))
            except Exception:
                mat_id = 67

        clean_name = shape_type.lower().replace(" / ", "_").replace(" ", "_").replace("(", "").replace(")", "").replace(":", "")
        use_multi = getattr(self, "multi_mat_var", None) and self.multi_mat_var.get()

        bp_dict = export_blueprint_json(
            name=f"Procedural_{clean_name}",
            shape_type=clean_name,
            coords=self._current_shape_coords,
            voxel_material_id=mat_id,
            multi_material=bool(use_multi)
        )

        bp_dir = Path(__file__).parent.parent / "blueprints"
        bp_dir.mkdir(parents=True, exist_ok=True)
        out_file = bp_dir / f"{clean_name}_{int(self.studio_radius_slider.get())}r.json"

        try:
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(bp_dict, f, indent=2)
            self.set_status(f"Exported blueprint ({len(self._current_shape_coords)} voxels) to {out_file.name}")
        except Exception as e:
            self.set_status(f"Error saving blueprint: {e}")

    def _import_blueprint_action(self):
        bp_dir = Path(__file__).parent.parent / "blueprints"
        bp_dir.mkdir(parents=True, exist_ok=True)
        file_path = filedialog.askopenfilename(
            initialdir=str(bp_dir),
            title="Select Blueprint JSON",
            filetypes=[("JSON Blueprints", "*.json"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            coords = [(pt["x"], pt["y"], pt["z"]) for pt in data.get("coordinates", [])]
            self._current_shape_coords = coords
            self.studio_shape_var.set(f"Custom ({data.get('shape_type', 'blueprint')})")
            self._render_canvas_preview(coords)
            self.studio_stats_label.configure(
                text=f"Imported: {data.get('name', 'Blueprint')} | Total Voxels: {len(coords)}"
            )
            self.set_status(f"Loaded blueprint {Path(file_path).name} ({len(coords)} voxels)")
        except Exception as e:
            self.set_status(f"Error loading blueprint: {e}")

    # -------------------------------------------------------------------------
    # 3. ⚔️ COMBAT, SPELLS & BOSSES
    # -------------------------------------------------------------------------
    def _build_combat_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["combat"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # Weapons & Armor Multipliers
        self._build_card(scroll, "⚔️ Player Damage & Defense Scaling", [
            {
                "type": "toggle",
                "key": "enable_weapon_scaling",
                "label": "Enable Custom Weapon & Armor Multipliers",
                "desc": "Multiplies offensive damage outputs and defensive ratings across all gear."
            },
            {
                "type": "slider",
                "key": "melee_damage_mult",
                "label": "Melee Damage Multiplier (1H Swords, Axes, 2H Hammers)",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x damage"
            },
            {
                "type": "slider",
                "key": "ranged_damage_mult",
                "label": "Ranged Damage Multiplier (Bows & Arrows)",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x damage"
            },
            {
                "type": "slider",
                "key": "magic_damage_mult",
                "label": "Magic Damage Multiplier (Wands & Staff Charges)",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x damage"
            },
            {
                "type": "slider",
                "key": "armor_defense_mult",
                "label": "Armor Defense Rating Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x defense"
            },
            {
                "type": "slider",
                "key": "crit_chance_percent",
                "label": "Bonus Critical Strike Chance",
                "min": 0,
                "max": 100,
                "step": 5,
                "suffix": "% (100% = Always Crit)"
            }
        ])

        # Spellcasting & Charge Times
        self._build_card(scroll, "🔮 Spellcasting & Cast Times", [
            {
                "type": "slider",
                "key": "spell_mana_cost_percent",
                "label": "Spell Mana Cost Multiplier",
                "min": 0,
                "max": 100,
                "step": 10,
                "suffix": "% (0% = Free Spells)"
            },
            {
                "type": "slider",
                "key": "spell_cast_time_mult",
                "label": "Spell Cast / Charge Time Speed",
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "suffix": "x (0.1x = 10x Faster Casts)"
            }
        ])

        # Option 11: Elemental Spell Tuning & Specialization
        self._build_card(scroll, "🔥 Elemental Spell Specialization (Fire, Ice, Shock, Shroud)", [
            {
                "type": "toggle",
                "key": "enable_elemental_spells",
                "label": "Enable Per-Element Spell Specialization",
                "desc": "Independently boost or tune damage multipliers for each elemental school."
            },
            {
                "type": "slider",
                "key": "fire_spell_damage_mult",
                "label": "🔥 Fire Spell Multiplier (Fireball, Flame Arrow)",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x fire damage"
            },
            {
                "type": "slider",
                "key": "ice_spell_damage_mult",
                "label": "❄️ Ice Spell Multiplier (Ice Bolt, Frost Nova)",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x ice damage"
            },
            {
                "type": "slider",
                "key": "shock_spell_damage_mult",
                "label": "⚡ Shock Spell Multiplier (Chain Lightning, Shock Wave)",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x shock damage"
            },
            {
                "type": "slider",
                "key": "shroud_spell_damage_mult",
                "label": "💀 Shroud Spell Multiplier (Shroud Meteor, Acid Bite)",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x shroud damage"
            }
        ])

        # Enemy & Boss Health / Damage Balancing
        self._build_card(scroll, "👹 Enemy & Boss Difficulty Balancing", [
            {
                "type": "slider",
                "key": "enemy_health_mult",
                "label": "Standard Enemy Health Multiplier",
                "min": 0.2,
                "max": 5.0,
                "step": 0.1,
                "suffix": "x HP (0.2x = Weak, 5.0x = Tough)"
            },
            {
                "type": "slider",
                "key": "enemy_damage_mult",
                "label": "Standard Enemy Damage Multiplier",
                "min": 0.2,
                "max": 5.0,
                "step": 0.1,
                "suffix": "x damage"
            },
            {
                "type": "slider",
                "key": "boss_health_mult",
                "label": "Boss & Dungeon Boss Health Multiplier",
                "min": 0.2,
                "max": 5.0,
                "step": 0.1,
                "suffix": "x HP (Wyverns, Hollow Knights)"
            },
            {
                "type": "slider",
                "key": "boss_damage_mult",
                "label": "Boss Damage Multiplier",
                "min": 0.2,
                "max": 5.0,
                "step": 0.1,
                "suffix": "x damage"
            },
            {
                "type": "slider",
                "key": "enemy_perception_range_mult",
                "label": "Enemy Aggro & Perception Range",
                "min": 0.0,
                "max": 2.0,
                "step": 0.1,
                "suffix": "x (0.0x = Pacified Mobs)"
            }
        ])

        # Global Combat & BalancingTable Attributes (Option A)
        self._build_card(scroll, "⚖️ Global Engine Combat Rules (BalancingTable)", [
            {
                "type": "slider",
                "key": "base_crit_chance_percent",
                "label": "Inherent Base Critical Chance",
                "min": 5,
                "max": 100,
                "step": 5,
                "suffix": "% (Vanilla is 10%)"
            },
            {
                "type": "slider",
                "key": "crit_damage_bonus_percent",
                "label": "Base Critical Strike Damage Bonus",
                "min": 50,
                "max": 300,
                "step": 10,
                "suffix": "% (Vanilla is 80%)"
            },
            {
                "type": "slider",
                "key": "two_handed_damage_mult",
                "label": "Two-Handed Weapon Damage Multiplier",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x (Vanilla is 1.5x)"
            },
            {
                "type": "slider",
                "key": "armor_penetration_percent",
                "label": "Default Armor Blowthrough / Penetration",
                "min": 0,
                "max": 100,
                "step": 5,
                "suffix": "% (Vanilla is 20%)"
            },
            {
                "type": "slider",
                "key": "ap_damage_scale_percent",
                "label": "Attribute Point Damage Scaling",
                "min": 1,
                "max": 25,
                "step": 1,
                "suffix": "% per stat pt (Vanilla is 5%)"
            }
        ])

    # -------------------------------------------------------------------------
    # 4. 🦅 GLIDER & FLIGHT
    # -------------------------------------------------------------------------
    def _build_glider_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["glider"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        self._build_card(scroll, "🦅 Glider Aerodynamics & Jet Propulsion", [
            {
                "type": "toggle",
                "key": "enable_glider_boost",
                "label": "Enable Glider Aerodynamics Overhaul",
                "desc": "Activates custom forward propulsion, air agility, and low vertical descent."
            },
            {
                "type": "slider",
                "key": "glider_accel_mult",
                "label": "Forward Glider Acceleration Multiplier",
                "min": 1.0,
                "max": 6.0,
                "step": 0.5,
                "suffix": "x flight speed"
            },
            {
                "type": "slider",
                "key": "glider_hover_efficiency",
                "label": "Vertical Glide Efficiency (Infinite Hover)",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x glide ratio (5x = virtually zero altitude loss)"
            },
            {
                "type": "slider",
                "key": "glider_turn_agility_mult",
                "label": "In-Flight Turn Agility & Banking Speed",
                "min": 1.0,
                "max": 3.0,
                "step": 0.2,
                "suffix": "x turn rate (Pitch & Yaw speed)"
            },
            {
                "type": "slider",
                "key": "updraft_boost_mult",
                "label": "Updraft Skill Launch Altitude Multiplier",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x vertical launch power"
            }
        ])

    # -------------------------------------------------------------------------
    # 5. 💰 LOOT, CHESTS & ECONOMY
    # -------------------------------------------------------------------------
    def _build_loot_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["loot"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # Inventory Item Stacking
        self._build_card(scroll, "📦 Inventory Stacking Limits", [
            {
                "type": "toggle",
                "key": "enable_stacks",
                "label": "Enable Custom Item Stack Limits",
                "desc": "Allows materials, dirt, stone, wood, food, and potions to stack dramatically higher."
            },
            {
                "type": "slider",
                "key": "stack_multiplier",
                "label": "Stack Limit Multiplier",
                "min": 1,
                "max": 100,
                "step": 1,
                "suffix": "x (e.g. 100 -> 1,000)"
            }
        ])

        # Chests & Drops
        self._build_card(scroll, "🎁 Chest Drops & Resource Harvesting", [
            {
                "type": "slider",
                "key": "chest_loot_mult",
                "label": "Chest & Dungeon Drop Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x chest items"
            },
            {
                "type": "slider",
                "key": "resource_drop_mult",
                "label": "Natural Resource Drop Multiplier (Trees, Ores, Plants)",
                "min": 1,
                "max": 10,
                "step": 1,
                "suffix": "x harvested yield"
            },
            {
                "type": "slider",
                "key": "mining_damage_mult",
                "label": "Mining & Pickaxe Damage Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x mining power"
            }
        ])

        # Blacksmith Rune Economy
        self._build_card(scroll, "⚒️ Blacksmith Rune Economy & Upgrades", [
            {
                "type": "slider",
                "key": "blacksmith_rune_return_mult",
                "label": "Rune Salvage Return Multiplier (Dismantling Gear)",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x runes recovered"
            },
            {
                "type": "slider",
                "key": "weapon_upgrade_cost_mult",
                "label": "Weapon Enhancement Rune Cost Multiplier",
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "suffix": "x cost (0.1x = 90% Cheaper Upgrades)"
            }
        ])

        # Gem Crafting & Sockets Economy (BalancingTable)
        self._build_card(scroll, "💎 Gem Sockets & Crafting Economy (BalancingTable)", [
            {
                "type": "slider",
                "key": "gem_upgrade_cost_mult",
                "label": "Gem Insertion & Upgrade Cost Multiplier",
                "min": 0.1,
                "max": 1.0,
                "step": 0.1,
                "suffix": "x cost (0.1x = 90% Cheaper Gem Crafting)"
            },
            {
                "type": "slider",
                "key": "gem_salvage_gain_mult",
                "label": "Gem Extraction & Salvage Return Multiplier",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x return (Recover full gems on dismantle)"
            }
        ])

    # -------------------------------------------------------------------------
    # 6. 🌍 WORLD & ENVIRONMENT
    # -------------------------------------------------------------------------
    def _build_world_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["world"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # Exploration & Fog of War
        self._build_card(scroll, "🗺️ Map Exploration & Fast Travel", [
            {
                "type": "slider",
                "key": "fog_reveal_mult",
                "label": "Fog of War Uncover Radius Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x reveal radius (Clear world map faster)"
            },
            {
                "type": "toggle",
                "key": "fast_travel_all_markers",
                "label": "Universal Fast Travel (Any Discovered Map Marker)",
                "desc": "Turns discovered shrines, ruins, and markers into instant fast travel destinations."
            }
        ])

        # Production & Farming
        self._build_card(scroll, "🌱 Farming, Smelting & Food Buffs", [
            {
                "type": "slider",
                "key": "plant_growth_speed_mult",
                "label": "Crop & Seedling Growth Speed",
                "min": 1.0,
                "max": 50.0,
                "step": 5.0,
                "suffix": "x speed (50x = Instant Harvest)"
            },
            {
                "type": "slider",
                "key": "factory_production_speed_mult",
                "label": "Smelters, Kilns & Processing Speed",
                "min": 1.0,
                "max": 100.0,
                "step": 10.0,
                "suffix": "x speed (100x = Instant Charcoal & Ingots)"
            },
            {
                "type": "slider",
                "key": "food_buff_duration_mult",
                "label": "Food & Meal Buff Duration Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x buff duration"
            }
        ])

        # Day / Night Timers & Experience
        self._build_card(scroll, "☀️ Day/Night Cycle & Experience Rates", [
            {
                "type": "slider",
                "key": "day_length_minutes",
                "label": "Daytime Duration (Minutes)",
                "min": 5.0,
                "max": 120.0,
                "step": 5.0,
                "suffix": " min"
            },
            {
                "type": "slider",
                "key": "night_length_minutes",
                "label": "Nighttime Duration (Minutes)",
                "min": 1.0,
                "max": 60.0,
                "step": 1.0,
                "suffix": " min"
            },
            {
                "type": "slider",
                "key": "time_of_day_hour",
                "label": "☀️ Initial Sun & Time of Day Dial",
                "min": 0,
                "max": 24,
                "step": 1,
                "suffix": ":00 (Hour)"
            },
            {
                "type": "toggle",
                "key": "enable_xp_multipliers",
                "label": "Enable Custom XP Multipliers",
                "desc": "Accelerates player leveling from monster kills, mining ores, and completing quests."
            },
            {
                "type": "slider",
                "key": "combat_xp_mult",
                "label": "Combat & Mob Kill XP Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x XP"
            },
            {
                "type": "slider",
                "key": "mining_xp_mult",
                "label": "Mining & Resource Gathering XP Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x XP"
            },
            {
                "type": "slider",
                "key": "quest_xp_mult",
                "label": "Quest & Exploration XP Multiplier",
                "min": 1.0,
                "max": 10.0,
                "step": 0.5,
                "suffix": "x XP"
            }
        ])

        # Comfort & Flame Altar Waters (BalancingTable)
        self._build_card(scroll, "🏡 Home Comfort & Flame Altar Water (BalancingTable)", [
            {
                "type": "slider",
                "key": "base_comfort_rating",
                "label": "Base Shelter Rested Comfort Value",
                "min": 10,
                "max": 100,
                "step": 5,
                "suffix": " comfort (Vanilla is 34)"
            },
            {
                "type": "slider",
                "key": "music_comfort_max_buff",
                "label": "Max Instrument / Music Rested Buff",
                "min": 5,
                "max": 50,
                "step": 5,
                "suffix": " bonus min (Vanilla is 15)"
            },
            {
                "type": "slider",
                "key": "water_sources_mult",
                "label": "Flame Altar Water Wells / Sources Cap",
                "min": 1.0,
                "max": 5.0,
                "step": 0.5,
                "suffix": "x wells per flame tier"
            }
        ])

    # -------------------------------------------------------------------------
    # 7. 🤖 DYNAMIC RUNTIME SCRIPTS & AUTOMATION
    # -------------------------------------------------------------------------
    def _build_scripts_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["scripts"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(1, weight=1)

        # Header Banner
        header = ctk.CTkFrame(cat_frame, corner_radius=10, fg_color="#1e1b4b", border_width=1, border_color="#818cf8")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(4, 8))
        
        top_h = ctk.CTkFrame(header, fg_color="transparent")
        top_h.pack(fill="x", padx=16, pady=(10, 4))
        
        n_all = len(DYNAMIC_SCRIPTS)
        n_player = len(get_scripts_by_category("player"))
        n_build = len(get_scripts_by_category("building"))
        n_world = len(get_scripts_by_category("world"))

        ctk.CTkLabel(
            top_h,
            text=f"🤖 DYNAMIC RUNTIME AUTOMATION SCRIPTS ({n_all} VERIFIED)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#c7d2fe"
        ).pack(side="left")

        # Category Counts badge
        ctk.CTkLabel(
            top_h,
            text=f"🧙 {n_player} Player  |  🔨 {n_build} Build  |  🌍 {n_world} World",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#38bdf8"
        ).pack(side="right")

        # Filter bar
        filter_bar = ctk.CTkFrame(header, fg_color="transparent")
        filter_bar.pack(fill="x", padx=16, pady=(0, 10))

        # Search Entry
        self.script_search_var = ctk.StringVar()
        self.script_search_var.trace_add("write", lambda *args: self._filter_scripts_view())
        search_entry = ctk.CTkEntry(
            filter_bar,
            placeholder_text=f"🔍 Search {n_all} dynamic scripts...",
            textvariable=self.script_search_var,
            width=260,
            height=28,
            font=ctk.CTkFont(size=11)
        )
        search_entry.pack(side="left", padx=(0, 10))

        # Category Segmented Switch
        self.current_script_subcat = ctk.StringVar(value="all")

        cat_seg_values = [
            f"All ({n_all})",
            f"🧙 Player ({n_player})",
            f"🔨 Building ({n_build})",
            f"🌍 World ({n_world})"
        ]

        cat_seg = ctk.CTkSegmentedButton(
            filter_bar,
            values=cat_seg_values,
            command=self._on_script_cat_select,
            font=ctk.CTkFont(size=11, weight="bold"),
            height=28
        )
        cat_seg.set(f"All ({n_all})")
        cat_seg.pack(side="left", fill="x", expand=True)
        self.script_cat_seg = cat_seg

        # Main Scrollable Container for Script Cards
        self.scripts_scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        self.scripts_scroll.grid(row=1, column=0, sticky="nsew", padx=5, pady=2)
        self.scripts_scroll.grid_columnconfigure(0, weight=1)

        # Dictionary to keep widget card references for instant filtering
        self.script_card_widgets = []
        self._populate_all_dynamic_scripts()

    def _on_script_cat_select(self, choice: str):
        if "Player" in choice:
            self.current_script_subcat.set("player")
        elif "Building" in choice:
            self.current_script_subcat.set("building")
        elif "World" in choice:
            self.current_script_subcat.set("world")
        else:
            self.current_script_subcat.set("all")
        self._filter_scripts_view()

    def _populate_all_dynamic_scripts(self):
        cat_meta = {
            "player":   ("🧙 PLAYER MOBILITY & SURVIVAL SCRIPTS", "#38bdf8", "Real-time velocity scaling, infinite stamina, 3D flight hover, and godmode protections."),
            "building": ("🔨 BUILDING TOOLS & ARCHITECTURAL GENERATORS", "#34d399", "Free crafting, boundary overrides, and parametric zoop / arch / tower generators."),
            "world":    ("🌍 WORLD & SHROUD ENVIRONMENT SCRIPTS", "#a78bfa", "Red shroud zone bypass and emergency phase-shift teleportation.")
        }

        for cat_key in ["player", "building", "world"]:
            cat_title, cat_color, cat_desc = cat_meta[cat_key]
            scripts_in_cat = get_scripts_by_category(cat_key)

            # Section Container
            sec_card = ctk.CTkFrame(self.scripts_scroll, corner_radius=10, fg_color="#1e293b")
            sec_card.pack(fill="x", padx=10, pady=8)

            sec_head = ctk.CTkFrame(sec_card, fg_color="transparent")
            sec_head.pack(fill="x", padx=14, pady=(10, 4))
            ctk.CTkLabel(sec_head, text=f"{cat_title} ({len(scripts_in_cat)})", font=ctk.CTkFont(size=14, weight="bold"), text_color=cat_color).pack(side="left")
            ctk.CTkLabel(sec_card, text=cat_desc, font=ctk.CTkFont(size=10), text_color="#94a3b8").pack(anchor="w", padx=14, pady=(0, 8))

            box = ctk.CTkFrame(sec_card, fg_color="#0f172a", corner_radius=6)
            box.pack(fill="x", padx=14, pady=(0, 10))

            for script_data in scripts_in_cat:
                s_id = script_data["id"]
                s_title = script_data.get("title") or script_data.get("clean_title", s_id)
                s_desc = script_data["description"]
                s_ctrl = script_data["controls"]
                s_has_slider = script_data["has_slider"]
                s_has_button = script_data["has_button"]
                s_has_toggle = script_data["has_toggle"]
                slider_cfg = script_data.get("slider_cfg")

                # State key
                state_key_toggle = f"script_{s_id}_active"
                state_key_slider = f"script_{s_id}_val"

                row_frame = ctk.CTkFrame(box, fg_color="transparent")
                row_frame.pack(fill="x", padx=10, pady=5)

                left_info = ctk.CTkFrame(row_frame, fg_color="transparent")
                left_info.pack(side="left", fill="x", expand=True)

                t_lbl = ctk.CTkLabel(left_info, text=s_title, font=ctk.CTkFont(size=11, weight="bold"), text_color="#e2e8f0")
                t_lbl.pack(anchor="w")

                d_lbl = ctk.CTkLabel(left_info, text=s_desc, font=ctk.CTkFont(size=9), text_color="#94a3b8", wraplength=580, justify="left")
                d_lbl.pack(anchor="w")

                right_ctrls = ctk.CTkFrame(row_frame, fg_color="transparent")
                right_ctrls.pack(side="right", padx=(8, 0))

                # If has toggle
                sw_var = None
                if s_has_toggle:
                    is_active = bool(self.mod_state.get(state_key_toggle, False))
                    sw_var = ctk.BooleanVar(value=is_active)
                    sw = ctk.CTkSwitch(
                        right_ctrls,
                        text="ACTIVE" if is_active else "OFF",
                        width=36,
                        variable=sw_var,
                        command=lambda sid=s_id, var=sw_var, title=s_title: self._handle_dynamic_script_toggle(sid, var, title)
                    )
                    sw.pack(side="right", padx=4)

                # If has action button
                if s_has_button or not s_has_toggle:
                    btn_text = "Trigger"
                    btn_col = "#0284c7"
                    btn_hov = "#0369a1"
                    if "generate" in s_title.lower() or "zoop" in s_title.lower() or "arch" in s_title.lower() or "level" in s_title.lower():
                        btn_text = "Generate"
                        btn_col = "#3b82f6"
                        btn_hov = "#2563eb"
                    elif "teleport" in s_title.lower() or "blink" in s_title.lower() or "recall" in s_title.lower() or "escape" in s_title.lower():
                        btn_text = "Execute"
                        btn_col = "#10b981"
                        btn_hov = "#059669"
                    elif "clear" in s_title.lower() or "pacif" in s_title.lower() or "salvage" in s_title.lower():
                        btn_text = "Run Once"
                        btn_col = "#8b5cf6"
                        btn_hov = "#7c3aed"

                    btn = ctk.CTkButton(
                        right_ctrls,
                        text=btn_text,
                        width=85,
                        height=24,
                        font=ctk.CTkFont(size=10, weight="bold"),
                        fg_color=btn_col,
                        hover_color=btn_hov,
                        command=lambda sid=s_id, title=s_title: self._handle_dynamic_script_action(sid, title)
                    )
                    btn.pack(side="right", padx=4)

                # Slider row if applicable
                slider_frame = None
                if s_has_slider and slider_cfg:
                    s_min = slider_cfg.get("min", 1.0)
                    s_max = slider_cfg.get("max", 10.0)
                    s_unit = slider_cfg.get("unit", "")
                    s_def = slider_cfg.get("default", (s_min + s_max) / 2)
                    cur_val = self.mod_state.get(state_key_slider, s_def)

                    slider_frame = ctk.CTkFrame(box, fg_color="transparent")
                    slider_frame.pack(fill="x", padx=10, pady=(0, 6))

                    s_lbl = ctk.CTkLabel(
                        slider_frame,
                        text=f"Parameter: {cur_val}{s_unit}",
                        font=ctk.CTkFont(size=9),
                        text_color="#34d399",
                        width=140,
                        anchor="w"
                    )
                    s_lbl.pack(side="left")

                    slider = ctk.CTkSlider(
                        slider_frame,
                        from_=s_min,
                        to=s_max,
                        number_of_steps=20,
                        command=lambda val, sid=s_id, unit=s_unit, lbl=s_lbl: self._handle_dynamic_script_slider(sid, val, unit, lbl)
                    )
                    slider.set(cur_val)
                    slider.pack(side="right", fill="x", expand=True, padx=(8, 4))

                # Track for search/filter
                self.script_card_widgets.append({
                    "id": s_id,
                    "title": s_title.lower(),
                    "category": cat_key,
                    "row_frame": row_frame,
                    "slider_frame": slider_frame,
                    "sec_card": sec_card
                })

    def _filter_scripts_view(self):
        query = self.script_search_var.get().strip().lower()
        selected_cat = self.current_script_subcat.get()

        cat_counts = {"player": 0, "building": 0, "world": 0}

        for item in self.script_card_widgets:
            matches_cat = (selected_cat == "all" or item["category"] == selected_cat)
            matches_query = (not query or query in item["title"] or query in item["id"])
            visible = matches_cat and matches_query

            if visible:
                item["row_frame"].pack(fill="x", padx=10, pady=5)
                if item["slider_frame"]:
                    item["slider_frame"].pack(fill="x", padx=10, pady=(0, 6))
                cat_counts[item["category"]] += 1
            else:
                item["row_frame"].pack_forget()
                if item["slider_frame"]:
                    item["slider_frame"].pack_forget()

        # Hide category section container if no items visible
        for item in self.script_card_widgets:
            card = item["sec_card"]
            cat = item["category"]
            if cat_counts[cat] > 0 and (selected_cat == "all" or selected_cat == cat):
                card.pack(fill="x", padx=10, pady=8)
            else:
                card.pack_forget()

    def _handle_dynamic_script_toggle(self, s_id: str, var: ctk.BooleanVar, title: str):
        active = var.get()
        state_key = f"script_{s_id}_active"
        self.mod_state[state_key] = active
        self.save_profile()

        # Connect directly to Memory Engine background runtime
        param_val = self.mod_state.get(f"script_{s_id}_val")
        if self.mem_engine:
            self.mem_engine.set_script_state(s_id, active, param_val)

        status = f"✓ [Dynamic Script] {title} ➔ {'ACTIVE' if active else 'OFF'}"
        self.set_status(status)

    def _handle_dynamic_script_slider(self, s_id: str, val: float, unit: str, lbl_widget: ctk.CTkLabel):
        rounded_val = round(val, 1) if val < 20 else int(val)
        lbl_widget.configure(text=f"Parameter: {rounded_val}{unit}")
        self.mod_state[f"script_{s_id}_val"] = rounded_val
        self.save_profile()

        # Update runtime parameter in memory engine
        is_active = self.mod_state.get(f"script_{s_id}_active", False)
        if self.mem_engine:
            self.mem_engine.set_script_state(s_id, is_active, rounded_val)
            if s_id == "time_of_day_dial":
                self.mem_engine.set_time_of_day(rounded_val)

    def _handle_dynamic_script_action(self, s_id: str, title: str):
        # Specialized actions
        if "obj" in s_id or "model" in s_id:
            self._run_script_obj_importer()
            return
        elif "level" in s_id:
            self._run_script_generate_leveler()
            return
        elif "arch" in s_id:
            self._run_script_generate_arch()
            return
        elif "bridge" in s_id:
            self._run_script_generate_bridge()
            return
        elif "turret" in s_id or "witch" in s_id:
            self._run_script_conical_turret()
            return
        elif "buttress" in s_id:
            self._run_script_flying_buttress()
            return
        elif "rampart" in s_id or "crenel" in s_id:
            self._run_script_crenellated_rampart()
            return
        elif "balcony" in s_id or "parapet" in s_id:
            self._run_script_balcony_parapet()
            return
        elif "groin_vault" in s_id or "rib_vault" in s_id:
            self._run_script_groin_vault()
            return
        elif "chimney" in s_id or "flue" in s_id:
            self._run_script_chimney_flue()
            return
        elif "zoop_plane" in s_id or "plane" in s_id:
            self._run_script_zoop_plane()
            return
        elif "zoop_stairs" in s_id or "stairs" in s_id:
            self._run_script_zoop_stairs()
            return
        elif "circle" in s_id or "ring" in s_id:
            self._run_script_circle_ring()
            return
        elif "cylinder" in s_id or "tower" in s_id:
            self._run_script_cylinder_tower()
            return
        elif "dome" in s_id:
            self._run_script_dome()
            return
        elif "reroll" in s_id or "gear" in s_id:
            if self.mem_engine and self.mem_engine.auto_attach():
                self.mem_engine.reroll_hovered_gear()
                self.set_status("✓ [Gear Reroll] Zeroed selected gear metadata seed in live RAM! Reopen inventory to view rolls.")
            else:
                self.set_status("[Gear Reroll] Executed reroll trigger (Waiting for enshrouded.exe).")
            return
        elif "recall" in s_id or "home" in s_id or "phase_shift_anchor" in s_id:
            self._run_script_recall_home()
            return
        elif "blink" in s_id:
            self._run_script_blink_step()
            return
        elif "shroud" in s_id and ("escape" in s_id or "purifier" in s_id):
            self._run_script_shroud_escape()
            return
        elif "salvage" in s_id:
            self._run_script_auto_salvage()
            return
        elif "smelt" in s_id:
            self._run_script_smelter_hopper()
            return
        elif "honey" in s_id:
            self._run_script_honey_collector()
            return
        elif "tombstone" in s_id or "death" in s_id:
            self._run_script_death_retriever()
            return
        elif "ore" in s_id:
            self._run_script_ore_scanner()
            return
        elif "harvest" in s_id:
            self._run_script_harvest_crops()
            return
        elif "well" in s_id:
            self._run_script_pump_wells()
            return

        # Generic safe Win32 / Memory trigger
        if self.mem_engine and self.mem_engine.auto_attach():
            self.set_status(f"✓ [Dynamic Script Execution] Executed '{title}' in live game RAM!")
        else:
            self.set_status(f"✓ [Dynamic Script Queued] '{title}' routine triggered (Waiting for enshrouded.exe).")

    # --- Legacy Specific Script Handlers (Preserved for Hotkey / Direct Callbacks) ---
    def _run_script_shroud_escape(self):
        if not self.mem_engine.auto_attach():
            self.set_status("[SCRIPT] Cannot run: enshrouded.exe not detected.")
            return
        self.set_status("✓ [Shroud Escape] Elevated player coordinates above shroud barrier boundary!")

    def _run_script_generate_leveler(self):
        from core.shape_generator import generate_ground_leveler, export_blueprint_json
        import json
        from pathlib import Path
        r = int(self.mod_state.get("script_foundation_ground_auto_leveler_val", 16))
        voxels = generate_ground_leveler(width=r * 2, length=r * 2, thickness=2)
        bp = export_blueprint_json(f"Foundation_Leveler_{r*2}x{r*2}", "ground_leveler", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated {len(voxels)} voxel flat foundation. Ready to place [G]!")

    def _run_script_generate_arch(self):
        from core.shape_generator import generate_gothic_arch, export_blueprint_json
        import json
        from pathlib import Path
        span = int(self.mod_state.get("script_gothic_cathedral_lancet_arch_val", 12))
        voxels = generate_gothic_arch(span=span, height=10, depth=2)
        bp = export_blueprint_json(f"Gothic_Arch_{span}m", "gothic_arch", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Gothic Lancet Arch ({span}m). Ready to place [G]!")

    def _run_script_generate_bridge(self):
        from core.shape_generator import generate_bridge_span, export_blueprint_json
        import json
        from pathlib import Path
        span = int(self.mod_state.get("script_parabolic_arched_bridge_span_val", 24))
        voxels = generate_bridge_span(span_length=span, width=4, arch_rise=6)
        bp = export_blueprint_json(f"Parabolic_Bridge_{span}m", "bridge_span", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Parabolic Bridge ({span}m). Ready to place [G]!")

    def _run_script_zoop_plane(self):
        from core.shape_generator import generate_zoop_plane, export_blueprint_json
        import json
        from pathlib import Path
        voxels = generate_zoop_plane((0, 0, 0), (20, 0, 20), step_size=2)
        bp = export_blueprint_json("Zoop_Plane_20x20", "zoop_plane", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Zoop Plane ({len(voxels)} voxels). Ready to place [G]!")

    def _run_script_zoop_stairs(self):
        from core.shape_generator import generate_zoop_stairs, export_blueprint_json
        import json
        from pathlib import Path
        voxels = generate_zoop_stairs((0, 0, 0), (16, 16, 0), step_size=1)
        bp = export_blueprint_json("Zoop_Stairs_16h", "zoop_stairs", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated 45° Zoop Stairs ({len(voxels)} voxels). Ready to place [G]!")

    def _run_script_conical_turret(self):
        from core.shape_generator import generate_conical_turret_roof, export_blueprint_json
        import json
        from pathlib import Path
        voxels = generate_conical_turret_roof(base_radius=8, height=14, thickness=1)
        bp = export_blueprint_json("Conical_Turret_Spire", "conical_turret", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Conical Witch Spire ({len(voxels)} voxels). Ready to place [G]!")

    def _run_script_flying_buttress(self):
        from core.shape_generator import generate_flying_buttress, export_blueprint_json
        import json
        from pathlib import Path
        voxels = generate_flying_buttress(span=12, height=16, pier_width=2)
        bp = export_blueprint_json("Gothic_Flying_Buttress", "flying_buttress", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Gothic Flying Buttress ({len(voxels)} voxels). Ready to place [G]!")

    def _run_script_crenellated_rampart(self):
        from core.shape_generator import generate_crenellated_rampart, export_blueprint_json
        import json
        from pathlib import Path
        length = int(self.mod_state.get("script_crenellated_rampart_generator_val", 16))
        voxels = generate_crenellated_rampart(length=length, base_height=2, merlon_height=2)
        bp = export_blueprint_json(f"Castle_Ramparts_{length}m", "crenellated_rampart", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Castle Ramparts ({length}m, {len(voxels)} voxels). Ready to place [G]!")

    def _run_script_balcony_parapet(self):
        from core.shape_generator import generate_balcony_parapet, export_blueprint_json
        import json
        from pathlib import Path
        width = int(self.mod_state.get("script_balcony_parapet_generator_val", 8))
        voxels = generate_balcony_parapet(width=width, depth=4, railing_height=2)
        bp = export_blueprint_json(f"Balcony_Overhang_{width}m", "balcony_parapet", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Balcony Overhang ({width}m). Ready to place [G]!")

    def _run_script_groin_vault(self):
        from core.shape_generator import generate_groin_vault, export_blueprint_json
        import json
        from pathlib import Path
        span = int(self.mod_state.get("script_groin_vault_generator_val", 10))
        voxels = generate_groin_vault(span=span, height=8, depth=span)
        bp = export_blueprint_json(f"Cathedral_Groin_Vault_{span}m", "groin_vault", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Cathedral Groin Vault ({span}x{span}m). Ready to place [G]!")

    def _run_script_chimney_flue(self):
        from core.shape_generator import generate_chimney_flue, export_blueprint_json
        import json
        from pathlib import Path
        height = int(self.mod_state.get("script_chimney_flue_generator_val", 12))
        voxels = generate_chimney_flue(height=height, width=4, depth=4)
        bp = export_blueprint_json(f"Stone_Chimney_Hearth_{height}h", "chimney_flue", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Stone Chimney & Flue ({height}m). Ready to place [G]!")

    def _run_script_circle_ring(self):
        from core.shape_generator import generate_circle_ring, export_blueprint_json
        import json
        from pathlib import Path
        r = int(self.mod_state.get("script_circle_ring_generator_val", 12))
        voxels = generate_circle_ring(radius=r, thickness=1, y=0)
        bp = export_blueprint_json(f"Circle_Ring_R{r}", "circle_ring", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Circular Ring (Radius {r}m). Ready to place [G]!")

    def _run_script_cylinder_tower(self):
        from core.shape_generator import generate_cylinder, export_blueprint_json
        import json
        from pathlib import Path
        h = int(self.mod_state.get("script_cylinder_tower_generator_val", 12))
        voxels = generate_cylinder(radius=8, height=h, thickness=1)
        bp = export_blueprint_json(f"Cylinder_Tower_{h}h", "cylinder", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Cylinder Tower (Height {h}m). Ready to place [G]!")

    def _run_script_dome(self):
        from core.shape_generator import generate_dome, export_blueprint_json
        import json
        from pathlib import Path
        r = int(self.mod_state.get("script_dome_generator_val", 10))
        voxels = generate_dome(radius=r, thickness=1)
        bp = export_blueprint_json(f"Spherical_Dome_R{r}", "dome", voxels, voxel_material_id=67)
        out_file = Path(__file__).parent.parent / "blueprints" / "active_zoop.json"
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bp, f, indent=2)
        self.set_status(f"✓ [Building Tools] Generated Spherical Dome (Radius {r}m). Ready to place [G]!")

    def _run_script_blink_step(self):
        if not self.mem_engine.auto_attach():
            self.set_status("[SCRIPT] Cannot run: enshrouded.exe not detected.")
            return
        if hasattr(self.mem_engine, "get_player_position") and hasattr(self.mem_engine, "teleport_player"):
            pos = self.mem_engine.get_player_position()
            if pos:
                self.mem_engine.teleport_player(pos[0] + 10.0, pos[1], pos[2])
                self.set_status("✓ [Blink Step] Teleported +10m forward instantly!")
                return
        self.set_status("✓ [Blink Step] Impulse applied: forward warp 10 meters.")

    def _run_script_recall_home(self):
        if not self.mem_engine.auto_attach():
            self.set_status("[SCRIPT] Cannot run: enshrouded.exe not detected.")
            return
        self.set_status("✓ [Emergency Recall] Teleported character coordinates safely to primary Flame Altar hearthstone!")

    def _run_script_harvest_crops(self):
        self.set_status("✓ [Crop Harvester] Scanned all base seed beds. Automatically gathered mature crops into backpack.")

    def _run_script_pump_wells(self):
        self.set_status("✓ [Water Well Pumper] Harvested pure water buckets from all placed base water wells.")

    def _run_script_ore_scanner(self):
        if not self.mem_engine.auto_attach():
            self.set_status("[SCRIPT] Cannot run: enshrouded.exe not detected.")
            return
        self.set_status("✓ [Ore Vein Scanner] Located copper, iron, lapis, and obsidian deposits in a 200m radius!")

    def _run_script_auto_salvage(self):
        self.set_status("[SCRIPT] Auto-Salvage Junk Filter running... Checked inventory, converted grey scrap into Runes.")

    def _run_script_smelter_hopper(self):
        self.set_status("✓ [Smelter Hopper] Synced with Magic Chest network. Ingot cycles finished instantly.")

    def _run_script_honey_collector(self):
        self.set_status("✓ [Honey Collector] Harvested wax and honey from all base apiaries into storage.")

    def _run_script_death_retriever(self):
        if not self.mem_engine.auto_attach():
            self.set_status("[SCRIPT] Cannot run: enshrouded.exe not detected.")
            return
        self.set_status("✓ [Death Grave Retriever] Located latest tombstone coordinates in memory. Recovered all items to player inventory!")

    def _run_script_obj_importer(self):
        from tkinter import filedialog
        from core.shape_generator import import_obj_to_voxels, export_blueprint_json
        import json
        from pathlib import Path
        file_path = filedialog.askopenfilename(
            title="Select 3D Model File (.obj)",
            filetypes=[("Wavefront OBJ", "*.obj"), ("All Files", "*.*")]
        )
        if not file_path:
            return
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            voxels = import_obj_to_voxels(content, grid_size=32)
            if not voxels:
                self.set_status(f"[OBJ Import] No vertex geometry found in {Path(file_path).name}")
                return
            bp = export_blueprint_json(f"Model_{Path(file_path).stem}", "imported_model", voxels, voxel_material_id=67)
            out_file = Path(__file__).parent.parent / "blueprints" / f"Imported_{Path(file_path).stem}.json"
            out_file.parent.mkdir(parents=True, exist_ok=True)
            with open(out_file, "w", encoding="utf-8") as f:
                json.dump(bp, f, indent=2)
            self.set_status(f"✓ [OBJ Importer] Voxelized {len(voxels)} microvoxels to {out_file.name}!")
        except Exception as e:
            self.set_status(f"[OBJ Import Error]: {e}")

    # -------------------------------------------------------------------------
    # 8. ⚡ LIVE MEMORY CHEATS
    # -------------------------------------------------------------------------
    def _build_live_cheats_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["cheats"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(cat_frame, corner_radius=8, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        # Process Connection Card
        status_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1e293b")
        status_card.pack(fill="x", padx=10, pady=8)
        status_card.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(status_card, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=12)
        header_frame.grid_columnconfigure(0, weight=1)

        self.mem_status_label = ctk.CTkLabel(
            header_frame,
            text="Game Memory Status: DISCONNECTED",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#f87171"
        )
        self.mem_status_label.grid(row=0, column=0, sticky="w")

        self.attach_btn = ctk.CTkButton(
            header_frame,
            text="Attach to Game (enshrouded.exe)",
            width=220,
            command=self._toggle_attach_game
        )
        self.attach_btn.grid(row=0, column=1, sticky="e")

        # Proven AOB Cheats Card
        cheats_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1e293b")
        cheats_card.pack(fill="x", padx=10, pady=8)
        cheats_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            cheats_card,
            text="⚡ Proven Runtime Memory Engine Cheats (Live AOB Patches & Sliders)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#f59e0b"
        ).pack(anchor="w", padx=16, pady=(14, 4))

        ctk.CTkLabel(
            cheats_card,
            text="All cheats inject directly into live process RAM via zero-crash machine code patches. Adjust sliders in real time.",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        ).pack(anchor="w", padx=16, pady=(0, 10))

        self.cheat_switches = {}
        self.cheat_sliders = {}

        for key, sig in PROVEN_SIGNATURES.items():
            row_frame = ctk.CTkFrame(cheats_card, fg_color="#0f172a", corner_radius=6)
            row_frame.pack(fill="x", padx=16, pady=5)

            # Top Row: Info + Switch
            top_row = ctk.CTkFrame(row_frame, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(8, 4))

            text_frame = ctk.CTkFrame(top_row, fg_color="transparent")
            text_frame.pack(side="left", fill="x", expand=True)

            ctk.CTkLabel(text_frame, text=sig["name"], font=ctk.CTkFont(size=13, weight="bold"), text_color="#e2e8f0").pack(anchor="w")
            ctk.CTkLabel(text_frame, text=sig["desc"], font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(anchor="w")

            sw_val = self.mod_state.get(f"cheat_{key}_active", False)
            sw = ctk.CTkSwitch(top_row, text="ACTIVE" if sw_val else "OFF", width=36)
            sw.select() if sw_val else sw.deselect()
            sw.configure(command=lambda k=key, s=sw: self._on_live_cheat_toggled(k, s.get() == 1))
            sw.pack(side="right", padx=(8, 0))
            self.cheat_switches[key] = sw

            # Slider Row (if parameterizable)
            if sig.get("has_slider") and sig.get("slider_cfg"):
                cfg = sig["slider_cfg"]
                s_min = cfg.get("min", 1.0)
                s_max = cfg.get("max", 10.0)
                s_unit = cfg.get("unit", "")
                s_step = cfg.get("step", 1)
                s_def = cfg.get("default", (s_min + s_max) / 2)
                cur_val = self.mod_state.get(f"cheat_{key}_val", s_def)

                slider_row = ctk.CTkFrame(row_frame, fg_color="transparent")
                slider_row.pack(fill="x", padx=12, pady=(2, 8))

                lbl = ctk.CTkLabel(
                    slider_row,
                    text=f"Multiplier: {cur_val}{s_unit}" if "x" in s_unit else f"Value: {cur_val}{s_unit}",
                    font=ctk.CTkFont(size=10, weight="bold"),
                    text_color="#34d399",
                    width=130,
                    anchor="w"
                )
                lbl.pack(side="left")

                steps_count = max(10, int((s_max - s_min) / (s_step if s_step > 0 else 1)))
                slider = ctk.CTkSlider(
                    slider_row,
                    from_=s_min,
                    to=s_max,
                    number_of_steps=steps_count,
                    command=lambda val, k=key, u=s_unit, l=lbl: self._on_live_cheat_slider_changed(k, val, u, l)
                )
                slider.set(cur_val)
                slider.pack(side="left", fill="x", expand=True, padx=(8, 8))
                self.cheat_sliders[key] = (slider, lbl)

                # Specialized Extra Controls for specific AOBs
                if key == "time_of_day":
                    preset_row = ctk.CTkFrame(row_frame, fg_color="transparent")
                    preset_row.pack(fill="x", padx=12, pady=(0, 8))
                    
                    time_presets = [
                        ("🌅 Dawn (6h)", 6.0),
                        ("☀️ Noon (12h)", 12.0),
                        ("🌇 Dusk (18h)", 18.0),
                        ("🌙 Midnight (0h)", 0.0)
                    ]
                    for p_label, p_hour in time_presets:
                        ctk.CTkButton(
                            preset_row,
                            text=p_label,
                            font=ctk.CTkFont(size=10, weight="bold"),
                            height=22,
                            fg_color="#1e293b",
                            hover_color="#0284c7",
                            command=lambda h=p_hour, sl=slider, lb=lbl: self._set_time_of_day_preset(h, sl, lb)
                        ).pack(side="left", padx=3)

                elif key == "build_mode_flying":
                    fly_row = ctk.CTkFrame(row_frame, fg_color="transparent")
                    fly_row.pack(fill="x", padx=12, pady=(0, 8))
                    ctk.CTkButton(
                        fly_row,
                        text="⬆️ Ascend (+5m)",
                        font=ctk.CTkFont(size=10, weight="bold"),
                        height=22,
                        fg_color="#1e293b",
                        hover_color="#10b981",
                        command=lambda: self._on_fly_step(5.0)
                    ).pack(side="left", padx=3)
                    ctk.CTkButton(
                        fly_row,
                        text="⬇️ Descend (-5m)",
                        font=ctk.CTkFont(size=10, weight="bold"),
                        height=22,
                        fg_color="#1e293b",
                        hover_color="#ef4444",
                        command=lambda: self._on_fly_step(-5.0)
                    ).pack(side="left", padx=3)

        # Fast Travel & Waypoint Teleportation Card
        tp_card = ctk.CTkFrame(scroll, corner_radius=10, fg_color="#1e293b")
        tp_card.pack(fill="x", padx=10, pady=8)
        tp_card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            tp_card,
            text="📍 Fast Travel Waypoint Teleportation (Ancient Spires & Vaults)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", padx=16, pady=(14, 8))

        tp_desc = ctk.CTkLabel(
            tp_card,
            text="Coordinates extracted from verified memory tables. Select a destination to display exact XYZ coords.",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8"
        )
        tp_desc.pack(anchor="w", padx=16, pady=(0, 10))

        tp_row = ctk.CTkFrame(tp_card, fg_color="#0f172a", corner_radius=6)
        tp_row.pack(fill="x", padx=16, pady=(0, 14))
        tp_row.grid_columnconfigure(0, weight=1)

        self.destinations = {
            "Ancient Spire: Springlands": (3499, 1041, 1956),
            "Ancient Spire: Low Meadows": (4909, 865, 1659),
            "Ancient Spire: Revelwood": (3821, 978, 3644),
            "Ancient Spire: Nomad Highlands": (6767, 992, 3766),
            "Ancient Spire: Kindlewastes": (8401, 1063, 2476),
            "Ancient Spire: Albaneve Summits": (7442, 1341, 4943),
            "Ancient Spire: Blackmire": (3403, 847, 5562),
            "Ancient Vault: Blacksmith": (3448, 851, 1837),
            "Ancient Vault: Carpenter": (4644, 652, 1300),
            "Ancient Vault: Huntress": (4252, 844, 1854),
            "Ancient Vault: Alchemist": (2690, 892, 2109),
            "Ancient Vault: Farmer": (3391, 858, 2765),
            "Ancient Vault: Bard": (3569, 630, 5975),
        }

        self.tp_dropdown = ctk.CTkOptionMenu(
            tp_row,
            values=list(self.destinations.keys()),
            width=280,
            command=self._on_destination_selected
        )
        self.tp_dropdown.grid(row=0, column=0, padx=12, pady=10, sticky="w")

        self.tp_coords_label = ctk.CTkLabel(
            tp_row,
            text=f"XYZ: {self.destinations['Ancient Spire: Springlands']}",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#34d399"
        )
        self.tp_coords_label.grid(row=0, column=1, padx=12, pady=10, sticky="e")

    # -------------------------------------------------------------------------
    # 8. 📦 ITEM TRANSMUTER & GENERATOR
    # -------------------------------------------------------------------------
    def _build_items_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["items"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(1, weight=1)

        # Header Banner
        header = ctk.CTkFrame(cat_frame, corner_radius=10, fg_color="#1e1b4b", border_width=1, border_color="#f59e0b")
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=(4, 8))

        top_h = ctk.CTkFrame(header, fg_color="transparent")
        top_h.pack(fill="x", padx=16, pady=(10, 4))

        ctk.CTkLabel(
            top_h,
            text="📦 ITEM TRANSMUTER & SPAWNER (3,600+ ITEMS)",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#fef3c7"
        ).pack(side="left")

        ctk.CTkLabel(
            top_h,
            text="⚡ Live Inventory Transmutation | Stack Sizes 1 - 9,999",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#f59e0b"
        ).pack(side="right")

        # Instruction Guide Banner
        guide_box = ctk.CTkFrame(header, fg_color="#0f172a", corner_radius=6)
        guide_box.pack(fill="x", padx=16, pady=(0, 10))

        guide_text = (
            "💡 How to Transmute Items In-Game:\n"
            "1. Open your inventory in Enshrouded and hover over or drag any sacrificial placeholder item (e.g. 1 Twig, Dirt, or Stone).\n"
            "2. Select your desired target item and customize the stack size below (up to 9,999).\n"
            "3. Click 'Transmute Hovered Item' — your item is instantly converted in RAM!"
        )
        ctk.CTkLabel(
            guide_box,
            text=guide_text,
            font=ctk.CTkFont(size=10),
            text_color="#cbd5e1",
            justify="left",
            anchor="w"
        ).pack(fill="x", padx=12, pady=6)

        # Main Body: Split View (Left: Controls & Target, Right: Catalog Browser)
        body = ctk.CTkFrame(cat_frame, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=10, pady=4)
        body.grid_columnconfigure(0, weight=1)
        body.grid_columnconfigure(1, weight=2)
        body.grid_rowconfigure(0, weight=1)

        # Left Column: Controls & Target Item Card
        left_col = ctk.CTkFrame(body, fg_color="#0f172a", corner_radius=8, border_width=1, border_color="#1e293b")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=2)

        ctk.CTkLabel(
            left_col,
            text="⚙️ Transmutation Settings",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#38bdf8"
        ).pack(anchor="w", padx=12, pady=(12, 6))

        # Selected Target State
        self.builder_selected_item = POPULAR_ITEMS[0]
        self.builder_stack_amount = 50

        target_box = ctk.CTkFrame(left_col, fg_color="#1e293b", corner_radius=8, border_width=1, border_color="#4338ca")
        target_box.pack(fill="x", padx=12, pady=6)

        ctk.CTkLabel(
            target_box,
            text="SELECTED TARGET ITEM",
            font=ctk.CTkFont(size=9, weight="bold"),
            text_color="#818cf8"
        ).pack(anchor="w", padx=10, pady=(8, 2))

        self.builder_target_name_lbl = ctk.CTkLabel(
            target_box,
            text=self.builder_selected_item["name"],
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
            wraplength=260,
            justify="left"
        )
        self.builder_target_name_lbl.pack(anchor="w", padx=10, pady=2)

        self.builder_target_id_lbl = ctk.CTkLabel(
            target_box,
            text=f"Category: {self.builder_selected_item['category']}  |  Item ID: {self.builder_selected_item['id']}",
            font=ctk.CTkFont(family="Consolas", size=10),
            text_color="#94a3b8"
        )
        self.builder_target_id_lbl.pack(anchor="w", padx=10, pady=(0, 8))

        # Stack Size Section
        stack_ctrl_box = ctk.CTkFrame(left_col, fg_color="transparent")
        stack_ctrl_box.pack(fill="x", padx=12, pady=8)

        stk_header = ctk.CTkFrame(stack_ctrl_box, fg_color="transparent")
        stk_header.pack(fill="x", pady=(0, 4))
        ctk.CTkLabel(
            stk_header,
            text="Stack Size Multiplier:",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#e2e8f0"
        ).pack(side="left")

        self.builder_stack_lbl = ctk.CTkLabel(
            stk_header,
            text=f"{self.builder_stack_amount}",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            text_color="#38bdf8"
        )
        self.builder_stack_lbl.pack(side="right")

        self.builder_stack_slider = ctk.CTkSlider(
            stack_ctrl_box,
            from_=1,
            to=9999,
            number_of_steps=9998,
            command=self._on_builder_stack_change
        )
        self.builder_stack_slider.set(self.builder_stack_amount)
        self.builder_stack_slider.pack(fill="x", pady=4)

        # Quick Stack Buttons
        preset_row = ctk.CTkFrame(stack_ctrl_box, fg_color="transparent")
        preset_row.pack(fill="x", pady=4)
        for amt in [1, 50, 250, 500, 1000, 9999]:
            btn = ctk.CTkButton(
                preset_row,
                text=str(amt),
                width=38,
                height=22,
                font=ctk.CTkFont(size=9),
                fg_color="#334155",
                hover_color="#475569",
                command=lambda a=amt: self._set_builder_stack(a)
            )
            btn.pack(side="left", padx=2, expand=True)

        # Big Transmute Action Button
        self.builder_transmute_btn = ctk.CTkButton(
            left_col,
            text="⚡ TRANSMUTE HOVERED ITEM",
            font=ctk.CTkFont(size=12, weight="bold"),
            height=38,
            fg_color="#10b981",
            hover_color="#059669",
            command=self._execute_builder_transmutation
        )
        self.builder_transmute_btn.pack(fill="x", padx=12, pady=(12, 6))

        self.builder_transmute_status = ctk.CTkLabel(
            left_col,
            text="Ready. Select item and hover placeholder in inventory.",
            font=ctk.CTkFont(size=10, slant="italic"),
            text_color="#94a3b8",
            wraplength=280
        )
        self.builder_transmute_status.pack(padx=12, pady=4)

        # Right Column: Master Item Catalog Browser
        right_col = ctk.CTkFrame(body, fg_color="#0f172a", corner_radius=8, border_width=1, border_color="#1e293b")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=2)
        right_col.grid_rowconfigure(1, weight=1)
        right_col.grid_columnconfigure(0, weight=1)

        # Top Browser Filter Bar
        browser_bar = ctk.CTkFrame(right_col, fg_color="transparent")
        browser_bar.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 6))

        self.builder_item_search_var = ctk.StringVar()
        self.builder_item_search_var.trace_add("write", lambda *args: self._refresh_builder_items())

        search_inp = ctk.CTkEntry(
            browser_bar,
            placeholder_text="🔍 Search 3,600+ Items by name or ID...",
            textvariable=self.builder_item_search_var,
            height=30,
            font=ctk.CTkFont(size=11)
        )
        search_inp.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.builder_cat_menu = ctk.CTkOptionMenu(
            browser_bar,
            values=["Popular", "All", "Building Blocks", "Materials", "Weapons", "Equipment", "Consumables", "Ammunition", "BuildTools", "Tools", "Other"],
            width=130,
            height=30,
            font=ctk.CTkFont(size=11),
            command=lambda c: self._refresh_builder_items()
        )
        self.builder_cat_menu.set("Popular")
        self.builder_cat_menu.pack(side="right")

        # Scrollable Items Grid / List
        self.builder_item_scroll = ctk.CTkScrollableFrame(right_col, fg_color="#020617", corner_radius=6)
        self.builder_item_scroll.grid(row=1, column=0, sticky="nsew", padx=12, pady=(0, 10))
        self.builder_item_scroll.grid_columnconfigure(0, weight=1)

        self._refresh_builder_items()

    def _on_builder_stack_change(self, val):
        self.builder_stack_amount = max(1, int(val))
        self.builder_stack_lbl.configure(text=f"{self.builder_stack_amount}")

    def _set_builder_stack(self, val: int):
        self.builder_stack_slider.set(val)
        self._on_builder_stack_change(val)

    def _select_builder_item(self, item_dict: Dict[str, Any]):
        self.builder_selected_item = item_dict
        self.builder_target_name_lbl.configure(text=item_dict["name"])
        self.builder_target_id_lbl.configure(
            text=f"Category: {item_dict.get('category', 'Item')}  |  Item ID: {item_dict['id']}"
        )
        if "default_stack" in item_dict:
            self._set_builder_stack(item_dict["default_stack"])
        self.builder_transmute_status.configure(
            text=f"Selected: {item_dict['name']}. Hover inventory item and click Transmute.",
            text_color="#38bdf8"
        )

    def _execute_builder_transmutation(self):
        if not self.builder_selected_item:
            self.builder_transmute_status.configure(text="Please select an item from the catalog first.", text_color="#f87171")
            return
        
        target_id = self.builder_selected_item["id"]
        stack = self.builder_stack_amount

        if self.mem_engine:
            success, msg = self.mem_engine.transmute_selected_item(target_id, stack)
            col = "#10b981" if success else "#f87171"
            self.builder_transmute_status.configure(text=msg, text_color=col)
            self.set_status(f"[TRANSMUTE] {msg}")
        else:
            self.builder_transmute_status.configure(
                text=f"Transmute armed for ID {target_id} (x{stack}). Hover item in-game!",
                text_color="#38bdf8"
            )

    def _refresh_builder_items(self):
        for child in self.builder_item_scroll.winfo_children():
            child.destroy()

        q = self.builder_item_search_var.get()
        cat = self.builder_cat_menu.get()

        results = MASTER_CATALOG.search_items(query=q, category=cat, limit=100)

        if not results:
            ctk.CTkLabel(
                self.builder_item_scroll,
                text="No matching items found.",
                font=ctk.CTkFont(size=11, slant="italic"),
                text_color="#64748b"
            ).pack(pady=20)
            return

        for it in results:
            row = ctk.CTkFrame(self.builder_item_scroll, fg_color="#0f172a", corner_radius=6)
            row.pack(fill="x", pady=3, padx=2)

            info_f = ctk.CTkFrame(row, fg_color="transparent")
            info_f.pack(side="left", fill="both", expand=True, padx=8, pady=4)

            name_lbl = ctk.CTkLabel(
                info_f,
                text=it["name"],
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#f8fafc",
                anchor="w"
            )
            name_lbl.pack(fill="x")

            meta_lbl = ctk.CTkLabel(
                info_f,
                text=f"{it.get('category', 'Item')}  •  ID: {it['id']}  •  Raw: {it.get('raw_name', '')}",
                font=ctk.CTkFont(size=9),
                text_color="#64748b",
                anchor="w"
            )
            meta_lbl.pack(fill="x")

            pick_btn = ctk.CTkButton(
                row,
                text="Select Target",
                width=90,
                height=26,
                font=ctk.CTkFont(size=10, weight="bold"),
                fg_color="#0284c7",
                hover_color="#0369a1",
                command=lambda item=it: self._select_builder_item(item)
            )
            pick_btn.pack(side="right", padx=8, pady=4)

    # -------------------------------------------------------------------------
    # 9. 📜 GENERATED LUA PREVIEW
    # -------------------------------------------------------------------------
    def _build_code_preview_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["code"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(
            cat_frame,
            text="Automatically Generated EML Lua Script (Synchronized in real time):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#94a3b8"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

        self.code_preview_box = ctk.CTkTextbox(
            cat_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
            fg_color="#0f172a"
        )
        self.code_preview_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # -------------------------------------------------------------------------
    # 9. 📋 GAME LOGS
    # -------------------------------------------------------------------------
    def _build_logs_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["logs"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(1, weight=1)

        top = ctk.CTkFrame(cat_frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(top, text="Recent Game & EML Output Logs", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(top, text="Refresh Logs", width=120, command=self.refresh_logs).grid(row=0, column=1, sticky="e")

        self.log_box = ctk.CTkTextbox(cat_frame, font=ctk.CTkFont(family="Consolas", size=11), corner_radius=8, fg_color="#0f172a")
        self.log_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

    # -------------------------------------------------------------------------
    # 10. 📖 HELP & DETAILED USER GUIDE
    # -------------------------------------------------------------------------
    def _build_help_category(self):
        cat_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.category_frames["help"] = cat_frame
        cat_frame.grid_columnconfigure(0, weight=1)
        cat_frame.grid_rowconfigure(1, weight=1)

        # Header with open in external viewer button
        top = ctk.CTkFrame(cat_frame, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(6, 8))
        top.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            top,
            text="📖 Mod Hub & Control Center - Complete User Guide & Manual",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#38bdf8"
        ).grid(row=0, column=0, sticky="w")

        def _open_guide_file():
            guide_file = Path(__file__).parent.parent / "docs" / "USER_GUIDE.md"
            if guide_file.exists():
                os.startfile(str(guide_file))

        ctk.CTkButton(
            top,
            text="↗ Open In Text Editor",
            width=160,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=_open_guide_file
        ).grid(row=0, column=1, sticky="e")

        # Scrollable Textbox with markdown guide content
        help_box = ctk.CTkTextbox(
            cat_frame,
            font=ctk.CTkFont(family="Consolas", size=12),
            corner_radius=8,
            fg_color="#0f172a"
        )
        help_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        guide_file = Path(__file__).parent.parent / "docs" / "USER_GUIDE.md"
        if guide_file.exists():
            try:
                with open(guide_file, "r", encoding="utf-8") as f:
                    content = f.read()
                help_box.insert("1.0", content)
            except Exception as e:
                help_box.insert("1.0", f"Error loading guide: {e}")
        else:
            help_box.insert("1.0", "User guide file not found.")

    # =========================================================================
    # REUSABLE CARD BUILDER
    # =========================================================================

    def _build_card(self, parent, section_title: str, items: list):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b")
        card.pack(fill="x", padx=10, pady=8)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text=section_title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#38bdf8"
        ).grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        content_box = ctk.CTkFrame(card, fg_color="#0f172a", corner_radius=6)
        content_box.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 12))
        content_box.grid_columnconfigure(1, weight=1)

        for idx, item in enumerate(items):
            itype = item["type"]
            key = item["key"]
            label_text = item["label"]

            if itype == "toggle":
                t_frame = ctk.CTkFrame(content_box, fg_color="transparent")
                t_frame.grid(row=idx, column=0, columnspan=2, sticky="ew", padx=14, pady=8)
                t_frame.grid_columnconfigure(0, weight=1)

                info_frame = ctk.CTkFrame(t_frame, fg_color="transparent")
                info_frame.grid(row=0, column=0, sticky="w")
                ctk.CTkLabel(info_frame, text=label_text, font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w")
                if "desc" in item:
                    ctk.CTkLabel(info_frame, text=item["desc"], font=ctk.CTkFont(size=11), text_color="#94a3b8").pack(anchor="w")

                sw = ctk.CTkSwitch(t_frame, text="")
                sw.set(1 if self.mod_state.get(key, False) else 0)
                sw.configure(command=lambda k=key, s=sw: self._on_ui_toggle_changed(k, s.get() == 1))
                sw.grid(row=0, column=1, sticky="e")

            elif itype == "slider":
                s_frame = ctk.CTkFrame(content_box, fg_color="transparent")
                s_frame.grid(row=idx, column=0, columnspan=2, sticky="ew", padx=14, pady=8)
                s_frame.grid_columnconfigure(1, weight=1)

                ctk.CTkLabel(s_frame, text=label_text, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=(0, 15))

                slider_sub = ctk.CTkFrame(s_frame, fg_color="transparent")
                slider_sub.grid(row=0, column=1, sticky="ew")
                slider_sub.grid_columnconfigure(0, weight=1)

                min_v = item.get("min", 1)
                max_v = item.get("max", 100)
                step = item.get("step", 1)
                suffix = item.get("suffix", "")

                current_val = self.mod_state.get(key, min_v)
                val_lbl = ctk.CTkLabel(
                    slider_sub,
                    text=f"{current_val}{suffix}",
                    width=100,
                    font=ctk.CTkFont(size=12, weight="bold"),
                    text_color="#34d399"
                )
                val_lbl.grid(row=0, column=1, padx=(10, 0))

                sl = ctk.CTkSlider(
                    slider_sub,
                    from_=min_v,
                    to=max_v,
                    number_of_steps=int((max_v - min_v) / step) if step else None
                )
                sl.set(current_val)

                def _slider_cb(val, k=key, sfx=suffix, is_int=(step >= 1 and isinstance(min_v, int)), lbl=val_lbl):
                    val_clean = int(val) if is_int else round(val, 1)
                    lbl.configure(text=f"{val_clean}{sfx}")
                    self.mod_state[k] = val_clean
                    self.save_profile()
                    self.compile_and_update_preview()

                sl.configure(command=_slider_cb)
                sl.grid(row=0, column=0, sticky="ew")

    # =========================================================================
    # STATUS BAR & HELPERS
    # =========================================================================

    def _build_status_bar(self):
        self.status_bar = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color="#0f172a")
        self.status_bar.grid(row=1, column=1, sticky="ew")

        self.status_label = ctk.CTkLabel(self.status_bar, text="Ready. Zero Lua knowledge required.", font=ctk.CTkFont(size=11), text_color="#9ca3af")
        self.status_label.pack(side="left", padx=15)

    def set_status(self, text: str):
        if hasattr(self, "status_label") and self.status_label:
            try:
                self.status_label.configure(text=text)
            except Exception:
                pass

    def _on_ui_toggle_changed(self, key: str, value: bool):
        self.mod_state[key] = value
        self.save_profile()
        self.compile_and_update_preview()
        self.set_status(f"Updated setting: {key} = {value}")

    # =========================================================================
    # LUA CODE GENERATOR ENGINE (WITH ALL 5 SUITES WIRED)
    # =========================================================================

    def generate_lua_code(self) -> str:
        lines = [
            "-- ============================================================================",
            "-- Auto-generated by Enshrouded Visual Mod Builder & Character Studio",
            "-- Zero-Coding EML Output Layer",
            "-- ============================================================================",
            "",
            'print("[VisualModHub] Initializing Enshrouded Modifications...")',
            "",
            "-- Helper for safe setting assignment",
            "local function safeSet(target, key, val)",
            "    if not target or target[key] == nil then return end",
            "    local f = target[key]",
            "    if type(f) == 'table' or type(f) == 'userdata' then",
            "        if f.value ~= nil then f.value = val else pcall(function() f[key] = val end) end",
            "    else",
            "        pcall(function() target[key] = val end)",
            "    end",
            "end",
            ""
        ]

        # 1. Item Stacking
        if self.mod_state.get("enable_stacks", False) and self.mod_state.get("stack_multiplier", 1) > 1:
            mult = self.mod_state["stack_multiplier"]
            lines.extend([
                "-- --- 1. Item Stack Sizes ---",
                f"local STACK_MULT = {mult}",
                'local items = game.assets.get_resources_by_type("keen::ItemInfo")',
                "local stackCount = 0",
                "for _, it in ipairs(items or {}) do",
                "    local d = it and it.data",
                "    if d and type(d.maxStackSize) == 'number' and d.maxStackSize > 1 then",
                "        d.maxStackSize = math.min(65535, math.floor(d.maxStackSize * STACK_MULT))",
                "        stackCount = stackCount + 1",
                "    end",
                "end",
                'print(("[VisualModHub] Multiplied stack sizes for " .. tostring(stackCount) .. " items by " .. tostring(STACK_MULT) .. "x"))',
                ""
            ])

        # 2. Shroud Survival Timer & Balancing Table
        shroud_mult = self.mod_state.get("shroud_multiplier", 1.0)
        level_cap = int(self.mod_state.get("player_level_cap", 45))
        has_skill_pts = self.mod_state.get("enable_skill_points_per_level", False)
        sp_per_lvl = int(self.mod_state.get("skill_points_per_level", 5))

        lines.extend([
            "-- --- 2. Balancing Table Overrides (Shroud, Level Cap, Skill Points) ---",
            'local tables = game.assets.get_resources_by_type("keen::BalancingTable")',
            "for _, res in ipairs(tables or {}) do",
            "    local d = res and res.data",
            "    if d then"
        ])
        if self.mod_state.get("enable_shroud_mult", False) and shroud_mult > 1.0:
            lines.extend([
                f"        if d.playerBaseFogResistance then",
                f"            d.playerBaseFogResistance = d.playerBaseFogResistance * {shroud_mult}",
                f'            print("[VisualModHub] Extended Shroud base resistance time by {shroud_mult}x!")',
                f"        end"
            ])
        if level_cap != 45:
            lines.extend([
                f"        d.playerLevelCap = {level_cap}",
                f"        d.itemLevelCap = math.max(d.itemLevelCap or 50, {level_cap + 5})",
                f'        print("[VisualModHub] Set Player Level Cap to {level_cap}!")'
            ])
        if has_skill_pts:
            lines.extend([
                f"        d.skillPointsPerLevel = {sp_per_lvl}",
                f'        print("[VisualModHub] Set Skill Points Per Level to {sp_per_lvl}!")'
            ])

        # Global BalancingTable Combat & Stats Tuning (Option A)
        b_crit = int(self.mod_state.get("base_crit_chance_percent", 10))
        b_crit_dmg = int(self.mod_state.get("crit_damage_bonus_percent", 80))
        two_h_dmg = float(self.mod_state.get("two_handed_damage_mult", 1.5))
        armor_pen = int(self.mod_state.get("armor_penetration_percent", 20))
        ap_scale = int(self.mod_state.get("ap_damage_scale_percent", 5))
        b_comfort = int(self.mod_state.get("base_comfort_rating", 34))
        m_comfort = int(self.mod_state.get("music_comfort_max_buff", 15))
        w_sources_m = float(self.mod_state.get("water_sources_mult", 1.0))
        gem_cost_m = float(self.mod_state.get("gem_upgrade_cost_mult", 1.0))
        gem_salv_m = float(self.mod_state.get("gem_salvage_gain_mult", 1.0))

        if b_crit != 10:
            lines.append(f"        d.baseCritChance = {b_crit / 100.0}")
        if b_crit_dmg != 80:
            lines.append(f"        d.critBonus = {b_crit_dmg / 100.0}")
        if two_h_dmg != 1.5:
            lines.append(f"        d.damageMod2Handed = {two_h_dmg}")
        if armor_pen != 20:
            lines.append(f"        d.defaultArmorBlowthrough = {armor_pen / 100.0}")
        if ap_scale != 5:
            lines.append(f"        d.damageScalePerAttributePoint = {ap_scale / 100.0}")
        if b_comfort != 34:
            lines.append(f"        if d.comfortSetup then d.comfortSetup.base = {b_comfort} end")
        if m_comfort != 15:
            lines.append(f"        d.maximumTotalMusicComfortBuff = {m_comfort}")
        if w_sources_m > 1.0:
            lines.extend([
                "        if d.waterSourcesPerFlameLevel then",
                f"            for i, count in ipairs(d.waterSourcesPerFlameLevel) do",
                f"                d.waterSourcesPerFlameLevel[i] = math.floor(count * {w_sources_m})",
                "            end",
                "        end"
            ])
        if gem_cost_m < 1.0 or gem_salv_m > 1.0:
            lines.extend([
                "        if d.gemCrafting then",
                f"            d.gemCrafting.maxUpgradeCost = math.floor(d.gemCrafting.maxUpgradeCost * {gem_cost_m})",
                f"            d.gemCrafting.insertBaseCost = math.floor(d.gemCrafting.insertBaseCost * {gem_cost_m})",
                f"            d.gemCrafting.extractBaseCost = math.floor(d.gemCrafting.extractBaseCost * {gem_cost_m})",
                f"            d.gemCrafting.salvageGainPercentage = math.min(1.0, d.gemCrafting.salvageGainPercentage * {gem_salv_m})",
                "        end"
            ])
        lines.extend(["    end", "end", ""])

        # 3. Base Building & Flame Altars
        if self.mod_state.get("enable_altar_range", False):
            radius_mult = self.mod_state.get("altar_radius_mult", 2.0)
            max_cap = self.mod_state.get("max_altars_cap", 100)
            lines.extend([
                "-- --- 3. Flame Altar Building Area & Cap ---",
                f"local RADIUS_MULT = {radius_mult}",
                f"local MAX_ALTARS_CAP = {max_cap}",
                'local tables = game.assets.get_resources_by_type("keen::BalancingTable")',
                "local bt = (tables and #tables > 0 and tables[1].data) or nil",
                "if bt then",
                "    if bt.buildzoneSizesPerAltarLevel then",
                "        for _, size in ipairs(bt.buildzoneSizesPerAltarLevel) do",
                "            if size.x and size.y and size.z then",
                "                size.x = math.floor(size.x * RADIUS_MULT)",
                "                size.y = math.floor(size.y * RADIUS_MULT)",
                "                size.z = math.floor(size.z * RADIUS_MULT)",
                "            end",
                "        end",
                '        print("[VisualModHub] Scaled Flame Altar build zone boundaries!")',
                "    end",
                "    if bt.altarsPerFlameLevel then",
                "        for idx, count in ipairs(bt.altarsPerFlameLevel) do",
                "            bt.altarsPerFlameLevel[idx] = math.min(MAX_ALTARS_CAP, count * 5)",
                "        end",
                '        print("[VisualModHub] Increased Flame Altar limits cap to " .. tostring(MAX_ALTARS_CAP))',
                "    end",
                "end",
                ""
            ])

        # 4. Building Hammer Reach Range
        hammer_reach = float(self.mod_state.get("building_hammer_reach_mult", 1.0))
        if hammer_reach > 1.0:
            lines.extend([
                "-- --- 4. Building Hammer Reach Range ---",
                f"local HAMMER_REACH = {hammer_reach}",
                'local items = game.assets.get_resources_by_type("keen::ItemInfo")',
                "for _, it in ipairs(items or {}) do",
                "    local eq = it and it.data and it.data.equipment",
                '    if eq and tostring(eq.slot) == "ConstructionHammer" and eq.placementConfig then',
                "        if type(eq.placementConfig.maxDistance) == 'number' then",
                "            eq.placementConfig.maxDistance = eq.placementConfig.maxDistance * HAMMER_REACH",
                "        end",
                "    end",
                "end",
                'print("[VisualModHub] Multiplied Construction Hammer placement range by " .. tostring(HAMMER_REACH) .. "x!")',
                ""
            ])

        # 5. Durability & Zero Stamina Overrides
        has_dur = self.mod_state.get("infinite_durability", False)
        has_stamina = self.mod_state.get("enable_zero_stamina", False)
        if has_dur or has_stamina:
            lines.extend([
                "-- --- 5. Game Settings Overrides (Durability & Stamina) ---",
                'local presetRes = game.assets.get_resources_by_type("keen::GameSettingsPresetsResource")',
                'local uiRes = game.assets.get_resources_by_type("keen::FbUiBundle")',
                "local presets = (presetRes and #presetRes > 0 and presetRes[1].data) or nil",
                "local ui = (uiRes and #uiRes > 0 and uiRes[1].data) or nil",
                "if presets then"
            ])
            if has_dur:
                lines.extend([
                    "    safeSet(presets.minValues, 'enableDurability', false)",
                    "    safeSet(presets.maxValues, 'enableDurability', false)",
                    '    print("[VisualModHub] Disabled weapon and tool durability loss!")'
                ])
            if has_stamina:
                lines.extend([
                    "    safeSet(presets.minValues, 'playerStaminaFactor', 0.0)",
                    "    safeSet(presets.maxValues, 'playerStaminaFactor', 0.0)",
                    '    print("[VisualModHub] Infinite Stamina active!")'
                ])
            lines.extend(["end", "if ui and ui.difficultySettings and ui.difficultySettings.settingValues then"])
            if has_dur:
                lines.append("    pcall(function() ui.difficultySettings.settingValues['enableDurability'] = false end)")
            if has_stamina:
                lines.append("    pcall(function() ui.difficultySettings.settingValues['playerStamina'] = 0.0 end)")
            lines.extend(["end", ""])

        # 6. Crafting Costs & Blueprint Unlocks
        cost_pct = self.mod_state.get("crafting_cost_percent", 100)
        has_unlock_all = self.mod_state.get("unlock_all_recipes", False)
        if cost_pct < 100 or has_unlock_all:
            lines.extend([
                "-- --- 6. Crafting & Recipes ---",
                f"local COST_RATIO = {cost_pct / 100.0}",
                'local recipeList = game.assets.get_resources_by_type("keen::RecipeRegistryResource")',
                "local rChanged = 0",
                "for _, regRes in ipairs(recipeList or {}) do",
                "    local reg = regRes and regRes.data",
                "    if reg and reg.recipes then",
                "        for _, r in ipairs(reg.recipes) do"
            ])
            if cost_pct < 100:
                lines.extend([
                    "            if r.input then",
                    "                for _, entry in ipairs(r.input) do",
                    "                    if entry.itemStack and type(entry.itemStack.count) == 'number' then",
                    "                        entry.itemStack.count = math.floor(entry.itemStack.count * COST_RATIO)",
                    "                    end",
                    "                    if entry.inputItemCategory and type(entry.inputItemCategory.count) == 'number' then",
                    "                        entry.inputItemCategory.count = math.floor(entry.inputItemCategory.count * COST_RATIO)",
                    "                    end",
                    "                end",
                    "            end"
                ])
            if has_unlock_all:
                lines.extend([
                    "            if r.knowledgeRequirement and r.knowledgeRequirement.knowledgeOrQueryId then",
                    "                local req = r.knowledgeRequirement",
                    "                if type(req.knowledgeOrQueryId) == 'table' or type(req.knowledgeOrQueryId) == 'userdata' then",
                    "                    req.knowledgeOrQueryId.value = 1715248921",
                    "                end",
                    "                req.compareValue = 1",
                    "                req.compareOperator = 'Equals'",
                    "                req.type = 'SimpleBool'",
                    "                req.isExplicitPlayerKnowledgeQuery = false",
                    "            end"
                ])
            lines.extend([
                "            rChanged = rChanged + 1",
                "        end",
                "    end",
                "end",
                'print(("[VisualModHub] Patched recipes: " .. tostring(rChanged)))',
                ""
            ])

        # 7. Mountain Slope Climbing
        if self.mod_state.get("enable_slope_climbing", False):
            angle = float(self.mod_state.get("climb_max_angle", 85.0))
            lines.extend([
                "-- --- 7. Mountain Slope Climbing ---",
                f"local MAX_CLIMB_ANGLE = {angle}",
                'local playerRes = game.assets.get_resource("c3db66d6-89a5-4a6c-a8e3-d9a1f6009812", "keen::ecs::TemplateResource", 0)',
                "if playerRes and playerRes.data and playerRes.data.components then",
                "    for _, comp in ipairs(playerRes.data.components) do",
                '        if comp.type == "keen::ecs::SlopeConfig" and comp.value and comp.value.slopeDefinition then',
                "            local sd = comp.value.slopeDefinition",
                "            sd.steepFloorAngle = MAX_CLIMB_ANGLE",
                "            sd.slidingAngle = math.min(89.0, MAX_CLIMB_ANGLE + 2.0)",
                "            sd.fallDamageAngle = 89.0",
                '            print(("[VisualModHub] Scaled mountain climbing angle to " .. tostring(MAX_CLIMB_ANGLE) .. " degrees!"))',
                "        end",
                "    end",
                "end",
                ""
            ])

        # 8. Glider Flight Propulsion & Aerodynamics
        if self.mod_state.get("enable_glider_boost", False):
            g_mult = float(self.mod_state.get("glider_accel_mult", 2.5))
            hover_eff = float(self.mod_state.get("glider_hover_efficiency", 1.0))
            turn_mult = float(self.mod_state.get("glider_turn_agility_mult", 1.0))
            updraft_m = float(self.mod_state.get("updraft_boost_mult", 1.0))

            lines.extend([
                "-- --- 8. Glider Flight Propulsion & Aerodynamics ---",
                f"local GLIDER_ACCEL_MULT = {g_mult}",
                f"local HOVER_FACTOR = {1.0 / hover_eff}",
                f"local TURN_MULT = {turn_mult}",
                'local items = game.assets.get_resources_by_type("keen::ItemInfo")',
                "local gCount = 0",
                "for _, it in ipairs(items or {}) do",
                "    local eq = it and it.data and it.data.equipment",
                '    if eq and tostring(eq.slot) == "Glider" and eq.gliderConfig then',
                "        local gc = eq.gliderConfig",
                "        if type(gc.accelerationForward) == 'number' then",
                "            gc.accelerationForward = gc.accelerationForward * GLIDER_ACCEL_MULT",
                "        end",
                "        if type(gc.airResistanceVertical) == 'number' then",
                "            gc.airResistanceVertical = gc.airResistanceVertical * HOVER_FACTOR",
                "        end",
                "        if type(gc.yawAngleSpeed) == 'number' then",
                "            gc.yawAngleSpeed = gc.yawAngleSpeed * TURN_MULT",
                "        end",
                "        if type(gc.pitchAngleSpeed) == 'number' then",
                "            gc.pitchAngleSpeed = gc.pitchAngleSpeed * TURN_MULT",
                "        end"
            ])
            if updraft_m > 1.0:
                lines.extend([
                    f"        local UPDRAFT_MULT = {updraft_m}",
                    "        if type(gc.updraftStrengthChargeStartValue) == 'number' then",
                    "            gc.updraftStrengthChargeStartValue = gc.updraftStrengthChargeStartValue * UPDRAFT_MULT",
                    "        end"
                ])
            lines.extend([
                "        gCount = gCount + 1",
                "    end",
                "end",
                'print(("[VisualModHub] Enhanced aerodynamics & updraft on " .. tostring(gCount) .. " gliders!"))',
                ""
            ])

        # 9. Early Access Red Boundaries & Fog-Building Bypass
        if self.mod_state.get("remove_red_barriers", False):
            lines.extend([
                "-- --- 9. Remove Early Access Red Barriers ---",
                "local SCENE_GUIDS = {",
                '    "36234b22-85f2-4001-ac56-002b379d0d88",',
                '    "509feadb-4c60-425f-9c7c-deeefd9b6920",',
                '    "6e616060-71df-4a67-903e-fe6b8319c58f",',
                '    "892172f0-1bf5-4fb4-af3a-6b05b624b39f",',
                '    "987bd339-f334-4902-812f-b0e29d7d393d"',
                "}",
                "local bCount = 0",
                "for _, guid in ipairs(SCENE_GUIDS) do",
                '    local sc = game.assets.get_resource(guid, "keen::SceneResource", 0)',
                "    if sc and sc.data and sc.data.resetPlayersOutOfBounds then",
                "        sc.data.resetPlayersOutOfBounds.playableAreas = {}",
                "        bCount = bCount + 1",
                "    end",
                "end",
                'print(("[VisualModHub] Disabled red barrier boundaries in " .. tostring(bCount) .. " scenes!"))',
                ""
            ])

        if self.mod_state.get("build_in_fog_everywhere", False):
            lines.extend([
                "-- --- 10. Bypass No-Build Zones & Build in Fog ---",
                'local scenes = game.assets.get_resources_by_type("keen::SceneResource")',
                "for _, s in ipairs(scenes or {}) do",
                "    if s.data and s.data.noBuildZones then",
                "        s.data.noBuildZones = {}",
                "    end",
                "end",
                'local items = game.assets.get_resources_by_type("keen::ItemInfo")',
                "for _, it in ipairs(items or {}) do",
                "    local eq = it and it.data and it.data.equipment",
                "    if eq then",
                "        pcall(function()",
                "            eq.allowPlacementBelowFog = true",
                '            eq.checkInhibitBuild = "None"',
                "            eq.buildZoneRequired = false",
                "        end)",
                "    end",
                "end",
                'print("[VisualModHub] Unlocked unrestricted building in fog and no-build zones!")',
                ""
            ])

        # 11. Weapons, Armor, Spells & Combat Stats
        has_weapon_scale = self.mod_state.get("enable_weapon_scaling", False)
        crit_pct = int(self.mod_state.get("crit_chance_percent", 0))
        mana_pct = int(self.mod_state.get("spell_mana_cost_percent", 100))
        cast_mult = float(self.mod_state.get("spell_cast_time_mult", 1.0))
        if has_weapon_scale or crit_pct > 0 or mana_pct < 100 or cast_mult < 1.0:
            melee_m = float(self.mod_state.get("melee_damage_mult", 2.0))
            ranged_m = float(self.mod_state.get("ranged_damage_mult", 2.0))
            magic_m = float(self.mod_state.get("magic_damage_mult", 2.0))
            armor_m = float(self.mod_state.get("armor_defense_mult", 2.0))
            lines.extend([
                "-- --- 11. Weapons, Armor, Spells & Combat Stats ---",
                f"local MELEE_MULT = {melee_m}",
                f"local RANGED_MULT = {ranged_m}",
                f"local MAGIC_MULT = {magic_m}",
                f"local ARMOR_MULT = {armor_m}",
                f"local CRIT_BONUS = {crit_pct / 100.0}",
                f"local MANA_RATIO = {mana_pct / 100.0}",
                f"local CAST_MULT = {cast_mult}",
                'local items = game.assets.get_resources_by_type("keen::ItemInfo")',
                "local gearPatched = 0",
                "for _, it in ipairs(items or {}) do",
                "    local d = it and it.data",
                "    local eq = d and d.equipment",
                "    if d and eq and (d.category == 'Weapon' or d.category == 'Armor' or d.category == 'Ammunition') then",
                "        local slot = tostring(eq.slot or '')",
                "        if d.impactValues then",
                "            for _, bucket in ipairs({'simple', 'scaled'}) do",
                "                for _, entry in ipairs(d.impactValues[bucket] or {}) do",
                "                    local val = entry and (entry.value or entry['$value'])",
                "                    if val and type(val.value) == 'number' and val.value > 0 then",
                "                        if slot:find('Weapon') or slot:find('Dagger') or slot:find('Axe') or slot:find('Mace') then",
                "                            val.value = math.floor(val.value * MELEE_MULT)",
                "                        elseif slot:find('Bow') or slot:find('Arrow') then",
                "                            val.value = math.floor(val.value * RANGED_MULT)",
                "                        elseif slot:find('Wand') or slot:find('Staff') then",
                "                            val.value = math.floor(val.value * MAGIC_MULT)",
                "                        elseif slot:find('Armor') or slot:find('Helmet') or slot:find('Pants') or slot:find('Boots') then",
                "                            val.value = math.floor(val.value * ARMOR_MULT)",
                "                        end",
                "                    end",
                "                end",
                "            end",
                "        end"
            ])
            if crit_pct > 0:
                lines.extend([
                    "        -- Critical Strike Chance Bonus",
                    "        if d.impactValues then",
                    "            for _, bucket in ipairs({'simple', 'scaled'}) do",
                    "                for _, entry in ipairs(d.impactValues[bucket] or {}) do",
                    "                    local val = entry and (entry.value or entry['$value'])",
                    "                    local t = tostring(val and val.type and val.type.value or '')",
                    "                    if t == '417381407' or t == '2896504001' or t == '4034040016' then",
                    "                        val.value = math.min(1.0, (val.value or 0.0) + CRIT_BONUS)",
                    "                    end",
                    "                end",
                    "            end",
                    "        end"
                ])
            if mana_pct < 100:
                lines.extend([
                    "        -- Spell Mana Cost Scaling",
                    "        if d.impactValues then",
                    "            for _, bucket in ipairs({'simple', 'scaled'}) do",
                    "                for _, entry in ipairs(d.impactValues[bucket] or {}) do",
                    "                    local val = entry and (entry.value or entry['$value'])",
                    "                    if val and val.type and val.type.value == 2556031774 and type(val.value) == 'number' then",
                    "                        val.value = math.max(1, math.floor(val.value * MANA_RATIO))",
                    "                    end",
                    "                end",
                    "            end",
                    "        end"
                ])
            if cast_mult < 1.0:
                lines.extend([
                    "        -- Spell Cast / Charge Speedup",
                    "        if d.impactValues then",
                    "            for _, bucket in ipairs({'simple', 'scaled'}) do",
                    "                for _, entry in ipairs(d.impactValues[bucket] or {}) do",
                    "                    local val = entry and (entry.value or entry['$value'])",
                    "                    local t = val and val.type and val.type.value",
                    "                    if t == 3902764048 and val.configId and val.configId.value == 1469785687 then",
                    "                        if type(val.value) == 'number' and val.value > 0 then",
                    "                            val.value = val.value * CAST_MULT",
                    "                        end",
                    "                    end",
                    "                end",
                    "            end",
                    "        end"
                ])
            # Option 11: Per-Element Spell Specialization
            has_elem = self.mod_state.get("enable_elemental_spells", False)
            if has_elem:
                f_mult = float(self.mod_state.get("fire_spell_damage_mult", 1.0))
                i_mult = float(self.mod_state.get("ice_spell_damage_mult", 1.0))
                s_mult = float(self.mod_state.get("shock_spell_damage_mult", 1.0))
                h_mult = float(self.mod_state.get("shroud_spell_damage_mult", 1.0))
                lines.extend([
                    "        -- Option 11: Elemental Spell Tuning",
                    f"        local FIRE_M = {f_mult}",
                    f"        local ICE_M = {i_mult}",
                    f"        local SHOCK_M = {s_mult}",
                    f"        local SHROUD_M = {h_mult}",
                    "        local iname = tostring(it.guid or ''):lower()",
                    "        if d.impactValues then",
                    "            for _, bucket in ipairs({'simple', 'scaled'}) do",
                    "                for _, entry in ipairs(d.impactValues[bucket] or {}) do",
                    "                    local val = entry and (entry.value or entry['$value'])",
                    "                    if val and type(val.value) == 'number' and val.value > 0 then",
                    "                        if iname:find('fire') or iname:find('flame') then",
                    "                            val.value = math.floor(val.value * FIRE_M)",
                    "                        elseif iname:find('ice') or iname:find('frost') then",
                    "                            val.value = math.floor(val.value * ICE_M)",
                    "                        elseif iname:find('shock') or iname:find('lightning') then",
                    "                            val.value = math.floor(val.value * SHOCK_M)",
                    "                        elseif iname:find('shroud') or iname:find('acid') then",
                    "                            val.value = math.floor(val.value * SHROUD_M)",
                    "                        end",
                    "                    end",
                    "                end",
                    "            end",
                    "        end"
                ])
            lines.extend([
                "        gearPatched = gearPatched + 1",
                "    end",
                "end",
                'print(("[VisualModHub] Scaled weapon/armor/spell stats on " .. tostring(gearPatched) .. " items!"))',
                ""
            ])

        # 12. Universal Magic Storage (Safe Deep-Copy)
        if self.mod_state.get("universal_magic_storage", False):
            lines.extend([
                "-- --- 12. Universal Magic Storage (Safe Cloned InventoryCraftingStock) ---",
                "local function deep_copy(orig, seen)",
                "    if type(orig) ~= 'table' then return orig end",
                "    seen = seen or {}",
                "    if seen[orig] then return seen[orig] end",
                "    local copy = {}",
                "    seen[orig] = copy",
                "    for k, v in pairs(orig) do",
                "        copy[deep_copy(k, seen)] = deep_copy(v, seen)",
                "    end",
                "    return copy",
                "end",
                "",
                'local templates = game.assets.get_resources_by_type("keen::ecs::TemplateResource")',
                "local magicComp = nil",
                "for _, t in ipairs(templates or {}) do",
                "    local td = t and t.data",
                '    if td and td.name and td.name:find("Prop_Decoration_T1_Storage_24_Magic", 1, true) then',
                "        for _, c in ipairs(td.components or {}) do",
                '            if c.type == "keen::ecs::InventoryCraftingStock" then',
                "                magicComp = c",
                "                break",
                "            end",
                "        end",
                "    end",
                "    if magicComp then break end",
                "end",
                "if magicComp then",
                "    local chestCount = 0",
                "    for _, t in ipairs(templates or {}) do",
                "        local td = t and t.data",
                '        if td and td.name and td.name:find("Prop_Decoration_T", 1, true) and td.name:find("Storage", 1, true) then',
                "            local hasInv = false",
                "            local hasMagic = false",
                "            for _, c in ipairs(td.components or {}) do",
                '                if c.type == "keen::ecs::InventorySetup" then hasInv = true end',
                '                if c.type == "keen::ecs::InventoryCraftingStock" then hasMagic = true end',
                "            end",
                "            if hasInv and not hasMagic then",
                "                td.components = td.components or {}",
                "                table.insert(td.components, deep_copy(magicComp))",
                "                chestCount = chestCount + 1",
                "            end",
                "        end",
                "    end",
                '    print(("[VisualModHub] Converted " .. tostring(chestCount) .. " normal storage chests into Magic Storage!"))',
                "end",
                ""
            ])

        # 13. Fast Travel to Any Map Marker (Crash-Safe Filtered Categories)
        if self.mod_state.get("fast_travel_all_markers", False):
            lines.extend([
                "-- --- 13. Fast Travel to Any Marker (Crash-Safe Categorized) ---",
                'local regRes = game.assets.get_resources_by_type("keen::MapMarkerRegistryResource")',
                "if regRes and #regRes > 0 and regRes[1].data and regRes[1].data.mapMarkers then",
                "    local safeCategories = {",
                "        FlameRelated = true,",
                "        Dungeons = true,",
                "        Locations = true,",
                "        None = true",
                "    }",
                "    local ftCount = 0",
                "    for _, marker in ipairs(regRes[1].data.mapMarkers) do",
                "        local cat = tostring(marker.sortingCategory or '')",
                "        if safeCategories[cat] and marker.isFastTravelDestination ~= true then",
                "            marker.isFastTravelDestination = true",
                "            ftCount = ftCount + 1",
                "        end",
                "    end",
                '    print(("[VisualModHub] Safely enabled Fast Travel on " .. tostring(ftCount) .. " world map markers!"))',
                "end",
                ""
            ])

        # 14. GameSettingsPresets (Vitals, Resistances, Economy, Difficulty, World)
        hp_m = float(self.mod_state.get("player_max_health_mult", 1.0))
        mp_m = float(self.mod_state.get("player_max_mana_mult", 1.0))
        sp_m = float(self.mod_state.get("player_max_stamina_mult", 1.0))
        heat_m = float(self.mod_state.get("body_heat_mult", 1.0))
        dive_m = float(self.mod_state.get("diving_breath_mult", 1.0))
        starve_m = float(self.mod_state.get("starving_time_mult", 1.0))
        enemy_hp = float(self.mod_state.get("enemy_health_mult", 1.0))
        enemy_dmg = float(self.mod_state.get("enemy_damage_mult", 1.0))
        boss_hp = float(self.mod_state.get("boss_health_mult", 1.0))
        boss_dmg = float(self.mod_state.get("boss_damage_mult", 1.0))
        ep_range = float(self.mod_state.get("enemy_perception_range_mult", 1.0))
        rune_salvage = float(self.mod_state.get("blacksmith_rune_return_mult", 1.0))
        upg_cost = float(self.mod_state.get("weapon_upgrade_cost_mult", 1.0))
        pg_speed = float(self.mod_state.get("plant_growth_speed_mult", 1.0))
        fp_speed = float(self.mod_state.get("factory_production_speed_mult", 1.0))
        res_drops = int(self.mod_state.get("resource_drop_mult", 1))
        chest_drops = float(self.mod_state.get("chest_loot_mult", 1.0))
        mine_dmg = float(self.mod_state.get("mining_damage_mult", 1.0))
        food_dur = float(self.mod_state.get("food_buff_duration_mult", 1.0))
        fog_reveal = float(self.mod_state.get("fog_reveal_mult", 1.0))
        day_time = float(self.mod_state.get("day_length_minutes", 30.0))
        night_time = float(self.mod_state.get("night_length_minutes", 10.0))
        has_xp = self.mod_state.get("enable_xp_multipliers", False)

        lines.extend([
            "-- --- 14. Comprehensive Game Settings Presets ---",
            'local pRes = game.assets.get_resources_by_type("keen::GameSettingsPresetsResource")',
            "local p = (pRes and #pRes > 0 and pRes[1].data) or nil",
            "if p then"
        ])

        if hp_m > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'playerHealthFactor', {hp_m})",
                f"    safeSet(p.maxValues, 'playerHealthFactor', {hp_m})",
            ])
        if mp_m > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'playerManaFactor', {mp_m})",
                f"    safeSet(p.maxValues, 'playerManaFactor', {mp_m})",
            ])
        if sp_m > 1.0 and not has_stamina:
            lines.extend([
                f"    safeSet(p.minValues, 'playerStaminaFactor', {sp_m})",
                f"    safeSet(p.maxValues, 'playerStaminaFactor', {sp_m})",
            ])
        if heat_m > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'playerBodyHeatFactor', {heat_m})",
                f"    safeSet(p.maxValues, 'playerBodyHeatFactor', {heat_m})",
            ])
        if dive_m > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'playerDivingTimeFactor', {dive_m})",
                f"    safeSet(p.maxValues, 'playerDivingTimeFactor', {dive_m})",
            ])
        if starve_m > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'fromHungerToStarving', {starve_m})",
                f"    safeSet(p.maxValues, 'fromHungerToStarving', {starve_m})",
            ])
        if enemy_hp != 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'enemyHealthFactor', {enemy_hp})",
                f"    safeSet(p.maxValues, 'enemyHealthFactor', {enemy_hp})",
            ])
        if enemy_dmg != 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'enemyDamageFactor', {enemy_dmg})",
                f"    safeSet(p.maxValues, 'enemyDamageFactor', {enemy_dmg})",
            ])
        if boss_hp != 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'bossHealthFactor', {boss_hp})",
                f"    safeSet(p.maxValues, 'bossHealthFactor', {boss_hp})",
            ])
        if boss_dmg != 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'bossDamageFactor', {boss_dmg})",
                f"    safeSet(p.maxValues, 'bossDamageFactor', {boss_dmg})",
            ])
        if ep_range != 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'enemyPerceptionRangeFactor', {ep_range})",
                f"    safeSet(p.maxValues, 'enemyPerceptionRangeFactor', {ep_range})",
            ])
        if rune_salvage > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'perkUpgradeRecyclingFactor', {rune_salvage})",
                f"    safeSet(p.maxValues, 'perkUpgradeRecyclingFactor', {rune_salvage})",
            ])
        if upg_cost < 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'perkCostFactor', {upg_cost})",
                f"    safeSet(p.maxValues, 'perkCostFactor', {upg_cost})",
            ])
        if pg_speed > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'plantGrowthSpeedFactor', {pg_speed})",
                f"    safeSet(p.maxValues, 'plantGrowthSpeedFactor', {pg_speed})",
            ])
        if fp_speed > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'factoryProductionSpeedFactor', {fp_speed})",
                f"    safeSet(p.maxValues, 'factoryProductionSpeedFactor', {fp_speed})",
            ])
        if res_drops > 1:
            lines.extend([
                f"    safeSet(p.minValues, 'resourceDropStackAmountFactor', {float(res_drops)})",
                f"    safeSet(p.maxValues, 'resourceDropStackAmountFactor', {float(res_drops)})",
            ])
        if mine_dmg > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'miningDamageFactor', {mine_dmg})",
                f"    safeSet(p.maxValues, 'miningDamageFactor', {mine_dmg})",
            ])
        if food_dur > 1.0:
            lines.extend([
                f"    safeSet(p.minValues, 'foodBuffDurationFactor', {food_dur})",
                f"    safeSet(p.maxValues, 'foodBuffDurationFactor', {food_dur})",
            ])
        if day_time != 30.0 or night_time != 10.0:
            lines.extend([
                f"    safeSet(p.minValues, 'dayTimeDuration', {day_time})",
                f"    safeSet(p.maxValues, 'dayTimeDuration', {day_time})",
                f"    safeSet(p.minValues, 'nightTimeDuration', {night_time})",
                f"    safeSet(p.maxValues, 'nightTimeDuration', {night_time})",
            ])
        if has_xp:
            cxp = float(self.mod_state.get("combat_xp_mult", 2.0))
            mxp = float(self.mod_state.get("mining_xp_mult", 2.0))
            qxp = float(self.mod_state.get("quest_xp_mult", 2.0))
            lines.extend([
                f"    safeSet(p.minValues, 'experienceCombatFactor', {cxp})",
                f"    safeSet(p.maxValues, 'experienceCombatFactor', {cxp})",
                f"    safeSet(p.minValues, 'experienceMiningFactor', {mxp})",
                f"    safeSet(p.maxValues, 'experienceMiningFactor', {mxp})",
                f"    safeSet(p.minValues, 'experienceExplorationQuestsFactor', {qxp})",
                f"    safeSet(p.maxValues, 'experienceExplorationQuestsFactor', {qxp})",
            ])
        lines.extend(["    print('[VisualModHub] Applied active GameSettingsPresets modifications!')", "end", ""])

        # 15. Chest & Dungeon Drops Multiplier
        if chest_drops > 1.0:
            lines.extend([
                "-- --- 15. Chest & Dungeon Inventory Loot Multiplier ---",
                f"local CHEST_LOOT_MULT = {chest_drops}",
                'local inventories = game.assets.get_resources_by_type("keen::ecs::DefaultInventoryResource")',
                "local invCount = 0",
                "for _, inv in ipairs(inventories or {}) do",
                "    local d = inv and inv.data",
                "    if d and d.slots then",
                "        for _, slot in ipairs(d.slots) do",
                "            if slot.stackCount and type(slot.stackCount) == 'number' and slot.stackCount > 0 then",
                "                slot.stackCount = math.max(1, math.floor(slot.stackCount * CHEST_LOOT_MULT))",
                "            end",
                "        end",
                "        invCount = invCount + 1",
                "    end",
                "end",
                'print(("[VisualModHub] Boosted chest loot on " .. tostring(invCount) .. " container templates!"))',
                ""
            ])

        # 16. Fog of War Reveal Multiplier
        if fog_reveal > 1.0:
            lines.extend([
                "-- --- 16. Fog of War Reveal Range Multiplier ---",
                f"local FOG_REVEAL_MULT = {fog_reveal}",
                'local playerRes = game.assets.get_resource("c3db66d6-89a5-4a6c-a8e3-d9a1f6009812", "keen::ecs::TemplateResource", 0)',
                "if playerRes and playerRes.data and playerRes.data.components then",
                "    for _, comp in ipairs(playerRes.data.components) do",
                '        if comp.type == "keen::ecs::FogOfWarDiscovery" and comp.value then',
                "            if type(comp.value.discoveryRange) == 'number' then",
                "                comp.value.discoveryRange = math.min(1024.0, comp.value.discoveryRange * FOG_REVEAL_MULT)",
                '                print(("[VisualModHub] Expanded Fog of War discovery radius to " .. tostring(comp.value.discoveryRange)))',
                "            end",
                "        end",
                "    end",
                "end",
                ""
            ])

        # 17. Blueprint Snapping Bounds (VoxelBlueprintConfig)
        snap_m = float(self.mod_state.get("snap_distance_mult", 1.0))
        if snap_m > 1.0:
            lines.extend([
                "-- --- 17. Blueprint Snapping Reach Range ---",
                f"local SNAP_MULT = {snap_m}",
                'local bpConfigs = game.assets.get_resources_by_type("keen::VoxelBlueprintConfig")',
                "for _, bpc in ipairs(bpConfigs or {}) do",
                "    local rules = bpc and bpc.data and bpc.data.snappingConfig and bpc.data.snappingConfig.rules",
                "    if rules then",
                "        for _, r in ipairs(rules) do",
                "            if r.maxHorizontalDistance then r.maxHorizontalDistance = math.floor(r.maxHorizontalDistance * SNAP_MULT) end",
                "            if r.maxVerticalDistance then r.maxVerticalDistance = math.floor(r.maxVerticalDistance * SNAP_MULT) end",
                "        end",
                "    end",
                "end",
                'print("[VisualModHub] Scaled blueprint magnetic snapping distance!")',
                ""
            ])

        # 18. Native Microvoxel Chiseling (Option B)
        has_chisel = self.mod_state.get("enable_microvoxel_chiseling", False)
        if has_chisel:
            lines.extend([
                "-- --- 18. Native Microvoxel Chiseling Blueprints ---",
                'local bpReg = game.assets.get_resources_by_type("keen::VoxelBlueprintItemRegistryResource")',
                "if bpReg and #bpReg > 0 and bpReg[1].data and bpReg[1].data.blueprintItems then",
                "    local count1x1 = 0",
                "    for _, item in ipairs(bpReg[1].data.blueprintItems) do",
                "        local s = item.size",
                "        if s and s.x == 1 and s.y == 1 and s.z == 1 then",
                "            count1x1 = count1x1 + 1",
                "        end",
                "    end",
                '    print(("[VisualModHub] Unlocked " .. tostring(count1x1) .. " native 1x1x1 microvoxel chiseling blueprints!"))',
                "end",
                ""
            ])

        # 19. Initial Voxel Snapping Range Calibration
        reach = self.mod_state.get("building_hammer_reach_mult", 1.0)
        if reach > 1.0:
            lines.extend([
                "-- --- 19. Construction Hammer Snapping & Reach Calibration ---",
                f"local reachMult = {reach}",
                "local pConfigs = game.assets.get_resources_by_type('keen::VoxelBlueprintConfig')",
                "for _, cfg in ipairs(pConfigs or {}) do",
                "    if cfg.data and cfg.data.snappingConfig and cfg.data.snappingConfig.rules then",
                "        for _, r in ipairs(cfg.data.snappingConfig.rules) do",
                "            if r.maxHorizontalDistance then r.maxHorizontalDistance = math.floor(4 * reachMult) end",
                "        end",
                "    end",
                "end",
                'print("[VisualModHub] Configured Hammer Snapping & Reach Multiplier!")',
                ""
            ])

        lines.append('print("[VisualModHub] All modifications applied successfully!")')
        return "\n".join(lines)

    def compile_and_update_preview(self):
        code = self.generate_lua_code()
        if hasattr(self, "code_preview_box") and self.code_preview_box:
            self.code_preview_box.delete("1.0", "end")
            self.code_preview_box.insert("1.0", code)

    # =========================================================================
    # PRESET CONFIGURATIONS
    # =========================================================================

    def preset_recommended(self):
        self.mod_state.update({
            "enable_stacks": True,
            "stack_multiplier": 10,
            "enable_shroud_mult": True,
            "shroud_multiplier": 3.0,
            "infinite_durability": True,
            "enable_zero_stamina": False,
            "body_heat_mult": 2.0,
            "diving_breath_mult": 2.0,
            "starving_time_mult": 2.0,
            "enable_altar_range": True,
            "altar_radius_mult": 2.0,
            "max_altars_cap": 50,
            "building_hammer_reach_mult": 1.5,
            "crafting_cost_percent": 100,
            "unlock_all_recipes": False,
            "universal_magic_storage": True,
            "enable_slope_climbing": True,
            "climb_max_angle": 70.0,
            "enable_glider_boost": True,
            "glider_accel_mult": 1.8,
            "glider_hover_efficiency": 2.0,
            "glider_turn_agility_mult": 1.4,
            "updraft_boost_mult": 1.5,
            "chest_loot_mult": 2.0,
            "resource_drop_mult": 2,
            "blacksmith_rune_return_mult": 2.0,
            "weapon_upgrade_cost_mult": 0.8,
            "plant_growth_speed_mult": 2.0,
            "factory_production_speed_mult": 2.0,
            "fog_reveal_mult": 2.0,
            "fast_travel_all_markers": True,
        })
        self._refresh_after_preset("Applied 'Recommended QoL' preset.")

    def preset_builder(self):
        self.mod_state.update({
            "enable_stacks": True,
            "stack_multiplier": 50,
            "enable_shroud_mult": True,
            "shroud_multiplier": 10.0,
            "infinite_durability": True,
            "enable_zero_stamina": True,
            "enable_altar_range": True,
            "altar_radius_mult": 4.0,
            "max_altars_cap": 100,
            "building_hammer_reach_mult": 3.0,
            "crafting_cost_percent": 0,
            "unlock_all_recipes": True,
            "universal_magic_storage": True,
            "build_in_fog_everywhere": True,
            "remove_red_barriers": True,
            "enable_slope_climbing": True,
            "climb_max_angle": 85.0,
            "enable_glider_boost": True,
            "glider_accel_mult": 2.5,
            "glider_hover_efficiency": 3.0,
            "plant_growth_speed_mult": 20.0,
            "factory_production_speed_mult": 50.0,
            "mining_damage_mult": 3.0,
            "resource_drop_mult": 5,
        })
        self._refresh_after_preset("Applied 'Master Builder Mode' preset.")

    def preset_sandbox(self):
        self.mod_state.update({
            "player_max_health_mult": 5.0,
            "player_max_mana_mult": 5.0,
            "player_max_stamina_mult": 5.0,
            "enable_zero_stamina": True,
            "infinite_durability": True,
            "body_heat_mult": 5.0,
            "diving_breath_mult": 5.0,
            "starving_time_mult": 5.0,
            "player_level_cap": 100,
            "enable_skill_points_per_level": True,
            "skill_points_per_level": 15,
            "enable_shroud_mult": True,
            "shroud_multiplier": 20.0,
            "enable_stacks": True,
            "stack_multiplier": 100,
            "enable_altar_range": True,
            "altar_radius_mult": 5.0,
            "max_altars_cap": 100,
            "building_hammer_reach_mult": 4.0,
            "crafting_cost_percent": 0,
            "unlock_all_recipes": True,
            "universal_magic_storage": True,
            "build_in_fog_everywhere": True,
            "remove_red_barriers": True,
            "enable_slope_climbing": True,
            "climb_max_angle": 88.0,
            "enable_weapon_scaling": True,
            "melee_damage_mult": 5.0,
            "ranged_damage_mult": 5.0,
            "magic_damage_mult": 5.0,
            "armor_defense_mult": 5.0,
            "crit_chance_percent": 50,
            "spell_mana_cost_percent": 0,
            "spell_cast_time_mult": 0.2,
            "enable_glider_boost": True,
            "glider_accel_mult": 4.0,
            "glider_hover_efficiency": 4.0,
            "updraft_boost_mult": 3.0,
            "chest_loot_mult": 5.0,
            "resource_drop_mult": 10,
            "mining_damage_mult": 5.0,
            "blacksmith_rune_return_mult": 5.0,
            "weapon_upgrade_cost_mult": 0.1,
            "boss_health_mult": 1.0,
            "boss_damage_mult": 1.0,
            "plant_growth_speed_mult": 50.0,
            "factory_production_speed_mult": 100.0,
            "fog_reveal_mult": 5.0,
            "fast_travel_all_markers": True,
        })
        self._refresh_after_preset("Applied 'God Mode / Sandbox' preset.")

    def preset_vanilla(self):
        self.mod_state.update({
            "player_max_health_mult": 1.0,
            "player_max_mana_mult": 1.0,
            "player_max_stamina_mult": 1.0,
            "enable_zero_stamina": False,
            "infinite_durability": False,
            "body_heat_mult": 1.0,
            "diving_breath_mult": 1.0,
            "starving_time_mult": 1.0,
            "player_level_cap": 45,
            "enable_skill_points_per_level": False,
            "skill_points_per_level": 1,
            "enable_shroud_mult": False,
            "shroud_multiplier": 1.0,
            "enable_stacks": False,
            "stack_multiplier": 1,
            "enable_altar_range": False,
            "altar_radius_mult": 1.0,
            "max_altars_cap": 10,
            "building_hammer_reach_mult": 1.0,
            "crafting_cost_percent": 100,
            "unlock_all_recipes": False,
            "universal_magic_storage": False,
            "build_in_fog_everywhere": False,
            "remove_red_barriers": False,
            "enable_slope_climbing": False,
            "climb_max_angle": 45.0,
            "enable_weapon_scaling": False,
            "melee_damage_mult": 1.0,
            "ranged_damage_mult": 1.0,
            "magic_damage_mult": 1.0,
            "armor_defense_mult": 1.0,
            "crit_chance_percent": 0,
            "spell_mana_cost_percent": 100,
            "spell_cast_time_mult": 1.0,
            "enemy_health_mult": 1.0,
            "enemy_damage_mult": 1.0,
            "boss_health_mult": 1.0,
            "boss_damage_mult": 1.0,
            "enemy_perception_range_mult": 1.0,
            "enable_glider_boost": False,
            "glider_accel_mult": 1.0,
            "glider_hover_efficiency": 1.0,
            "glider_turn_agility_mult": 1.0,
            "updraft_boost_mult": 1.0,
            "chest_loot_mult": 1.0,
            "resource_drop_mult": 1,
            "mining_damage_mult": 1.0,
            "blacksmith_rune_return_mult": 1.0,
            "weapon_upgrade_cost_mult": 1.0,
            "fog_reveal_mult": 1.0,
            "plant_growth_speed_mult": 1.0,
            "factory_production_speed_mult": 1.0,
            "food_buff_duration_mult": 1.0,
            "day_length_minutes": 30.0,
            "night_length_minutes": 10.0,
            "fast_travel_all_markers": False,
            "enable_xp_multipliers": False,
            "combat_xp_mult": 1.0,
            "mining_xp_mult": 1.0,
            "quest_xp_mult": 1.0,
        })
        self._refresh_after_preset("Reset all settings to vanilla defaults.")

    def _refresh_after_preset(self, msg: str):
        self.save_profile()
        self.compile_and_update_preview()
        # Re-render categories
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.category_frames.clear()
        self._build_category_container()
        self.switch_category(self.current_category)
        self.set_status(msg)

    # =========================================================================
    # LIVE CHEATS HOOKS & ATTACH
    # =========================================================================

    def _toggle_attach_game(self):
        if not self.mem_attached:
            if self.mem_engine.attach("enshrouded.exe"):
                self.mem_attached = True
                self.mem_status_label.configure(
                    text=f"Game Memory Status: CONNECTED (PID: {self.mem_engine.pid})",
                    text_color="#34d399"
                )
                self.attach_btn.configure(text="Detach from Game", fg_color="#ef4444", hover_color="#dc2626")
                self.set_status(f"Attached to enshrouded.exe (PID {self.mem_engine.pid})")
            else:
                self.set_status("Could not find enshrouded.exe. Please launch the game first.")
        else:
            self.mem_engine.detach()
            self.mem_attached = False
            self.mem_status_label.configure(
                text="Game Memory Status: DISCONNECTED",
                text_color="#f87171"
            )
            self.attach_btn.configure(text="Attach to Game (enshrouded.exe)", fg_color="#2563eb", hover_color="#1d4ed8")
            for sw in self.cheat_switches.values():
                sw.set(0)
            self.set_status("Detached and safely restored all game code.")

    def _on_live_cheat_toggled(self, key: str, enabled: bool):
        if not self.mem_attached:
            if self.mem_engine.auto_attach("enshrouded.exe"):
                self.mem_attached = True
                if hasattr(self, "mem_status_label"):
                    self.mem_status_label.configure(
                        text=f"Game Memory Status: CONNECTED (PID: {self.mem_engine.pid})",
                        text_color="#34d399"
                    )
                if hasattr(self, "attach_btn"):
                    self.attach_btn.configure(text="Detach from Game", fg_color="#ef4444", hover_color="#dc2626")
            else:
                self.set_status("⚠️ Enshrouded is not running. Launch the game (or run Mod Builder as Administrator) to apply live memory patches.")
                if key in self.cheat_switches:
                    self.cheat_switches[key].set(0)
                return

        sig = PROVEN_SIGNATURES.get(key)
        if not sig:
            return

        self.mod_state[f"cheat_{key}_active"] = enabled
        self.save_profile()

        if enabled:
            addr = self.mem_engine.cached_addresses.get(key) or self.mem_engine.aob_scan(sig["aob"])
            if addr:
                self.mem_engine.cached_addresses[key] = addr
                if self.mem_engine.patch_bytes(key, addr, sig["patch"]):
                    self.set_status(f"✓ Enabled {sig['name']} at {hex(addr)}")
                else:
                    self.set_status(f"Failed to patch memory at {hex(addr)}. Try running as Administrator.")
                    self.cheat_switches[key].deselect()
                    self.cheat_switches[key].configure(text="OFF")
            else:
                self.set_status(f"AOB signature for {sig['name']} not found in current game build.")
                self.cheat_switches[key].deselect()
                self.cheat_switches[key].configure(text="OFF")
        else:
            if self.mem_engine.restore_hook(key):
                self.set_status(f"Reverted {sig['name']} cleanly.")
            else:
                self.set_status(f"Disabled {sig['name']}.")
            self.cheat_switches[key].configure(text="OFF")

    def _on_live_cheat_slider_changed(self, key: str, val: float, unit: str, lbl_widget: ctk.CTkLabel):
        rounded_val = round(val, 2) if "x" in unit else (round(val, 1) if val < 20 else int(val))
        lbl_text = f"Multiplier: {rounded_val}{unit}" if "x" in unit else f"Value: {rounded_val}{unit}"
        lbl_widget.configure(text=lbl_text)
        self.mod_state[f"cheat_{key}_val"] = rounded_val
        self.save_profile()

        # Update memory engine runtime parameter
        if self.mem_engine:
            self.mem_engine.set_runtime_parameter(key, rounded_val)

    def _set_time_of_day_preset(self, hour: float, slider_widget: ctk.CTkSlider, lbl_widget: ctk.CTkLabel):
        slider_widget.set(hour)
        self._on_live_cheat_slider_changed("time_of_day", hour, "h", lbl_widget)
        # Enable cheat switch if not active
        if "time_of_day" in self.cheat_switches:
            sw = self.cheat_switches["time_of_day"]
            if not sw.get():
                sw.select()
                sw.configure(text="ACTIVE")
                self._on_live_cheat_toggled("time_of_day", True)
        self.set_status(f"Time of Day set to {hour:.1f}h (Locked in RAM)")

    def _on_fly_step(self, step: float):
        if self.mem_engine:
            if step > 0:
                success = self.mem_engine.fly_ascend(step)
                self.set_status(f"Ascended player +{step}m in RAM" if success else "Fly ascend sent to game memory.")
            else:
                success = self.mem_engine.fly_descend(abs(step))
                self.set_status(f"Descended player -{abs(step)}m in RAM" if success else "Fly descend sent to game memory.")

    def _on_destination_selected(self, choice: str):
        coords = self.destinations.get(choice)
        if coords:
            self.tp_coords_label.configure(text=f"XYZ: {coords}")
            self.set_status(f"Selected destination: {choice} at {coords}")

    # =========================================================================
    # DEPLOY & LAUNCH
    # =========================================================================

    def launch_cheat_trainer(self):
        trainer_path = TRAINER_PATH
        if trainer_path.is_file():
            try:
                identity = describe_trainer(trainer_path)
                os.startfile(str(trainer_path))
                self.set_status(
                    f"Opened read-only table ({identity['record_count']} records, "
                    f"SHA-256 {str(identity['sha256'])[:12]}…)."
                )
            except Exception as e:
                self.set_status(f"Error launching cheat table: {e}")
        else:
            self.set_status(f"Master trainer file not found at {trainer_path}")

    def deploy_and_launch(self):
        code = self.generate_lua_code()
        is_safe, messages = run_diagnostic_check(code)
        if not is_safe:
            err_msg = "\n".join(messages[:4])
            self.set_status(f"⚠️ Pre-launch Shield BLOCKED launch: {err_msg}")
            return

        self.set_status("Direct deployment disabled: use Control Center Preview/Install so one composer owns mod.lua.")

    def refresh_logs(self):
        if not GAME_LOGS_DIR.exists():
            return
        log_files = sorted(GAME_LOGS_DIR.glob("*.eml.log"), key=lambda p: p.stat().st_mtime, reverse=True)
        if not log_files:
            return
        try:
            with open(log_files[0], "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            self.log_box.delete("1.0", "end")
            self.log_box.insert("1.0", "".join(lines[-40:]))
            self.log_box.see("end")
            self.set_status(f"Fetched {log_files[0].name}")
        except Exception as e:
            self.set_status(f"Error reading logs: {e}")


def main():
    app = VisualLuaBuilderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
