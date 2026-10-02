"""Category view: human-readable resource cards for one category."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..core.display import access_level_label


class _ScrollableCards(ttk.Frame):
    """A vertically scrollable container of card frames."""

    def __init__(self, master):
        super().__init__(master)
        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        self.scroll = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        self.inner = ttk.Frame(self.canvas)
        self._window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._window, width=event.width)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        for child in self.inner.winfo_children():
            child.destroy()


class CategoryView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.category = None

        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Button(top, text="< Back", command=lambda: app.show_home()).pack(side="left")
        self.title_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.title_var,
                  font=("Segoe UI", 13, "bold")).pack(side="left", padx=8)

        self.cards = _ScrollableCards(self)
        self.cards.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def show(self, category):
        self.category = category
        self.title_var.set(category.upper())
        self.cards.clear()
        entries = self.app.catalog.entries_in_category(category)
        entries = sorted(entries, key=lambda e: e.friendly_name.lower())
        for entry in entries:
            self._add_card(entry)

    def _add_card(self, entry):
        card = ttk.Frame(self.cards.inner, relief="solid", borderwidth=1)
        card.pack(fill="x", padx=4, pady=4)

        head = ttk.Frame(card)
        head.pack(fill="x", padx=8, pady=(6, 0))
        ttk.Label(head, text=entry.friendly_name,
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        if entry.access_level == "ADVANCED":
            ttk.Label(head, text="Advanced", foreground="#a60").pack(side="left", padx=6)
        if entry.friendly_controls_available:
            ttk.Label(head, text="\u2699 friendly controls",
                      foreground="#06a").pack(side="left", padx=6)

        ttk.Label(card, text=entry.description, wraplength=640,
                  justify="left", foreground="#333").pack(fill="x", padx=8, pady=2)

        actions = ttk.Frame(card)
        actions.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(actions, text="Open",
                   command=lambda rt=entry.resource_type: self.app.show_resource(rt)
                   ).pack(side="left")
        ttk.Button(actions, text="Browse Raw Fields",
                   command=lambda rt=entry.resource_type: self.app.show_advanced(rt)
                   ).pack(side="left", padx=6)
        ttk.Label(actions, text=entry.resource_type,
                  foreground="#888").pack(side="right")
