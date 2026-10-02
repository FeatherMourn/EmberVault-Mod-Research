"""Resource view: friendly overview of one resource, with optional controls."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from ..core.display import friendly_status
from ..core.field_paths import resolve_path


class ResourceView(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.resource_type = None
        self._control_widgets = {}
        self._back_target = None
        self._build()

    def _build(self):
        top = ttk.Frame(self)
        top.pack(fill="x", padx=12, pady=(12, 4))
        self.back_btn = ttk.Button(top, text="< Back", command=self._back)
        self.back_btn.pack(side="left")
        self.title_var = tk.StringVar(value="")
        ttk.Label(top, textvariable=self.title_var,
                  font=("Segoe UI", 13, "bold")).pack(side="left", padx=8)

        body = ttk.Frame(self)
        body.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.desc_var = tk.StringVar(value="")
        ttk.Label(body, textvariable=self.desc_var, wraplength=720,
                  justify="left").pack(anchor="w", pady=2)

        self.status_var = tk.StringVar(value="")
        ttk.Label(body, textvariable=self.status_var,
                  foreground="#555").pack(anchor="w", pady=2)

        # Friendly controls section
        self.controls_label = ttk.Label(body, text="Friendly controls",
                                        font=("Segoe UI", 11, "bold"))
        self.controls_frame = ttk.Frame(body)
        self.no_controls_var = tk.StringVar(value="")
        self.no_controls_label = ttk.Label(body, textvariable=self.no_controls_var,
                                           foreground="#777")

        # Technical details (expandable)
        self.tech_toggle_var = tk.StringVar(value="Show Technical Details")
        self.tech_toggle = ttk.Checkbutton(
            body, textvariable=self.tech_toggle_var, command=self._toggle_tech)
        self.tech_frame = ttk.LabelFrame(body, text="Technical Details")
        self.tech_text = tk.StringVar(value="")
        ttk.Label(self.tech_frame, textvariable=self.tech_text, justify="left",
                  foreground="#333").pack(anchor="w", padx=8, pady=6)

        actions = ttk.Frame(body)
        actions.pack(fill="x", pady=8)
        ttk.Button(actions, text="Browse Raw Fields (Advanced Editor)",
                   command=self._browse_raw).pack(side="left")

    # -- lifecycle -----------------------------------------------------------

    def show(self, resource_type, back=None):
        self.resource_type = resource_type
        self._back_target = back
        self._control_widgets = {}

        catalog = self.app.catalog
        entry = catalog.get(resource_type) if catalog else None
        lab = self.app.lab

        if entry:
            self.title_var.set(entry.friendly_name)
            self.desc_var.set(entry.description)
            status_bits = ["Status: Schema available"]
            if entry.access_level == "ADVANCED":
                status_bits.append("Advanced reflected resource")
            self.status_var.set("  |  ".join(status_bits))
        else:
            self.title_var.set(resource_type)
            self.desc_var.set("")
            self.status_var.set("Status: Schema available")

        # Field/class info
        lua_class = lab.class_for_resource_type(resource_type)
        fields = lab.fields_of(resource_type)
        tags = ", ".join(entry.tags) if entry else ""
        self.tech_text.set(
            "Resource: %s\nReflected class: %s\nDirect fields: %d\nTags: %s"
            % (resource_type, lua_class or "(unknown)", len(fields), tags or "(none)"))
        self._hide_tech()

        # Friendly controls
        self._build_controls(resource_type)

    def _build_controls(self, resource_type):
        for child in self.controls_frame.winfo_children():
            child.destroy()
        controls = []
        if self.app.controls is not None:
            controls = [c for c in self.app.controls.controls
                        if c.resource_type == resource_type]

        if not controls:
            self.controls_label.pack_forget()
            self.controls_frame.pack_forget()
            self.no_controls_var.set(
                "No friendly controls yet for this resource. Use "
                "\"Browse Raw Fields\" to edit reflected fields directly.")
            self.no_controls_label.pack(anchor="w", pady=4)
            return

        self.no_controls_label.pack_forget()
        self.controls_label.pack(anchor="w", pady=(8, 2))
        self.controls_frame.pack(fill="x")
        for control in controls:
            self._add_control_row(control)

    def _add_control_row(self, control):
        row = ttk.Frame(self.controls_frame, relief="solid", borderwidth=1)
        row.pack(fill="x", padx=2, pady=4)

        head = ttk.Frame(row)
        head.pack(fill="x", padx=8, pady=(6, 0))
        ttk.Label(head, text=control.name,
                  font=("Segoe UI", 10, "bold")).pack(side="left")
        ttk.Label(head, text=friendly_status(control.status),
                  foreground="#a60").pack(side="left", padx=8)

        ttk.Label(row, text=control.description, wraplength=640,
                  justify="left", foreground="#333").pack(fill="x", padx=8, pady=2)

        input_frame = ttk.Frame(row)
        input_frame.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Label(input_frame, text="Value:").pack(side="left")

        var = tk.StringVar()
        widget = self._make_input_widget(input_frame, control, var)
        widget.pack(side="left", padx=6)
        self._control_widgets[control.id] = var

        ttk.Button(input_frame, text="Add change",
                   command=lambda c=control: self._apply_control(c)).pack(side="left", padx=6)
        ttk.Label(input_frame, text="Restart required",
                  foreground="#888").pack(side="left", padx=6)

    def _make_input_widget(self, parent, control, var):
        ui_type = control.ui_type
        if ui_type == "bool":
            var.set("false")
            return ttk.Combobox(parent, textvariable=var, state="readonly",
                                values=("true", "false"), width=8)
        if ui_type == "enum":
            choices = self._enum_choices(control)
            return ttk.Combobox(parent, textvariable=var, values=choices, width=24)
        # number / string / guid
        return ttk.Entry(parent, textvariable=var, width=24)

    def _enum_choices(self, control):
        lab = self.app.lab
        lua_class = lab.class_for_resource_type(control.resource_type)
        if not lua_class:
            return []
        resolution = resolve_path(lab.schema(), lua_class, control.path)
        if resolution.ok and resolution.choices:
            return resolution.choices
        return []

    def _apply_control(self, control):
        var = self._control_widgets.get(control.id)
        if var is None:
            return
        raw = var.get()
        if control.ui_type == "bool":
            value = (str(raw).strip().lower() == "true")
        else:
            value = raw
        edit, error = self.app.lab.make_control_edit(control, value)
        if error:
            messagebox.showwarning("Invalid value", error)
            return
        self.app.profile.edits.append(edit)
        self.app.refresh_changes_badge()
        self.app.set_status("Added change: %s = %r" % (control.name, edit.value))
        messagebox.showinfo("Change added",
                            "%s set to %r.\n\nFind it under My Changes."
                            % (control.name, edit.value))

    # -- technical details ---------------------------------------------------

    def _toggle_tech(self):
        if self.tech_frame.winfo_ismapped():
            self._hide_tech()
        else:
            self._show_tech()

    def _show_tech(self):
        self.tech_toggle_var.set("Hide Technical Details")
        self.tech_frame.pack(fill="x", pady=4)

    def _hide_tech(self):
        self.tech_toggle_var.set("Show Technical Details")
        self.tech_frame.pack_forget()

    # -- navigation ----------------------------------------------------------

    def _browse_raw(self):
        self.app.show_advanced(self.resource_type)

    def _back(self):
        if self._back_target:
            self._back_target()
        else:
            self.app.show_home()
