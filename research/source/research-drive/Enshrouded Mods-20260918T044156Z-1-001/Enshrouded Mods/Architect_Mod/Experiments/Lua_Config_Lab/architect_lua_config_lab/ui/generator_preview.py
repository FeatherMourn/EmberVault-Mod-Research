"""Generator preview: show the generated Lua and a human-readable summary."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class GeneratorPreview(tk.Toplevel):
    """Modal-ish preview window showing the Lua text and the edit summary."""

    def __init__(self, master, lua_text, summary):
        super().__init__(master)
        self.title("Generator Preview")
        self.geometry("760x680")

        ttk.Label(self, text="Generated Lua (deterministic)").pack(anchor="w", padx=8, pady=(8, 2))
        text = tk.Text(self, wrap="none", height=26)
        text.insert("1.0", lua_text)
        text.configure(state="disabled")
        text.pack(fill="both", expand=True, padx=8)
        scroll = ttk.Scrollbar(self, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        text.pack(fill="both", expand=True, padx=8)

        ttk.Label(self, text="Modification Summary").pack(anchor="w", padx=8, pady=(8, 2))
        summary_box = tk.Text(self, wrap="none", height=12)
        summary_box.insert("1.0", summary)
        summary_box.configure(state="disabled")
        summary_box.pack(fill="both", expand=False, padx=8, pady=(0, 8))

        ttk.Button(self, text="Close", command=self.destroy).pack(pady=4)
