"""Advanced Resource Editor.

This is the original three-panel workspace (Resource Browser | Field Tree |
Edit Panel) plus the profile panel. It is preserved in full and reachable from
any resource in the friendly catalog via "Browse Raw Fields".
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..core.profile import Profile
from .edit_panel import EditPanel
from .field_tree import FieldTree
from .generator_preview import GeneratorPreview
from .profile_panel import ProfilePanel
from .resource_browser import ResourceBrowser


class AdvancedWorkspace(ttk.Frame):
    def __init__(self, master, app, lab, profile: Profile):
        super().__init__(master)
        self.app = app
        self.lab = lab
        self.profile = profile
        self.current_resource_type = None

        self._build()

    def _build(self):
        left = ttk.Frame(self)
        left.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        middle = ttk.Frame(self)
        middle.grid(row=0, column=1, sticky="nsew", padx=4, pady=4)
        right = ttk.Frame(self)
        right.grid(row=0, column=2, sticky="nsew", padx=4, pady=4)

        self.columnconfigure(0, weight=1, minsize=240)
        self.columnconfigure(1, weight=2, minsize=320)
        self.columnconfigure(2, weight=2, minsize=420)
        self.rowconfigure(0, weight=1)

        self.browser = ResourceBrowser(left, on_select=self._on_resource_selected)
        self.browser.pack(fill="both", expand=True)

        self.field_tree = FieldTree(middle, on_select=self._on_field_selected)
        self.field_tree.pack(fill="both", expand=True)

        self.edit_panel = EditPanel(right)
        self.edit_panel.pack(fill="x")

        ttk.Button(right, text="Add Edit to Preset", command=self._add_edit).pack(
            fill="x", padx=4, pady=2)

        self.profile_panel = ProfilePanel(right)
        self.profile_panel.pack(fill="both", expand=True)

        actions = ttk.Frame(right)
        actions.pack(fill="x", padx=4, pady=4)
        ttk.Button(actions, text="Preview Lua", command=self._preview).pack(
            side="left", padx=2)
        ttk.Button(actions, text="Build Mod...", command=self._export).pack(
            side="left", padx=2)

        self.field_tree.set_lab(self.lab)
        self.edit_panel.set_lab(self.lab)

    # -- lifecycle -----------------------------------------------------------

    def show(self, focus_resource_type=None):
        self.browser.set_entries(self.lab.root_entries())
        self.profile_panel.set_profile(self.profile)
        if focus_resource_type:
            self.focus_resource(focus_resource_type)

    def sync(self):
        """Pull name/description edits back into the shared profile."""
        self.profile_panel.sync_profile()

    def focus_resource(self, resource_type):
        entry = None
        for candidate in self.lab.root_entries():
            if candidate["resource_type"] == resource_type:
                entry = candidate
                break
        if entry is None:
            return
        # Select it in the browser list if visible.
        self._on_resource_selected(entry)

    # -- wiring --------------------------------------------------------------

    def _on_resource_selected(self, entry):
        self.current_resource_type = entry["resource_type"]
        self.field_tree.show_resource(entry["resource_type"])
        self.edit_panel.set_context(entry["resource_type"], "")
        self.app.set_status("Resource: %s" % entry["resource_type"])

    def _on_field_selected(self, path):
        if self.current_resource_type:
            self.edit_panel.set_context(self.current_resource_type, path)

    def _add_edit(self):
        if not self.current_resource_type:
            messagebox.showinfo("Add Edit", "Select a resource and field first.")
            return
        edit, error = self.edit_panel.build_edit()
        if error:
            messagebox.showwarning("Invalid edit", error)
            self.edit_panel.status_var.set(error)
            return
        self.profile_panel.add_edit(edit)
        self.app.set_status("Added edit: %s %s" % (edit.resource_type, edit.path))
        self.app.refresh_changes_badge()

    def _preview(self):
        self.sync()
        problem = self.profile.validate()
        if problem:
            messagebox.showwarning("Preset invalid", problem)
            return
        try:
            lua_text = self.lab.generate(self.profile)
            summary = self.lab.summary(self.profile)
        except Exception as exc:  # noqa: BLE001
            messagebox.showerror("Generation failed", str(exc))
            return
        GeneratorPreview(self, lua_text, summary)

    def _export(self):
        self.sync()
        self.app.build_mod()
