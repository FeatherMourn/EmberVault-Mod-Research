"""Resource browser: searchable list of the KFC resource roots."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class ResourceBrowser(ttk.Frame):
    """Search box + list of resource root families."""

    def __init__(self, master, on_select=None):
        super().__init__(master)
        self._on_select = on_select
        self._entries = []

        ttk.Label(self, text="Resource Browser").pack(anchor="w", padx=4, pady=(4, 0))

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search_changed)
        search = ttk.Entry(self, textvariable=self.search_var)
        search.pack(fill="x", padx=4, pady=4)

        self.listbox = tk.Listbox(self, exportselection=False)
        self.listbox.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

    def set_entries(self, entries):
        """``entries`` is a list of dicts with ``family`` and ``resource_type``."""
        self._entries = list(entries)
        self._refresh("")

    def _refresh(self, query):
        self.listbox.delete(0, tk.END)
        query = (query or "").strip().lower()
        for entry in self._entries:
            if not query or query in entry["family"].lower() or query in entry["resource_type"].lower():
                self.listbox.insert(tk.END, entry["family"])
                self.listbox.insert(tk.END, "    " + entry["resource_type"])

    def _on_search_changed(self, *_):
        self._refresh(self.search_var.get())

    def _on_listbox_select(self, *_):
        if not self._on_select:
            return
        selection = self.listbox.curselection()
        if not selection:
            return
        # Each family occupies two rows (family + resource type); map back.
        row = selection[0]
        entry_index = row // 2
        if entry_index < len(self._entries):
            self._on_select(self._entries[entry_index])
