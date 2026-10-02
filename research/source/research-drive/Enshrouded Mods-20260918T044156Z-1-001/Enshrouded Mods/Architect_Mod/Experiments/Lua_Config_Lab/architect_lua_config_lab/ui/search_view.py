"""Search view: global search results across friendly + technical metadata."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class SearchView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self._results = []
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Button(top, text="< Back", command=lambda: self.app.show_home()).pack(side="left")
        ttk.Label(top, text="Search", font=("Segoe UI", 13, "bold")).pack(side="left", padx=8)

        bar = ttk.Frame(self)
        bar.pack(fill="x", padx=12, pady=4)
        self.query_var = tk.StringVar()
        entry = ttk.Entry(bar, textvariable=self.query_var)
        entry.pack(side="left", fill="x", expand=True)
        entry.bind("<Return>", lambda _e: self.show(self.query_var.get()))
        ttk.Button(bar, text="Search",
                   command=lambda: self.show(self.query_var.get())).pack(side="left", padx=6)

        self.count_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.count_var, foreground="#555").pack(
            anchor="w", padx=12)

        self.list_frame = ttk.Frame(self)
        self.list_frame.pack(fill="both", expand=True, padx=12, pady=8)
        self.listbox = tk.Listbox(self.list_frame, exportselection=False,
                                  font=("Segoe UI", 10))
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(self.list_frame, orient="vertical",
                               command=self.listbox.yview)
        self.listbox.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.listbox.bind("<Double-1>", self._on_open)
        ttk.Button(self, text="Open Selected", command=self._on_open).pack(pady=4)

    def show(self, query):
        self.query_var.set(query)
        self.listbox.delete(0, tk.END)
        self._results = self.app.lab.search_catalog(query)
        self.count_var.set("%d result(s) for %r" % (len(self._results), query))
        for match in self._results:
            entry = match["entry"]
            line = "%s   [%s]" % (entry.friendly_name, entry.primary_category)
            self.listbox.insert(tk.END, line)
            self.listbox.insert(tk.END, "      technical: %s" % entry.family)

    def _on_open(self, _event=None):
        selection = self.listbox.curselection()
        if not selection:
            return
        index = selection[0] // 2
        if index < len(self._results):
            entry = self._results[index]["entry"]
            self.app.show_resource(entry.resource_type)
