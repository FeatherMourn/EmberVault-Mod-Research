"""My Changes view: summary of pending configuration edits."""

from __future__ import annotations

import copy
import tkinter as tk
from tkinter import messagebox, ttk


class MyChangesView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._edit_rows = {}
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Button(top, text="< Back to Catalog", command=lambda: self.app.show_home()).pack(side="left")
        ttk.Label(top, text="My Changes", font=("Segoe UI", 13, "bold")).pack(side="left", padx=8)

        notice_frame = ttk.Frame(self)
        notice_frame.pack(fill="x", padx=12, pady=(4, 8))
        ttk.Label(
            notice_frame,
            text="All changes are applied when Enshrouded starts. Restart the game after changing a generated configuration.",
            font=("Segoe UI", 9, "italic"),
            foreground="#666",
        ).pack(anchor="w")

        header = ttk.Frame(self)
        header.pack(fill="x", padx=12, pady=4)
        ttk.Label(header, text="Preset Name:").pack(side="left")
        self.name_var = tk.StringVar(value="Untitled")
        name_entry = ttk.Entry(header, textvariable=self.name_var, width=24)
        name_entry.pack(side="left", padx=6)
        name_entry.bind("<FocusOut>", lambda _e: self._sync_name())
        name_entry.bind("<Return>", lambda _e: self._sync_name())

        self.count_var = tk.StringVar(value="0 changes")
        ttk.Label(header, textvariable=self.count_var, foreground="#444").pack(side="left", padx=12)

        columns = ("enabled", "name", "resource", "path", "value", "restart")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("enabled", text="On")
        self.tree.heading("name", text="Setting / Name")
        self.tree.heading("resource", text="Resource")
        self.tree.heading("path", text="Field Path")
        self.tree.heading("value", text="New Value")
        self.tree.heading("restart", text="Requires")

        self.tree.column("enabled", width=35, anchor="center")
        self.tree.column("name", width=200)
        self.tree.column("resource", width=180)
        self.tree.column("path", width=180)
        self.tree.column("value", width=120)
        self.tree.column("restart", width=110, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=12, pady=4)
        self.tree.bind("<Double-1>", self._on_toggle)

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        btn_bar = ttk.Frame(self)
        btn_bar.pack(fill="x", padx=12, pady=4)
        ttk.Button(btn_bar, text="Toggle On/Off", command=self._toggle).pack(side="left", padx=2)
        ttk.Button(btn_bar, text="Remove", command=self._remove).pack(side="left", padx=2)
        ttk.Button(btn_bar, text="Duplicate", command=self._duplicate).pack(side="left", padx=2)
        ttk.Button(btn_bar, text="Move Up", command=self._move_up).pack(side="left", padx=2)
        ttk.Button(btn_bar, text="Move Down", command=self._move_down).pack(side="left", padx=2)
        ttk.Button(btn_bar, text="Clear All", command=self._clear_all).pack(side="left", padx=6)

        actions_bar = ttk.Frame(self)
        actions_bar.pack(fill="x", padx=12, pady=(6, 12))
        ttk.Button(actions_bar, text="Save Preset...", command=self._save_preset).pack(side="left", padx=2)
        ttk.Button(actions_bar, text="Load Preset...", command=self._load_preset).pack(side="left", padx=2)
        ttk.Button(actions_bar, text="Preview Lua", command=self._preview_lua).pack(side="left", padx=2)
        ttk.Button(actions_bar, text="Build Mod...", command=self._build_mod).pack(side="left", padx=6)
        ttk.Button(actions_bar, text="Open in Advanced Editor", command=self._open_advanced).pack(side="right", padx=2)

    def _sync_name(self):
        if self.app.profile:
            self.app.profile.name = self.name_var.get().strip() or "Untitled"

    def show(self):
        if self.app.profile:
            self.name_var.set(self.app.profile.name)
        self._refresh()

    def _resolve_control_name(self, edit):
        if self.app.controls is not None:
            for control in self.app.controls.controls:
                if control.resource_type == edit.resource_type and control.path == edit.path:
                    return control.name
        return edit.path

    def _refresh(self):
        self.tree.delete(*self.tree.get_children())
        self._edit_rows = {}
        if not self.app.profile:
            self.count_var.set("0 changes")
            return

        edits = self.app.profile.edits
        for edit in edits:
            self._insert_row(edit)

        total = len(edits)
        enabled = sum(1 for e in edits if e.enabled)
        self.count_var.set(f"{total} change(s) ({enabled} enabled)")
        self.app.refresh_changes_badge()

    def _insert_row(self, edit):
        friendly_name = self._resolve_control_name(edit)
        item = self.tree.insert(
            "", "end",
            values=(
                "Y" if edit.enabled else "N",
                friendly_name,
                edit.resource_type,
                edit.path,
                str(edit.value),
                "Restart game",
            )
        )
        self._edit_rows[item] = edit
        return item

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
        self._app_refresh()

    def _on_toggle(self, _event=None):
        self._toggle()

    def _remove(self):
        item, edit = self._selected_edit()
        if edit is None:
            return
        self.app.profile.edits.remove(edit)
        self._refresh()

    def _clear_all(self):
        if not self.app.profile.edits:
            return
        if messagebox.askyesno("Clear All", "Remove all pending changes?"):
            self.app.profile.edits.clear()
            self._refresh()

    def _duplicate(self):
        _, edit = self._selected_edit()
        if edit is None:
            return
        duplicate = copy.deepcopy(edit)
        self.app.profile.edits.append(duplicate)
        self._refresh()

    def _move_up(self):
        item, edit = self._selected_edit()
        if edit is None:
            return
        index = self.app.profile.edits.index(edit)
        if index == 0:
            return
        edits = self.app.profile.edits
        edits[index - 1], edits[index] = edits[index], edits[index - 1]
        self._refresh()
        children = self.tree.get_children()
        self.tree.selection_set(children[index - 1])

    def _move_down(self):
        item, edit = self._selected_edit()
        if edit is None:
            return
        edits = self.app.profile.edits
        index = edits.index(edit)
        if index >= len(edits) - 1:
            return
        edits[index + 1], edits[index] = edits[index], edits[index + 1]
        self._refresh()
        children = self.tree.get_children()
        self.tree.selection_set(children[index + 1])

    def _app_refresh(self):
        total = len(self.app.profile.edits)
        enabled = sum(1 for e in self.app.profile.edits if e.enabled)
        self.count_var.set(f"{total} change(s) ({enabled} enabled)")
        self.app.refresh_changes_badge()

    def _save_preset(self):
        self._sync_name()
        self.app.save_profile()

    def _load_preset(self):
        self.app.load_profile()
        self.show()

    def _preview_lua(self):
        self._sync_name()
        self.app.preview_lua()

    def _build_mod(self):
        self._sync_name()
        self.app.build_mod()

    def _open_advanced(self):
        self.app.show_advanced()
