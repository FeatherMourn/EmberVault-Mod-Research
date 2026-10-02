"""Edit panel: enter and validate a value for a selected field path."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..core.field_paths import resolve_path


class EditPanel(ttk.Frame):
    """Form for describing a single edit (field + value + target)."""

    def __init__(self, master):
        super().__init__(master)
        self._lab = None
        self._resource_type = None
        self._path = None
        self._choices = []

        self._build()

    def _build(self):
        ttk.Label(self, text="Edit Panel").pack(anchor="w", padx=4, pady=(4, 0))

        # Field info
        info = ttk.LabelFrame(self, text="Field Information")
        info.pack(fill="x", padx=4, pady=4)

        self.info_var = tk.StringVar(value="(no field selected)")
        ttk.Label(info, textvariable=self.info_var, wraplength=420, justify="left").pack(
            anchor="w", padx=4, pady=2)

        self.evidence_var = tk.StringVar(value="SCHEMA-VALIDATED / RUNTIME EFFECT UNPROVEN")
        ttk.Label(info, textvariable=self.evidence_var, foreground="#777").pack(
            anchor="w", padx=4, pady=2)

        # Path
        path_frame = ttk.Frame(self)
        path_frame.pack(fill="x", padx=4, pady=2)
        ttk.Label(path_frame, text="Field path:").pack(side="left")
        self.path_var = tk.StringVar()
        ttk.Entry(path_frame, textvariable=self.path_var).pack(
            side="left", fill="x", expand=True, padx=4)

        # Value
        value_frame = ttk.Frame(self)
        value_frame.pack(fill="x", padx=4, pady=2)
        ttk.Label(value_frame, text="New value:").pack(side="left")
        self.value_var = tk.StringVar()
        self.value_entry = ttk.Entry(value_frame, textvariable=self.value_var)
        self.value_entry.pack(side="left", fill="x", expand=True, padx=4)
        self.value_combo = ttk.Combobox(value_frame, textvariable=self.value_var, state="readonly")

        # Target mode
        target_frame = ttk.Frame(self)
        target_frame.pack(fill="x", padx=4, pady=2)
        ttk.Label(target_frame, text="Target:").pack(side="left")
        self.mode_var = tk.StringVar(value="first")
        ttk.Combobox(
            target_frame, textvariable=self.mode_var, state="readonly",
            values=("first", "all", "match"), width=8,
        ).pack(side="left", padx=4)

        # Selector (match mode)
        selector = ttk.LabelFrame(self, text="Selector (MATCH mode)")
        selector.pack(fill="x", padx=4, pady=4)
        row = ttk.Frame(selector)
        row.pack(fill="x", padx=4, pady=2)
        ttk.Label(row, text="Field:").pack(side="left")
        self.selector_field_var = tk.StringVar()
        ttk.Entry(row, textvariable=self.selector_field_var).pack(
            side="left", fill="x", expand=True, padx=4)
        row2 = ttk.Frame(selector)
        row2.pack(fill="x", padx=4, pady=2)
        ttk.Label(row2, text="Equals:").pack(side="left")
        self.selector_value_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.selector_value_var).pack(
            side="left", fill="x", expand=True, padx=4)

        # Optional precondition
        pre = ttk.LabelFrame(self, text="Precondition (optional)")
        pre.pack(fill="x", padx=4, pady=4)
        row3 = ttk.Frame(pre)
        row3.pack(fill="x", padx=4, pady=2)
        ttk.Label(row3, text="Expected original:").pack(side="left")
        self.expected_var = tk.StringVar()
        ttk.Entry(row3, textvariable=self.expected_var).pack(
            side="left", fill="x", expand=True, padx=4)

        # Evidence state
        ev = ttk.Frame(self)
        ev.pack(fill="x", padx=4, pady=2)
        ttk.Label(ev, text="Evidence:").pack(side="left")
        self.evidence_state_var = tk.StringVar(value="EXPERIMENTAL")
        ttk.Combobox(
            ev, textvariable=self.evidence_state_var, state="readonly", width=22,
            values=("SCHEMA_VALIDATED", "EXPERIMENTAL", "PROVEN_STARTUP_EFFECT",
                    "DISPROVEN", "UNSUPPORTED"),
        ).pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.status_var, foreground="#a00",
                  wraplength=420, justify="left").pack(anchor="w", padx=4, pady=4)

    # -- context -------------------------------------------------------------

    def set_lab(self, lab):
        self._lab = lab

    def set_context(self, resource_type, path):
        self._resource_type = resource_type
        self._path = path
        self.path_var.set(path or "")
        self.status_var.set("")
        self._refresh_field_info()

    def _refresh_field_info(self):
        if self._lab is None or not self._resource_type or not self._path:
            return
        lua_class = self._lab.class_for_resource_type(self._resource_type)
        if not lua_class:
            return
        resolution = resolve_path(self._lab.schema(), lua_class, self._path)
        if not resolution.ok:
            self.info_var.set("path: %s\n(resolution: %s)" % (self._path, resolution.error))
            self._show_entry_widget()
            return

        leaf = resolution.leaf_type
        lines = [
            "field path: %s" % resolution.path,
            "declared type: %s" % leaf.raw,
            "root resource type: %s" % self._resource_type,
        ]
        if resolution.choices:
            lines.append("enum choices: %s" % ", ".join(resolution.choices))
        lines.append("kind: %s" % resolution.kind_label)
        lines.append("editable: %s" % ("yes" if resolution.editable else "no (MVP)"))
        lines.append("evidence: %s" % self.evidence_var.get())
        self.info_var.set("\n".join(lines))
        self.evidence_var.set("SCHEMA-VALIDATED / RUNTIME EFFECT UNPROVEN")

        self._choices = resolution.choices
        if resolution.choices:
            self._show_combo_widget()
        else:
            self._show_entry_widget()

    def _show_entry_widget(self):
        self.value_combo.pack_forget()
        self.value_entry.pack(side="left", fill="x", expand=True, padx=4)

    def _show_combo_widget(self):
        self.value_entry.pack_forget()
        self.value_combo["values"] = self._choices
        self.value_combo.pack(side="left", fill="x", expand=True, padx=4)
        if self.value_var.get() not in self._choices:
            self.value_var.set(self._choices[0] if self._choices else "")

    # -- value coercion ------------------------------------------------------

    def _coerce_value(self, text, leaf_type):
        """Coerce raw text into a Python value using the schema type."""
        from ..core.validation import validate_value

        result = validate_value(self._lab.schema(), leaf_type, text)
        if not result.ok:
            return None, result.error
        return result.value, None

    # -- collect -------------------------------------------------------------

    def build_edit(self):
        """Build a validated Edit from the form; returns ``(edit, error)``."""
        if self._lab is None or not self._resource_type:
            return None, "no resource selected"

        path = self.path_var.get().strip()
        if not path:
            return None, "no field path"

        resolution = self._lab.resolve(self._resource_type, path)
        if not resolution.ok:
            return None, resolution.error
        if not resolution.editable:
            return None, "field %r is not editable by the MVP (%s)" % (
                path, resolution.kind_label)

        value_text = self.value_var.get()
        value, value_error = self._coerce_value(value_text, resolution.leaf_type)
        if value_error:
            return None, "value: " + value_error

        mode = self.mode_var.get()
        selector = None
        if mode == "match":
            selector_field = self.selector_field_var.get().strip()
            if not selector_field:
                return None, "MATCH target requires a selector field"
            selector_value_text = self.selector_value_var.get()
            # Resolve selector field and coerce its value.
            selector_resolution = self._lab.resolve(self._resource_type, selector_field)
            if not selector_resolution.ok:
                return None, "selector: " + selector_resolution.error
            if not selector_resolution.editable:
                return None, "selector field %r is not a scalar" % selector_field
            sel_value, sel_error = self._coerce_value(
                selector_value_text, selector_resolution.leaf_type)
            if sel_error:
                return None, "selector value: " + sel_error
            selector = {
                "field": selector_resolution.path,
                "operator": "eq",
                "value": sel_value,
            }

        expected = None
        expected_text = self.expected_var.get().strip()
        if expected_text:
            exp_value, exp_error = self._coerce_value(expected_text, resolution.leaf_type)
            if exp_error:
                return None, "expected original: " + exp_error
            expected = exp_value

        edit, error = self._lab.make_edit(
            resource_type=self._resource_type,
            path=resolution.path,
            value=value,
            mode=mode,
            selector=selector,
            evidence_state=self.evidence_state_var.get(),
            expected_original=expected,
        )
        if error:
            return None, error
        self.status_var.set("")
        return edit, None
