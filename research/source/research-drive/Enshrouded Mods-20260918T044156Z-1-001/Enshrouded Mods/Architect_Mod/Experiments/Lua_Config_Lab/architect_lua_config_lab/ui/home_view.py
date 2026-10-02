"""Home / catalog view: the default screen."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..core.resource_catalog import CATEGORIES


class HomeView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._build()

    def _build(self):
        header = ttk.Frame(self)
        header.pack(fill="x", padx=16, pady=(16, 4))
        ttk.Label(header, text="Enshrouded Lua Config Lab",
                  font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(header,
                  text="Configure game resources before Enshrouded starts.",
                  foreground="#555").pack(anchor="w")

        search = ttk.Frame(self)
        search.pack(fill="x", padx=16, pady=8)
        ttk.Label(search, text="Search settings and resources...").pack(anchor="w")
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search, textvariable=self.search_var)
        entry.pack(fill="x", pady=2)
        entry.bind("<Return>", self._on_search)
        ttk.Button(search, text="Search", command=self._on_search).pack(anchor="e", pady=2)

        ttk.Label(self, text="Categories", font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=16, pady=(8, 2))

        list_frame = ttk.Frame(self)
        list_frame.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        self.category_list = tk.Listbox(list_frame, exportselection=False,
                                        font=("Segoe UI", 10))
        self.category_list.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(list_frame, orient="vertical",
                               command=self.category_list.yview)
        self.category_list.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.category_list.bind("<Double-1>", self._on_category)
        self.category_list.bind("<Return>", self._on_category)

        for category in CATEGORIES:
            self.category_list.insert(tk.END, category)

        btn_row = ttk.Frame(self)
        btn_row.pack(fill="x", padx=16, pady=4)
        ttk.Button(btn_row, text="Open Selected Category",
                   command=self._on_category).pack(side="left")
        ttk.Button(btn_row, text="All Resources (131)",
                   command=lambda: self.app.show_all_resources()).pack(side="left", padx=8)

    def show(self):
        self.search_var.set("")

    def _on_search(self, _event=None):
        query = self.search_var.get().strip()
        if query:
            self.app.show_search(query)

    def _on_category(self, _event=None):
        selection = self.category_list.curselection()
        if not selection:
            return
        category = self.category_list.get(selection[0])
        self.app.show_category(category)
