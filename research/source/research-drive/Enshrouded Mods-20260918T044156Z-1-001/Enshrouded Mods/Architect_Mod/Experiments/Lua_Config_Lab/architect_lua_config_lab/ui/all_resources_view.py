"""All Resources view: complete alphabetical list of the 131 roots."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class AllResourcesView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._rows = []  # parallel list of resource_type per tree row
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Button(top, text="< Back", command=lambda: self.app.show_home()).pack(side="left")
        ttk.Label(top, text="All Resources",
                  font=("Segoe UI", 13, "bold")).pack(side="left", padx=8)

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=12, pady=4)
        ttk.Label(bar, text="Filter:").pack(side="left")
        self.filter_var = tk.StringVar()
        self.filter_var.trace_add("write", lambda *_: self._refresh())
        ttk.Entry(bar, textvariable=self.filter_var).pack(side="left", fill="x",
                                                          expand=True, padx=6)
        self.count_var = tk.StringVar(value="")
        ttk.Label(bar, textvariable=self.count_var, foreground="#555").pack(side="left")

        columns = ("friendly", "category", "family", "status")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="browse")
        self.tree.heading("friendly", text="Friendly Name")
        self.tree.heading("category", text="Category")
        self.tree.heading("family", text="Technical Family")
        self.tree.heading("status", text="Status")
        self.tree.column("friendly", width=220)
        self.tree.column("category", width=200)
        self.tree.column("family", width=240)
        self.tree.column("status", width=90, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=12, pady=4)
        self.tree.bind("<Double-1>", self._on_open)

        scroll = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)

        ttk.Button(self, text="Open Selected", command=self._on_open).pack(pady=4)

    def show(self):
        self.filter_var.set("")
        self._refresh()

    def _refresh(self):
        catalog = self.app.catalog
        total = len(catalog.entries) if catalog else 0
        self.tree.delete(*self.tree.get_children())
        self._rows = []
        query = self.filter_var.get().strip().lower()
        entries = sorted(catalog.entries, key=lambda e: e.friendly_name.lower()) if catalog else []
        shown = 0
        for entry in entries:
            if query and query not in entry.friendly_name.lower() \
                    and query not in entry.family.lower() \
                    and query not in entry.primary_category.lower():
                continue
            status = "Advanced" if entry.access_level == "ADVANCED" else "Standard"
            self.tree.insert("", "end", values=(
                entry.friendly_name, entry.primary_category, entry.family, status))
            self._rows.append(entry.resource_type)
            shown += 1
        self.count_var.set("%d / %d resources cataloged" % (shown, total))

    def _on_open(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        if index < len(self._rows):
            self.app.show_resource(self._rows[index])
