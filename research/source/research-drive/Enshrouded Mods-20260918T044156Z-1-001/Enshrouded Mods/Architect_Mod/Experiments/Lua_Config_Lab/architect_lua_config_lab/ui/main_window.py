"""Main application window with 2-level navigation (Simple Catalog & Advanced Editor)."""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .. import __tool_name__, __version__
from ..config import (
    base_lua_path,
    cache_dir,
    kfc_dir,
    output_dir,
    types_lua_path,
)
from ..core.lab import Lab
from ..core.profile import Profile, load_profile, save_profile
from .advanced_workspace import AdvancedWorkspace
from .all_resources_view import AllResourcesView
from .category_view import CategoryView
from .generator_preview import GeneratorPreview
from .home_view import HomeView
from .my_changes_view import MyChangesView
from .resource_view import ResourceView
from .search_view import SearchView


class MainWindow(tk.Tk):
    def __init__(self, args):
        super().__init__()
        self.title(f"{__tool_name__} v{__version__}")
        self.geometry("1180x760")

        self.args = args
        self.lab: Lab | None = None
        self.profile: Profile = Profile(name="Untitled", game_build="1076226")

        self._build_menu()
        self._build_shell()
        self._build_status()

        self._load_schema()
        self.show_home()

    @property
    def catalog(self):
        return self.lab.catalog if self.lab else None

    @property
    def controls(self):
        return self.lab.controls if self.lab else None

    # -- construction --------------------------------------------------------

    def _build_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Reload Schema", command=self._reload_schema)
        file_menu.add_separator()
        file_menu.add_command(label="Load Profile / Preset...", command=self.load_profile)
        file_menu.add_command(label="Save Profile / Preset...", command=self.save_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Export Mod...", command=self.build_mod)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.destroy)
        menubar.add_cascade(label="File", menu=file_menu)

        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Home / Catalog", command=self.show_home)
        view_menu.add_command(label="All Resources (131)", command=self.show_all_resources)
        view_menu.add_command(label="My Changes", command=self.show_my_changes)
        view_menu.add_command(label="Advanced Editor", command=lambda: self.show_advanced())
        menubar.add_cascade(label="View", menu=view_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._about)
        menubar.add_cascade(label="Help", menu=help_menu)
        self.config(menu=menubar)

    def _build_shell(self):
        # 1. Startup reminder banner
        self.banner = ttk.Frame(self, relief="groove", borderwidth=1)
        self.banner.pack(fill="x", padx=6, pady=(4, 2))
        ttk.Label(
            self.banner,
            text="Notice: Changes are applied when Enshrouded starts. Restart the game after changing a generated configuration.",
            font=("Segoe UI", 9, "italic"),
            foreground="#555",
            anchor="center",
        ).pack(fill="x", padx=4, pady=3)

        # 2. Top global navigation bar
        nav_bar = ttk.Frame(self)
        nav_bar.pack(fill="x", padx=6, pady=2)
        ttk.Button(nav_bar, text="Home", command=self.show_home).pack(side="left", padx=2)
        ttk.Button(nav_bar, text="All Resources", command=self.show_all_resources).pack(side="left", padx=2)

        self.changes_btn_var = tk.StringVar(value="My Changes (0)")
        ttk.Button(nav_bar, textvariable=self.changes_btn_var, command=self.show_my_changes).pack(side="left", padx=2)

        ttk.Button(nav_bar, text="Advanced Editor", command=lambda: self.show_advanced()).pack(side="right", padx=2)
        ttk.Button(nav_bar, text="Build Mod...", command=self.build_mod).pack(side="right", padx=2)
        ttk.Button(nav_bar, text="Preview Lua", command=self.preview_lua).pack(side="right", padx=2)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=6, pady=4)

        # 3. Main container for view switching
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True, padx=6, pady=2)

        # Pre-instantiate views
        self.home_view = HomeView(self.container, self)
        self.category_view = CategoryView(self.container, self)
        self.resource_view = ResourceView(self.container, self)
        self.search_view = SearchView(self.container, self)
        self.all_resources_view = AllResourcesView(self.container, self)
        self.my_changes_view = MyChangesView(self.container, self)
        self.advanced_view = None  # Instantiated after lab is loaded

    def _build_status(self):
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(self, textvariable=self.status_var, relief="sunken",
                  anchor="w").pack(fill="x", side="bottom")

    def set_status(self, text: str):
        self.status_var.set(text)

    def refresh_changes_badge(self):
        count = len(self.profile.edits) if self.profile else 0
        self.changes_btn_var.set(f"My Changes ({count})")

    # -- navigation ----------------------------------------------------------

    def _switch_view(self, view_widget):
        for child in self.container.winfo_children():
            child.pack_forget()
        view_widget.pack(fill="both", expand=True)

    def show_home(self):
        self.home_view.show()
        self._switch_view(self.home_view)
        self.set_status("Home: Select a category or search resources.")

    def show_category(self, category: str):
        self.category_view.show(category)
        self._switch_view(self.category_view)
        self.set_status(f"Category: {category}")

    def show_resource(self, resource_type: str, back=None):
        self.resource_view.show(resource_type, back=back)
        self._switch_view(self.resource_view)
        self.set_status(f"Resource: {resource_type}")

    def show_search(self, query: str):
        self.search_view.show(query)
        self._switch_view(self.search_view)
        self.set_status(f"Search results for: '{query}'")

    def show_all_resources(self):
        self.all_resources_view.show()
        self._switch_view(self.all_resources_view)
        self.set_status("All Resources (131/131 roots cataloged)")

    def show_my_changes(self):
        self.my_changes_view.show()
        self._switch_view(self.my_changes_view)
        self.set_status("My Changes: Review pending configuration edits.")

    def show_advanced(self, focus_resource_type=None):
        if self.advanced_view is None and self.lab is not None:
            self.advanced_view = AdvancedWorkspace(self.container, self, self.lab, self.profile)
        if self.advanced_view is not None:
            self.advanced_view.show(focus_resource_type=focus_resource_type)
            self._switch_view(self.advanced_view)
            self.set_status("Advanced Resource Editor: Direct reflected schema workspace.")

    # -- schema --------------------------------------------------------------

    def _load_schema(self):
        types_path = self.args.types_lua or types_lua_path()
        if not os.path.isfile(types_path):
            if not messagebox.askyesno(
                "types.lua not found",
                "types.lua was not found at:\\n%s\\n\\nWould you like to locate it?"
                % types_path,
            ):
                self.destroy()
                return
            types_path = filedialog.askopenfilename(
                title="Select types.lua",
                filetypes=[("Lua files", "*.lua"), ("All files", "*.* ")],
            )
            if not types_path:
                self.destroy()
                return

        try:
            self.lab = Lab(
                types_lua_path=types_path,
                base_lua_path=self.args.base_lua or base_lua_path(),
                kfc_dir=self.args.kfc_dir or kfc_dir(),
                cache_dir=None if self.args.no_cache else cache_dir(),
            )
            self.lab.load()
        except Exception as exc:
            messagebox.showerror("Schema load failed", str(exc))
            self.destroy()
            return

        self.advanced_view = AdvancedWorkspace(self.container, self, self.lab, self.profile)
        self.status_var.set(
            "Loaded %d classes, %d resource roots" % (
                self.lab.schema().class_count(), len(self.lab.root_entries())))

    def _reload_schema(self):
        if self.lab is not None:
            try:
                self.lab.load(force_rebuild=True)
                if self.advanced_view:
                    self.advanced_view.browser.set_entries(self.lab.root_entries())
                self.status_var.set("Schema reloaded.")
            except Exception as exc:
                messagebox.showerror("Reload failed", str(exc))

    # -- shared actions ------------------------------------------------------

    def load_profile(self):
        path = filedialog.askopenfilename(
            title="Load Profile / Preset", filetypes=[("JSON", "*.json"), ("All files", "*.* ")])
        if not path:
            return
        try:
            profile = load_profile(path)
            self.profile = profile
            if self.advanced_view:
                self.advanced_view.profile = profile
                self.advanced_view.profile_panel.set_profile(profile)
            self.refresh_changes_badge()
            self.set_status(f"Loaded preset: {profile.name}")
        except Exception as exc:
            messagebox.showerror("Load failed", str(exc))

    def save_profile(self):
        if self.advanced_view:
            self.advanced_view.sync()
        if self.lab is not None:
            self.profile.types_lua_sha256 = self.lab.types_sha256
        path = filedialog.asksaveasfilename(
            title="Save Profile / Preset", defaultextension=".json",
            filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            save_profile(self.profile, path)
            self.set_status(f"Saved preset: {path}")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))

    def preview_lua(self):
        if self.lab is None:
            return
        if self.advanced_view:
            self.advanced_view.sync()
        problem = self.profile.validate()
        if problem:
            messagebox.showwarning("Preset invalid", problem)
            return
        try:
            lua_text = self.lab.generate(self.profile)
            summary = self.lab.summary(self.profile)
        except Exception as exc:
            messagebox.showerror("Generation failed", str(exc))
            return
        GeneratorPreview(self, lua_text, summary)

    def build_mod(self):
        if self.lab is None:
            return
        if self.advanced_view:
            self.advanced_view.sync()
        problem = self.profile.validate()
        if problem:
            messagebox.showwarning("Preset invalid", problem)
            return

        if any(e.enabled and e.target.mode == "all" for e in self.profile.edits):
            if not messagebox.askyesno(
                "ALL target confirmation",
                "One or more edits use target mode ALL, which modifies every "
                "resource of that type. Continue?",
            ):
                return

        mismatch, revalidations = self.lab.compatibility(self.profile)
        if mismatch:
            summary = "\\n".join(
                "%s: %s" % (r["path"], r["result"]) for r in revalidations)
            if not messagebox.askyesno(
                "Schema version mismatch",
                "This profile was created against a different types.lua.\\n\\n"
                "%s\\n\\nContinue anyway?" % summary,
            ):
                return

        directory = filedialog.askdirectory(
            title="Select output directory", initialdir=output_dir())
        if not directory:
            return
        try:
            paths = self.lab.export(self.profile, base_output_dir=directory)
        except Exception as exc:
            messagebox.showerror("Export failed", str(exc))
            return
        messagebox.showinfo("Mod Built Successfully", "Exported to:\\n%s" % paths["directory"])
        self.set_status(f"Built mod: {paths['directory']}")

    def _about(self):
        messagebox.showinfo(
            "About",
            f"{__tool_name__} v{__version__}\\n\\n"
            "Startup resource configuration editor for Enshrouded (EML/Lua backend).\\n"
            "Schema-validated; runtime effects are unproven until tested in-game.\\n\\n"
            "Phase 2 Catalog: 131 known KFC resource families across 16 categories.",
        )


def launch(args) -> int:
    window = MainWindow(args)
    window.mainloop()
    return 0
