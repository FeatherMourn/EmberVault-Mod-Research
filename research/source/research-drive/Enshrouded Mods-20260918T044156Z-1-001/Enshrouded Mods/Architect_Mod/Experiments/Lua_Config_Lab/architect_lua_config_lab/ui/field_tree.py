"""Field tree: lazy nested field browser for a selected resource root."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ..core.field_paths import resolve_path


def _field_label(name, type_raw):
    return "%s : %s" % (name, type_raw)


class FieldTree(ttk.Frame):
    """Treeview of the fields of a selected resource, expandable on demand."""

    def __init__(self, master, on_select=None):
        super().__init__(master)
        self._on_select = on_select
        self._lab = None
        self._root_class = None
        self._path_by_id = {}

        ttk.Label(self, text="Field Tree").pack(anchor="w", padx=4, pady=(4, 0))

        self.tree = ttk.Treeview(self, columns=("path", "type"), show="tree headings")
        self.tree.heading("#0", text="Field")
        self.tree.column("#0", width=260)
        self.tree.pack(fill="both", expand=True, padx=4, pady=4)

        self.tree.bind("<<TreeviewOpen>>", self._on_open)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_internal)

    def set_lab(self, lab):
        self._lab = lab

    def show_resource(self, resource_type):
        if self._lab is None:
            return
        lua_class = self._lab.class_for_resource_type(resource_type)
        if not lua_class:
            self.clear()
            return
        self._root_class = lua_class
        self._path_by_id = {}
        self.tree.delete(*self.tree.get_children())
        self._populate_children("", lua_class, "")

    def clear(self):
        self._path_by_id = {}
        self.tree.delete(*self.tree.get_children())

    # -- child computation ---------------------------------------------------

    def _populate_children(self, parent_item, class_name, base_path):
        cls = self._lab.schema().get_class(class_name)
        if cls is None:
            return
        for field in cls.fields:
            path = (base_path + "." + field.name) if base_path else field.name
            resolution = resolve_path(self._lab.schema(), self._root_class, path)
            leaf_kind = resolution.kind_label if resolution.ok else "unknown"
            label = _field_label(field.name, field.declared_type)
            item = self.tree.insert(
                parent_item, "end", text=label,
                values=(path, leaf_kind),
            )
            self._path_by_id[item] = path
            # Add a dummy child so the expand arrow appears if expandable.
            if self._is_expandable(path):
                self.tree.insert(item, "end")

    def _is_expandable(self, path):
        resolution = resolve_path(self._lab.schema(), self._root_class, path)
        if not resolution.ok:
            return False
        kind = resolution.leaf_type.kind
        if kind == "named" and resolution.leaf_type.name and \
                self._lab.schema().has_class(resolution.leaf_type.name):
            return True
        if kind in ("array", "static_array"):
            return True
        return False

    def _on_open(self, event):
        item = self.tree.focus()
        path = self._path_by_id.get(item)
        if not path:
            return
        # Remove dummy children, then populate real children.
        children = self.tree.get_children(item)
        if children and not self.tree.get_children(children[0]):
            self.tree.delete(children[0])

        resolution = resolve_path(self._lab.schema(), self._root_class, path)
        if not resolution.ok:
            return
        kind = resolution.leaf_type.kind
        if kind == "named" and resolution.leaf_type.name and \
                self._lab.schema().has_class(resolution.leaf_type.name):
            self._populate_children(item, resolution.leaf_type.name, path)
        elif kind in ("array", "static_array"):
            self._populate_array_element(item, path, resolution)

    def _populate_array_element(self, item, path, resolution):
        element = resolution.leaf_type.inner
        if element is None:
            return
        child_path = path + "[1]"
        child_resolution = resolve_path(self._lab.schema(), self._root_class, child_path)
        leaf_kind = child_resolution.kind_label if child_resolution.ok else "unknown"
        label = "[1] : %s" % element.raw
        child = self.tree.insert(
            item, "end", text=label,
            values=(child_path, leaf_kind),
        )
        self._path_by_id[child] = child_path
        if self._is_expandable(child_path):
            self.tree.insert(child, "end")

    # -- selection -----------------------------------------------------------

    def _on_select_internal(self, *_):
        if not self._on_select:
            return
        selection = self.tree.selection()
        if not selection:
            return
        item = selection[0]
        path = self._path_by_id.get(item)
        if path is not None:
            self._on_select(path)

    def current_path(self):
        selection = self.tree.selection()
        if not selection:
            return None
        return self._path_by_id.get(selection[0])
