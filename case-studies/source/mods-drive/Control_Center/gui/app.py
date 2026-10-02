"""
Enshrouded Mod Hub & Control Center GUI.
Pure EML / Lua / KFC Pregame Configuration Architecture.
Features:
1. Modular Pregame Table Tuning (28 Modules with Proportional Sliding Scales)
2. Custom Content & Asset Studio (12 Comprehensive Multi-Attribute Wizards)
3. Dynamic Recipe & Ingredient Matrix Engine
4. Live EML Lua Script Inspector & Compiler
5. One-Click Steam Launcher & Deployment
"""

import os
import sys
import json
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox

# Add parent directory to path to import manager & importer
sys.path.append(str(Path(__file__).parent.parent))
from core.manager import ModuleManager
from core.installer import InstallerService, InstallerError
from core.content_importer import ContentImporter, MATERIAL_PRESETS

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

RARITY_COLORS = {
    "Common": "#9ca3af",
    "Uncommon": "#22c55e",
    "Rare": "#3b82f6",
    "Epic": "#a855f7",
    "Legendary": "#f59e0b"
}


class EnshroudedHubApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Enshrouded Mod Hub & Control Center [EML / KFC Reflection]")
        self.geometry("1300x860")
        self.minsize(1150, 750)

        self.base_dir = Path(__file__).parent.parent
        self.manager = ModuleManager(self.base_dir)
        self.installer = InstallerService(self.base_dir, self.manager)
        self.importer = ContentImporter(self.base_dir)

        # Main Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_area()
        self._build_status_bar()

        # Start on Modules View
        self.show_modules_view()

    # =========================================================================
    # LAYOUT BUILDERS
    # =========================================================================

    def _build_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#0b0f19")
        self.sidebar_frame.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        # Title
        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame,
            text="⚡ ENSHROUDED\nMOD HUB",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#38bdf8",
            justify="center"
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 15))

        # Divider
        ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="#1e293b").grid(row=1, column=0, sticky="ew", padx=15, pady=(0, 15))

        # Nav Buttons
        self.mods_nav_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="⚙️ Gameplay Modules",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            fg_color="#2563eb",
            hover_color="#1d4ed8",
            height=38,
            command=self.show_modules_view
        )
        self.mods_nav_btn.grid(row=2, column=0, padx=15, pady=5, sticky="ew")

        self.studio_nav_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🎨 Custom Studios (12)",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            fg_color="transparent",
            border_width=1,
            border_color="#4b5563",
            hover_color="#1e293b",
            height=38,
            command=lambda: self.show_custom_studio_view("furniture")
        )
        self.studio_nav_btn.grid(row=3, column=0, padx=15, pady=5, sticky="ew")

        self.lua_nav_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="📜 EML Script Inspector",
            font=ctk.CTkFont(size=13, weight="bold"),
            anchor="w",
            fg_color="transparent",
            border_width=1,
            border_color="#4b5563",
            hover_color="#1e293b",
            height=38,
            command=self.show_lua_inspector_view
        )
        self.lua_nav_btn.grid(row=4, column=0, padx=15, pady=5, sticky="ew")

        # Action Buttons
        ctk.CTkFrame(self.sidebar_frame, height=2, fg_color="#1e293b").grid(row=5, column=0, sticky="ew", padx=15, pady=15)

        self.recompile_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="🔄 Recompile & Deploy",
            font=ctk.CTkFont(size=12),
            fg_color="#0284c7",
            hover_color="#0369a1",
            height=32,
            command=self.deploy_mods
        )
        self.recompile_btn.grid(row=6, column=0, padx=15, pady=6, sticky="ew")

        self.install_btn = ctk.CTkButton(self.sidebar_frame, text="Choose Game Folder", height=30, command=self.choose_game_folder)
        self.install_btn.grid(row=7, column=0, padx=15, pady=(12, 4), sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="Validate", height=30, command=self.validate_install).grid(row=8, column=0, padx=15, pady=3, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="Preview", height=30, command=self.preview_install).grid(row=9, column=0, padx=15, pady=3, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="Install / Repair", height=30, fg_color="#059669", command=self.install_mod).grid(row=10, column=0, padx=15, pady=3, sticky="ew")
        ctk.CTkButton(self.sidebar_frame, text="Uninstall (owned files)", height=30, fg_color="#7f1d1d", command=self.uninstall_mod).grid(row=11, column=0, padx=15, pady=3, sticky="ew")

        self.reset_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="♻️ Reset to Vanilla",
            font=ctk.CTkFont(size=12),
            fg_color="#475569",
            hover_color="#334155",
            height=32,
            command=self.reset_to_defaults
        )
        self.reset_btn.grid(row=7, column=0, padx=15, pady=6, sticky="ew")

        # Launch Game Button
        self.launch_btn = ctk.CTkButton(
            self.sidebar_frame,
            text="▶ LAUNCH GAME",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#10b981",
            hover_color="#059669",
            height=45,
            command=self.launch_game
        )
        self.launch_btn.grid(row=12, column=0, padx=15, pady=15, sticky="ew")

    def _game_path(self):
        path = self.installer.selected_game_path()
        if not path or not path.exists():
            messagebox.showinfo("Game folder", "Choose the Enshrouded installation folder first.")
            return None
        return path

    def choose_game_folder(self):
        path = filedialog.askdirectory(title="Choose Enshrouded game folder")
        if path:
            self.installer.save_game_path(Path(path))
            self.set_status(f"Game folder saved: {path}")

    def validate_install(self):
        path = self._game_path()
        if not path: return
        try:
            messages = self.installer.validate(path)
            self.set_status("Validation passed. Existing EML proxy files will be preserved." if not messages or all("preserved" in x.lower() for x in messages) else "; ".join(messages))
        except Exception as exc: messagebox.showerror("Validation failed", str(exc)); self.set_status("Validation failed")

    def preview_install(self):
        path = self._game_path()
        if not path: return
        try:
            plan = self.installer.preview(path)
            messagebox.showinfo("Deployment preview", "Owned files to install:\n" + "\n".join(plan.files) + "\n\n" + "\n".join(plan.warnings))
            self.set_status("Deployment preview ready; no game files changed.")
        except Exception as exc: messagebox.showerror("Preview failed", str(exc))

    def install_mod(self):
        path = self._game_path()
        if not path: return
        try:
            self.installer.install(path, self.set_status)
            self.set_status("Installed and verified. Restart Enshrouded to load the package.")
        except InstallerError as exc: messagebox.showerror("Install blocked", str(exc)); self.set_status("Install blocked")
        except Exception as exc: messagebox.showerror("Install failed", str(exc)); self.set_status("Install failed; backup retained for recovery")

    def uninstall_mod(self):
        path = self._game_path()
        if not path or not messagebox.askyesno("Uninstall", "Remove only files recorded in the Mod Hub ownership manifest?"): return
        try:
            self.installer.uninstall(path); self.set_status("Owned Mod Hub files removed. Restart required.")
        except Exception as exc: messagebox.showerror("Uninstall failed", str(exc))

    def _build_main_area(self):
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#0f172a")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=0, pady=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        # Header bar
        self.header_frame = ctk.CTkFrame(self.main_frame, height=60, corner_radius=0, fg_color="#1e293b")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        self.header_frame.grid_columnconfigure(1, weight=1)

        self.header_title = ctk.CTkLabel(
            self.header_frame,
            text="Modules & Configuration",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#f8fafc"
        )
        self.header_title.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Search bar
        self.search_entry = ctk.CTkEntry(
            self.header_frame,
            placeholder_text="🔍 Search settings, modules, parameters...",
            width=280,
            height=32
        )
        self.search_entry.grid(row=0, column=1, padx=(10, 5), pady=12, sticky="e")
        self.search_entry.bind("<KeyRelease>", self._on_search_changed)

        self.clear_search_btn = ctk.CTkButton(
            self.header_frame,
            text="✕",
            width=28,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self._clear_search
        )
        self.clear_search_btn.grid(row=0, column=2, padx=(0, 20), pady=12, sticky="e")

        # Content container
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=15)
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

    def _build_status_bar(self):
        self.status_frame = ctk.CTkFrame(self, height=28, corner_radius=0, fg_color="#111827")
        self.status_frame.grid(row=1, column=1, sticky="ew")
        self.status_frame.grid_columnconfigure(0, weight=1)

        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Ready. All 28 modules and 12 studios compile directly to mod.lua.",
            font=ctk.CTkFont(size=11),
            text_color="#9ca3af",
            anchor="w"
        )
        self.status_label.grid(row=0, column=0, padx=15, pady=4, sticky="w")

    def set_status(self, text: str):
        self.status_label.configure(text=text)

    def _clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _update_nav_highlight(self, active_btn):
        for btn in [self.mods_nav_btn, self.studio_nav_btn, self.lua_nav_btn]:
            if btn == active_btn:
                btn.configure(fg_color="#2563eb", border_width=0)
            else:
                btn.configure(fg_color="transparent", border_width=1, border_color="#4b5563")

    def _on_search_changed(self, event=None):
        query = self.search_entry.get().strip().lower()
        self.show_modules_view(search_query=query)

    def _clear_search(self):
        self.search_entry.delete(0, "end")
        self.show_modules_view()

    # =========================================================================
    # VIEW 1: MODULES & SLIDERS
    # =========================================================================

    def show_modules_view(self, search_query: str = ""):
        self._update_nav_highlight(self.mods_nav_btn)
        self.header_title.configure(text="Pregame Gameplay & Balance Modules")
        self._clear_content()

        scroll = ctk.CTkScrollableFrame(self.content_frame, fg_color="transparent")
        scroll.grid(row=0, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        modules = self.manager.modules
        active_cfg = self.manager.active_config

        filtered_count = 0
        for mod_id, mod in modules.items():
            name = mod.get("name", mod_id)
            desc = mod.get("description", "")
            category = mod.get("category", "General")
            settings = mod.get("settings", [])

            # Filter logic
            if search_query:
                text_blob = f"{name} {desc} {category} " + " ".join(s.get("label", "") for s in settings)
                if search_query not in text_blob.lower():
                    continue

            filtered_count += 1
            is_enabled = active_cfg.get("enabled_modules", {}).get(mod_id, True)

            # Module Card
            card = ctk.CTkFrame(scroll, corner_radius=8, fg_color="#1e293b", border_width=1, border_color="#334155")
            card.pack(fill="x", padx=10, pady=8)
            card.grid_columnconfigure(0, weight=1)

            # Card Header
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.grid(row=0, column=0, sticky="ew", padx=15, pady=(12, 6))
            header.grid_columnconfigure(0, weight=1)

            title_txt = f"{name}  v{mod.get('version', '1.0')}"
            title_lbl = ctk.CTkLabel(header, text=title_txt, font=ctk.CTkFont(size=15, weight="bold"), text_color="#f8fafc")
            title_lbl.grid(row=0, column=0, sticky="w")

            cat_badge = ctk.CTkLabel(header, text=f"[{category}]", font=ctk.CTkFont(size=12), text_color="#38bdf8")
            cat_badge.grid(row=0, column=1, sticky="w", padx=(10, 0))

            toggle = ctk.CTkSwitch(
                header,
                text="Active",
                command=lambda m=mod_id, sw=None: self._on_module_toggled(m, sw),
                width=50
            )
            toggle.select() if is_enabled else toggle.deselect()
            toggle.configure(command=lambda m=mod_id, t=toggle: self._on_module_toggled(m, t.get() == 1))
            toggle.grid(row=0, column=2, sticky="e", padx=(10, 0))

            # Description
            if desc:
                desc_lbl = ctk.CTkLabel(card, text=desc, font=ctk.CTkFont(size=12), text_color="#94a3b8", wraplength=800, justify="left")
                desc_lbl.grid(row=1, column=0, sticky="w", padx=15, pady=(0, 10))

            # Settings
            if settings:
                set_container = ctk.CTkFrame(card, corner_radius=6, fg_color="#0f172a")
                set_container.grid(row=2, column=0, sticky="ew", padx=15, pady=(0, 12))
                set_container.grid_columnconfigure(1, weight=1)

                for idx, s in enumerate(settings):
                    k = s["key"]
                    lbl_txt = s.get("label", k)
                    stype = s.get("type", "toggle")
                    val = active_cfg.get("module_settings", {}).get(mod_id, {}).get(k, s.get("default"))

                    s_lbl = ctk.CTkLabel(set_container, text=lbl_txt, font=ctk.CTkFont(size=12), text_color="#cbd5e1")
                    s_lbl.grid(row=idx, column=0, padx=12, pady=6, sticky="w")

                    if stype == "toggle":
                        sw = ctk.CTkSwitch(set_container, text="", width=40)
                        sw.select() if val else sw.deselect()
                        sw.configure(command=lambda m=mod_id, key=k, s_w=sw, d=s.get("dynamic", False): self._on_setting_changed(m, key, s_w.get() == 1, d))
                        sw.grid(row=idx, column=1, padx=12, pady=6, sticky="e")
                    elif stype == "slider":
                        min_v = s.get("min", 0.0)
                        max_v = s.get("max", 10.0)
                        step_v = s.get("step", 0.1)

                        val_frame = ctk.CTkFrame(set_container, fg_color="transparent")
                        val_frame.grid(row=idx, column=1, padx=12, pady=6, sticky="ew")
                        val_frame.grid_columnconfigure(0, weight=1)

                        val_display = ctk.CTkLabel(val_frame, text=f"{val:.2f}" if isinstance(val, float) else str(val), width=45, font=ctk.CTkFont(size=12, weight="bold"), text_color="#38bdf8")
                        val_display.grid(row=0, column=1, padx=(8, 0), sticky="e")

                        slider = ctk.CTkSlider(
                            val_frame,
                            from_=min_v,
                            to=max_v,
                            number_of_steps=int((max_v - min_v) / step_v) if step_v > 0 else 100
                        )
                        slider.set(val)
                        slider.configure(command=lambda new_v, m=mod_id, key=k, lbl=val_display, st=step_v, d=s.get("dynamic", False): self._on_slider_changed(m, key, new_v, lbl, st, d))
                        slider.grid(row=0, column=0, sticky="ew")

        if filtered_count == 0:
            ctk.CTkLabel(scroll, text="No matching modules found.", font=ctk.CTkFont(size=14), text_color="#94a3b8").pack(pady=40)

    def _on_slider_changed(self, mod_id: str, key: str, value: float, display_lbl, step: float, is_dynamic: bool):
        if step >= 1.0:
            rounded = int(round(value))
            display_lbl.configure(text=str(rounded))
            self._on_setting_changed(mod_id, key, rounded, is_dynamic)
        else:
            rounded = round(value, 2)
            display_lbl.configure(text=f"{rounded:.2f}")
            self._on_setting_changed(mod_id, key, rounded, is_dynamic)

    # =========================================================================
    # VIEW 2: 12 CUSTOM CONTENT STUDIOS
    # =========================================================================

    def show_custom_studio_view(self, active_tab: str = "furniture"):
        self._update_nav_highlight(self.studio_nav_btn)
        self.header_title.configure(text="Custom Content & Asset Studio (12 Modules)")
        self._clear_content()

        container = ctk.CTkFrame(self.content_frame, corner_radius=8, fg_color="transparent")
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        # Studio Category Bar
        nav_bar = ctk.CTkFrame(container, height=48, corner_radius=8, fg_color="#1e293b")
        nav_bar.grid(row=0, column=0, sticky="ew", padx=10, pady=(0, 10))
        nav_bar.grid_columnconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(container, fg_color="transparent")
        scroll.grid(row=1, column=0, sticky="nsew")
        scroll.grid_columnconfigure(0, weight=1)

        studios_map = {
            "🪑 Furniture & Props": "furniture",
            "🖼️ Art & Paintings": "art",
            "💇 Hair & Beards": "hair",
            "🧪 Potions & Alchemy": "potions",
            "⚡ Spells & Magic": "spells",
            "🧱 Building Blocks": "blocks",
            "🎨 Color Palettes & Dyes": "colors",
            "🪂 Gliders & Hooks": "gliders",
            "⚔️ Weapons & Armor": "weapons",
            "🐾 Pets & Companions": "pets",
            "🌾 Farming & Botany": "farming",
            "🎼 Campfire Music & MIDI": "music"
        }

        inv_map = {v: k for k, v in studios_map.items()}
        current_display = inv_map.get(active_tab, "🪑 Furniture & Props")

        drop_frame = ctk.CTkFrame(nav_bar, fg_color="transparent")
        drop_frame.grid(row=0, column=0, sticky="w", padx=14, pady=10)

        ctk.CTkLabel(drop_frame, text="Active Studio:", font=ctk.CTkFont(size=13, weight="bold"), text_color="#94a3b8").pack(side="left", padx=(0, 10))
        studio_menu = ctk.CTkOptionMenu(
            drop_frame,
            values=list(studios_map.keys()),
            command=lambda choice: self.show_custom_studio_view(studios_map[choice]),
            width=260
        )
        studio_menu.set(current_display)
        studio_menu.pack(side="left")

        # Action creation button mapping
        create_handlers = {
            "furniture": ("➕ Create Furniture", self._open_furniture_wizard),
            "art": ("➕ Create Art / Tapestry", self._open_art_wizard),
            "hair": ("➕ Create Hairstyle / Beard", self._open_hair_wizard),
            "potions": ("➕ Brew Potion / Elixir", self._open_potion_wizard),
            "spells": ("➕ Inscribe Spell", self._open_spell_wizard),
            "blocks": ("➕ Forge Material Block", self._open_block_wizard),
            "colors": ("➕ Create Color Preset", self._open_color_wizard),
            "gliders": ("➕ Craft Traversal Gear", self._open_glider_wizard),
            "weapons": ("➕ Forge Weapon / Armor", self._open_weapon_wizard),
            "pets": ("➕ Craft Companion Whistle", self._open_pet_wizard),
            "farming": ("➕ Cultivate Crop Seed", self._open_farming_wizard),
            "music": ("➕ Compose Campfire Song", self._open_music_wizard)
        }

        btn_txt, btn_cmd = create_handlers.get(active_tab, ("➕ Create Item", None))
        ctk.CTkButton(nav_bar, text=btn_txt, fg_color="#10b981", hover_color="#059669", font=ctk.CTkFont(weight="bold"), command=btn_cmd).grid(row=0, column=1, sticky="e", padx=14, pady=10)

        # Render corresponding subtab items
        items_dict = {
            "furniture": (self.importer.furniture_items, self._render_furniture_card),
            "art": (self.importer.art_items, self._render_art_card),
            "hair": (self.importer.hair_items, self._render_hair_card),
            "potions": (self.importer.potion_items, self._render_potion_card),
            "spells": (self.importer.spell_items, self._render_spell_card),
            "blocks": (self.importer.building_block_items, self._render_block_card),
            "colors": (self.importer.color_items, self._render_color_card),
            "gliders": (self.importer.glider_items, self._render_glider_card),
            "weapons": (self.importer.weapon_items, self._render_weapon_card),
            "pets": (self.importer.pet_items, self._render_pet_card),
            "farming": (self.importer.farming_items, self._render_farming_card),
            "music": (self.importer.music_items, self._render_music_card)
        }

        item_list, renderer = items_dict.get(active_tab, ([], None))
        if item_list and renderer:
            for itm in item_list:
                renderer(scroll, itm)
        else:
            ctk.CTkLabel(scroll, text="No custom items in this studio yet. Click the button above to create one!", font=ctk.CTkFont(size=13), text_color="#94a3b8").pack(pady=40)

    # ------------------ Card Renderers ------------------

    def _render_furniture_card(self, parent, item: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(item.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=item["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(item.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda iid=item["id"]: self._delete_item("furniture", iid)).grid(row=0, column=1, sticky="e")
        badge = f"[{item.get('rarity', 'Common')} Lv.{item.get('level', 1)}] • Category: {item.get('category', 'Furniture')} • Comfort: +{item.get('comfort_score', 10)} • Station: {item.get('crafting_station', 'Carpenter')}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#38bdf8").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in item.get("ingredients", [])) if item.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{item.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_art_card(self, parent, art: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(art.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=art["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(art.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda aid=art["id"]: self._delete_item("art", aid)).grid(row=0, column=1, sticky="e")
        badge = f"[{art.get('rarity', 'Rare')} Lv.{art.get('level', 15)}] • Frame: {art.get('frame_style', 'Wood')} • Size: {art.get('dimensions', '2x2')} • Comfort: +{art.get('comfort_score', 8)}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#fbbf24").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in art.get("ingredients", [])) if art.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{art.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_hair_card(self, parent, hair: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color="#f472b6")
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=hair["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color="#f472b6").grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda hid=hair["id"]: self._delete_item("hair", hid)).grid(row=0, column=1, sticky="e")
        badge = f"[{hair.get('type', 'Hair')}] • Gender: {hair.get('gender', 'Male')} • Color Preset: {hair.get('color_preset', 'Default')}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#f472b6").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ctk.CTkLabel(card, text=hair.get("description", ""), wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_potion_card(self, parent, pot: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(pot.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=pot["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(pot.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda pid=pot["id"]: self._delete_item("potions", pid)).grid(row=0, column=1, sticky="e")
        badge = f"[{pot.get('rarity', 'Epic')} {pot.get('category', 'Potion')} Lv.{pot.get('level', 15)}] • Duration: {int(pot.get('duration_seconds', 1200)/60)}m • Shroud Immunity: +{pot.get('shroud_time_bonus', 0)}s • Dmg: {pot.get('damage_multiplier', 1.0)}x"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#a855f7").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in pot.get("ingredients", [])) if pot.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{pot.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_spell_card(self, parent, sp: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(sp.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=sp["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(sp.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda sid=sp["id"]: self._delete_item("spells", sid)).grid(row=0, column=1, sticky="e")
        badge = f"[{sp.get('rarity', 'Legendary')} Lv.{sp.get('level', 25)}] • Element: {sp.get('magic_element', 'Fire')} • Dmg: {sp.get('base_damage', 300)} • Mana: {sp.get('mana_cost', 50)} • Radius: {sp.get('explosion_radius', 8.0)}m • Charges: {sp.get('charges', 100)}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#ec4899").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in sp.get("ingredients", [])) if sp.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{sp.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_block_card(self, parent, blk: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(blk.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=blk["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(blk.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda bid=blk["id"]: self._delete_item("blocks", bid)).grid(row=0, column=1, sticky="e")
        badge = f"[{blk.get('category', 'Stone')}] • Hardness: {blk.get('hardness_rating', 5.0)}/10 • Glow: {blk.get('emissive_glow', 'None')} • Yield: {blk.get('craft_yield', 100)}x"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#10b981").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in blk.get("ingredients", [])) if blk.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{blk.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_color_card(self, parent, col: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=col.get("hex_color", "#38bdf8"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=col["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=col.get("hex_color", "#38bdf8")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda cid=col["id"]: self._delete_item("colors", cid)).grid(row=0, column=1, sticky="e")
        badge = f"[{col.get('type', 'Color')}] • Hex: {col.get('hex_color', '#ffffff')} • Metallic Sheen: {col.get('metallic_sheen', 0.5)} • Glow: {col.get('glow_intensity', 1.0)}x"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#38bdf8").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ctk.CTkLabel(card, text=col.get("description", ""), wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_glider_card(self, parent, g: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(g.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=g["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(g.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda gid=g["id"]: self._delete_item("gliders", gid)).grid(row=0, column=1, sticky="e")
        badge = f"[{g.get('rarity', 'Legendary')} {g.get('type', 'Glider')} Lv.{g.get('level', 25)}] • Glide Ratio: {g.get('glide_ratio', 4.0)} • Speed: {g.get('speed_multiplier', 1.5)}x • Stamina: {g.get('stamina_drain_per_sec', 0.0)}/s"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#06b6d4").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in g.get("ingredients", [])) if g.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{g.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_weapon_card(self, parent, w: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(w.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=w["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(w.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda wid=w["id"]: self._delete_item("weapons", wid)).grid(row=0, column=1, sticky="e")
        badge = f"[{w.get('rarity', 'Legendary')} {w.get('type', 'Weapon')} Lv.{w.get('level', 25)}] • Damage/Armor: {w.get('damage', 200)} • Crit Rate: {int(w.get('crit_rate', 0.25)*100)}% • Station: {w.get('crafting_station', 'Blacksmith')}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#f59e0b").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in w.get("ingredients", [])) if w.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{w.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_pet_card(self, parent, p: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(p.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=p["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(p.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda pid=p["id"]: self._delete_item("pets", pid)).grid(row=0, column=1, sticky="e")
        badge = f"[{p.get('species', 'Wolf')} • {p.get('combat_role', 'Defender')}] • HP: {p.get('health', 1000)} • ATK: {p.get('attack_power', 150)} • Slots: {p.get('carry_slots', 16)}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#14b8a6").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in p.get("ingredients", [])) if p.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{p.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_farming_card(self, parent, c: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(c.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=c["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(c.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda cid=c["id"]: self._delete_item("farming", cid)).grid(row=0, column=1, sticky="e")
        badge = f"[{c.get('crop_type', 'Herb')}] • Growth: {c.get('growth_time_seconds', 120)}s • Harvest Yield: {c.get('harvest_yield', 5)}x • Station: {c.get('crafting_station', 'Farmer')}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#a3e635").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in c.get("ingredients", [])) if c.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{c.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    def _render_music_card(self, parent, m: dict):
        card = ctk.CTkFrame(parent, corner_radius=10, fg_color="#1e293b", border_width=1, border_color=RARITY_COLORS.get(m.get("rarity", "Common"), "#334155"))
        card.pack(fill="x", padx=10, pady=6)
        card.grid_columnconfigure(0, weight=1)
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))
        header.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(header, text=m["name"], font=ctk.CTkFont(size=15, weight="bold"), text_color=RARITY_COLORS.get(m.get("rarity", "Common"), "#f8fafc")).grid(row=0, column=0, sticky="w")
        ctk.CTkButton(header, text="Delete", width=70, height=26, fg_color="#ef4444", hover_color="#dc2626", command=lambda mid=m["id"]: self._delete_item("music", mid)).grid(row=0, column=1, sticky="e")
        badge = f"[{m.get('instrument', 'Lute')}] • Tempo: {m.get('tempo_bpm', 110)} BPM • Campfire Aura: {m.get('buff_effect', 'Regen')}"
        ctk.CTkLabel(card, text=badge, font=ctk.CTkFont(size=11), text_color="#c084fc").grid(row=1, column=0, sticky="w", padx=16, pady=(0, 4))
        ings_str = "Ingredients: " + ", ".join(f"{ing.get('amount', 1)}x {ing.get('name')}" for ing in m.get("ingredients", [])) if m.get("ingredients") else "Ingredients: Default"
        ctk.CTkLabel(card, text=f"{m.get('description', '')}\n{ings_str}", wraplength=700, justify="left", text_color="#cbd5e1", font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))

    # ------------------ Deletion Handler ------------------

    def _delete_item(self, tab: str, item_id: str):
        if tab == "furniture": self.importer.remove_furniture_item(item_id)
        elif tab == "art": self.importer.remove_art_item(item_id)
        elif tab == "hair": self.importer.remove_hair_item(item_id)
        elif tab == "potions": self.importer.remove_potion_item(item_id)
        elif tab == "spells": self.importer.remove_spell_item(item_id)
        elif tab == "blocks": self.importer.remove_building_block_item(item_id)
        elif tab == "colors": self.importer.remove_color_item(item_id)
        elif tab == "gliders": self.importer.remove_glider_item(item_id)
        elif tab == "weapons": self.importer.remove_weapon_item(item_id)
        elif tab == "pets": self.importer.remove_pet_item(item_id)
        elif tab == "farming": self.importer.remove_farming_item(item_id)
        elif tab == "music": self.importer.remove_music_item(item_id)

        self.manager.discover_modules()
        self.manager.compile_master_lua()
        self.show_custom_studio_view(tab)
        self.set_status(f"Removed custom item '{item_id}' from {tab} studio.")

    # =========================================================================
    # REUSABLE MODAL INGREDIENTS BUILDER
    # =========================================================================

    def _create_base_wizard_dialog(self, title: str, w=620, h=720):
        dialog = ctk.CTkToplevel(self)
        dialog.title(title)
        dialog.geometry(f"{w}x{h}")
        dialog.minsize(580, 650)
        dialog.transient(self)
        dialog.grab_set()

        scroll = ctk.CTkScrollableFrame(dialog, fg_color="#0f172a")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)
        scroll.grid_columnconfigure(0, weight=1)

        title_lbl = ctk.CTkLabel(scroll, text=title, font=ctk.CTkFont(size=18, weight="bold"), text_color="#38bdf8")
        title_lbl.pack(pady=(10, 15))

        return dialog, scroll

    def _build_recipe_ingredients_section(self, parent):
        sec = ctk.CTkFrame(parent, corner_radius=8, fg_color="#1e293b", border_width=1, border_color="#334155")
        sec.pack(fill="x", padx=10, pady=8)
        sec.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(sec, text="📦 Crafting Recipe & Ingredients", font=ctk.CTkFont(size=13, weight="bold"), text_color="#f8fafc").grid(row=0, column=0, columnspan=3, padx=12, pady=(10, 6), sticky="w")

        # Crafting Station
        ctk.CTkLabel(sec, text="Crafting Station:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=4, sticky="w")
        station_menu = ctk.CTkOptionMenu(sec, values=["Universal Handcrafting (V)", "Workbench", "Carpenter", "Blacksmith", "Alchemist", "Farmer", "Hunter"], width=280)
        station_menu.grid(row=1, column=1, columnspan=2, padx=12, pady=4, sticky="ew")

        # Craft Yield & Duration
        ctk.CTkLabel(sec, text="Output Yield & Time (s):", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=2, column=0, padx=12, pady=4, sticky="w")
        yield_entry = ctk.CTkEntry(sec, placeholder_text="Yield (e.g. 1)", width=120)
        yield_entry.insert(0, "1")
        yield_entry.grid(row=2, column=1, padx=(12, 4), pady=4, sticky="w")

        time_entry = ctk.CTkEntry(sec, placeholder_text="Secs (e.g. 3)", width=120)
        time_entry.insert(0, "3")
        time_entry.grid(row=2, column=2, padx=(4, 12), pady=4, sticky="w")

        # Material 1
        mat_names = list(MATERIAL_PRESETS.keys())
        ctk.CTkLabel(sec, text="Primary Material:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=3, column=0, padx=12, pady=4, sticky="w")
        mat1_menu = ctk.CTkOptionMenu(sec, values=mat_names, width=180)
        mat1_menu.set("Hardwood")
        mat1_menu.grid(row=3, column=1, padx=(12, 4), pady=4, sticky="ew")
        mat1_amt = ctk.CTkEntry(sec, placeholder_text="Qty", width=80)
        mat1_amt.insert(0, "5")
        mat1_amt.grid(row=3, column=2, padx=(4, 12), pady=4, sticky="w")

        # Material 2
        ctk.CTkLabel(sec, text="Secondary Material:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=4, column=0, padx=12, pady=4, sticky="w")
        mat2_menu = ctk.CTkOptionMenu(sec, values=mat_names, width=180)
        mat2_menu.set("Linen")
        mat2_menu.grid(row=4, column=1, padx=(12, 4), pady=4, sticky="ew")
        mat2_amt = ctk.CTkEntry(sec, placeholder_text="Qty", width=80)
        mat2_amt.insert(0, "2")
        mat2_amt.grid(row=4, column=2, padx=(4, 12), pady=4, sticky="w")

        # Catalyst Material
        ctk.CTkLabel(sec, text="Catalyst / Rare (Opt):", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=5, column=0, padx=12, pady=(4, 10), sticky="w")
        mat3_menu = ctk.CTkOptionMenu(sec, values=["None"] + mat_names, width=180)
        mat3_menu.set("None")
        mat3_menu.grid(row=5, column=1, padx=(12, 4), pady=(4, 10), sticky="ew")
        mat3_amt = ctk.CTkEntry(sec, placeholder_text="Qty", width=80)
        mat3_amt.insert(0, "1")
        mat3_amt.grid(row=5, column=2, padx=(4, 12), pady=(4, 10), sticky="w")

        def _get_ingredients():
            ings = []
            m1 = mat1_menu.get()
            if m1 and m1 in MATERIAL_PRESETS:
                ings.append({"name": m1, "itemId": MATERIAL_PRESETS[m1], "amount": int(mat1_amt.get().strip() or "1")})
            m2 = mat2_menu.get()
            if m2 and m2 in MATERIAL_PRESETS:
                ings.append({"name": m2, "itemId": MATERIAL_PRESETS[m2], "amount": int(mat2_amt.get().strip() or "1")})
            m3 = mat3_menu.get()
            if m3 and m3 != "None" and m3 in MATERIAL_PRESETS:
                ings.append({"name": m3, "itemId": MATERIAL_PRESETS[m3], "amount": int(mat3_amt.get().strip() or "1")})
            return ings, station_menu.get(), int(yield_entry.get().strip() or "1"), int(time_entry.get().strip() or "3")

        return _get_ingredients

    # ------------------ Comprehensive Studio Wizards ------------------

    def _open_furniture_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🪑 Custom Furniture & Prop Wizard")

        # Identity
        name_entry = ctk.CTkEntry(scroll, placeholder_text="Item Name (e.g. Celestial Archmage Throne)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Lore Description", width=500); desc_entry.pack(pady=4)

        # Tier & Mesh
        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Rarity & Level:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        rarity_menu = ctk.CTkOptionMenu(opt_frame, values=["Common", "Uncommon", "Rare", "Epic", "Legendary"], width=150); rarity_menu.set("Epic"); rarity_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        lvl_entry = ctk.CTkEntry(opt_frame, placeholder_text="Level (1-35)", width=80); lvl_entry.insert(0, "25"); lvl_entry.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Category & Comfort:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        cat_menu = ctk.CTkOptionMenu(opt_frame, values=["Comfort & Seating", "Beds & Sleeping", "Tables & Dining", "Lighting & Fireplaces", "Decoration & Trophies"], width=200); cat_menu.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        comfort_entry = ctk.CTkEntry(opt_frame, placeholder_text="Comfort (+1-50)", width=80); comfort_entry.insert(0, "18"); comfort_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Item Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "description": desc_entry.get().strip() or "Custom handcrafted furniture.",
                "category": cat_menu.get(), "rarity": rarity_menu.get(), "level": int(lvl_entry.get().strip() or "20"),
                "comfort_score": int(comfort_entry.get().strip() or "15"), "crafting_station": station,
                "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_furniture_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("furniture")
            self.set_status(f"Created custom furniture '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Save & Deploy Furniture", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_art_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🖼️ Custom Art & Painting Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Artwork Name (e.g. Spires of Embervale)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Lore Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Frame & Dimensions:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        frame_menu = ctk.CTkOptionMenu(opt_frame, values=["Gilded Ornate Gold", "Polished Dark Oak", "Ancient Carved Stone", "Woven Wall Hanging"], width=200); frame_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        dim_menu = ctk.CTkOptionMenu(opt_frame, values=["Small (1x1)", "Medium (2x2)", "Large (3x2)", "Grand (4x3)"], width=140); dim_menu.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Rarity & Comfort Bonus:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        rarity_menu = ctk.CTkOptionMenu(opt_frame, values=["Common", "Uncommon", "Rare", "Epic", "Legendary"], width=200); rarity_menu.set("Rare"); rarity_menu.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        comfort_entry = ctk.CTkEntry(opt_frame, placeholder_text="Comfort", width=80); comfort_entry.insert(0, "12"); comfort_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Artwork Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "description": desc_entry.get().strip() or "Custom fine art piece.",
                "frame_style": frame_menu.get(), "dimensions": dim_menu.get(), "rarity": rarity_menu.get(), "level": 15,
                "comfort_score": int(comfort_entry.get().strip() or "12"), "crafting_station": station,
                "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_art_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("art")
            self.set_status(f"Created custom artwork '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Save & Deploy Art", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_hair_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("💇 Custom Hairstyle & Beard Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Style Name (e.g. Braided Warlord Crest)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Style Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Type & Gender Target:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        type_menu = ctk.CTkOptionMenu(opt_frame, values=["Hair", "Beard"], width=180); type_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        gender_menu = ctk.CTkOptionMenu(opt_frame, values=["Male", "Female", "Unisex"], width=140); gender_menu.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Color Swatch Preset:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        color_menu = ctk.CTkOptionMenu(opt_frame, values=["Platinum Silver", "Raven Black", "Auburn / Copper", "Starlight White", "Neon Astral Cyan", "Golden Sunfire"], width=200); color_menu.grid(row=1, column=1, padx=6, pady=6, sticky="w")

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Style Name is required."); return
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "description": desc_entry.get().strip() or "Custom cosmetic style.",
                "type": type_menu.get(), "gender": gender_menu.get(), "color_preset": color_menu.get()
            }
            self.importer.add_hair_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("hair")
            self.set_status(f"Added custom {type_menu.get()} '{name}' into character mirror and mod.lua!")
        ctk.CTkButton(scroll, text="💾 Save Custom Hairstyle / Beard", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_potion_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🧪 Custom Potions & Alchemy Lab Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Potion Name (e.g. Draught of the Shroudbreaker)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Potion Effect Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Type & Quality Tier:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        cat_menu = ctk.CTkOptionMenu(opt_frame, values=["Elixir", "Potion", "Flask", "Draught"], width=180); cat_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        rarity_menu = ctk.CTkOptionMenu(opt_frame, values=["Common", "Uncommon", "Rare", "Epic", "Legendary"], width=140); rarity_menu.set("Legendary"); rarity_menu.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Duration (s) & Shroud Bonus (s):", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        dur_entry = ctk.CTkEntry(opt_frame, placeholder_text="Duration (e.g. 1800)", width=120); dur_entry.insert(0, "1800"); dur_entry.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        shroud_entry = ctk.CTkEntry(opt_frame, placeholder_text="Shroud (+s)", width=100); shroud_entry.insert(0, "600"); shroud_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Potion Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "description": desc_entry.get().strip() or "Custom alchemical elixir.",
                "category": cat_menu.get(), "rarity": rarity_menu.get(), "duration_seconds": int(dur_entry.get().strip() or "1800"),
                "shroud_time_bonus": int(shroud_entry.get().strip() or "600"), "damage_multiplier": 1.5,
                "stack_size": 50, "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_potion_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("potions")
            self.set_status(f"Brewed custom potion '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Brew & Deploy Potion", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_spell_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("⚡ Custom Spells & Magic Charges Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Spell Name (e.g. Glacial Absolute Zero)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Spell Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Element & Base Damage:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        elem_menu = ctk.CTkOptionMenu(opt_frame, values=["Fire", "Ice / Frost", "Lightning / Holy", "Shroud / Void"], width=180); elem_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        dmg_entry = ctk.CTkEntry(opt_frame, placeholder_text="Damage", width=100); dmg_entry.insert(0, "450"); dmg_entry.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Mana Cost & Charges:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        mana_entry = ctk.CTkEntry(opt_frame, placeholder_text="Mana Cost", width=120); mana_entry.insert(0, "45"); mana_entry.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        charge_entry = ctk.CTkEntry(opt_frame, placeholder_text="Charges", width=100); charge_entry.insert(0, "150"); charge_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Spell Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "description": desc_entry.get().strip() or "Custom magic spell charge.",
                "magic_element": elem_menu.get(), "base_damage": int(dmg_entry.get().strip() or "400"),
                "mana_cost": int(mana_entry.get().strip() or "40"), "explosion_radius": 10.0,
                "charges": int(charge_entry.get().strip() or "100"), "rarity": "Legendary", "level": 25,
                "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_spell_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("spells")
            self.set_status(f"Inscribed custom spell '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Inscribe & Deploy Spell", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_block_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🧱 Custom Building Materials & Blocks Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Block Name (e.g. Royal Gilded Marble)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Material Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Category & Glow:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        cat_menu = ctk.CTkOptionMenu(opt_frame, values=["Stone / Masonry", "Wood / Timber", "Metal / Iron", "Luminous / Decorative"], width=180); cat_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        glow_menu = ctk.CTkOptionMenu(opt_frame, values=["None", "Cyan / Astral Blue", "Golden Sunfire", "Emerald Green", "Purple Shroud"], width=150); glow_menu.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Block Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "description": desc_entry.get().strip() or "Custom construction material.",
                "category": cat_menu.get(), "emissive_glow": glow_menu.get(), "hardness_rating": 8.0,
                "craft_yield": yield_cnt if yield_cnt > 1 else 100, "rarity": "Rare", "level": 15,
                "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_building_block_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("blocks")
            self.set_status(f"Forged custom material '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Forge & Deploy Block", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_color_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🎨 Custom Color Palette & Dye Wizard", h=600)

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Swatch Name (e.g. Celestial Void Indigo)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Type & Hex Swatch:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        type_menu = ctk.CTkOptionMenu(opt_frame, values=["Hair & Beard Preset", "Armor & Glider Dye", "Flame & Light Color", "Eye Color Swatch"], width=200); type_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        hex_entry = ctk.CTkEntry(opt_frame, placeholder_text="#hex (e.g. #06b6d4)", width=120); hex_entry.insert(0, "#06b6d4"); hex_entry.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Metallic Sheen & Glow:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        sheen_entry = ctk.CTkEntry(opt_frame, placeholder_text="Sheen 0.0-1.0", width=120); sheen_entry.insert(0, "0.8"); sheen_entry.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        glow_entry = ctk.CTkEntry(opt_frame, placeholder_text="Glow (e.g. 1.2)", width=120); glow_entry.insert(0, "1.2"); glow_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Swatch Name is required."); return
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "type": type_menu.get(),
                "hex_color": hex_entry.get().strip() or "#ffffff", "metallic_sheen": float(sheen_entry.get().strip() or "0.5"),
                "glow_intensity": float(glow_entry.get().strip() or "1.0"), "description": desc_entry.get().strip() or "Custom color palette."
            }
            self.importer.add_color_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("colors")
            self.set_status(f"Saved custom color preset '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Save Color Palette", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_glider_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🪂 Custom Glider & Grappling Hook Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Gear Name (e.g. Ghost Glider Infinite)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Traversal Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Type & Quality Tier:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        type_menu = ctk.CTkOptionMenu(opt_frame, values=["Glider", "Grapple Hook"], width=180); type_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        rarity_menu = ctk.CTkOptionMenu(opt_frame, values=["Common", "Uncommon", "Rare", "Epic", "Legendary"], width=140); rarity_menu.set("Legendary"); rarity_menu.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Glide Ratio / Range & Speed:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        ratio_entry = ctk.CTkEntry(opt_frame, placeholder_text="Glide Ratio (e.g. 6.0)", width=120); ratio_entry.insert(0, "6.0"); ratio_entry.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        spd_entry = ctk.CTkEntry(opt_frame, placeholder_text="Speed Mult (e.g. 2.5)", width=120); spd_entry.insert(0, "2.5"); spd_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Gear Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "type": type_menu.get(),
                "glide_ratio": float(ratio_entry.get().strip() or "5.0"), "speed_multiplier": float(spd_entry.get().strip() or "2.0"),
                "stamina_drain_per_sec": 0.0, "rarity": rarity_menu.get(), "level": 25,
                "description": desc_entry.get().strip() or "Custom traversal equipment.",
                "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_glider_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("gliders")
            self.set_status(f"Crafted custom traversal gear '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Craft & Deploy Traversal Gear", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_weapon_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("⚔️ Custom Weapons & Legendary Armor Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Gear Name (e.g. Sunfire Warlord Bastion Blade)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Weapon / Armor Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Gear Type & Rarity:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        type_menu = ctk.CTkOptionMenu(opt_frame, values=["One-Handed Sword", "Two-Handed Greatsword", "Battleaxe", "Bow", "Magic Wand", "Staff", "Shield", "Chest Armor", "Helmet", "Boots"], width=200); type_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        rarity_menu = ctk.CTkOptionMenu(opt_frame, values=["Common", "Uncommon", "Rare", "Epic", "Legendary"], width=140); rarity_menu.set("Legendary"); rarity_menu.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Damage/Armor Rating & Crit:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        dmg_entry = ctk.CTkEntry(opt_frame, placeholder_text="Damage/Armor", width=120); dmg_entry.insert(0, "320"); dmg_entry.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        crit_entry = ctk.CTkEntry(opt_frame, placeholder_text="Crit Rate %", width=120); crit_entry.insert(0, "40"); crit_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Gear Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "type": type_menu.get(),
                "damage": int(dmg_entry.get().strip() or "300"), "armor_rating": int(dmg_entry.get().strip() or "300"),
                "crit_rate": float(crit_entry.get().strip() or "40") / 100.0, "rarity": rarity_menu.get(), "level": 30,
                "description": desc_entry.get().strip() or "Masterwork equipment.",
                "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_weapon_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("weapons")
            self.set_status(f"Forged custom weapon/armor '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Forge & Deploy Gear", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_pet_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🐾 Custom Pets & Companions Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Companion Name (e.g. Astral Direwolf Companion)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Companion Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Species & Combat Role:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        species_menu = ctk.CTkOptionMenu(opt_frame, values=["Direwolf", "Dragon / Drake", "Forest Panther", "Vukah Warrior", "Gryphon"], width=180); species_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        role_menu = ctk.CTkOptionMenu(opt_frame, values=["Fierce Defender", "Vicious Striker", "Pack Carrier", "Scout / Hunter"], width=140); role_menu.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Health & Attack Power:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        hp_entry = ctk.CTkEntry(opt_frame, placeholder_text="Health", width=120); hp_entry.insert(0, "1500"); hp_entry.grid(row=1, column=1, padx=6, pady=6, sticky="w")
        atk_entry = ctk.CTkEntry(opt_frame, placeholder_text="Attack Power", width=120); atk_entry.insert(0, "220"); atk_entry.grid(row=1, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Companion Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "species": species_menu.get(),
                "combat_role": role_menu.get(), "health": int(hp_entry.get().strip() or "1500"),
                "attack_power": int(atk_entry.get().strip() or "200"), "carry_slots": 16, "rarity": "Epic", "level": 25,
                "description": desc_entry.get().strip() or "Loyal bonded companion.",
                "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_pet_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("pets")
            self.set_status(f"Crafted companion whistle '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Inscribe Companion Whistle", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_farming_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🌾 Custom Farming & Botany Lab Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Crop Name (e.g. Astral Twilight Lotus)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Crop / Seed Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Crop Type & Growth Time (s):", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        type_menu = ctk.CTkOptionMenu(opt_frame, values=["Magical Herb", "Food Staple", "Alchemy Ingredient", "Luminescent Flower"], width=200); type_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        growth_entry = ctk.CTkEntry(opt_frame, placeholder_text="Growth (s)", width=120); growth_entry.insert(0, "45"); growth_entry.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Crop Name is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "crop_type": type_menu.get(),
                "growth_time_seconds": int(growth_entry.get().strip() or "45"), "harvest_yield": yield_cnt if yield_cnt > 1 else 10,
                "rarity": "Rare", "level": 15, "description": desc_entry.get().strip() or "High-yield botanical seedling.",
                "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_farming_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("farming")
            self.set_status(f"Cultivated custom crop seedling '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Cultivate & Deploy Seed", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    def _open_music_wizard(self):
        dialog, scroll = self._create_base_wizard_dialog("🎼 Custom Campfire Music & MIDI Wizard")

        name_entry = ctk.CTkEntry(scroll, placeholder_text="Song Title (e.g. Ballad of Embervale Spires)", width=500); name_entry.pack(pady=4)
        desc_entry = ctk.CTkEntry(scroll, placeholder_text="Song Description", width=500); desc_entry.pack(pady=4)

        opt_frame = ctk.CTkFrame(scroll, fg_color="#1e293b", corner_radius=8); opt_frame.pack(fill="x", padx=10, pady=8)
        opt_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(opt_frame, text="Instrument & Tempo (BPM):", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=0, column=0, padx=12, pady=6, sticky="w")
        inst_menu = ctk.CTkOptionMenu(opt_frame, values=["Lute", "Flute", "Harp", "Drums"], width=180); inst_menu.grid(row=0, column=1, padx=6, pady=6, sticky="w")
        bpm_entry = ctk.CTkEntry(opt_frame, placeholder_text="BPM (e.g. 115)", width=120); bpm_entry.insert(0, "115"); bpm_entry.grid(row=0, column=2, padx=12, pady=6, sticky="w")

        ctk.CTkLabel(opt_frame, text="Campfire Aura Buff Effect:", font=ctk.CTkFont(size=12), text_color="#cbd5e1").grid(row=1, column=0, padx=12, pady=6, sticky="w")
        buff_entry = ctk.CTkEntry(opt_frame, placeholder_text="Buff Description", width=320); buff_entry.insert(0, "+30% Stamina & Health Regen Aura"); buff_entry.grid(row=1, column=1, columnspan=2, padx=6, pady=6, sticky="ew")

        get_recipe = self._build_recipe_ingredients_section(scroll)

        def _on_save():
            name = name_entry.get().strip()
            if not name: messagebox.showerror("Error", "Song Title is required."); return
            ings, station, yield_cnt, craft_dur = get_recipe()
            data = {
                "id": name.lower().replace(" ", "_"), "name": name, "instrument": inst_menu.get(),
                "tempo_bpm": int(bpm_entry.get().strip() or "115"), "buff_effect": buff_entry.get().strip(),
                "rarity": "Rare", "level": 15, "description": desc_entry.get().strip() or "Playable campfire ballad.",
                "crafting_station": station, "craft_duration": craft_dur, "yield_amount": yield_cnt, "ingredients": ings
            }
            self.importer.add_music_item(data)
            self.manager.discover_modules(); self.manager.compile_master_lua()
            dialog.destroy(); self.show_custom_studio_view("music")
            self.set_status(f"Composed custom campfire song '{name}' and compiled to mod.lua!")
        ctk.CTkButton(scroll, text="💾 Inscribe & Deploy Sheet Music", fg_color="#10b981", hover_color="#059669", height=40, font=ctk.CTkFont(weight="bold"), command=_on_save).pack(pady=15, fill="x", padx=10)

    # =========================================================================
    # VIEW 3: EML LUA INSPECTOR
    # =========================================================================

    def show_lua_inspector_view(self):
        self._update_nav_highlight(self.lua_nav_btn)
        self.header_title.configure(text="Compiled EML Lua Script [Pregame Output]")
        self._clear_content()

        container = ctk.CTkFrame(self.content_frame, corner_radius=8, fg_color="#1e293b")
        container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        container.grid_columnconfigure(0, weight=1)
        container.grid_rowconfigure(1, weight=1)

        ctrl_frame = ctk.CTkFrame(container, fg_color="transparent")
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 6))
        ctrl_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(ctrl_frame, text="Live Generated mod.lua (Interception Hook Layer)", font=ctk.CTkFont(size=14, weight="bold")).grid(row=0, column=0, sticky="w")
        refresh_btn = ctk.CTkButton(ctrl_frame, text="🔄 Recompile Preview", width=140, command=self._refresh_lua_preview)
        refresh_btn.grid(row=0, column=1, sticky="e", padx=(0, 8))

        self.lua_textbox = ctk.CTkTextbox(container, font=ctk.CTkFont(family="Consolas", size=12), wrap="none")
        self.lua_textbox.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

        self._refresh_lua_preview()

    def _refresh_lua_preview(self):
        self.manager.compile_master_lua()
        master_lua_path = self.manager.base_dir / "runtime" / "master_loader.lua"
        if master_lua_path.exists():
            with open(master_lua_path, "r", encoding="utf-8") as f:
                code = f.read()
            self.lua_textbox.delete("1.0", "end")
            self.lua_textbox.insert("1.0", code)
            self.set_status("Recompiled master Lua script preview.")

    # =========================================================================
    # ACTIONS & LAUNCHER
    # =========================================================================

    def _on_module_toggled(self, mod_id: str, enabled: bool):
        self.manager.set_module_enabled(mod_id, enabled)
        self.manager.compile_master_lua()
        self.set_status(f"Module '{mod_id}' {'enabled' if enabled else 'disabled'}.")

    def _on_setting_changed(self, mod_id: str, key: str, value, is_dynamic: bool):
        self.manager.update_setting(mod_id, key, value, is_dynamic)
        self.manager.compile_master_lua()
        self.set_status(f"Updated setting: {key} = {value} (Compiled to mod.lua)")

    def rescan_modules(self):
        self.manager.discover_modules()
        self.manager.load_profile()
        self.show_modules_view()
        self.set_status("Rescanned modules directory successfully.")

    def reset_to_defaults(self):
        if messagebox.askyesno(
            "Reset to Vanilla Defaults",
            "Are you sure you want to reset all module settings, sliders, and tweaks back to vanilla game defaults?\n\nThis will recompile mod.lua to baseline values."
        ):
            self.manager.reset_to_defaults()
            self.show_modules_view()
            self.set_status("All modules and tweaks have been reset to vanilla game defaults.")

    def deploy_mods(self):
        out = self.manager.compile_master_lua()
        self.set_status(f"Successfully compiled & deployed to: {out}")

    def launch_game(self):
        self.manager.compile_master_lua()
        self.set_status("Compiled active modules. Launching Enshrouded via Steam...")
        try:
            os.startfile("steam://rungameid/1203620")
            self.set_status("Game launched! EML pregame configuration active.")
        except Exception as e:
            self.set_status(f"Launch triggered (Steam ID 1203620): {e}")


def main():
    app = EnshroudedHubApp()
    app.mainloop()


if __name__ == "__main__":
    main()
