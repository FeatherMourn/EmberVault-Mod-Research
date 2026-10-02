"""Profile panel: view and manipulate the active profile's pending edits."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..core.profile import Profile


class ProfilePanel(ttk.Frame):
    """Lists edits; supports enable/disable, remove, duplicate, and reorder."""

    def __init__(self, master):
        super().__init__(master)
        self.profile = Profile(name="Untitled", game_build="1076226")
        self._edit_rows = {}  # tree item id -> Edit

        self._build()

    def _build(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=4, pady=(4, 0))
        ttk.Label(header, text="Active Profile").pack(side="left")
        self.name_var = tk.StringVar(value="Untitled")
        ttk.Entry(header, textvariable=self.name_var, width=28).pack(
            side="left", padx=8)
        self.count_var = tk.StringVar(value="0 edits")
        ttk.Label(header, textvariable=self.count_var).pack(side="left", padx=4)

        desc = ttk.Frame(self)
        desc.pack(fill="x", padx=4, pady=2)
        ttk.Label(desc, text="Description:").pack(side="left")
        self.desc_var = tk.StringVar()
        ttk.Entry(desc, textvariable=self.desc_var).pack(
            side="left", fill="x", expand=True, padx=4)

        self.tree = ttk.Treeview(
            self, columns=("enabled", "resource", "path", "value"),
            show="headings", selectmode="browse")
        self.tree.heading("enabled", text="On")
        self.tree.heading("resource", text="Resource Type")
        self.tree.heading("path", text="Field Path")
        self.tree.heading("value", text="Value")
        self.tree.column("enabled", width=30, anchor="center")
        self.tree.column("resource", width=180)
        self.tree.column("path", width=180)
        self.tree.column("value", width=100)
        self.tree.pack(fill="both", expand=True, padx=4, pady=2)
        self.tree.bind("<Double-1>", self._on_toggle)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=4, pady=4)
        ttk.Button(buttons, text="Toggle", command=self._toggle).pack(side="left", padx=2)
        ttk.Button(buttons, text="Remove", command=self._remove).pack(side="left", padx=2)
        ttk.Button(buttons, text="Duplicate", command=self._duplicate).pack(side="left", padx=2)
        ttk.Button(buttons, text="Up", command=self._move_up).pack(side="left", padx=2)
        ttk.Button(buttons, text="Down", command=self._move_down).pack(side="left", padx=2)

    # -- model sync ----------------------------------------------------------

    def set_profile(self, profile):
        self.profile = profile
        self.name_var.set(profile.name)
        self.desc_var.set(profile.description)
        self._refresh()

    def sync_profile(self):
        self.profile.name = self.name_var.get().strip() or "Untitled"
        self.profile.description = self.desc_var.get().strip()

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._edit_rows = {}
        for edit in self.profile.edits:
            self._insert_row(edit)
        self.count_var.set("%d edits" % len(self.profile.edits))

    def _insert_row(self, edit):
        item = self.tree.insert(
            "", "end",
            values=(
                "Y" if edit.enabled else "N",
                edit.resource_type,
                edit.path,
                str(edit.value),
            ))
        self._edit_rows[item] = edit
        return item

    def add_edit(self, edit):
        self.profile.edits.append(edit)
        self._insert_row(edit)
        self.count_var.set("%d edits" % len(self.profile.edits))

    # -- actions -------------------------------------------------------------

    def _selected_edit(self):
        selection = self.tree.selection()
        if not selection:
            return None, None
        item = selection[0]
        return item, self._edit_rows.get(item)

    def _toggle(self):
        item, edit = self._selected_edit()
        if edit is None:
            return
        edit.enabled = not edit.enabled
        self.tree.set(item, "enabled", "Y" if edit.enabled else "N")

    def _on_toggle(self, _event):
        self._toggle()

    def _remove(self):
        item, edit = self._selected_edit()
        if edit is None:
            return
        self.profile.edits.remove(edit)
        self._refresh()

    def _duplicate(self):
        _, edit = self._selected_edit()
        if edit is None:
            return
        import copy
        duplicate = copy.deepcopy(edit)
        self.profile.edits.append(duplicate)
        self._refresh()

    def _move_up(self):
        item, edit = self._selected_edit()
        if edit is None:
            return
        index = self.profile.edits.index(edit)
        if index == 0:
            return
        self.profile.edits[index - 1], self.profile.edits[index] = (
            self.profile.edits[index], self.profile.edits[index - 1])
        self._refresh()
        # Re-select the moved edit.
        children = self.tree.get_children()
        self.tree.selection_set(children[index - 1])

    def _move_down(self):
        item, edit = self._selected_edit()
        if edit is None:
            return
        index = self.profile.edits.index(edit)
        if index >= len(self.profile.edits) - 1:
            return
        self.profile.edits[index + 1], self.profile.edits[index] = (
            self.profile.edits[index], self.profile.edits[index + 1])
        self._refresh()
        children = self.tree.get_children()
        self.tree.selection_set(children[index + 1])
