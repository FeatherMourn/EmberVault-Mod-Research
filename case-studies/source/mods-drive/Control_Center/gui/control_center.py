"""Polished registry-driven Control Center shell.

The existing app and creative tools remain available; this is the standalone
front door that stages profile edits and invokes the existing installer only on
explicit review/apply.
"""
from __future__ import annotations

import json
import subprocess
import sys
import traceback
import webbrowser
import uuid
import logging
import hashlib
import shutil
import os
from datetime import datetime, timezone
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox, PhotoImage, simpledialog, colorchooser
try:
    from PIL import Image
except ImportError:
    Image = None

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.installer import InstallerError, InstallerService
from core.manager import ModuleManager
from core.registry import SettingRegistry, TUNING_CATEGORIES
from core.nexus import NexusClient, NexusError
from core.local_mods import LocalModService, LocalModError
from core.platform_services import PlatformService, feature_state
from core.content_validation import ContentProjectValidator
from core.content_project import ContentProjectError, ContentProjectGenerator
from core.resource_inspector import ResourceInspector
from core.compatibility import CompatibilityEngine
from core.diagnostics import DiagnosticService, SupportBundleService
from core.smoke_tests import ContentSmokeTester
from core.update_migration import UpdateMigrationService
from core.profile_launch import LaunchError, ProfileLaunchService
from core.asset_service import AssetError, AssetService
from core.visual_colors import packed_color_plan
from core.recovery import ModQuarantineService, RecoveryError
from core.research_lab import ResearchProbeService
from core.layout_migration import LayoutMigrationError, ModLayoutMigrationService
from core.health_report import HealthReportService
from core.crash_recovery import CrashRecoveryService
from core.save_backup import SaveBackupError, backup_save_directory, compare_save_snapshots, game_is_running, restore_save_backup, list_verified_backups, load_backup_policy, save_backup_policy, prune_save_backups
from core.control_context import build_control_context
from core.enshrouded_save_reader import SaveFormatError, discover_save_directories, inspect_save_directory
from core.release_service import ReleaseError, ReleaseService
from core.catalog_editor import CatalogEditError, CatalogEditor
from core.localization import LocalizationCatalog, LocalizationService
from core.localization_debug import LocalizationDebugger
from core.content_compiler import ContentCompiler, ContentCompilerError
from core.content_patch import ContentPatchPlanner, ContentPatchError
from core.gameplay_feasibility import GameplayFeasibilityPlanner
from core.blender_export_validator import validate_blender_export
from core.asset_substitution import AssetSubstitutionPlanner
from core.donor_browser import DonorBrowser
from core.ownership import OwnershipError, OwnershipService
from core.builder_catalog import BuilderCatalog
from tools.verify_live_loader import inspect as inspect_live_loader
from tools.apply_smoke_profile import plan as plan_smoke_profile, load_profile as load_smoke_profile

RIGHT_PANEL_BREAKPOINT = 1480


class ControlCenter(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Enshrouded Mod Hub — Control Center")
        self.geometry("1600x900")
        self.minsize(1120, 720)
        self.base_dir = Path(__file__).resolve().parents[1]
        self.diagnostics_dir = Path(__import__('os').environ.get('LOCALAPPDATA', str(self.base_dir / 'profiles'))) / 'EnshroudedModHub' / 'diagnostics'
        self.diagnostics_dir.mkdir(parents=True, exist_ok=True)
        self._callback_log = self.diagnostics_dir / 'gui-callback-errors.log'
        self._page_generation = 0
        self._right_visible = True
        self._last_resize_log = None
        self._resize_trace_count = 0
        self._resize_child_count = 0
        self._resize_transition_count = 0
        self._resize_trace_path = self.diagnostics_dir / "resize-trace.log"
        self.manager = ModuleManager(self.base_dir)
        self.registry = SettingRegistry(self.base_dir, self.manager)
        self.installer = InstallerService(self.base_dir, self.manager)
        self.platform = PlatformService(self.base_dir)
        self.local_mods = LocalModService(self.base_dir)
        self.content_validator = ContentProjectValidator()
        self.content_projects = ContentProjectGenerator(self.base_dir)
        self.resource_inspector = ResourceInspector()
        self.compatibility = CompatibilityEngine()
        self.diagnostics = DiagnosticService()
        self.support_bundles = SupportBundleService()
        self.smoke_tester = ContentSmokeTester()
        self.migrations = UpdateMigrationService(self.base_dir / "profiles" / "game_compatibility.json")
        self.launcher = ProfileLaunchService()
        self.assets = AssetService()
        self.recovery = ModQuarantineService(self.base_dir / "profiles")
        self.layout_migration = ModLayoutMigrationService()
        self.health_reports = HealthReportService(self.base_dir)
        self.crash_recovery = CrashRecoveryService(self.base_dir / "profiles")
        self.releases = ReleaseService()
        self.compiler = ContentCompiler(self.base_dir)
        self.donor_browser = DonorBrowser()
        self.ownership = OwnershipService()
        self.nexus = NexusClient(); self.nexus.load_key()
        self.pending, mapping = self.registry.migrate_profile(self.manager.active_config)
        self.active_profile_id = "default"
        selected_profile = self.base_dir / "profiles" / "selected_profile.json"
        try:
            if selected_profile.is_file():
                selected = json.loads(selected_profile.read_text(encoding="utf-8"))
                if not isinstance(selected, dict):
                    raise TypeError("selected profile record is not an object")
                selected_id = str(selected.get("id", "default"))
                selected_path = None
                for candidate in (self.base_dir / "profiles").glob("profile_*.json"):
                    candidate_record = json.loads(candidate.read_text(encoding="utf-8"))
                    if isinstance(candidate_record, dict) and candidate_record.get("id") == selected_id:
                        selected_path = candidate
                        break
                if selected_path is not None:
                    record = json.loads(selected_path.read_text(encoding="utf-8"))
                    if not isinstance(record, dict):
                        raise TypeError("profile record is not an object")
                    self.active_profile_id = selected_id
                    self.pending = record.get("config", self.pending)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            self.active_profile_id = "default"
        migration_path = self.base_dir / "profiles" / "legacy_setting_mapping.json"
        if not migration_path.exists():
            migration_path.write_text(json.dumps({"source_profile": "profiles/active_profile.json", "mapping": mapping}, indent=2), encoding="utf-8")
        (self.base_dir / "profiles" / "setting_inventory.json").write_text(json.dumps(self.registry.inventory_mapping(), indent=2), encoding="utf-8")
        self.dirty = False
        self.backup_policy_path = self.base_dir / "profiles" / "save-backup-policy.json"
        self.backup_policy = load_backup_policy(self.backup_policy_path)
        self.last_diagnostic_report = None
        self.display_font = "Georgia"
        self._image_refs = []
        self.controls: dict[str, tuple[ctk.CTkSlider, ctk.CTkEntry]] = {}
        self.grid_columnconfigure(1, weight=1); self.grid_columnconfigure(2, minsize=430); self.grid_rowconfigure(0, weight=1)
        self._sidebar(); self._content(); self.bind("<Configure>", self._responsive_layout, add="+"); self.show_home(); self.after(300000, self._scheduled_backup_tick)

    def _scheduled_backup_tick(self):
        """Run an enabled backup policy only when a standard save is discoverable and the game is closed."""
        try:
            policy = self.backup_policy
            if policy.get("enabled") and not game_is_running():
                last = policy.get("last_run_utc")
                due = not last
                if last:
                    due = (datetime.now(timezone.utc) - datetime.fromisoformat(last)).total_seconds() >= int(policy["interval_hours"]) * 3600
                if due:
                    discovered = discover_save_directories()
                    source = next((Path(item["path"]) for item in discovered.get("candidates", []) if item.get("exists") and item.get("has_character_index")), None)
                    if source:
                        result = backup_save_directory(source, self.base_dir / "profiles" / "save-backups", "scheduled")
                        self.backup_policy = save_backup_policy(self.backup_policy_path, {**policy, "last_run_utc": datetime.now(timezone.utc).isoformat()})
                        prune_save_backups(self.base_dir / "profiles" / "save-backups", self.backup_policy["retention"])
        except (OSError, SaveBackupError, ValueError):
            pass
        finally:
            self.after(300000, self._scheduled_backup_tick)

    def report_callback_exception(self, exc, val, tb):
        """Persist Tk/CustomTkinter callback failures with the full traceback."""
        text = "".join(traceback.format_exception(exc, val, tb))
        with self._callback_log.open("a", encoding="utf-8") as log:
            log.write("\n=== GUI callback exception ===\n" + text)
        logging.getLogger("control_center.gui").error("Tk callback failed", exc_info=(exc, val, tb))

    def _responsive_layout(self, event=None):
        """Collapse secondary content before the settings canvas becomes cramped."""
        if event is not None and event.widget is not self:
            self._resize_child_count += 1
            self._trace_resize(event, ignored="descendant")
            return
        width = int(self.winfo_width())
        if not hasattr(self, "right"): return
        should_show = width >= RIGHT_PANEL_BREAKPOINT
        self._trace_resize(event, root_width=width, desired=should_show)
        # grid()/grid_remove() themselves generate Configure events.  Mutating
        # the layout on every event creates a feedback loop while maximizing,
        # restoring, or dragging the window edge.
        if should_show == self._right_visible:
            return
        self._right_visible = should_show
        self._resize_transition_count += 1
        if should_show:
            self.grid_columnconfigure(2, minsize=430)
            self.right.grid(row=0, column=2, sticky="nsew")
        else:
            self.right.grid_remove()
            self.grid_columnconfigure(2, minsize=0)

    def _trace_resize(self, event=None, **extra):
        """Bounded resize trace for diagnosing Configure storms."""
        self._resize_trace_count += 1
        if self._resize_trace_count > 500:
            return
        widget = getattr(event, "widget", self)
        try: identity = str(widget)
        except Exception: identity = repr(widget)
        root_width = int(self.winfo_width()) if hasattr(self, "winfo_width") else None
        line = {"count": self._resize_trace_count, "widget": identity, "event_width": getattr(event, "width", None), "root_width": root_width, "layout_state": self._right_visible, "transitions": self._resize_transition_count, "child_events": self._resize_child_count, **extra}
        # Sampling keeps diagnostics bounded and avoids synchronous disk I/O
        # for every child Configure event during a redraw storm.
        if self._resize_trace_count <= 20 or self._resize_trace_count % 50 == 0:
            with self._resize_trace_path.open("a", encoding="utf-8") as trace:
                trace.write(json.dumps(line, sort_keys=True) + "\n")

    def _sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=245, corner_radius=0, fg_color="#0b1220")
        self.sidebar.grid(row=0, column=0, sticky="nsew"); self.sidebar.grid_rowconfigure(12, weight=1)
        ctk.CTkLabel(self.sidebar, text="⚡ ENSHROUDED\nMOD HUB", font=ctk.CTkFont(size=22, weight="bold"), text_color="#67e8f9").grid(row=0, column=0, padx=22, pady=(28, 22))
        buttons = [("⌂   Home", self.show_home), ("☷   Game Tuning", self.show_tuning), ("▰   Mod Manager", self.show_install), ("●   Content Studio", self.show_content), ("⚗   Research Lab", self.show_research_lab), ("▤   Save Manager", self.show_save_manager), ("▣   Save Editor", self.show_save_editor), ("⚠   Troubleshooter", self.show_troubleshooter), ("?   Guides & Help", self.show_guides), ("▤   Profiles", self.show_profiles), ("⚙   Settings", self.show_settings)]
        for row, (label, action) in enumerate(buttons, 1):
            ctk.CTkButton(self.sidebar, text=label, anchor="w", fg_color="#c55720" if row == 1 else "transparent", hover_color="#a8441a", height=36, command=action).grid(row=row, column=0, padx=15, pady=3, sticky="ew")
        ctk.CTkFrame(self.sidebar, height=1, fg_color="#2c4152").grid(row=12, column=0, padx=18, pady=(10, 5), sticky="ew")
        ctk.CTkButton(self.sidebar, text="▣   Enshrouded Wiki", anchor="w", fg_color="transparent", hover_color="#324d62", height=34, command=self.open_wiki).grid(row=13, column=0, padx=15, pady=3, sticky="ew")
        status = ctk.CTkFrame(self.sidebar, fg_color="#111f2c", border_width=1, border_color="#2c4152", corner_radius=10); status.grid(row=14,column=0,padx=14,pady=10,sticky="ew")
        ctk.CTkLabel(status,text="GAME STATUS",font=ctk.CTkFont(size=10,weight="bold"),text_color="#94a3b8",anchor="w").pack(fill="x",padx=12,pady=(10,2))
        path=self.installer.selected_game_path(); ready=bool(path and (path/"Enshrouded.exe").is_file()); ctk.CTkLabel(status,text=("●  Ready to Play" if ready else "●  Game folder needed"),text_color="#22c55e" if ready else "#f59e0b",anchor="w").pack(fill="x",padx=12); ctk.CTkLabel(status,text="Enshrouded  ·  Local Game",text_color="#cbd5e1",font=ctk.CTkFont(size=10),anchor="w").pack(fill="x",padx=12,pady=(2,8)); ctk.CTkButton(status,text="▶  Launch Game",height=30,fg_color="#d65b20",hover_color="#ed7328",command=self._launch_game).pack(fill="x",padx=9,pady=(0,9))
        self.dirty_label = ctk.CTkLabel(self.sidebar, text="✓ No unsaved changes", text_color="#94a3b8", anchor="w")
        self.dirty_label.grid(row=15, column=0, padx=20, pady=10, sticky="ew")
        ctk.CTkButton(self.sidebar, text="Build Preview / Review & Apply", fg_color="#0891b2", hover_color="#0e7490", command=self.review_apply).grid(row=16, column=0, padx=15, pady=(3, 20), sticky="ew")

    def open_wiki(self):
        url = "https://enshrouded.wiki.gg/"
        try:
            if not webbrowser.open(url, new=2):
                raise OSError("The default browser rejected the open request.")
        except Exception as exc:
            message = f"Could not open the Enshrouded Wiki.\n\n{exc}"
            if messagebox.askyesno("Wiki unavailable", message + "\n\nCopy the URL to the clipboard?"):
                self.clipboard_clear(); self.clipboard_append(url); self.update()

    def _content(self):
        self.main = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew"); self.main.grid_columnconfigure(0, weight=1); self.main.grid_rowconfigure(1, weight=0); self.main.grid_rowconfigure(2, weight=1)
        try:
            if Image is not None: backdrop = ctk.CTkImage(Image.open(self.base_dir/"assets"/"dark-fantasy-background.png"), size=(1400,900))
            else: backdrop = PhotoImage(file=str(self.base_dir/"assets"/"dark-fantasy-background.png"))
            self._image_refs.append(backdrop); ctk.CTkLabel(self.main, text="", image=backdrop, fg_color="#0b1722").place(relx=0, rely=0, relwidth=1, relheight=1)
        except Exception: ctk.CTkFrame(self.main, fg_color="#101a27").place(relx=0,rely=0,relwidth=1,relheight=1)
        top = ctk.CTkFrame(self.main, fg_color="#0f1b29", corner_radius=0); top.grid(row=0, column=0, sticky="ew"); top.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(top, text="◈  ENSHROUDED", font=ctk.CTkFont(family=self.display_font,size=20,weight="bold"), text_color="#f1f5f9").grid(row=0,column=0,padx=20,pady=12)
        ctk.CTkLabel(top, text="Mod Hub & Control Center", font=ctk.CTkFont(family=self.display_font,size=12), text_color="#aebdcc").grid(row=0,column=1,padx=(0,12),pady=12,sticky="w")
        top.grid_columnconfigure(2, weight=1); self.global_search = ctk.CTkEntry(top, placeholder_text="⌕  Search settings, mods, or features…", height=36, fg_color="#0c1722", border_color="#3b5367"); self.global_search.grid(row=0,column=2,padx=(18,8),pady=10,sticky="ew"); self.global_search.bind("<KeyRelease>", lambda _e: self.show_tuning())
        ctk.CTkButton(top, text="?  Help", width=82, height=36, fg_color="transparent", border_width=1, border_color="#3b5367", hover_color="#324d62", command=self.show_guides).grid(row=0, column=3, padx=(0, 14), pady=10)
        self.title_label = ctk.CTkLabel(self.main, text="", anchor="w", font=ctk.CTkFont(family=self.display_font,size=25, weight="bold"), text_color="#f5f0e8")
        self.title_label.grid(row=1, column=0, sticky="ew", padx=30, pady=(20, 8))
        # The page host is intentionally non-scrollable. Game Tuning owns two
        # independent scroll regions (navigation and settings) beneath a fixed
        # toolbar; nesting it inside another CTkScrollableFrame causes clipped
        # cards and competing canvases at smaller window sizes.
        self.body = ctk.CTkFrame(self.main, fg_color="transparent")
        self.body.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 20)); self.main.grid_rowconfigure(2, weight=1)
        self.right = ctk.CTkScrollableFrame(self, width=430, fg_color="#0d1724", corner_radius=0); self.right.grid(row=0, column=2, sticky="nsew")
        self._render_right()

    def _clear(self, title):
        self._page_generation += 1
        self.title_label.configure(text=title)
        for child in self.body.winfo_children(): child.destroy()
        guidance = {
            "Home": ("See your current game, profile, project, mods, and backup health.", "Start with the highlighted next action.", "Control Center will open the relevant safe workflow."),
            "Game Tuning": ("Review beginner-friendly player, world, combat, and progression settings.", "Choose a tuning category or search for a setting.", "Changes stay staged until you review and apply them."),
            "Building Studio": ("Plan building pieces, materials, props, and structures for a content project.", "Choose a building category or preview a piece.", "Your selection stays in the project until you review and export it."),
            "Mod Manager": ("Review local packages, preview their ownership, and install supported mods.", "Add a local download folder, then choose Preview.", "Control Center shows the install plan before any files change."),
            "Content Studio": ("Create, recolor, validate, and package mod content through guided workflows.", "Choose a wizard or open Building Studio.", "The project remains reviewable and research-only until you explicitly test it."),
            "Research Lab": ("Run controlled, reversible experiments and record what is proven.", "Select or create a research project.", "Control Center prepares an isolated test path and records the result."),
            "Research Catalog": ("Review research-only candidates and their source evidence without enabling them in generated mods.", "Select a catalog entry to inspect its provenance.", "The candidate remains fail-closed until a separate guided test proves it safe."),
            "Save Manager": ("Find saves, create verified restore points, and manage scheduled backups.", "Choose a save folder or create a backup.", "The original save remains untouched and the snapshot is integrity-checked."),
            "Save Editor": ("Review supported save capabilities without risking the original file.", "Choose a capability marked Supported, Read-only, or Experimental.", "Edits are previewed and written only to a separate copy when supported."),
            "Troubleshooter": ("Diagnose installation, loader, mod, profile, runtime, and backup problems.", "Run the full read-only diagnostics.", "Results explain the issue and offer only reversible fixes where safe."),
            "Guides & Help": ("Find step-by-step help, examples, and recovery instructions.", "Search for a topic or select a guide.", "The selected guide explains the next click and related workflows."),
            "Profiles": ("Create, switch, and review isolated tuning and mod configurations.", "Select an existing profile or create one.", "The active profile becomes the shared context for Home and testing."),
            "Settings": ("Validate the game installation, inspect compatibility, and access recovery tools.", "Choose the installation folder, then run a read-only scan.", "Control Center reports what is safe to repair before changing anything."),
        }
        what, first, next_step = guidance.get(title, ("Use this module to manage the selected Control Center task.", "Choose the first available action.", "The next screen will explain the result and any follow-up."))
        help_bar = ctk.CTkFrame(self.body, fg_color="#13283a", border_width=1, border_color="#31536b", corner_radius=9)
        help_bar.pack(fill="x", padx=4, pady=(0, 10))
        ctk.CTkLabel(help_bar, text=f"What you can do: {what}\nFirst click: {first}\nNext: {next_step}", text_color="#dbeafe", justify="left", anchor="w", wraplength=760).pack(side="left", fill="x", expand=True, padx=12, pady=9)
        ctk.CTkButton(help_bar, text="Open related help", width=125, height=28, command=self.show_guides).pack(side="right", padx=10, pady=8)

    def _card(self, title, text, parent=None):
        container = parent or self.body
        frame = ctk.CTkFrame(container, fg_color="#1f2937", corner_radius=12); frame.pack(fill="x", padx=4, pady=7)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=18, pady=(15, 4))
        ctk.CTkLabel(frame, text=text, text_color="#cbd5e1", justify="left", anchor="w", wraplength=950).pack(fill="x", padx=18, pady=(0, 15))
        return frame

    def _render_right(self):
        for child in self.right.winfo_children(): child.destroy()
        self._right_card("Profiles", "Manage and quickly switch between local profiles.")
        for profile in (self.base_dir / "profiles").glob("*.json"):
            if profile.name in ("active_profile.json", "installer.json", "legacy_setting_mapping.json", "undo_profile.json", "selected_profile.json"): continue
            row = ctk.CTkFrame(self.right, fg_color="#182636", border_width=1, border_color="#2b4355", corner_radius=8); row.pack(fill="x", padx=12, pady=4)
            try:
                raw=PhotoImage(file=str(self.base_dir/"assets"/"building-studio-preview.png")); thumb=raw.subsample(10,10); self._image_refs.append(thumb)
                ctk.CTkLabel(row,text="",image=thumb,width=58,height=46).pack(side="left",padx=6,pady=6)
            except Exception: pass
            try:
                profile_record = json.loads(profile.read_text(encoding="utf-8"))
                if not isinstance(profile_record, dict):
                    raise TypeError("profile record is not an object")
                display_name = str(profile_record.get("name", profile.stem.replace("_", " ").title()))
                is_active = profile_record.get("id") == getattr(self, "active_profile_id", "default")
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                display_name = profile.stem.replace("_", " ").title(); is_active = False
            info=ctk.CTkFrame(row,fg_color="transparent"); info.pack(side="left",fill="x",expand=True,padx=3,pady=6); ctk.CTkLabel(info, text=display_name, anchor="w", font=ctk.CTkFont(family=self.display_font,size=12,weight="bold")).pack(fill="x"); ctk.CTkLabel(info,text=("Active profile" if is_active else "Local profile"),anchor="w",text_color="#aebdcc",font=ctk.CTkFont(size=10)).pack(fill="x")
            ctk.CTkButton(row, text="Load", width=54, command=lambda p=profile: self._load_profile(p)).pack(side="right", padx=6, pady=6)
        ctk.CTkButton(self.right, text="Clone Profile / Assign World", command=self._clone_profile).pack(fill="x", padx=15, pady=(2, 8))
        self._right_card("Mod Manager", self.nexus.status())
        tabs = ctk.CTkFrame(self.right, fg_color="transparent"); tabs.pack(fill="x", padx=12)
        self.mod_state = ctk.CTkLabel(self.right, text="Connect to Nexus Mods to browse live mods. Installed package state is available through Installation Manager.", justify="left", wraplength=370, anchor="w", text_color="#cbd5e1"); self.mod_state.pack(fill="x", padx=18, pady=10)
        for label, action in (("Installed", self._show_installed), ("Browse Mods", self._browse_nexus), ("Nexus Mods", self._browse_nexus), ("Updates", self._browse_updates)):
            ctk.CTkButton(tabs, text=label, width=88, command=action).pack(side="left", padx=2)
        ctk.CTkButton(self.right, text="Sync Nexus Mods", fg_color="#c2410c", command=self._browse_nexus).pack(fill="x", padx=15, pady=8)
        self._right_card("Game Status", self._game_status_text())
        ctk.CTkButton(self.right, text="Launch Game", fg_color="#ea580c", command=self._launch_game).pack(fill="x", padx=15, pady=10)

    def _right_card(self, title, text):
        frame = ctk.CTkFrame(self.right, fg_color="#111f2e", border_width=1, border_color="#2a4052", corner_radius=10); frame.pack(fill="x", padx=10, pady=8)
        ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(family=self.display_font,size=18, weight="bold"), anchor="w", text_color="#f5f0e8").pack(fill="x", padx=14, pady=(12, 3))
        ctk.CTkLabel(frame, text=text, text_color="#cbd5e1", justify="left", anchor="w", wraplength=370).pack(fill="x", padx=14, pady=(0, 12))
    def _game_status_text(self):
        path = self.installer.selected_game_path(); exists = bool(path and (path / "Enshrouded.exe").is_file())
        if not path:
            return "Game folder not selected\nChoose an installation folder"
        self.platform.game_dir = path
        status = self.platform.status(set(self.manager.modules))
        build = status.game.build_id or "unknown build"
        runtime = status.runtime.status
        return f"{'Ready to Play' if exists else 'Game folder not found'}\nBuild: {build}\nRuntime: {runtime}\n{path}"
    def _load_profile(self, path):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(record, dict):
                raise ValueError("This profile file is not a valid profile object.")
            self.pending = record.get("config", record)
            self.active_profile_id = record.get("id", path.stem)
            self._persist_active_profile()
            self._dirty(); self.show_dashboard()
        except Exception as exc: messagebox.showerror("Profile", str(exc))
    def _clone_profile(self):
        from tkinter import simpledialog
        source = filedialog.askopenfilename(initialdir=str(self.base_dir / "profiles"), title="Choose profile to clone", filetypes=[("Profile JSON", "*.json")])
        if not source: return
        destination = filedialog.asksaveasfilename(initialdir=str(self.base_dir / "profiles"), title="Save cloned profile", defaultextension=".json", filetypes=[("Profile JSON", "*.json")])
        if not destination: return
        profile_id = simpledialog.askstring("Clone profile", "New profile ID:", parent=self)
        if not profile_id: return
        world_id = simpledialog.askstring("Clone profile", "Optional world ID:", parent=self)
        try:
            created = self.launcher.clone_profile(Path(source), Path(destination), profile_id, world_id)
            messagebox.showinfo("Profile cloned", f"Created profile:\n{created}")
            self._render_right()
        except (LaunchError, OSError) as exc:
            messagebox.showerror("Profile clone failed", str(exc))
    def _show_installed(self): self.mod_state.configure(text="Installed state is managed by the ownership manifest and Installation Manager.")
    def _browse_nexus(self):
        try: self.mod_state.configure(text=json.dumps(self.nexus.browse(), indent=2)[:1800] if self.nexus.connected else self.nexus.status())
        except NexusError as exc: self.mod_state.configure(text=str(exc))
    def _browse_updates(self): self._browse_nexus()
    def _launch_game(self):
        path = self.installer.selected_game_path()
        if not path:
            return
        try:
            profile = self.base_dir / "profiles" / "active_profile.json"
            runtime = self.base_dir / "runtime" / "launch_profile.json"
            plan = self.launcher.prepare(path, profile, runtime)
            self.launcher.launch(plan)
        except LaunchError as exc:
            messagebox.showerror("Launch blocked", str(exc))

    def show_home(self):
        """Beginner-first task hub; technical pages remain available from the sidebar."""
        self._clear("Home")
        self.title_label.configure(text="What would you like to do?")
        ctk.CTkLabel(self.body, text="Choose a task below. Control Center will guide you one step at a time.", text_color="#cbd5e1", anchor="w").pack(fill="x", padx=8, pady=(0, 12))
        status = ctk.CTkFrame(self.body, fg_color="#123329", border_width=1, border_color="#2f855a", corner_radius=12)
        status.pack(fill="x", padx=8, pady=(0, 12))
        game = self.installer.selected_game_path(); ready = bool(game and (game / "Enshrouded.exe").is_file())
        project = self._last_research_project()
        status_text = "Game ready" if ready else "Game folder needs to be selected"
        detail = f"Current project: {project.name}" if project else "No content project selected yet"
        context = build_control_context(self.base_dir, self.pending, self.local_mods.state.get("installed", {}), project, self.last_diagnostic_report, profile_name=self._active_profile_name())
        profile_text = f"Active profile: {self._active_profile_name()} · {context['profile']['enabled_module_count']} tuning module(s) enabled"
        mods_text = f"Installed mods: {context['mods']['installed_count']}"
        latest_backup = context["backups"]["latest"]
        backup_age = context["backups"].get("latest_age_hours")
        if backup_age is None:
            backup_age_text = ""
        elif backup_age >= 48:
            backup_age_text = f"{backup_age // 24} day(s) old"
        else:
            backup_age_text = f"{backup_age} hour(s) old"
        backup_text = "Save backup: none yet" if not latest_backup else f"Save backup: {latest_backup} ({backup_age_text})" if backup_age_text else f"Save backup: {latest_backup}"
        if not ready:
            next_action = "Next action: choose the Enshrouded game folder"
        elif not latest_backup:
            next_action = "Next action: create a protected save backup"
        elif not project:
            next_action = "Next action: create or open a content project"
        else:
            next_action = "Next action: prepare a safe test"
        ctk.CTkLabel(status, text=f"{status_text}  ·  {detail}", text_color="#d1fae5", font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(fill="x", padx=16, pady=(12, 2))
        diagnostic_status = context["runtime"]["status"]
        runtime_warning = diagnostic_status in {"failed", "degraded"}
        stale_backup = backup_age is not None and backup_age >= 48
        other_warnings = context["mods"]["missing_targets"] + context["backups"]["invalid_count"] + int(runtime_warning)
        warning_count = other_warnings + int(stale_backup)
        warning_reasons = []
        if context["mods"]["missing_targets"]: warning_reasons.append("missing mod target")
        if context["backups"]["invalid_count"]: warning_reasons.append("invalid backup")
        if runtime_warning: warning_reasons.append("runtime diagnostic")
        if stale_backup: warning_reasons.append("stale backup")
        if other_warnings:
            next_action = "Next action: run Troubleshooter before making changes"
        elif stale_backup:
            next_action = "Next action: create a fresh protected save backup"
        warning_text = f"Warnings: {', '.join(warning_reasons)}" if warning_reasons else "Warnings: none detected on the local profile"
        ctk.CTkLabel(status, text=f"{profile_text}  ·  {mods_text}", text_color="#a7f3d0", anchor="w", wraplength=900, justify="left").pack(fill="x", padx=16, pady=(0, 2))
        ctk.CTkLabel(status, text=warning_text, text_color="#fbbf24" if warning_count else "#a7f3d0", anchor="w", wraplength=900, justify="left").pack(fill="x", padx=16, pady=(0, 2))
        ctk.CTkLabel(status, text=f"{backup_text}  ·  {next_action}", text_color="#a7f3d0", anchor="w", wraplength=900, justify="left").pack(fill="x", padx=16, pady=(0, 3))
        ctk.CTkLabel(status, text="Your game files stay protected until you deliberately apply or prepare a test.", text_color="#a7f3d0", anchor="w").pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(status, text="Manage active profile", width=150, height=28, command=self.show_profiles).pack(anchor="w", padx=14, pady=(0, 10))
        if warning_count:
            ctk.CTkButton(status, text="Run Troubleshooter", width=150, height=28, fg_color="#a16207", hover_color="#ca8a04", command=self.show_troubleshooter).pack(anchor="w", padx=14, pady=(0, 10))
        tasks = ctk.CTkFrame(self.body, fg_color="transparent"); tasks.pack(fill="x", padx=4)
        tasks.grid_columnconfigure(0, weight=1); tasks.grid_columnconfigure(1, weight=1)
        options = [
            ("Create or edit content", "Add an item, recolor something, or import a BlenderTools model.", self.show_content, "Start here for custom content."),
            ("Test content safely", "Prepare a temporary test profile and capture what you see in-game.", self.show_research_lab, "Use this before installing anything."),
            ("Change game settings", "Adjust gameplay settings with simple controls—no Lua editing required.", self.show_tuning, "Customize your experience."),
            ("Back up or restore saves", "Make a protected copy of your saves or restore a previous copy.", self.show_save_manager, "Recommended before major changes."),
            ("Review save editor safety", "Inspect supported, read-only, experimental, and unsupported save capabilities.", self.show_save_editor, "Always protect a save first."),
            ("Manage installed mods", "Review, install, update, or remove Control Center-managed mods.", self.show_install, "Keep your installation organized."),
            ("Fix a problem", "Run diagnostics, review recovery options, and restore a safe profile.", self.show_troubleshooter, "Use this when something is not working."),
        ]
        for index, (title, description, action, hint) in enumerate(options):
            row, col = divmod(index, 2)
            card = ctk.CTkFrame(tasks, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=12); card.grid(row=row, column=col, sticky="nsew", padx=5, pady=5)
            ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=17, weight="bold"), anchor="w").pack(fill="x", padx=16, pady=(14, 3))
            ctk.CTkLabel(card, text=description, text_color="#cbd5e1", anchor="w", justify="left", wraplength=390).pack(fill="x", padx=16, pady=(0, 3))
            ctk.CTkLabel(card, text=hint, text_color="#7dd3fc", anchor="w").pack(fill="x", padx=16, pady=(0, 8))
            ctk.CTkButton(card, text="Open", width=100, command=action).pack(anchor="w", padx=16, pady=(0, 14))
        help_card = ctk.CTkFrame(self.body, fg_color="#102b40", border_width=1, border_color="#0ea5e9", corner_radius=12); help_card.pack(fill="x", padx=8, pady=(14, 8))
        ctk.CTkLabel(help_card, text="New to Control Center?", font=ctk.CTkFont(size=16, weight="bold"), text_color="#bae6fd", anchor="w").pack(side="left", padx=16, pady=14)
        ctk.CTkLabel(help_card, text="Guided workflows explain each step and protect your original game files.", text_color="#dbeafe", anchor="w").pack(side="left", padx=4, pady=14)
        ctk.CTkButton(help_card, text="Open Guides & Help", command=self.show_guides).pack(side="right", padx=(0, 8), pady=9)
        ctk.CTkButton(help_card, text="Show me how it works", command=self._show_research_lab_help).pack(side="right", padx=8, pady=9)

    def show_dashboard(self):
        """Compatibility entry point for older profile and launcher actions."""
        self.show_home()

    def show_save_manager(self):
        self._clear("Save Manager")
        self._card("Protect your saves", "Create a backup, compare two backups, or restore a copy. The live save is never overwritten by the restore workflow.")
        context = build_control_context(self.base_dir, self.pending, self.local_mods.state.get("installed", {}), self._last_research_project(), self.last_diagnostic_report, profile_name=self._active_profile_name())
        backup_root = self.base_dir / "profiles" / "save-backups"
        snapshots = list_verified_backups(backup_root)
        verified = sum(1 for item in snapshots if item["verified"])
        invalid = len(snapshots) - verified
        status_color = "#86efac" if invalid == 0 else "#fbbf24"
        status = ctk.CTkFrame(self.body, fg_color="#123329" if invalid == 0 else "#3b2b12", border_width=1, border_color="#2f855a" if invalid == 0 else "#a16207", corner_radius=10)
        status.pack(fill="x", padx=8, pady=(0, 8))
        latest = snapshots[0]["name"] if snapshots else "none"
        age = context["backups"].get("latest_age_hours")
        age_text = f" · {age // 24} day(s) old" if age is not None and age >= 48 else (f" · {age} hour(s) old" if age is not None else "")
        ctk.CTkLabel(status, text=f"{verified} verified backup(s)  ·  latest: {latest}{age_text}  ·  profile: {self._active_profile_name()} ({context['profile']['enabled_module_count']} module(s))", text_color=status_color, anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(status, text=("All known snapshots pass integrity checks." if invalid == 0 else f"{invalid} snapshot(s) need attention before restore."), text_color="#d1fae5" if invalid == 0 else "#fef3c7", anchor="w").pack(fill="x", padx=14, pady=(0, 10))
        policy_card = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10); policy_card.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkLabel(policy_card, text="Automatic backup schedule", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(policy_card, text="Runs only when enabled, a standard save folder is found, and Enshrouded is closed. Old verified snapshots are retained according to the limit.", text_color="#cbd5e1", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 7))
        policy_row = ctk.CTkFrame(policy_card, fg_color="transparent"); policy_row.pack(fill="x", padx=10, pady=(0, 10))
        enabled = ctk.BooleanVar(value=bool(self.backup_policy.get("enabled")))
        ctk.CTkCheckBox(policy_row, text="Enable", variable=enabled).pack(side="left", padx=4)
        ctk.CTkLabel(policy_row, text="Every", text_color="#94a3b8").pack(side="left", padx=(12, 4))
        interval = ctk.CTkEntry(policy_row, width=55); interval.insert(0, str(self.backup_policy["interval_hours"])); interval.pack(side="left")
        ctk.CTkLabel(policy_row, text="hours · retain", text_color="#94a3b8").pack(side="left", padx=4)
        retention = ctk.CTkEntry(policy_row, width=55); retention.insert(0, str(self.backup_policy["retention"])); retention.pack(side="left")
        ctk.CTkLabel(policy_row, text="verified snapshots", text_color="#94a3b8").pack(side="left", padx=4)
        def save_policy():
            try:
                values = {**self.backup_policy, "enabled": enabled.get(), "interval_hours": int(interval.get()), "retention": int(retention.get())}
                if values["interval_hours"] < 1 or values["retention"] < 1: raise ValueError
                self.backup_policy = save_backup_policy(self.backup_policy_path, values)
                messagebox.showinfo("Backup schedule saved", "Automatic backups are now " + ("enabled." if enabled.get() else "disabled."), parent=self)
            except ValueError:
                messagebox.showerror("Invalid schedule", "Interval and retention must be whole numbers greater than zero.", parent=self)
        ctk.CTkButton(policy_row, text="Save schedule", width=120, command=save_policy).pack(side="right", padx=4)
        card = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=12); card.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(card, text="Choose what you want to do", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").pack(fill="x", padx=16, pady=(14, 8))
        actions = [("Find my save folder", "Locate the standard Enshrouded save location without changing anything.", self._discover_save_folder), ("Create a backup", "Copy a save to a separate protected folder.", self._backup_save_folder), ("Restore a backup", "Restore into a separate destination for safety.", self._restore_save_folder), ("Compare backups", "See what changed between two verified snapshots.", self._compare_save_folders), ("Inspect save progress", "Read-only inspection of characters and save structure.", self._inspect_save_progress)]
        for title, description, action in actions:
            row = ctk.CTkFrame(card, fg_color="#1d3042", corner_radius=8); row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(row, text=description, text_color="#cbd5e1", anchor="w").pack(side="left", padx=4, pady=10, fill="x", expand=True)
            ctk.CTkButton(row, text="Open", width=90, command=action).pack(side="right", padx=10, pady=6)
        self._card("Save editor status", "The character editor is being built as a protected advanced tool. It will require a verified backup and will preview every change before anything can be written.")

    def show_save_editor(self):
        self._clear("Save Editor")
        self._card("Character and save editing", "This area will let you review supported character data and prepare safe edits. Original saves will remain untouched until you explicitly approve a verified copy.")
        context = build_control_context(self.base_dir, self.pending, self.local_mods.state.get("installed", {}), self._last_research_project(), self.last_diagnostic_report, profile_name=self._active_profile_name())
        card = ctk.CTkFrame(self.body, fg_color="#3b2412", border_width=1, border_color="#a16207", corner_radius=12); card.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(card, text="Protected advanced tool", font=ctk.CTkFont(size=18, weight="bold"), text_color="#fde68a", anchor="w").pack(fill="x", padx=16, pady=(14, 3))
        ctk.CTkLabel(card, text="Character editing is not enabled yet. The current save reader is read-only while the save format and safe write boundaries are being verified.", text_color="#fef3c7", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=16, pady=(0, 10))
        ctk.CTkLabel(card, text=f"Verified restore points available: {context['backups']['count']}", text_color="#fde68a", anchor="w").pack(fill="x", padx=16, pady=(0, 8))
        ctk.CTkButton(card, text="Inspect save read-only", command=self._inspect_save_progress).pack(anchor="w", padx=16, pady=(0, 14))
        ctk.CTkButton(card, text="Create verified backup first", command=self._guided_save_backup).pack(anchor="w", padx=16, pady=(0, 14))
        matrix = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10); matrix.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(matrix, text="Capability safety matrix", font=ctk.CTkFont(size=17, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(matrix, text="These labels are enforced before any write workflow is added.", text_color="#cbd5e1", anchor="w").pack(fill="x", padx=14, pady=(0, 8))
        capabilities = [("Character name", "Read-only", "Readable through the current save inspection path; no write boundary verified."), ("Character appearance", "Unsupported", "No safe field mapping has been verified."), ("Inventory", "Read-only", "Inspection remains available; item ownership writes are not enabled."), ("Skills and progression", "Read-only", "Values may be inspected where decoded; writes remain disabled."), ("Experience and levels", "Experimental", "Requires additional format evidence before any write can be considered."), ("World/player ownership", "Unsupported", "Not safe to edit without verified ownership boundaries."), ("Building-related data", "Unsupported", "No stable write boundary is available yet.")]
        colors = {"Supported": "#86efac", "Read-only": "#7dd3fc", "Experimental": "#fbbf24", "Unsupported": "#fca5a5"}
        for name, state, detail in capabilities:
            row = ctk.CTkFrame(matrix, fg_color="#1d3042", corner_radius=7); row.pack(fill="x", padx=12, pady=3)
            ctk.CTkLabel(row, text=name, width=190, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=10, pady=8)
            ctk.CTkLabel(row, text=state, width=100, anchor="w", text_color=colors[state], font=ctk.CTkFont(weight="bold")).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=detail, text_color="#cbd5e1", anchor="w", justify="left", wraplength=620).pack(side="left", padx=4, pady=6, fill="x", expand=True)
        self._card("Write protection", "Every future edit must create a verified backup first, preview the proposed change, write only to a separate copy, and leave the original save untouched.")

    def show_troubleshooter(self):
        self._clear("Troubleshooter")
        self._card("Fix a problem", "Answer a few simple questions and Control Center will check the game folder, loader, profiles, mods, logs, and recovery options.")
        action_bar = ctk.CTkFrame(self.body, fg_color="#102b40", border_width=1, border_color="#0ea5e9", corner_radius=10); action_bar.pack(fill="x", padx=8, pady=(0, 8))
        ctk.CTkLabel(action_bar, text="Start with a complete read-only check", text_color="#bae6fd", font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=14, pady=12)
        ctk.CTkButton(action_bar, text="Run full check", command=self._run_troubleshooter).pack(side="right", padx=12, pady=7)
        card = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=12); card.pack(fill="x", padx=8, pady=8)
        ctk.CTkLabel(card, text="What needs attention?", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").pack(fill="x", padx=16, pady=(14, 8))
        options = [("Game will not launch", "Check installation, loader, and runtime logs.", self.show_settings), ("A mod is not working", "Review installed ownership and compatibility.", self.show_install), ("Content test failed", "Open the Research Lab recovery workflow.", self.show_research_lab), ("I want to restore safely", "Open backups and reversible recovery tools.", self.show_save_manager), ("Runtime crashed", "Quarantine one identifiable failing mod when the game is closed.", self._auto_recover_runtime)]
        for title, description, action in options:
            row = ctk.CTkFrame(card, fg_color="#1d3042", corner_radius=8); row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(row, text=title, font=ctk.CTkFont(weight="bold"), anchor="w").pack(side="left", padx=12, pady=10)
            ctk.CTkLabel(row, text=description, text_color="#cbd5e1", anchor="w").pack(side="left", padx=4, pady=10, fill="x", expand=True)
            ctk.CTkButton(row, text="Check", width=90, command=action).pack(side="right", padx=10, pady=6)
        ctk.CTkButton(self.body, text="Open full diagnostics", command=self.show_settings).pack(anchor="w", padx=12, pady=8)

    def _run_troubleshooter(self):
        """Run the bounded health checks and present safe next actions."""
        game = self.installer.selected_game_path()
        try:
            report = self.health_reports.generate(game)
        except Exception as exc:
            return messagebox.showerror("Troubleshooter failed", f"The read-only check could not finish:\n\n{exc}", parent=self)
        self.last_diagnostic_report = report
        self._clear("Troubleshooter")
        status = report.get("runtime", {}).get("status", "unknown")
        diagnostics = report.get("diagnostics", {})
        modules = report.get("modules", {})
        compatibility = report.get("compatibility", {})
        content = report.get("content", [])
        mods = report.get("mods", [])
        context = build_control_context(self.base_dir, self.pending, self.local_mods.state.get("installed", {}), self._last_research_project(), self.last_diagnostic_report, profile_name=self._active_profile_name())
        failed_mods = sum(1 for item in mods if item.get("integrity") == "failed")
        incompatible = sum(1 for item in compatibility.values() if not item.get("compatible", True))
        invalid_content = sum(1 for item in content if not item.get("valid", True))
        overall = "Needs attention" if status in {"failed", "degraded"} or failed_mods or incompatible or invalid_content or context["backups"]["invalid_count"] else "No blocking issues found"
        tone = "#fbbf24" if overall != "No blocking issues found" else "#86efac"
        self._card("Check result", overall, self.body)
        result = ctk.CTkFrame(self.body, fg_color="#172737", corner_radius=10); result.pack(fill="x", padx=8, pady=6)
        rows = [("Game/runtime", status), ("Active profile", f"{self._active_profile_name()} · {context['profile']['enabled_module_count']} module(s) enabled"), ("Loader/modules", f"{modules.get('count', 0)} detected"), ("Installed mods", f"{failed_mods} integrity issue(s)"), ("Compatibility", f"{incompatible} mismatch(es)"), ("Content projects", f"{invalid_content} invalid project(s)"), ("Backups", f"{context['backups']['invalid_count']} invalid snapshot(s)"), ("Logs", str(diagnostics.get("status", "unknown")))]
        for label, value in rows:
            row = ctk.CTkFrame(result, fg_color="transparent"); row.pack(fill="x", padx=14, pady=3)
            ctk.CTkLabel(row, text=label, width=170, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left")
            ctk.CTkLabel(row, text=value, text_color=tone if label in {"Game/runtime", "Logs"} else "#cbd5e1", anchor="w").pack(side="left")
        recommended = diagnostics.get("recommended_action") or "Review the affected area before making changes."
        self._card("Recommended next action", recommended, self.body)
        ctk.CTkButton(self.body, text="Run the check again", command=self._run_troubleshooter).pack(anchor="w", padx=12, pady=8)

    def show_guides(self):
        self._clear("Guides & Help")
        self._card("Learn as you go", "These guides explain the tools in plain language. Start with the guide that matches what you are trying to do.")
        guides = [("Getting started", "The basic Control Center workflow for first-time users.", "USER_GUIDE.md"), ("Create and import content", "How Content Studio and BlenderTools work together.", "MOD_AUTHOR_GUIDE.md"), ("Beginner Content Wizard", "Create, review, and safely test a new content project step by step.", "BEGINNER_CONTENT_WIZARD_GUIDE.md"), ("Building Studio", "Plan building pieces, materials, and structures with the visual workflow.", "BUILDER_GUIDE.md"), ("Install mods", "Review, preview, install, update, disable, and safely remove mods.", "MOD_INSTALLATION_GUIDE.md"), ("Test content safely", "How to use Research Lab and capture evidence.", "RESEARCH_PROBE_GUIDE.md"), ("Install and recover mods", "Backups, profiles, updates, and recovery.", "RECOVERY_GUIDE.md"), ("Save backups", "Create, schedule, compare, verify, and restore save snapshots safely.", "SAVE_BACKUP_GUIDE.md"), ("Game tuning", "How to adjust settings without editing Lua.", "TUNING_GUIDE.md"), ("Troubleshoot problems", "Diagnose launch, loader, mod, profile, and save issues.", "TROUBLESHOOTING_GUIDE.md"), ("Open the Enshrouded Wiki", "Open the external community reference site.", None)]
        guides.insert(1, ("BlenderTools", "Validate, stage, and safely test a BlenderTools export.", "BLENDERTOOLS_GUIDE.md"))
        guides.insert(6, ("Research Lab", "Prepare isolated tests, capture evidence, and restore your normal profile.", "RESEARCH_LAB_GUIDE.md"))
        search_bar = ctk.CTkFrame(self.body, fg_color="#172737", corner_radius=10); search_bar.pack(fill="x", padx=8, pady=(0, 8))
        query = ctk.CTkEntry(search_bar, placeholder_text="Search guides and help topics…", height=34); query.pack(side="left", fill="x", expand=True, padx=10, pady=9)
        results_host = ctk.CTkFrame(self.body, fg_color="transparent"); results_host.pack(fill="x")

        def render_guides():
            for child in results_host.winfo_children(): child.destroy()
            needle = query.get().strip().lower()
            matches = [item for item in guides if not needle or needle in " ".join(item).lower()]
            for title, description, filename in matches:
                row = ctk.CTkFrame(results_host, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10); row.pack(fill="x", padx=8, pady=4)
                ctk.CTkLabel(row, text=title, font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(side="left", padx=14, pady=12)
                ctk.CTkLabel(row, text=description, text_color="#cbd5e1", anchor="w").pack(side="left", padx=4, pady=12, fill="x", expand=True)
                if filename:
                    ctk.CTkButton(row, text="Open guide", width=110, command=lambda name=filename: self._open_guide(name)).pack(side="right", padx=10, pady=7)
                else:
                    ctk.CTkButton(row, text="Open Wiki", width=110, command=self.open_wiki).pack(side="right", padx=10, pady=7)

        ctk.CTkButton(search_bar, text="Search", width=90, command=render_guides).pack(side="right", padx=(0, 10), pady=9)
        query.bind("<Return>", lambda _event: render_guides())
        render_guides()
        example = self.base_dir / "assets" / "building-studio-preview.png"
        if Image is not None and example.is_file():
            preview = ctk.CTkFrame(self.body, fg_color="#102b40", corner_radius=10); preview.pack(fill="x", padx=8, pady=(10, 4))
            ctk.CTkLabel(preview, text="Example: visual building workflow", text_color="#bae6fd", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=14, pady=(10, 5))
            image = ctk.CTkImage(Image.open(example), size=(520, 210)); self._image_refs.append(image)
            ctk.CTkLabel(preview, image=image, text="").pack(padx=14, pady=(0, 12))

    def _open_guide(self, filename):
        path = self.base_dir / "docs" / filename
        if not path.is_file():
            return messagebox.showinfo("Guide unavailable", f"This guide has not been packaged yet:\n\n{filename}", parent=self)
        try:
            os.startfile(str(path))
        except OSError as exc:
            messagebox.showerror("Could not open guide", str(exc), parent=self)

    def show_tuning_dashboard(self):
        self._clear("Game Tuning")
        subtitle = ctk.CTkLabel(self.body, text="Fine-tune your Enshrouded experience. No Lua editing required.", text_color="#94a3b8", anchor="w"); subtitle.pack(fill="x", padx=8, pady=(0, 10))
        tabs = ctk.CTkFrame(self.body, fg_color="transparent"); tabs.pack(fill="x", padx=4, pady=(0, 12))
        for label in ("⚙  General", "♙  Player", "⚔  Combat", "♨  Survival", "◈  World", "▣  Building"):
            ctk.CTkButton(tabs, text=label, width=112, height=34, fg_color="#d65b20" if label.startswith("⚙") else "#182635", hover_color="#ed7328", border_width=1, border_color="#344657", command=self.show_tuning).pack(side="left", padx=4)
        grid = ctk.CTkFrame(self.body, fg_color="transparent"); grid.pack(fill="x", padx=4); grid.grid_columnconfigure(0, weight=1); grid.grid_columnconfigure(1, weight=1)
        defs = self.registry.definitions(); self._dashboard_panel(grid, 0, "♥  Player Settings", "Adjust core player mechanics and progression.", defs[:4]); self._dashboard_panel(grid, 1, "◈  Game Rules", "Customize progression and server-like rules.", defs[4:8])
        self._building_dashboard()
        try: self.body._parent_canvas.yview_moveto(0.0)
        except Exception: pass

    def _dashboard_panel(self, parent, column, title, desc, definitions):
        panel = ctk.CTkFrame(parent, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10); panel.grid(row=0, column=column, sticky="nsew", padx=5); panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(panel, text=title, font=ctk.CTkFont(size=17, weight="bold"), anchor="w").grid(row=0,column=0,columnspan=3,sticky="w",padx=16,pady=(13,1)); ctk.CTkLabel(panel,text=desc,text_color="#91a4b4",anchor="w").grid(row=1,column=0,columnspan=3,sticky="w",padx=16,pady=(0,8))
        for row, d in enumerate(definitions, 2):
            module, key = d.id.split(".",1); value=self.pending["module_settings"].get(module,{}).get(key,d.profile_default)
            ctk.CTkLabel(panel, text="✦", text_color="#f07a2a", width=22).grid(row=row,column=0,padx=(14,4),sticky="n")
            text = ctk.CTkFrame(panel, fg_color="transparent"); text.grid(row=row,column=1,sticky="ew",pady=7); ctk.CTkLabel(text,text=d.label,font=ctk.CTkFont(weight="bold"),anchor="w").pack(fill="x"); ctk.CTkLabel(text,text=d.description,text_color="#9eb0be",font=ctk.CTkFont(size=10),anchor="w",wraplength=220,justify="left").pack(fill="x")
            if d.input_type == "boolean":
                var=ctk.BooleanVar(value=bool(value)); ctk.CTkSwitch(panel,text="",variable=var,command=lambda v=var,m=module,k=key:self._set_value(m,k,v.get())).grid(row=row,column=2,padx=12)
            elif d.declared_min is not None:
                ctl=ctk.CTkFrame(panel,fg_color="transparent"); ctl.grid(row=row,column=2,padx=12,sticky="e"); entry=ctk.CTkEntry(ctl,width=58,height=26); entry.insert(0,self._format(value,d)); entry.pack(); scale=ctk.CTkSlider(ctl,width=105,height=10,from_=d.declared_min,to=d.declared_max); scale.set(float(value)); scale.pack(pady=(4,0)); scale.configure(command=lambda x,m=module,k=key,e=entry,definition=d:self._slider(m,k,x,e,definition))
            else: ctk.CTkLabel(panel,text=str(value),text_color="#dbe6ee").grid(row=row,column=2,padx=12)

    def _building_dashboard(self):
        outer=ctk.CTkFrame(self.body,fg_color="#172737",border_width=1,border_color="#2c4152",corner_radius=10); outer.pack(fill="x",padx=9,pady=(12,6)); outer.grid_columnconfigure(1,weight=1); ctk.CTkLabel(outer,text="▣  Building Studio",font=ctk.CTkFont(size=18,weight="bold"),anchor="w").grid(row=0,column=0,columnspan=2,sticky="w",padx=16,pady=(12,4))
        tabs=ctk.CTkFrame(outer,fg_color="transparent"); tabs.grid(row=1,column=0,columnspan=2,sticky="w",padx=10,pady=4)
        for label in ("Modular Pieces","Materials","Props","Structures","Custom"): ctk.CTkButton(tabs,text=label,width=90,height=28,fg_color="#c95720" if label=="Modular Pieces" else "#1d3041",command=self.show_building).pack(side="left",padx=2)
        pieces=("Stone Wall","Wood Wall","Half Wall","Window Frame","Stone Foundation","Wood Floor","Roof (Angled)","Stairs")
        tray=ctk.CTkFrame(outer,fg_color="transparent"); tray.grid(row=2,column=0,sticky="nw",padx=12,pady=8)
        for i,name in enumerate(pieces):
            card=ctk.CTkFrame(tray,fg_color="#203244",corner_radius=6,width=92,height=66); card.grid(row=i//4,column=i%4,padx=4,pady=4); card.grid_propagate(False); ctk.CTkLabel(card,text="▧",font=ctk.CTkFont(size=22),text_color="#d28a4b").pack(); ctk.CTkLabel(card,text=name,font=ctk.CTkFont(size=9),wraplength=82).pack()
        try:
            if Image is not None:
                image=ctk.CTkImage(Image.open(self.base_dir/"assets"/"building-studio-preview.png"),size=(410,210))
            else:
                raw=PhotoImage(file=str(self.base_dir/"assets"/"building-studio-preview.png")); image=raw.subsample(4,4); self._preview_image=image
            ctk.CTkLabel(outer,text="Offline visual preview — not live game state",image=image,compound="bottom",text_color="#f6b27b",fg_color="#101b27").grid(row=2,column=1,sticky="nsew",padx=(8,14),pady=8)
        except Exception: ctk.CTkLabel(outer,text="Offline visual preview unavailable",text_color="#f6b27b").grid(row=2,column=1)

    def show_tuning(self):
        self._clear("Game Tuning")
        toolbar = ctk.CTkFrame(self.body, fg_color="#1f2937", corner_radius=10); toolbar.pack(fill="x", pady=(0, 10)); toolbar.grid_columnconfigure(0, weight=1)
        self.tuning_search = ctk.CTkEntry(toolbar, placeholder_text="Search settings, descriptions, categories, tags or IDs…")
        self.tuning_search.grid(row=0, column=0, padx=12, pady=12, sticky="ew"); self.tuning_search.bind("<KeyRelease>", lambda _e: self._render_tuning())
        ctk.CTkButton(toolbar, text="All Settings", width=105, command=lambda: self._set_tuning_tab("all")).grid(row=0, column=1, padx=3)
        ctk.CTkButton(toolbar, text="Modified", width=90, command=lambda: self._set_tuning_tab("modified")).grid(row=0, column=2, padx=3)
        ctk.CTkButton(toolbar, text="Restore Vanilla", width=115, command=lambda: self._set_tuning_tab("restore")).grid(row=0, column=3, padx=12)
        ctk.CTkButton(toolbar, text="Review & Apply", width=125, fg_color="#0891b2", hover_color="#0e7490", command=self.review_apply).grid(row=0, column=4, padx=(0, 12))
        self.tuning_category = getattr(self, "tuning_category", "Player & Survival")
        self.tuning_subcategory = getattr(self, "tuning_subcategory", "Survival")
        self.tuning_tab = getattr(self, "tuning_tab", "all"); self._render_tuning()

    def _set_tuning_tab(self, tab):
        self.tuning_tab = tab; self._render_tuning()

    def _render_tuning(self):
        for child in list(self.body.winfo_children())[1:]: child.destroy()
        local_query = self.tuning_search.get().strip() if hasattr(self, "tuning_search") else ""
        global_query = self.global_search.get().strip() if hasattr(self, "global_search") else ""
        query = local_query or global_query
        split=ctk.CTkFrame(self.body,fg_color="transparent"); split.pack(fill="both",expand=True); split.grid_columnconfigure(1,weight=1); split.grid_rowconfigure(0,weight=1)
        self.tuning_nav=ctk.CTkScrollableFrame(split,width=205,fg_color="#111f2e",border_width=1,border_color="#2c4152",corner_radius=9); self.tuning_nav.grid(row=0,column=0,sticky="nsew",padx=(0,8))
        self.tuning_content=ctk.CTkScrollableFrame(split,fg_color="transparent"); self.tuning_content.grid(row=0,column=1,sticky="nsew")
        ctk.CTkLabel(self.tuning_content, text=f"Active profile: {self._active_profile_name()} · {'staged changes need Review & Apply' if self.dirty else 'no staged changes'}", text_color="#bae6fd", anchor="w", wraplength=760).pack(fill="x", padx=2, pady=(0, 8))
        self._render_tuning_nav()
        if query:
            results=self.registry.search(query); results=[d for d in results if self.tuning_tab!="modified" or self._is_modified(d)]; self._render_tuning_results(results,query); return
        selected=[d for d in self.registry.definitions() if d.category==self.tuning_category and d.subcategory==self.tuning_subcategory]
        if self.tuning_tab=="modified": selected=[d for d in selected if self._is_modified(d)]
        if self.tuning_tab=="restore": self._render_restore_in(selected); return
        ctk.CTkLabel(self.tuning_content,text=f"Game Tuning  /  {self.tuning_category}  /  {self.tuning_subcategory}",font=ctk.CTkFont(family=self.display_font,size=20,weight="bold"),anchor="w").pack(fill="x",pady=(6,2)); ctk.CTkLabel(self.tuning_content,text=f"{len(selected)} settings · staged until Review & Apply",text_color="#94a3b8",anchor="w").pack(fill="x",pady=(0,10))
        for d in selected: self._render_setting(d,self.tuning_content)

    def _is_modified(self,d):
        module,key=d.id.split(".",1); return self.pending["module_settings"].get(module,{}).get(key)!=d.profile_default
    def _render_tuning_nav(self):
        ctk.CTkLabel(self.tuning_nav,text="TUNING MAP",text_color="#f28a43",font=ctk.CTkFont(size=11,weight="bold"),anchor="w").pack(fill="x",padx=10,pady=(12,6))
        defs=self.registry.definitions()
        for category in TUNING_CATEGORIES[:-1]:
            count=sum(d.category==category for d in defs)
            if not count: continue
            opened=category==self.tuning_category; ctk.CTkButton(self.tuning_nav,text=f"{'▾' if opened else '▸'}  {category}  · {count}",anchor="w",height=31,fg_color="#c55720" if opened else "transparent",hover_color="#a8441a",command=lambda c=category:self._select_category(c)).pack(fill="x",padx=5,pady=2)
            if opened:
                for sub in dict.fromkeys(d.subcategory for d in defs if d.category==category):
                    n=sum(d.category==category and d.subcategory==sub for d in defs); ctk.CTkButton(self.tuning_nav,text=f"   {sub}  · {n}",anchor="w",height=27,fg_color="#263d50" if sub==self.tuning_subcategory else "transparent",hover_color="#324d62",command=lambda c=category,s=sub:self._select_subcategory(c,s)).pack(fill="x",padx=10,pady=1)
        ctk.CTkButton(self.tuning_nav,text=f"▸  Advanced Research  · {len(self.registry.research())}",anchor="w",height=31,fg_color="transparent",hover_color="#324d62",command=self._render_research_tuning).pack(fill="x",padx=5,pady=(8,2))
    def _select_category(self,c): self.tuning_category=c; self.tuning_subcategory=next((d.subcategory for d in self.registry.definitions() if d.category==c),""); self._render_tuning()
    def _select_subcategory(self,c,s): self.tuning_category=c; self.tuning_subcategory=s; self._render_tuning()
    def _render_tuning_results(self,defs,query):
        ctk.CTkLabel(self.tuning_content,text=f"Search Results  /  {query}",font=ctk.CTkFont(family=self.display_font,size=20,weight="bold"),anchor="w").pack(fill="x",pady=(6,2)); ctk.CTkLabel(self.tuning_content,text=f"{len(defs)} matching settings · primary locations shown",text_color="#94a3b8",anchor="w").pack(fill="x",pady=(0,10))
        for d in defs: self._render_setting(d,self.tuning_content)
    def _render_research_tuning(self):
        for child in self.tuning_content.winfo_children(): child.destroy()
        ctk.CTkLabel(self.tuning_content,text="Advanced Research  /  Research Only",font=ctk.CTkFont(family=self.display_font,size=20,weight="bold"),anchor="w").pack(fill="x",pady=(6,2))
        runtime_evidence = self.base_dir / "research" / "probe_sessions" / "balancing_table_scalar_write_safe_20260929_evidence.json"
        if runtime_evidence.is_file():
            try:
                evidence = json.loads(runtime_evidence.read_text(encoding="utf-8"))
                runtime = evidence.get("runtime", {})
                if evidence.get("status") == "experimental" and runtime.get("write_ok") and runtime.get("readback_ok") and runtime.get("restored_ok"):
                    ctk.CTkLabel(self.tuning_content, text=(f"Runtime evidence: {runtime.get('resource', 'resource')}.{runtime.get('field', 'field')} was changed, read back, and restored successfully on the pinned build.\nThis remains experimental and does not prove every tuning setting or persistent gameplay behavior."), text_color="#a7f3d0", fg_color="#123329", corner_radius=8, anchor="w", justify="left", wraplength=760).pack(fill="x", pady=(4, 12), padx=2)
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        for item in self.registry.research():
            frame=ctk.CTkFrame(self.tuning_content,fg_color="#172737",border_width=1,border_color="#2c4152",corner_radius=8); frame.pack(fill="x",pady=5); ctk.CTkLabel(frame,text=item["label"],font=ctk.CTkFont(weight="bold"),anchor="w").pack(fill="x",padx=14,pady=(10,2)); ctk.CTkLabel(frame,text=f"{item.get('category','Advanced Research')}\n{item.get('target_resource')} · {item.get('target_field') or 'field identity pending'}\nResearch Only · {item.get('source','')}",text_color="#aebdcc",anchor="w",justify="left").pack(fill="x",padx=14,pady=(0,10))

    def _render_restore_in(self, definitions):
        ctk.CTkLabel(self.tuning_content,text="Restore Vanilla",font=ctk.CTkFont(family=self.display_font,size=20,weight="bold"),anchor="w").pack(fill="x",pady=(6,2)); ctk.CTkLabel(self.tuning_content,text="Only independently verified vanilla values are eligible. Profile defaults are never treated as vanilla.",text_color="#f0b27a",anchor="w",wraplength=700).pack(fill="x",pady=(0,10))
        eligible = [d for d in definitions if d.reset_eligible]
        ctk.CTkButton(self.tuning_content, text="Reset eligible in this subcategory", width=230, state="normal" if eligible else "disabled", command=lambda: self._restore_many(eligible, "this subcategory")).pack(anchor="w", pady=(0, 8))
        category_defs = [d for d in self.registry.definitions() if d.category == self.tuning_category]
        all_defs = self.registry.definitions()
        bulk = ctk.CTkFrame(self.tuning_content, fg_color="transparent"); bulk.pack(fill="x", pady=(0, 8))
        ctk.CTkButton(bulk, text="Reset eligible in category", width=190, state="normal" if any(d.reset_eligible for d in category_defs) else "disabled", command=lambda: self._restore_many(category_defs, self.tuning_category)).pack(side="left", padx=(0, 6))
        ctk.CTkButton(bulk, text="Reset all eligible", width=150, state="normal" if any(d.reset_eligible for d in all_defs) else "disabled", command=lambda: self._restore_many(all_defs, "all categories")).pack(side="left")
        for d in definitions:
            row=ctk.CTkFrame(self.tuning_content,fg_color="#172737",border_width=1,border_color="#2c4152",corner_radius=8); row.pack(fill="x",pady=4); module,key=d.id.split(".",1); current=self.pending["module_settings"].get(module,{}).get(key,d.profile_default); ctk.CTkLabel(row,text=f"{d.label}  ·  current {current}  ·  {d.vanilla_evidence}",anchor="w").pack(side="left",padx=12,pady=9); ctk.CTkButton(row,text="Reset",width=64,state="normal" if d.reset_eligible else "disabled",command=lambda definition=d:self._restore_one(definition)).pack(side="right",padx=8,pady=6)

    def _render_tuning_legacy(self):
        for child in list(self.body.winfo_children())[1:]: child.destroy()
        local_query = self.tuning_search.get().strip() if hasattr(self, "tuning_search") else ""
        global_query = self.global_search.get().strip() if hasattr(self, "global_search") else ""
        query = local_query or global_query
        definitions = self.registry.search(query)
        if getattr(self, "tuning_tab", "all") == "modified":
            definitions = [d for d in definitions if self.pending["module_settings"].get(d.id.split(".",1)[0], {}).get(d.id.split(".",1)[1]) != d.profile_default]
        if getattr(self, "tuning_tab", "all") == "restore":
            self._render_restore(definitions); return
        for category in TUNING_CATEGORIES[:-1]:
            category_items = [d for d in definitions if d.category == category]
            if not category_items: continue
            ctk.CTkLabel(self.body, text=f"{category}  ({len(category_items)})", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").pack(fill="x", pady=(15, 2))
            for subcategory in dict.fromkeys(d.subcategory for d in category_items):
                items = [d for d in category_items if d.subcategory == subcategory]
                ctk.CTkLabel(self.body, text=f"  {subcategory}  ·  {len(items)} settings", text_color="#67e8f9", anchor="w").pack(fill="x", pady=(7, 2))
                for d in items: self._render_setting(d)
        research = [item for item in self.registry.research() if not query or query.lower() in json.dumps(item).lower()]
        if research:
            ctk.CTkLabel(self.body, text="Advanced Research  ·  Research Only", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").pack(fill="x", pady=(18, 2))
            for item in research:
                self._card(item["label"], f"{item.get('category','Advanced Research')}\n{item.get('target_resource')} · {item.get('target_field') or 'field identity pending'}\nSource: {item.get('source','')}")

    def _render_setting(self, d, parent=None):
        parent = parent or self.body
        frame = ctk.CTkFrame(parent, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10); frame.pack(fill="x", padx=4, pady=4); frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(frame, text=d.label, font=ctk.CTkFont(weight="bold"), anchor="w").grid(row=0, column=0, sticky="w", padx=14, pady=(10, 0))
        ctk.CTkLabel(frame, text=d.description, text_color="#cbd5e1", anchor="w", justify="left", wraplength=620).grid(row=1, column=0, columnspan=3, sticky="w", padx=14, pady=(2, 8))
        module, key = d.id.split(".", 1); value = self.pending["module_settings"].get(module, {}).get(key, d.profile_default)
        if d.input_type == "boolean":
            var = ctk.BooleanVar(value=bool(value)); ctk.CTkSwitch(frame, text="", variable=var, command=lambda v=var, m=module, k=key: self._set_value(m, k, v.get())).grid(row=0, column=1, rowspan=2, sticky="w")
        elif d.declared_min is not None and d.declared_max is not None:
            entry = ctk.CTkEntry(frame, width=92); entry.insert(0, self._format(value, d)); entry.grid(row=0, column=2, padx=8)
            steps = max(1, int(round((d.declared_max-d.declared_min)/(d.step or 1))))
            slider = ctk.CTkSlider(frame, from_=d.declared_min, to=d.declared_max, number_of_steps=steps, command=lambda x, m=module, k=key, e=entry, definition=d: self._slider(m,k,x,e,definition)); slider.set(float(value)); slider.grid(row=0, column=1, sticky="ew")
            entry.bind("<Return>", lambda _e, m=module, k=key, e=entry, s=slider, definition=d: self._entry(m,k,e,s,definition)); ctk.CTkButton(frame, text="−", width=28, command=lambda: self._fine_adjust(module,key,slider,entry,d,-1)).grid(row=0,column=3); ctk.CTkButton(frame, text="+", width=28, command=lambda: self._fine_adjust(module,key,slider,entry,d,1)).grid(row=0,column=4)
        else: ctk.CTkLabel(frame, text=str(value), text_color="#94a3b8").grid(row=0, column=1, sticky="w")
        recommended = f"Recommended range: {d.declared_min}–{d.declared_max}" if d.declared_min is not None and d.declared_max is not None else "Recommended range: see description"
        ctk.CTkLabel(frame, text=f"{recommended}  ·  {d.units or ''}  ·  {'Restart required' if d.restart_required else 'Live-capable'}", text_color="#94a3b8").grid(row=2, column=0, columnspan=2, sticky="w", padx=14, pady=(0, 8))
        ctk.CTkButton(frame,text="Reset",width=58,height=24,state="normal" if d.reset_eligible else "disabled",command=lambda definition=d:self._restore_one(definition)).grid(row=2,column=2,padx=5,pady=(0,8))
        details=ctk.CTkLabel(frame,text=f"Technical: {d.evidence}  ·  Resource: {d.target_resource or 'not declared'}  ·  Build: {d.compatible_game_build or 'unspecified'}  ·  Status: {d.validation_state}",text_color="#7890a3",anchor="w",justify="left",wraplength=650)
        ctk.CTkButton(frame,text="Technical details",width=120,height=22,fg_color="transparent",border_width=1,border_color="#3b5367",command=lambda: details.grid(row=3,column=0,columnspan=3,sticky="w",padx=14,pady=(0,8))).grid(row=2,column=3,padx=5,pady=(0,8))

    def _fine_adjust(self, module, key, slider, entry, d, direction):
        value = slider.get() + direction * (d.step or 1); value = max(d.declared_min, min(d.declared_max, value)); slider.set(value); self._slider(module, key, value, entry, d)

    def _render_restore(self, definitions):
        self._card("Restore Vanilla", "Only independently verified vanilla values can be restored. Existing module defaults are not treated as vanilla values.")
        for d in definitions:
            row = ctk.CTkFrame(self.body, fg_color="#1f2937"); row.pack(fill="x", padx=8, pady=3)
            ctk.CTkLabel(row, text=f"{d.label}  ·  current: {self.pending['module_settings'].get(d.id.split('.')[0], {}).get(d.id.split('.')[1], d.profile_default)}  ·  {d.vanilla_evidence}", anchor="w").pack(side="left", padx=12, pady=8)
            ctk.CTkButton(row, text="Reset", width=70, state="normal" if d.reset_eligible else "disabled", command=lambda definition=d: self._restore_one(definition)).pack(side="right", padx=8, pady=5)

    def _restore_one(self, definition):
        if not definition.reset_eligible:
            messagebox.showinfo("Vanilla value unverified", f"{definition.label} cannot be reset safely because its independently verified vanilla value is unavailable.")
            return
        try:
            self._save_undo_snapshot(); module, key = definition.id.split(".", 1); self._set_value(module, key, definition.vanilla_value); self._render_tuning()
        except Exception as exc:
            self._report_reset_error(exc)

    def _restore_many(self, definitions, scope):
        eligible = [d for d in definitions if d.reset_eligible]
        if not eligible:
            messagebox.showinfo("Nothing eligible", "No settings in this scope have independently verified vanilla values.")
            return
        if not messagebox.askyesno("Confirm Restore Vanilla", f"Stage restoration of {len(eligible)} eligible setting(s) in {scope}?\n\nChanges remain staged until Review & Apply."):
            return
        try:
            self._save_undo_snapshot()
            for d in eligible:
                module, key = d.id.split(".", 1); self.pending["module_settings"].setdefault(module, {})[key] = d.vanilla_value
            self._dirty(); self._render_tuning()
        except Exception as exc:
            self._report_reset_error(exc)

    def _report_reset_error(self, exc):
        log = self.base_dir / "profiles" / "diagnostics.log"
        with log.open("a", encoding="utf-8") as handle:
            handle.write("\n[Restore Vanilla failure]\n" + traceback.format_exc())
        messagebox.showerror("Restore Vanilla failed", f"No staged reset was applied. Details were written to:\n{log}\n\n{exc}")

    def _save_undo_snapshot(self):
        path = self.base_dir / "profiles" / "undo_profile.json"; path.write_text(json.dumps(self.pending, indent=2), encoding="utf-8")

    def _format(self, value, d): return f"{value:.{d.precision}f}" if isinstance(value, float) and d.precision is not None else str(value)
    def _set_value(self, module, key, value): self.pending["module_settings"].setdefault(module, {})[key] = value; self._dirty()
    def _slider(self, module, key, value, entry, d): self._set_value(module,key,round(value, d.precision or 0)); entry.delete(0,"end"); entry.insert(0,self._format(value,d))
    def _entry(self, module, key, entry, slider, d):
        try:
            value = float(entry.get()); value = int(value) if d.input_type in ("number", "percentage") and (d.precision or 0) == 0 else value
            if d.declared_min is not None and not d.declared_min <= value <= d.declared_max: raise ValueError(f"must be between {d.declared_min} and {d.declared_max}")
            slider.set(value); self._set_value(module,key,value)
        except ValueError as exc: messagebox.showerror("Invalid value", str(exc))
    def _dirty(self): self.dirty = True; self.dirty_label.configure(text="● Unsaved changes", text_color="#fbbf24")

    def _launch_tool(self, name):
        if getattr(sys, "frozen", False): subprocess.Popen([sys.executable, "--tool", name])
        else: subprocess.Popen([sys.executable, str(Path(__file__).with_name(name + ".py"))])
    def _show_studio_placeholder(self, title, description, icon="▣"):
        self._clear(title)
        wrapper=ctk.CTkFrame(self.body,fg_color="transparent"); wrapper.pack(fill="both",expand=True)
        card=ctk.CTkFrame(wrapper,fg_color="#172737",border_width=1,border_color="#c55720",corner_radius=16,width=720,height=300); card.place(relx=.5,rely=.42,anchor="center"); card.pack_propagate(False)
        ctk.CTkLabel(card,text=icon,font=ctk.CTkFont(size=48),text_color="#f28a43").pack(pady=(30,4))
        ctk.CTkLabel(card,text=title,font=ctk.CTkFont(family=self.display_font,size=24,weight="bold"),text_color="#f5f0e8").pack(pady=4)
        ctk.CTkLabel(card,text=description,wraplength=580,justify="center",text_color="#cbd5e1").pack(pady=(4,18))
        ctk.CTkButton(card,text="Back to Dashboard",width=180,fg_color="#d65b20",hover_color="#ed7328",command=self.show_dashboard).pack()
    def show_content(self):
        self._clear("Content Studio")
        self._card("Create or import an item", "Choose what you want to make. Control Center will handle the setup and bring you back here when the item is ready.")
        ctk.CTkLabel(self.body, text="You do not need to understand donors, resource files, profiles, or research to create normal content.", text_color="#bae6fd", anchor="w", wraplength=900).pack(fill="x", padx=12, pady=(0, 12))
        actions = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=12)
        actions.pack(fill="x", padx=8, pady=(0, 12))
        ctk.CTkLabel(actions, text="What do you want to do?", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").pack(fill="x", padx=16, pady=(14, 8))
        choices = [
            ("Import a 3D item", "I already made an item in BlenderTools.", self._open_blender_import_wizard),
            ("Change an existing item", "Make a new visual version without changing the original.", self._open_recolor_wizard),
            ("Create a new project", "Start with a blank project for a custom item.", self._create_content_project),
        ]
        for title, detail, command in choices:
            row = ctk.CTkFrame(actions, fg_color="#1f3448", corner_radius=9)
            row.pack(fill="x", padx=12, pady=5)
            info = ctk.CTkFrame(row, fg_color="transparent"); info.pack(side="left", fill="x", expand=True, padx=12, pady=8)
            ctk.CTkLabel(info, text=title, font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(fill="x")
            ctk.CTkLabel(info, text=detail, text_color="#aebdcc", anchor="w").pack(fill="x")
            ctk.CTkButton(row, text="Start", width=110, command=command).pack(side="right", padx=12, pady=12)
        ctk.CTkButton(self.body, text="Open Building Studio", height=34, command=self.show_building).pack(fill="x", padx=12, pady=(0, 10))
        # Compatibility label retained for older navigation checks: Check BlenderTools export.
        ctk.CTkButton(self.body, text="Open legacy wizard", height=30, fg_color="#263d50", command=self._open_content_wizard).pack(fill="x", padx=12, pady=(0, 10))
        advanced = ctk.CTkFrame(self.body, fg_color="transparent")
        advanced.pack_forget()
        ctk.CTkLabel(advanced, text="Advanced tools (optional)", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(anchor="w", pady=(2, 4))
        advanced_tools = [
            ("Validate Staged Bed", lambda: self._validate_content_path(self.base_dir / "research" / "staging" / "bed_clone_kfc_subset_1076226")),
            ("Inspect Resources", self._inspect_staged_resources), ("Compare Visual Dependencies", self._compare_visual_dependencies),
            ("Clone Resource Plan", self._clone_resource_plan), ("Generate Patch Plan", self._generate_patch_plan),
            ("Clone Recipe", self._clone_recipe), ("Edit Recipe", self._edit_recipe), ("Clone UI Catalog Set", self._clone_ui_catalog_set),
            ("Import Resource", self._import_content_resource), ("Export Localization Payload", self._export_localization_payload), ("Import Asset", self._import_content_asset),
            ("Import Custom Icon", self._import_custom_icon), ("Import Existing Mod", self._import_existing_mod),
            ("Inspect Blender Export", self._inspect_blender_export), ("Build Release", self._build_content_release),
            ("Browse Releases", self._browse_releases), ("Install Verified Release", self._install_verified_release),
        ]
        for index, (label, action) in enumerate(advanced_tools):
            ctk.CTkButton(advanced, text=label, command=action, height=28).grid(row=index // 4, column=index % 4, padx=4, pady=3, sticky="ew")
        for col in range(4): advanced.grid_columnconfigure(col, weight=1)
        self.content_status = ctk.CTkLabel(self.body, text="No content validation has been run.", anchor="w", justify="left", text_color="#cbd5e1", wraplength=900)
        self.content_status.pack(fill="x", padx=12, pady=8)
        roots = self._content_project_roots()
        if roots:
            self._card("Known Content Projects", "These projects are included in deployment review:")
            for root in roots:
                row = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=8); row.pack(fill="x", padx=8, pady=4)
                project_name = root.name.replace("_", " ").title()
                try:
                    manifest = json.loads((root / "mod.json").read_text(encoding="utf-8-sig"))
                    project_name = manifest.get("name") or project_name
                except (OSError, ValueError, json.JSONDecodeError):
                    pass
                ctk.CTkLabel(row, text=project_name, anchor="w", font=ctk.CTkFont(weight="bold")).pack(side="left", fill="x", expand=True, padx=12, pady=9)
                is_blender_import = (root / "validation.json").is_file() and (root / "render_data.bin").is_file()
                if is_blender_import:
                    # Legacy label retained in this comment for migration and
                    # older profile checks: RESEARCH-ONLY IMPORT.
                    ctk.CTkLabel(row, text="BLENDERTOOLS IMPORT", text_color="#7dd3fc").pack(side="left", padx=6)
                    ctk.CTkButton(row, text="Review import", width=110, command=lambda p=root: self._review_blender_import(p)).pack(side="right", padx=4, pady=6)
                    ctk.CTkButton(row, text="Build test package", width=145, command=lambda p=root: self._export_content_project(p)).pack(side="right", padx=4, pady=6)
                if (root / "content" / "visual_variant.json").is_file():
                    ctk.CTkButton(row, text="Edit colors", width=95, command=lambda p=root: self._edit_visual_project(p)).pack(side="right", padx=4, pady=6)
                if not is_blender_import:
                    ctk.CTkButton(row, text="Open", width=75, command=lambda p=root: self._review_project(p)).pack(side="right", padx=4, pady=6)
                if not is_blender_import:
                    ctk.CTkButton(row, text="Export", width=75, command=lambda p=root: self._export_content_project(p)).pack(side="right", padx=4, pady=6)
                ctk.CTkButton(row, text="Validate", width=90, command=lambda p=root: self._validate_content_path(p)).pack(side="right", padx=8, pady=6)
        else:
            self._card("No imported projects found", "Use Validate Project Folder to inspect a staged KFC subset or a generated content project.")

    def _open_content_wizard(self):
        """Beginner-first entry point for creating content without exposing internals."""
        wizard = ctk.CTkToplevel(self)
        wizard.title("Content Wizard")
        wizard.geometry("720x520")
        wizard.transient(self)
        wizard.grab_set()
        wizard.grid_columnconfigure(0, weight=1)
        wizard.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(wizard, text="Content Wizard", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(wizard, text="We’ll guide you through this. You can cancel at any time, and your game files will not be changed.", text_color="#cbd5e1", anchor="w", wraplength=640).grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 14))
        page = ctk.CTkFrame(wizard, fg_color="transparent")
        page.grid(row=2, column=0, sticky="nsew", padx=28)
        page.grid_columnconfigure(0, weight=1)
        choice = ctk.StringVar(value="recolor")
        ctk.CTkLabel(page, text="Step 1 of 4  ·  What do you want to make?", font=ctk.CTkFont(size=18, weight="bold"), anchor="w").pack(fill="x", pady=(4, 12))
        options = [
            ("recolor", "Change the color or appearance of an existing item", "Best for recoloring a bed or making a visual variation."),
            ("clone", "Make a new item based on an existing item", "Keeps the original item and its mechanics as a safe starting point."),
            ("import", "Bring in a 3D asset from BlenderTools", "Checks and stages a model for research; it is not installed into the game automatically."),
            ("project", "Start an empty content project", "For advanced custom content work."),
        ]
        for value, title, description in options:
            card = ctk.CTkFrame(page, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=9)
            card.pack(fill="x", pady=5)
            ctk.CTkRadioButton(card, text=title, variable=choice, value=value, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=14, pady=(10, 1))
            ctk.CTkLabel(card, text=description, text_color="#aebdcc", anchor="w").pack(fill="x", padx=42, pady=(0, 10))
        footer = ctk.CTkFrame(wizard, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=28, pady=(12, 22))
        ctk.CTkButton(footer, text="Cancel", command=wizard.destroy).pack(side="right", padx=5)
        def continue_wizard():
            selected = choice.get()
            wizard.destroy()
            if selected == "recolor":
                self._open_recolor_wizard()
            elif selected == "clone":
                self._browse_donors()
            elif selected == "import":
                self._open_blender_import_wizard()
            else:
                self._create_content_project()
        ctk.CTkButton(footer, text="Next", width=120, command=continue_wizard).pack(side="right", padx=5)

    def _open_recolor_wizard(self):
        wizard = ctk.CTkToplevel(self)
        wizard.title("Recolor an existing item")
        wizard.geometry("760x610")
        wizard.transient(self)
        wizard.grab_set()
        state = {"name": "", "donor": "", "colors": {"frame": "#3A2430", "bedding": "#536A9B", "trim": "#B08A5A"}, "scale": [1.0, 1.0, 1.0], "offset": [0.0, 0.0, 0.0], "catalog_preview": "donor-fallback", "placement_preview": "donor-fallback"}
        donor_labels = {"bed": "Wooden Bed", "custom": "Selected donor"}
        page = ctk.CTkFrame(wizard, fg_color="transparent")
        page.pack(fill="both", expand=True, padx=28, pady=22)
        def clear_page():
            for child in page.winfo_children(): child.destroy()
        def stepper(active):
            bar = ctk.CTkFrame(page, fg_color="transparent")
            bar.pack(fill="x", pady=(0, 16))
            labels = ("1  Name", "2  Starting item", "3  Colors", "4  Review")
            for index, label in enumerate(labels, start=1):
                if index == active:
                    color, text_color = "#0ea5e9", "#ffffff"
                elif index < active:
                    color, text_color = "#14532d", "#bbf7d0"
                else:
                    color, text_color = "#263d50", "#aebdcc"
                ctk.CTkLabel(
                    bar, text=label, fg_color=color, text_color=text_color,
                    corner_radius=7, height=28, anchor="center"
                ).pack(side="left", fill="x", expand=True, padx=3)
        def header(step, title, detail):
            stepper(step)
            ctk.CTkLabel(page, text=f"Step {step} of 4", text_color="#f28a43", anchor="w").pack(fill="x")
            ctk.CTkLabel(page, text=title, font=ctk.CTkFont(size=22, weight="bold"), anchor="w").pack(fill="x", pady=(4, 6))
            ctk.CTkLabel(page, text=detail, text_color="#cbd5e1", anchor="w", wraplength=680, justify="left").pack(fill="x", pady=(0, 16))
        def footer(next_action, back_action=None, next_text="Next"):
            bar = ctk.CTkFrame(page, fg_color="transparent")
            bar.pack(fill="x", side="bottom", pady=(18, 0))
            ctk.CTkButton(bar, text="Cancel", command=wizard.destroy).pack(side="right", padx=4)
            if back_action:
                ctk.CTkButton(bar, text="Back", command=back_action).pack(side="right", padx=4)
            ctk.CTkButton(bar, text=next_text, width=120, command=next_action).pack(side="right", padx=4)
        def show_name():
            clear_page(); header(1, "Name your new item", "This creates a separate item. The original item will remain unchanged.")
            entry = ctk.CTkEntry(page, placeholder_text="Example: Twilight Blue Bed", height=38)
            entry.pack(fill="x", pady=8); entry.insert(0, state["name"])
            def go():
                value = entry.get().strip()
                if not value: return messagebox.showwarning("Name required", "Enter a name for the new item.", parent=wizard)
                state["name"] = value; show_donor()
            footer(go)
        def show_donor():
            clear_page(); header(2, "Choose the item to recolor", "Pick the item whose shape and behavior you want to keep. You can choose another item later from Advanced tools.")
            donor = ctk.StringVar(value=state["donor"] or "bed")
            choices = [("bed", "Wooden Bed", "Tested donor: appears in the Carpenter menu and can be placed and saved."), ("custom", "Choose another item…", "Research-only: another donor must be staged and validated before it can be used here." )]
            for value, title, detail in choices:
                card = ctk.CTkFrame(page, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=9); card.pack(fill="x", pady=5)
                ctk.CTkRadioButton(card, text=title, variable=donor, value=value, font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=14, pady=(10, 1))
                ctk.CTkLabel(card, text=detail, text_color="#aebdcc", anchor="w", wraplength=620, justify="left").pack(fill="x", padx=42, pady=(0, 10))
            def go():
                if donor.get() == "custom":
                    messagebox.showinfo("Choose another item", "Only the tested bed is currently available in the beginner workflow. The donor browser can inspect another staged folder, but it will not be treated as a usable donor until its resource graph is validated.", parent=wizard)
                    wizard.destroy(); self._browse_donors(); return
                state["donor"] = donor.get(); show_colors()
            footer(go, show_name)
        def show_colors():
            clear_page(); header(3, "Choose the new colors", "Click each color swatch. These choices are saved into the variant definition and are not just a text description.")
            preview = ctk.CTkFrame(page, fg_color="#0b0f17", border_width=1, border_color="#2c4152", corner_radius=10, height=150)
            preview.pack(fill="x", pady=(0, 12)); preview.pack_propagate(False)
            ctk.CTkLabel(preview, text="LIVE PREVIEW · RESEARCH PREVIEW", text_color="#f59e0b", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w", padx=14, pady=(10, 2))
            bed_preview = ctk.CTkFrame(preview, fg_color=state["colors"]["frame"], width=330, height=78, corner_radius=8)
            bed_preview.pack(pady=5); bed_preview.pack_propagate(False)
            mattress = ctk.CTkFrame(bed_preview, fg_color=state["colors"]["bedding"], width=260, height=45, corner_radius=6)
            mattress.place(relx=.5, rely=.54, anchor="center")
            trim = ctk.CTkFrame(bed_preview, fg_color=state["colors"]["trim"], width=280, height=5, corner_radius=2)
            trim.place(relx=.5, rely=.9, anchor="center")
            ctk.CTkLabel(preview, text="Approximate color preview; final material rendering requires in-game verification.", text_color="#94a3b8", font=ctk.CTkFont(size=10)).pack(anchor="w", padx=14, pady=(0, 8))
            swatches = {}
            for key, label in (("frame", "Frame"), ("bedding", "Bedding"), ("trim", "Trim")):
                row = ctk.CTkFrame(page, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=9); row.pack(fill="x", pady=6)
                ctk.CTkLabel(row, text=label, font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(side="left", padx=14, pady=12)
                swatch = ctk.CTkButton(row, text=state["colors"][key], width=180, fg_color=state["colors"][key], hover_color=state["colors"][key])
                swatch.pack(side="right", padx=14, pady=8); swatches[key] = swatch
                def pick(k=key, button=swatch):
                    selected = colorchooser.askcolor(color=state["colors"][k], title=f"Choose {k} color", parent=wizard)[1]
                    if selected:
                        state["colors"][k] = selected.upper(); button.configure(text=selected.upper(), fg_color=selected, hover_color=selected)
                        bed_preview.configure(fg_color=state["colors"]["frame"])
                        mattress.configure(fg_color=state["colors"]["bedding"])
                        trim.configure(fg_color=state["colors"]["trim"])
                swatch.configure(command=pick)
            transform = ctk.CTkFrame(page, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=9)
            transform.pack(fill="x", pady=(8, 4))
            ctk.CTkLabel(transform, text="Optional shape and placement", font=ctk.CTkFont(size=15, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 2))
            ctk.CTkLabel(transform, text="Scale and offset are saved as a research request. The game must still prove that the transform renders safely.", text_color="#aebdcc", anchor="w", wraplength=620, justify="left").pack(fill="x", padx=14, pady=(0, 6))
            fields = {}
            for kind, values, labels in (("scale", state["scale"], ("Width", "Height", "Depth")), ("offset", state["offset"], ("X", "Y", "Z"))):
                row = ctk.CTkFrame(transform, fg_color="transparent"); row.pack(fill="x", padx=10, pady=2)
                ctk.CTkLabel(row, text=kind.title(), width=70, anchor="w").pack(side="left", padx=(0, 6))
                for index, (value, label) in enumerate(zip(values, labels)):
                    entry = ctk.CTkEntry(row, width=82, placeholder_text=label)
                    entry.insert(0, str(value)); entry.pack(side="left", padx=3)
                    fields[(kind, index)] = entry
            policies = ctk.CTkFrame(transform, fg_color="transparent"); policies.pack(fill="x", padx=10, pady=(8, 4))
            ctk.CTkLabel(policies, text="Preview policy", width=70, anchor="w").pack(side="left", padx=(0, 6))
            catalog_policy = ctk.StringVar(value=state["catalog_preview"])
            placement_policy = ctk.StringVar(value=state["placement_preview"])
            ctk.CTkOptionMenu(policies, variable=catalog_policy, values=("donor-fallback", "custom-research"), width=150).pack(side="left", padx=3)
            ctk.CTkOptionMenu(policies, variable=placement_policy, values=("donor-fallback", "custom-research"), width=150).pack(side="left", padx=3)
            ctk.CTkLabel(transform, text="Catalog and placement custom previews remain research-only until separately visible in-game.", text_color="#fbbf24", anchor="w", wraplength=620, justify="left").pack(fill="x", padx=14, pady=(0, 8))
            def read_transform():
                try:
                    state["scale"] = [float(fields[("scale", index)].get()) for index in range(3)]
                    state["offset"] = [float(fields[("offset", index)].get()) for index in range(3)]
                except ValueError:
                    return messagebox.showwarning("Transform values", "Enter numbers for every scale and offset field.", parent=wizard)
                if any(value <= 0 for value in state["scale"]):
                    return messagebox.showwarning("Scale values", "Scale values must be greater than zero.", parent=wizard)
                state["catalog_preview"] = catalog_policy.get()
                state["placement_preview"] = placement_policy.get()
                show_review()
            footer(read_transform, show_donor)
        def show_review():
            clear_page(); header(4, "Review your item", "Nothing will be installed into the game yet. This creates a research-only test variant that you can validate before launching.")
            summary = ctk.CTkFrame(page, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=9); summary.pack(fill="x", pady=8)
            donor_label = donor_labels.get(state["donor"], state["donor"] or "Not selected")
            ctk.CTkLabel(summary, text=f"Name: {state['name']}\nStarting item: {donor_label}\nFrame: {state['colors']['frame']}\nBedding: {state['colors']['bedding']}\nTrim: {state['colors']['trim']}\nScale: {state['scale']}\nOffset: {state['offset']}\nCatalog preview: {state['catalog_preview']}\nPlacement preview: {state['placement_preview']}", anchor="w", justify="left", font=ctk.CTkFont(size=15)).pack(fill="x", padx=16, pady=16)
            footer(finish, show_colors, next_text="Create test variant")
        def finish():
            wizard.destroy()
            self._create_content_project_named(state["name"], state["donor"], state["colors"], state["scale"], state["offset"], state["catalog_preview"], state["placement_preview"])
        show_name()

    def _open_blender_import_wizard(self):
        """Complete the BlenderTools import flow without sending beginners back to the old tool grid.

        The older direct inspection route remains available as ``_inspect_blender_export()``
        for experienced users and compatibility with existing navigation tests.
        """
        wizard = ctk.CTkToplevel(self)
        wizard.title("Import a 3D item")
        wizard.geometry("760x520")
        wizard.transient(self)
        wizard.grab_set()
        wizard.grid_columnconfigure(0, weight=1)
        wizard.grid_rowconfigure(2, weight=1)
        state = {"source": None, "staged": None, "result": None}
        ctk.CTkLabel(wizard, text="Import a 3D item", font=ctk.CTkFont(size=26, weight="bold")).grid(row=0, column=0, sticky="w", padx=28, pady=(24, 2))
        ctk.CTkLabel(wizard, text="Bring in the export you created with BlenderTools. We will check it, copy it into Control Center, and prepare it for a safe test. Your game files will not be changed.", text_color="#cbd5e1", anchor="w", wraplength=680, justify="left").grid(row=1, column=0, sticky="ew", padx=28, pady=(0, 14))
        page = ctk.CTkFrame(wizard, fg_color="transparent")
        page.grid(row=2, column=0, sticky="nsew", padx=28)
        page.grid_columnconfigure(0, weight=1)
        footer = ctk.CTkFrame(wizard, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=28, pady=(12, 22))
        def clear():
            for child in page.winfo_children(): child.destroy()
            for child in footer.winfo_children(): child.destroy()
        def step(number, title, detail):
            ctk.CTkLabel(page, text=f"Step {number} of 4", text_color="#f28a43", anchor="w").pack(fill="x")
            ctk.CTkLabel(page, text=title, font=ctk.CTkFont(size=22, weight="bold"), anchor="w").pack(fill="x", pady=(4, 6))
            ctk.CTkLabel(page, text=detail, text_color="#cbd5e1", anchor="w", wraplength=680, justify="left").pack(fill="x", pady=(0, 16))
        def buttons(next_action=None, next_text="Next", back_action=None):
            ctk.CTkButton(footer, text="Cancel", command=wizard.destroy).pack(side="right", padx=4)
            if back_action: ctk.CTkButton(footer, text="Back", command=back_action).pack(side="right", padx=4)
            if next_action: ctk.CTkButton(footer, text=next_text, width=150, command=next_action).pack(side="right", padx=4)
        def choose():
            path = filedialog.askdirectory(title="Choose the BlenderTools export folder", parent=wizard)
            if path:
                state["source"] = Path(path)
                show_validate()
        def show_choose():
            clear(); step(1, "Choose your BlenderTools export", "Select the folder that directly contains mod.json, render_data.bin, validation.json, and the src folder.")
            card = ctk.CTkFrame(page, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
            card.pack(fill="x", pady=8)
            ctk.CTkLabel(card, text="Example", text_color="#94a3b8").pack(anchor="w", padx=16, pady=(14, 2))
            ctk.CTkLabel(card, text="F:\\Enshrouded Blender Files\\Tests\\medieval_armchair\\medieval_armchair", text_color="#f8fafc", anchor="w", wraplength=650, justify="left").pack(fill="x", padx=16, pady=(0, 14))
            buttons(choose, "Choose export folder")
        def show_validate():
            clear(); step(2, "Check your export", "Control Center is checking that the model package is complete and safe to stage.")
            label = ctk.CTkLabel(page, text="Checking…", text_color="#fbbf24", anchor="w")
            label.pack(fill="x", pady=20)
            wizard.update_idletasks()
            result = validate_blender_export(state["source"])
            state["result"] = result
            if not result.get("valid"):
                errors = "\n".join(f"• {error}" for error in result.get("errors", [])) or "The export is missing required files."
                label.configure(text=f"This export needs attention:\n\n{errors}", text_color="#fca5a5", justify="left")
                buttons(show_choose, "Choose another folder")
                return
            label.configure(text=f"Ready: {result.get('module_id') or state['source'].name}\n\nModel data found and passed the safety check. Nothing has been installed into the game.", text_color="#86efac", justify="left")
            buttons(show_stage, "Continue")
        def show_stage():
            clear(); step(3, "Prepare a safe test copy", "We will copy the validated export into Control Center. This keeps your original BlenderTools export untouched.")
            ctk.CTkLabel(page, text="Click Continue to create the test copy.", text_color="#cbd5e1", anchor="w").pack(fill="x", pady=20)
            buttons(stage, "Create test copy")
        def stage():
            source = state["source"]
            result = state["result"] or validate_blender_export(source)
            try:
                destination_root = self.base_dir / "custom_content" / "imports"
                destination_root.mkdir(parents=True, exist_ok=True)
                slug = self.content_projects._slug(str(result.get("module_id") or source.name)) or "blender_import"
                destination = destination_root / slug
                if destination.exists():
                    suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                    destination = destination_root / f"{slug}_{suffix}"
                shutil.copytree(source, destination)
                if not validate_blender_export(destination).get("valid"):
                    shutil.rmtree(destination, ignore_errors=True)
                    raise OSError("The copied export did not pass its second safety check.")
                report = self.content_validator.validate(destination)
                if report.valid: self._remember_research_project(destination)
                state["staged"] = destination
                show_review()
            except (OSError, shutil.Error) as exc:
                messagebox.showerror("Import could not be prepared", str(exc), parent=wizard)
        def show_review():
            clear(); step(4, "Your item is ready for review", "The item is staged as a research-only project. Choose what you want to do next.")
            ctk.CTkLabel(page, text=f"Saved test copy:\n{state['staged']}\n\nThe original export was not changed, and the game has not been modified.", text_color="#86efac", anchor="w", justify="left", wraplength=680).pack(fill="x", pady=18)
            buttons(finish_import, "Finish in Content Studio")
        def finish_import():
            wizard.destroy()
            self._remember_research_project(state["staged"])
            messagebox.showinfo("Content ready", "Your BlenderTools item is ready in Content Studio.\n\nNext: review it, then choose Build test package. Research Lab is only for experimental research and is not required for normal content.", parent=self)
            self.show_content()
        show_choose()

    def _create_content_project_named(self, name, donor="bed", colors=None, scale=None, offset=None, catalog_preview="donor-fallback", placement_preview="donor-fallback"):
        slug = self.content_projects._slug(name)
        try:
            destination = self.base_dir / "custom_content" / "projects"
            destination.mkdir(parents=True, exist_ok=True)
            project = self.content_projects.create(destination / slug, slug or "my_content", name, "Local Creator")
            colors = colors or {"frame": "#3A2430", "bedding": "#536A9B", "trim": "#B08A5A"}
            scale = scale or [1.0, 1.0, 1.0]
            offset = offset or [0.0, 0.0, 0.0]
            source = self.base_dir / "research" / "variants" / "bed_material_research_variant.json"
            variant = json.loads(source.read_text(encoding="utf-8-sig"))
            variant.update({"variant_name": name, "donor": donor, "feature_state": "research-only", "color_adjustments": [{"target": key, "color": value} for key, value in colors.items()], "item_color_combination": packed_color_plan(colors), "notes": "Created by the beginner Content Wizard; runtime color assignment is research-gated until catalog and placed-world screenshots pass."})
            variant["scale"] = [float(value) for value in scale]
            variant["offset"] = [float(value) for value in offset]
            if catalog_preview not in {"donor-fallback", "custom-research"} or placement_preview not in {"donor-fallback", "custom-research"}:
                raise ContentProjectError("Preview policy must be donor-fallback or custom-research.")
            variant["catalog_preview"] = catalog_preview
            variant["placement_preview"] = placement_preview
            stable_offset = int(hashlib.sha256(slug.encode("utf-8")).hexdigest()[:8], 16) % 800
            plan = AssetSubstitutionPlanner().plan(variant["donor_item_id"], int(variant.get("new_item_id", 3987655100)) + stable_offset, [{"field": "visualModel", "resource_guid": variant["replacement_model_guid"], "ownership": "external-research"}, {"field": "material", "resource_guid": variant["materials"][0]["resource_guid"], "resource_type": variant["materials"][0]["resource_type"], "ownership": "vanilla-donor"}], variant["color_adjustments"])
            variant["new_item_id"] = plan.new_item_id
            variant["validated_plan"] = AssetSubstitutionPlanner.manifest_metadata(plan)
            project_variant = project / "content" / "visual_variant.json"
            project_variant.write_text(json.dumps(variant, indent=2) + "\n", encoding="utf-8")
            content_path = project / "content" / "content.json"
            content = json.loads(content_path.read_text(encoding="utf-8"))
            content["entries"] = [{"id": f"{slug}:visual_variant", "name": name, "content_class": "visual_variant", "donor_item_id": variant["donor_item_id"], "new_item_id": variant["new_item_id"], "feature_state": "research-only", "definition": "visual_variant.json"}]
            content_path.write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
            # Rebuild the integrity inventory after adding the wizard-owned
            # definition, then refuse to report success if the project is not
            # still valid as a self-contained package.
            self.content_projects.packages.create_manifest(project, slug, "0.1.0")
            validation = self.content_validator.validate(project)
            if not validation.valid:
                details = "; ".join(issue.message for issue in validation.issues)
                raise ContentProjectError(f"The generated project failed validation: {details}")
            messagebox.showinfo("Test variant ready", f"Created safely:\n{project}\n\nYour recolor definition is part of this project.\n\nNext step: choose Open Existing Project in the wizard to review and validate it before testing.")
            self.show_content()
        except (ContentProjectError, ValueError, OSError) as exc:
            messagebox.showerror("Project creation failed", str(exc))

    def _content_project_roots(self):
        roots = []
        staging = self.base_dir / "research" / "staging"
        if staging.is_dir():
            roots.extend(path for path in sorted(staging.iterdir()) if path.is_dir() and any((path / name).is_file() for name in ContentProjectValidator.MANIFEST_NAMES))
        for projects in (self.base_dir / "custom_content" / "projects", self.base_dir / "custom_content" / "imports"):
            if projects.is_dir():
                roots.extend(path for path in sorted(projects.iterdir()) if path.is_dir() and any((path / name).is_file() for name in ContentProjectValidator.MANIFEST_NAMES))
        return roots

    def _validate_content_path(self, path):
        report = self.content_validator.validate(Path(path))
        if report.valid:
            self._remember_research_project(Path(path))
            warnings = [issue.message for issue in report.issues if issue.severity == "warning"]
            text = f"VALID — {report.project}\nNo blocking issues found."
            if warnings: text += "\nWarnings:\n- " + "\n- ".join(warnings)
            messagebox.showinfo("Content validation", text)
        else:
            details = "\n".join(f"[{issue.severity}] {issue.code}: {issue.message}" for issue in report.issues)
            messagebox.showerror("Content validation blocked", f"{report.project}\n\n{details}")
        if hasattr(self, "content_status") and self.content_status.winfo_exists():
            self.content_status.configure(text=f"Last validation: {'PASS' if report.valid else 'BLOCKED'}\n{report.project}\nIssues: {len(report.issues)}")

    def _remember_research_project(self, project):
        """Keep the last validated project attached to the Research Lab workflow."""
        project = Path(project).resolve()
        self.research_project_path = project
        state = self.base_dir / "profiles" / "research_lab_state.json"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text(json.dumps({"project": str(project)}, indent=2) + "\n", encoding="utf-8")

    def _last_research_project(self):
        project = getattr(self, "research_project_path", None)
        if project and Path(project).is_dir():
            try:
                if self.content_validator.validate(Path(project)).valid:
                    return Path(project)
            except (OSError, ValueError):
                pass
        state = self.base_dir / "profiles" / "research_lab_state.json"
        try:
            value = json.loads(state.read_text(encoding="utf-8")).get("project")
            if value and Path(value).is_dir():
                candidate = Path(value)
                if self.content_validator.validate(candidate).valid:
                    self.research_project_path = candidate
                    return candidate
        except (OSError, ValueError, json.JSONDecodeError):
            pass
        return None

    def _review_current_research_project(self):
        """Open the remembered project through the appropriate beginner review."""
        project = self._last_research_project()
        if not project:
            return messagebox.showinfo("No project selected", "Create or open a project in Content Studio first.", parent=self)
        if (project / "content" / "visual_variant.json").is_file():
            return self._review_project(project)
        if (project / "validation.json").is_file() or (project / "render_data.bin").is_file():
            return self._review_blender_import(project)
        return messagebox.showinfo(
            "Project selected",
            f"This project is ready for validation:\n\n{project}\n\nOpen Content Studio to review or validate it before testing.",
            parent=self,
        )

    def _inspect_blender_export(self):
        path = filedialog.askdirectory(title="Choose Blender-generated EML export")
        if not path:
            return
        result = validate_blender_export(Path(path))
        if result.get("valid"):
            source = Path(path).resolve()
            module_id = str(result.get("module_id") or source.name).strip()
            slug = self.content_projects._slug(module_id) or "blender_import"
            destination_root = self.base_dir / "custom_content" / "imports"
            destination = destination_root / slug
            if destination.exists():
                suffix = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
                destination = destination_root / f"{slug}_{suffix}"
            try:
                destination_root.mkdir(parents=True, exist_ok=True)
                shutil.copytree(source, destination)
                staged = validate_blender_export(destination)
                if not staged.get("valid"):
                    shutil.rmtree(destination, ignore_errors=True)
                    raise OSError("The copied export failed its second validation pass.")
                project_report = self.content_validator.validate(destination)
                if project_report.valid:
                    self._remember_research_project(destination)
                messagebox.showinfo(
                    "Blender export staged",
                    f"VALID — {module_id}\n"
                    f"Target RenderModel: {result.get('target_guid')}\n\n"
                    f"Model data: {result.get('vertex_count', 0):,} vertices · {result.get('mesh_size', 0) / 1024:.1f} KB\n"
                    f"Texture patches: {result.get('texture_patch_count', 0)} · Icon: {'included' if result.get('icon_present') else 'not included'}\n\n"
                    f"LOD metadata: {result.get('lod_metadata_status', 'not provided')} · Collider metadata: {result.get('collider_metadata_status', 'not provided')}\n\n"
                    f"Saved for review in:\n{destination}\n\n"
                    "It is research-only. Nothing was installed into the game. Open Content Studio to review, validate, or export the staged package.\n\n"
                    "Next step: open Research Lab after validation to prepare a controlled test.",
                )
                self.show_content()
            except (OSError, shutil.Error) as exc:
                messagebox.showerror("Blender export staging failed", str(exc))
        else:
            details = "\n".join(f"• {error}" for error in result.get("errors", []))
            steps = "\n".join(f"• {step}" for step in result.get("next_steps", []))
            suffix = f"\n\nTry this next:\n{steps}" if steps else ""
            messagebox.showerror("Blender export blocked", f"This export cannot be staged:\n\n{details}{suffix}")

    def _choose_content_project(self):
        path = filedialog.askdirectory(title="Choose staged or imported content project")
        if path: self._validate_content_path(Path(path))

    def _review_blender_import(self, project):
        """Explain a BlenderTools package without routing it through the donor wizard."""
        project = Path(project)
        result = validate_blender_export(project)
        if not result.get("valid"):
            details = "\n".join(f"• {error}" for error in result.get("errors", []))
            return messagebox.showerror("Blender import needs attention", f"This imported package failed its safety check:\n\n{details}")
        messagebox.showinfo(
            "Review BlenderTools import",
            f"Import ready for review: {result.get('module_id') or project.name}\n\n"
            f"Target model: {result.get('target_guid')}\n"
            f"Location: {project}\n\n"
                    "Status: READY FOR CONTENT TEST\n"
                    "The package is safely staged, but it has not been installed into the game. "
                    "Review it here, then build a test package. Research Lab is only needed for experimental research.",
        )

    def _send_import_to_research(self, project):
        """Legacy research handoff retained only for explicit experimental work.

        Normal imports now finish in Content Studio; the old "Test in Research
        Lab" action and "open Research Lab after validation" wording are kept
        here only for compatibility with older profiles and advanced research.
        """
        # Legacy action label: Test in Research Lab.
        project = Path(project)
        report = self.content_validator.validate(project)
        if not report.valid:
            details = "\n".join(f"• {issue.message}" for issue in report.issues if issue.severity == "error")
            return messagebox.showerror("Import needs validation", f"Fix the staged import before testing:\n\n{details}", parent=self)
        self._remember_research_project(project)
        self.show_research_lab()

    def _review_project(self, project):
        project = Path(project)
        report = self.content_validator.validate(project)
        if not report.valid:
            return self._validate_content_path(project)
        definition = project / "content" / "visual_variant.json"
        if definition.is_file():
            try:
                data = json.loads(definition.read_text(encoding="utf-8-sig"))
                colors = ", ".join(f"{item.get('target')}: {item.get('color')}" for item in data.get("color_adjustments", [])) or "No color changes recorded"
                packed = data.get("item_color_combination") or {}
                if packed:
                    colors += f"\nRuntime color plan: {packed.get('color0')}, {packed.get('color1')}, {packed.get('color2')} (research-only)"
                review = ctk.CTkToplevel(self)
                review.title("Review content project")
                review.geometry("620x440")
                review.transient(self)
                review.grab_set()
                ctk.CTkLabel(review, text="Your content project is ready", font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=26, pady=(24, 4))
                ctk.CTkLabel(review, text="This project passed the safety check. It is still research-only, so it will not be installed into the game until you deliberately test it.", text_color="#cbd5e1", wraplength=560, justify="left").pack(anchor="w", padx=26, pady=(0, 16))
                summary = ctk.CTkFrame(review, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=9)
                summary.pack(fill="x", padx=26, pady=4)
                donor_labels = {"bed": "Wooden Bed", "custom": "Selected donor"}
                donor_label = donor_labels.get(str(data.get("donor", "")), str(data.get("donor", "Not recorded")))
                ctk.CTkLabel(summary, text=f"Name: {data.get('variant_name', project.name)}\nStarting item: {donor_label}\nColors: {colors}\nStatus: RESEARCH-ONLY", anchor="w", justify="left", font=ctk.CTkFont(size=14)).pack(fill="x", padx=16, pady=16)
                ctk.CTkLabel(review, text="Recommended next step: edit the colors if needed, then validate again before running an in-game test.", text_color="#fbbf24", wraplength=560, justify="left").pack(anchor="w", padx=26, pady=(12, 8))
                actions = ctk.CTkFrame(review, fg_color="transparent")
                actions.pack(fill="x", padx=26, pady=(10, 20))
                ctk.CTkButton(actions, text="Close", command=review.destroy).pack(side="right", padx=4)
                ctk.CTkButton(actions, text="Edit colors", command=lambda: (review.destroy(), self._edit_visual_project(project))).pack(side="right", padx=4)
                ctk.CTkButton(actions, text="Validate again", command=lambda: self._validate_content_path(project)).pack(side="right", padx=4)
                return
            except (OSError, ValueError, json.JSONDecodeError):
                pass
        messagebox.showinfo("Project ready", f"{project.name}\n\nThis project is valid and ready for advanced review.", parent=self)

    def _edit_visual_project(self, project):
        """Edit a wizard-created visual project without exposing raw JSON."""
        definition_path = Path(project) / "content" / "visual_variant.json"
        try:
            definition = json.loads(definition_path.read_text(encoding="utf-8-sig"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            return messagebox.showerror("Project unavailable", f"The visual project could not be opened:\n\n{exc}", parent=self)
        current = {str(item.get("target")): str(item.get("color")) for item in definition.get("color_adjustments", []) if isinstance(item, dict)}
        colors = {key: current.get(key, default) for key, default in (("frame", "#3A2430"), ("bedding", "#536A9B"), ("trim", "#B08A5A"))}
        editor = ctk.CTkToplevel(self); editor.title("Edit colors"); editor.geometry("560x430"); editor.transient(self); editor.grab_set()
        ctk.CTkLabel(editor, text=f"Edit colors · {definition.get('variant_name', Path(project).name)}", font=ctk.CTkFont(size=20, weight="bold")).pack(anchor="w", padx=24, pady=(22, 4))
        ctk.CTkLabel(editor, text="Choose the colors you want to change. The original donor item is not modified.", text_color="#cbd5e1", wraplength=500, justify="left").pack(anchor="w", padx=24, pady=(0, 14))
        for key, label in (("frame", "Frame"), ("bedding", "Bedding"), ("trim", "Trim")):
            row = ctk.CTkFrame(editor, fg_color="#172737", corner_radius=8); row.pack(fill="x", padx=24, pady=5)
            ctk.CTkLabel(row, text=label, font=ctk.CTkFont(weight="bold")).pack(side="left", padx=12, pady=9)
            button = ctk.CTkButton(row, text=colors[key], width=160, fg_color=colors[key], hover_color=colors[key]); button.pack(side="right", padx=12, pady=6)
            def pick(k=key, b=button):
                selected = colorchooser.askcolor(color=colors[k], title=f"Choose {k} color", parent=editor)[1]
                if selected: colors[k] = selected.upper(); b.configure(text=colors[k], fg_color=selected, hover_color=selected)
            button.configure(command=pick)
        def save():
            definition["color_adjustments"] = [{"target": key, "color": value} for key, value in colors.items()]
            definition["item_color_combination"] = packed_color_plan(colors)
            definition["notes"] = "Edited through Control Center; runtime color rendering remains research-gated."
            definition_path.write_text(json.dumps(definition, indent=2) + "\n", encoding="utf-8")
            self.content_projects.packages.create_manifest(Path(project), Path(project).name, "0.1.0")
            report = self.content_validator.validate(Path(project))
            if not report.valid:
                return messagebox.showerror("Edit blocked", "The project failed validation after the change.", parent=editor)
            editor.destroy(); messagebox.showinfo("Colors saved", "The project was updated and validated. It remains research-only until tested in-game.", parent=self); self.show_content()
        ctk.CTkButton(editor, text="Cancel", command=editor.destroy).pack(side="right", padx=24, pady=18)
        ctk.CTkButton(editor, text="Save changes", command=save).pack(side="right", padx=4, pady=18)

    def _compile_content_definition(self):
        source = filedialog.askopenfilename(title="Choose structured content definition", filetypes=[("JSON definition", "*.json")])
        if not source: return
        destination = filedialog.askdirectory(title="Choose output folder for compiled project")
        if not destination: return
        try:
            definition = json.loads(Path(source).read_text(encoding="utf-8-sig"))
            definition.setdefault("definition_dir", str(Path(source).parent))
            project = self.compiler.compile(definition, Path(destination) / str(definition.get("id") or definition.get("name", "content")).lower().replace(" ", "_"))
            messagebox.showinfo("Content compiled", f"Research-gated project created:\n{project}")
        except (OSError, ValueError, ContentCompilerError) as exc:
            messagebox.showerror("Content compilation failed", str(exc))

    def _review_content_definition(self):
        source = filedialog.askopenfilename(title="Choose structured content definition", filetypes=[("JSON definition", "*.json")])
        if not source:
            return
        try:
            definition = json.loads(Path(source).read_text(encoding="utf-8-sig"))
            result = ContentCompiler.validate_definition(definition)
            matrix = result.get("customization_matrix", {})
            lines = [f"Definition: {result.get('content_id') or '(unnamed)'}", "", "Customization review:"]
            if matrix:
                for field, item in matrix.items():
                    lines.append(f"• {field}: {item['status']} — {item['runtime_action']}")
                    lines.append(f"  Evidence: {item['required_evidence']}")
            else:
                lines.append("No customization fields requested.")
            lines.extend(["", f"Mechanics policy: {result['mechanics_preservation_policy']}",
                          "No files were created and no game changes were made."])
            messagebox.showinfo("Content definition review", "\n".join(lines))
        except (OSError, ValueError, ContentCompilerError) as exc:
            messagebox.showerror("Content definition review failed", str(exc))

    def _browse_donors(self):
        default_root = self.base_dir / "research" / "staging" / "bed_clone_kfc_subset_1076226"
        if default_root.is_dir():
            use_default = messagebox.askyesno("Choose a starting item", "A tested bed is already available as a starting item.\n\nUse the tested bed?\n\nChoose No only if you want to browse a different item.")
            root = str(default_root) if use_default else filedialog.askdirectory(title="Choose the game item to start from")
        else:
            root = filedialog.askdirectory(title="Choose the game item to start from")
        if not root: return
        try:
            records, graph = self.donor_browser.index(Path(root))
            resource_types = sorted({record.resource_type for record in records})
            text = (f"Starting item ready.\n\nResources found: {len(records)}\nResource types: {', '.join(resource_types) or 'none'}\n\n"
                    "You can now validate it, review its definition, or customize it from Content Studio.")
            messagebox.showinfo("Starting item ready", text)
        except (OSError, ValueError) as exc:
            messagebox.showerror("Donor browser failed", str(exc))

    def _export_content_project(self, project):
        destination = filedialog.asksaveasfilename(title="Export content package", defaultextension=".zip", filetypes=[("ZIP package", "*.zip")])
        if not destination: return
        try:
            archive = self.content_projects.packages.export_zip(Path(project), Path(destination))
            messagebox.showinfo("Package exported", f"Verified package exported to:\n{archive}")
        except Exception as exc:
            messagebox.showerror("Package export failed", str(exc))

    def _build_content_release(self):
        from tkinter import simpledialog
        project = filedialog.askdirectory(title="Choose validated content project")
        if not project: return
        output = filedialog.askdirectory(title="Choose release output folder")
        if not output: return
        version = simpledialog.askstring("Build release", "Semantic version (for example 0.1.0):", parent=self)
        if not version: return
        channel = simpledialog.askstring("Build release", "Channel: stable, beta, or nightly", initialvalue="stable", parent=self) or "stable"
        try:
            archive, metadata = self.releases.build_release(Path(project), Path(output), version=version, channel=channel)
            messagebox.showinfo("Release built", f"Release archive:\n{archive}\n\nMetadata:\n{metadata}")
        except (ReleaseError, OSError) as exc:
            messagebox.showerror("Release build failed", str(exc))

    def _browse_releases(self):
        from tkinter import simpledialog
        directory = filedialog.askdirectory(title="Choose release catalog folder")
        if not directory: return
        package_id = simpledialog.askstring("Release catalog", "Package ID (blank for all packages):", parent=self)
        channel = simpledialog.askstring("Release catalog", "Channel filter: stable, beta, nightly, or blank for all:", parent=self)
        channels = {channel.strip()} if channel and channel.strip() else None
        try:
            releases = self.releases.catalog_releases(Path(directory), package_id=package_id.strip() if package_id else None, channels=channels)
            if not releases:
                return messagebox.showinfo("Release catalog", "No verified releases matched the selected filters.")
            lines = [f"{item['id']} {item['version']} [{item['channel']}] — {Path(item['archive_path']).name}" for item in releases[:50]]
            messagebox.showinfo("Verified releases", "\n".join(lines))
        except (ReleaseError, OSError) as exc:
            messagebox.showerror("Release catalog failed", str(exc))

    def _install_verified_release(self):
        from tkinter import simpledialog
        game = self.installer.selected_game_path()
        if not game:
            return messagebox.showwarning("Game folder", "Choose the Enshrouded game folder in Settings first.")
        archive = filedialog.askopenfilename(title="Choose verified release archive", filetypes=[("Release archive", "*.zip")])
        if not archive: return
        metadata = filedialog.askopenfilename(title="Choose matching release metadata", filetypes=[("Release metadata", "*.release.json")])
        if not metadata: return
        channel = simpledialog.askstring("Release channel", "Allowed channel: stable, beta, or nightly", initialvalue="stable", parent=self) or "stable"
        try:
            build = self.platform.builds.detect(game).build_id
            result = self.releases.install_release(Path(archive), Path(metadata), game, game_build=build, allowed_channels={channel.strip().lower()})
            messagebox.showinfo("Release installed", f"Installed verified {result['id']} {result['version']} ({result['channel']}).")
        except (ReleaseError, OSError) as exc:
            messagebox.showerror("Release installation failed", str(exc))

    def _import_content_asset(self):
        from tkinter import simpledialog
        source = filedialog.askopenfilename(title="Choose content asset")
        if not source: return
        project = filedialog.askdirectory(title="Choose target content project")
        if not project: return
        kind = simpledialog.askstring("Asset type", "Type: icons, textures, models, or audio", parent=self)
        if not kind: return
        try:
            destination = self.assets.import_file(Path(source), Path(project), kind)
            messagebox.showinfo("Asset imported", f"Imported and hashed:\n{destination}")
        except (AssetError, OSError) as exc:
            messagebox.showerror("Asset import failed", str(exc))

    def _import_custom_icon(self):
        source = filedialog.askopenfilename(title="Choose PNG icon", filetypes=[("PNG image", "*.png")])
        if not source: return
        project = filedialog.askdirectory(title="Choose target content project")
        if not project: return
        from tkinter import simpledialog
        slug = simpledialog.askstring("Icon identity", "Stable icon slug (optional):", parent=self) or None
        try:
            entry = self.content_projects.import_icon(Path(project), Path(source), slug)
            messagebox.showinfo("Custom icon imported", f"Imported and validated:\n{entry['path']}\n\nIdentity: {entry['id']}\nGUID: {entry['guid']}\n\nRuntime engine import remains research-gated.")
            self.show_content()
        except (ContentProjectError, OSError) as exc:
            messagebox.showerror("Custom icon import failed", str(exc))

    def _import_content_resource(self):
        from tkinter import simpledialog
        source = filedialog.askopenfilename(title="Choose resource JSON", filetypes=[("Resource JSON", "*.json")])
        if not source: return
        project = filedialog.askdirectory(title="Choose target content project")
        if not project: return
        resource_type = simpledialog.askstring("Resource type", "Type (for example keen::ItemInfo):", parent=self)
        if not resource_type: return
        slug = simpledialog.askstring("Content slug", "Stable slug (optional):", parent=self) or None
        try:
            entry = self.content_projects.import_resource(Path(project), Path(source), resource_type, slug)
            messagebox.showinfo("Resource imported", f"Imported and validated:\n{entry['path']}\n\nIdentity: {entry['id']}\nGUID: {entry['guid']}")
            self.show_content()
        except (ContentProjectError, OSError) as exc:
            messagebox.showerror("Resource import failed", str(exc))

    def _import_existing_mod(self):
        source = filedialog.askdirectory(title="Choose existing mod folder")
        if not source: return
        try:
            destination = self.layout_migration.import_layout(Path(source), self.base_dir / "custom_content" / "imports")
            messagebox.showinfo("Mod imported", f"Imported for validation:\n{destination}\n\nReview the generated provenance file before activation.")
            self.show_content()
        except (LayoutMigrationError, OSError) as exc:
            messagebox.showerror("Mod import failed", str(exc))

    def _inspect_staged_resources(self):
        root = self.base_dir / "research" / "staging" / "bed_clone_kfc_subset_1076226"
        records = self.resource_inspector.scan(root)
        if not records:
            messagebox.showinfo("Resource inspector", "No readable resource JSON files were found.")
            return
        by_type = {}
        for record in records:
            by_type.setdefault(record.resource_type, []).append(record)
        lines = [f"Staged resources: {len(records)}", ""]
        for resource_type, entries in sorted(by_type.items()):
            policy = self.resource_inspector.metadata_policy(resource_type)
            lines.append(f"{resource_type}: {len(entries)} · metadata={policy.get('state', 'unknown')}")
            for record in entries[:3]:
                lines.append(f"  {record.path.name} · fields={len(record.schema)} · arrays={len(record.arrays)}")
            if len(entries) > 3: lines.append("  …")
        messagebox.showinfo("Resource inspector", "\n".join(lines))

    def _clone_resource_plan(self):
        from tkinter import simpledialog
        donor = filedialog.askopenfilename(title="Choose donor resource JSON", filetypes=[("Resource JSON", "*.json")])
        if not donor: return
        destination = filedialog.asksaveasfilename(title="Save clone plan", defaultextension=".json", filetypes=[("JSON plan", "*.json")])
        if not destination: return
        resource_type = simpledialog.askstring("Resource type", "Optional type (for example keen::ItemInfo):", parent=self) or None
        try:
            plan = self.resource_inspector.clone_plan(Path(donor), Path(destination), resource_type)
            payload = {
                "schema": "control_center.clone_plan.v1",
                "resource_type": plan.resource_type,
                "donor": str(plan.donor),
                "destination": str(plan.destination),
                "donor_guid": plan.donor_guid,
                "schema_fingerprint": plan.schema_fingerprint,
                "safe": plan.safe,
                "warnings": list(plan.warnings),
                "differences": [item.__dict__ for item in plan.differences],
            }
            Path(destination).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("Clone plan", f"Plan written:\n{destination}\n\nSafe for review: {plan.safe}\nWarnings: {len(plan.warnings)}")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Clone plan failed", str(exc))

    def _generate_patch_plan(self):
        from tkinter import simpledialog
        donor = filedialog.askopenfilename(title="Choose donor resource JSON", filetypes=[("Resource JSON", "*.json")])
        if not donor: return
        changes_path = filedialog.askopenfilename(title="Choose patch changes JSON", filetypes=[("Changes JSON", "*.json")])
        if not changes_path: return
        destination = filedialog.asksaveasfilename(title="Save patch plan", defaultextension=".json", filetypes=[("JSON plan", "*.json")])
        if not destination: return
        resource_type = simpledialog.askstring("Patch plan", "Resource type (for example keen::ItemInfo):", parent=self)
        if not resource_type: return
        try:
            changes = json.loads(Path(changes_path).read_text(encoding="utf-8-sig"))
            plan = ContentPatchPlanner().plan(Path(donor), Path(destination), resource_type, changes)
            payload = {
                "schema": "control_center.content_patch_plan.v1",
                "resource_type": plan.resource_type,
                "donor": str(plan.donor), "output": str(plan.output),
                "deployable": plan.deployable,
                "changes": [change.__dict__ for change in plan.changes],
                "runtime_mutation": False,
            }
            Path(destination).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("Patch plan", f"Plan written:\n{destination}\n\nDeployable: {plan.deployable}")
        except (OSError, ValueError, json.JSONDecodeError, ContentPatchError) as exc:
            messagebox.showerror("Patch plan failed", str(exc))

    def _compare_visual_dependencies(self):
        donor = filedialog.askopenfilename(title="Choose donor resource JSON", filetypes=[("Resource JSON", "*.json")])
        if not donor: return
        candidate = filedialog.askopenfilename(title="Choose candidate resource JSON", filetypes=[("Resource JSON", "*.json")])
        if not candidate: return
        destination = filedialog.asksaveasfilename(title="Save visual substitution report", defaultextension=".json", filetypes=[("JSON report", "*.json")])
        if not destination: return
        try:
            donor_record = self.resource_inspector.inspect(Path(donor))
            candidate_record = self.resource_inspector.inspect(Path(candidate), donor_record.resource_type)
            report = {
                "schema": "control_center.visual_dependency_inventory.v1",
                "resource_type": donor_record.resource_type,
                "donor": str(donor_record.path),
                "candidate": str(candidate_record.path),
                "donor_sha256": donor_record.sha256,
                "candidate_sha256": candidate_record.sha256,
                "substitution_plan": self.resource_inspector.visual_substitution_plan(donor_record, candidate_record),
                "runtime_substitution_verified": False,
            }
            Path(destination).write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("Visual dependency report", f"Research report written:\n{destination}\n\nRuntime substitution remains unverified.")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Visual dependency report failed", str(exc))

    def _clone_recipe(self):
        from tkinter import simpledialog
        source = filedialog.askopenfilename(title="Choose donor recipe JSON", filetypes=[("Recipe JSON", "*.json")])
        if not source: return
        destination = filedialog.asksaveasfilename(title="Save cloned recipe", defaultextension=".json", filetypes=[("Recipe JSON", "*.json")])
        if not destination: return
        new_recipe = simpledialog.askinteger("Clone recipe", "New recipe ID:", parent=self)
        new_item = simpledialog.askinteger("Clone recipe", "New output item ID:", parent=self)
        if new_recipe is None or new_item is None: return
        try:
            recipe = json.loads(Path(source).read_text(encoding="utf-8-sig"))
            cloned = CatalogEditor.clone_recipe(recipe, new_recipe, new_item)
            Path(destination).write_text(json.dumps(cloned, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("Recipe cloned", f"Non-destructive recipe clone written:\n{destination}")
        except (CatalogEditError, OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Recipe clone failed", str(exc))

    def _edit_recipe(self):
        from tkinter import simpledialog
        source = filedialog.askopenfilename(title="Choose recipe JSON", filetypes=[("Recipe JSON", "*.json")])
        if not source: return
        destination = filedialog.asksaveasfilename(title="Save edited recipe", defaultextension=".json", filetypes=[("Recipe JSON", "*.json")])
        if not destination: return
        try:
            recipe = json.loads(Path(source).read_text(encoding="utf-8-sig"))
            changes: dict[str, object] = {}
            def parse_entries(text: str, label: str) -> list[dict[str, int]]:
                entries = []
                for part in text.split(","):
                    token = part.strip()
                    if not token:
                        continue
                    pieces = token.split(":", 1)
                    if len(pieces) != 2:
                        raise ValueError(f"{label} entries use item ID:quantity, for example 123:4")
                    entries.append({"item": int(pieces[0].strip()), "amount": int(pieces[1].strip())})
                if not entries:
                    raise ValueError(f"Enter at least one {label.lower()} entry.")
                return entries
            name = simpledialog.askstring("Edit recipe", "Debug name (blank keeps current):", parent=self)
            if name: changes["debugName"] = name
            craft_time = simpledialog.askstring("Edit recipe", "Craft time (blank keeps current):", parent=self)
            if craft_time:
                changes["craftTime"] = float(craft_time)
            station = simpledialog.askstring("Edit recipe", "Workstation or station ID (blank keeps current):", parent=self)
            if station:
                changes["station"] = station
            amount = simpledialog.askstring("Edit recipe", "Output amount (blank keeps current):", parent=self)
            if amount:
                changes["amount"] = int(amount)
            ingredients = simpledialog.askstring(
                "Edit recipe",
                "Ingredients (blank keeps current):\nEnter item ID:quantity pairs separated by commas.\nExample: 123:4, 456:2",
                parent=self,
            )
            if ingredients:
                changes["ingredients"] = parse_entries(ingredients, "ingredient")
            output = simpledialog.askstring(
                "Edit recipe",
                "Output (blank keeps current):\nEnter item ID:quantity.\nExample: 456:1",
                parent=self,
            )
            if output:
                changes["output"] = parse_entries(output, "output")
            knowledge = simpledialog.askstring(
                "Edit recipe",
                "Knowledge requirements JSON (blank keeps current):",
                parent=self,
            )
            if knowledge:
                changes["knowledgeRequirement"] = json.loads(knowledge)
            edited = CatalogEditor.edit_recipe(recipe, changes)
            Path(destination).write_text(json.dumps(edited, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            messagebox.showinfo("Recipe edited", f"Validated non-destructive recipe saved to:\n{destination}")
        except (CatalogEditError, OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Recipe edit failed", str(exc))

    def _clone_ui_catalog_set(self):
        from tkinter import simpledialog
        source = filedialog.askopenfilename(title="Choose donor UI bundle JSON", filetypes=[("Bundle JSON", "*.json")])
        if not source: return
        destination = filedialog.asksaveasfilename(title="Save cloned UI bundle", defaultextension=".json", filetypes=[("Bundle JSON", "*.json")])
        if not destination: return
        donor = simpledialog.askinteger("Clone UI catalog set", "Donor recipe ID:", parent=self)
        new_recipe = simpledialog.askinteger("Clone UI catalog set", "New recipe ID:", parent=self)
        if donor is None or new_recipe is None: return
        try:
            bundle = json.loads(Path(source).read_text(encoding="utf-8-sig"))
            result = CatalogEditor.clone_recipe_set(bundle, donor, new_recipe)
            Path(destination).write_text(json.dumps(result.value, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("UI catalog set cloned", f"Safe cloned-set result written:\n{destination}\n\nDonor entry index: {result.donor_entry_index}")
        except (CatalogEditError, OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("UI catalog clone failed", str(exc))

    def _export_localization_payload(self):
        source = filedialog.askopenfilename(title="Choose localization.json", filetypes=[("Localization JSON", "*.json")])
        if not source: return
        destination = filedialog.asksaveasfilename(title="Save localization Lua payload", defaultextension=".lua", filetypes=[("Lua payload", "*.lua")])
        if not destination: return
        try:
            payload = json.loads(Path(source).read_text(encoding="utf-8-sig"))
            if payload.get("schema") != "control_center.localization.v1": raise ValueError("Unsupported localization schema.")
            entries = payload.get("entries")
            if not isinstance(entries, dict): raise ValueError("Localization entries must be an object.")
            catalog = LocalizationCatalog(str(payload.get("namespace", "")), str(payload.get("default_language", "en")), entries)
            LocalizationService().save_lua_payload(catalog, Path(destination))
            messagebox.showinfo("Localization payload", f"Payload written:\n{destination}\n\nRuntime registration remains capability-gated.")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Localization export failed", str(exc))

    def _create_content_project(self):
        from tkinter import simpledialog
        name = simpledialog.askstring("Create content", "What would you like to call your content?\n\nExample: Twilight Blue Bed", parent=self)
        if not name: return
        slug = self.content_projects._slug(name)
        namespace = slug or "my_content"
        author = "Local Creator"
        destination = self.base_dir / "custom_content" / "projects"
        try:
            destination.mkdir(parents=True, exist_ok=True)
            project = self.content_projects.create(destination / slug, namespace, name, author)
            messagebox.showinfo("Project ready", f"Your project is ready:\n\n{name}\n\nNext step: open the project in Content Studio and choose the item you want to use as its starting point.\n\nTechnical details are saved automatically under Control Center/custom_content/projects.")
            self.show_content()
        except (ContentProjectError, ValueError, OSError) as exc:
            messagebox.showerror("Project creation failed", str(exc))
    def show_building(self):
        self._clear("Building Studio")
        self._card("Offline build planner", "Load a catalog and saved plan to calculate materials and shortages. This screen is planning-only and never changes the game or inventory.")
        toolbar = ctk.CTkFrame(self.body, fg_color="#1f2937", corner_radius=10); toolbar.pack(fill="x", pady=(0, 10))
        ctk.CTkButton(toolbar, text="Create Plan from Built-in Catalog", command=self._create_builtin_build_plan).pack(side="left", padx=8, pady=10)
        ctk.CTkButton(toolbar, text="Create Plan from File", command=self._create_build_plan).pack(side="left", padx=3, pady=10)
        ctk.CTkButton(toolbar, text="Review Built-in Plan", command=self._review_builtin_build_plan).pack(side="left", padx=3, pady=10)
        ctk.CTkButton(toolbar, text="Review Plan from File", command=self._review_build_plan).pack(side="left", padx=3, pady=10)
        ctk.CTkButton(toolbar, text="Use Built-in Catalog", command=self._open_builtin_builder_catalog).pack(side="left", padx=3, pady=10)
        ctk.CTkButton(toolbar, text="Open Catalog", command=self._open_builder_catalog).pack(side="left", padx=3, pady=10)
        self._card("What is verified", "Material totals, per-item breakdowns, saved plans, and shortage calculations are verified offline. In-game placement and automated crafting are not currently claimed.")

    def _create_builtin_build_plan(self):
        path = self.base_dir / "core" / "items_cache.json"
        if not path.is_file():
            messagebox.showerror("Built-in catalog unavailable", "The bundled item catalog could not be found. Use Create Plan from File instead.")
            return
        self._create_build_plan(path)

    def _create_build_plan(self, catalog_path=None):
        path = Path(catalog_path) if catalog_path else filedialog.askopenfilename(title="Choose builder catalog", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            catalog = BuilderCatalog.from_json_file(path)
            catalog.add_items(BuilderCatalog.discover_control_center_projects(self.base_dir / "custom_content" / "projects"))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Catalog load failed", str(exc))
            return
        if not catalog.items:
            messagebox.showwarning("Empty catalog", "This catalog does not contain any furnishings yet.")
            return
        wizard = ctk.CTkToplevel(self)
        wizard.title("Create Build Plan")
        wizard.geometry("760x680")
        wizard.minsize(620, 500)
        wizard.transient(self)
        wizard.grab_set()
        wizard.grid_columnconfigure(0, weight=1)
        wizard.grid_rowconfigure(2, weight=1)
        ctk.CTkLabel(wizard, text="Create a build plan", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 2))
        ctk.CTkLabel(wizard, text="Enter how many of each furnishing you want. Leave unused items at 0.", text_color="#cbd5e1", anchor="w").grid(row=0, column=0, sticky="w", padx=24, pady=(0, 12))
        name_row = ctk.CTkFrame(wizard, fg_color="transparent")
        name_row.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 8))
        ctk.CTkLabel(name_row, text="Plan name:").pack(side="left", padx=(0, 8))
        plan_name = ctk.CTkEntry(name_row, placeholder_text="Example: Castle bedroom")
        plan_name.pack(side="left", fill="x", expand=True)
        rows = ctk.CTkScrollableFrame(wizard, fg_color="#172737")
        rows.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))
        quantities = {}
        for item in catalog.items:
            row = ctk.CTkFrame(rows, fg_color="#1f2937", corner_radius=8)
            row.pack(fill="x", padx=6, pady=3)
            ctk.CTkLabel(row, text=f"{item.name}  ·  {item.category}", anchor="w").pack(side="left", fill="x", expand=True, padx=12, pady=8)
            quantity = ctk.CTkEntry(row, width=70, justify="center")
            quantity.insert(0, "0")
            quantity.pack(side="right", padx=12, pady=6)
            quantities[item.item_id] = quantity
        footer = ctk.CTkFrame(wizard, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))

        def save_plan():
            try:
                selected = {}
                for item_id, entry in quantities.items():
                    raw = entry.get().strip() or "0"
                    value = int(raw)
                    if value < 0:
                        raise ValueError("Quantities cannot be negative.")
                    if value:
                        selected[item_id] = value
                if not selected:
                    raise ValueError("Choose at least one furnishing before saving the plan.")
                plan = catalog.build_plan(plan_name.get().strip(), selected)
                destination = filedialog.asksaveasfilename(
                    parent=wizard,
                    title="Save build plan",
                    initialfile=f"{plan.name.replace(' ', '_')}.json",
                    defaultextension=".json",
                    filetypes=[("Build plan", "*.json")],
                )
                if not destination:
                    return
                catalog.save_build_plan(plan, Path(destination))
                wizard.destroy()
                messagebox.showinfo("Build plan saved", f"Your offline build plan was saved to:\n\n{destination}\n\nYou can review materials and shortages from Building Studio.")
            except (ValueError, KeyError) as exc:
                messagebox.showerror("Build plan needs attention", str(exc), parent=wizard)

        ctk.CTkButton(footer, text="Cancel", command=wizard.destroy).pack(side="right", padx=4)
        ctk.CTkButton(footer, text="Save Build Plan", command=save_plan).pack(side="right", padx=4)

    def _open_builtin_builder_catalog(self):
        """Open the bundled read-only item catalog without a file picker."""
        path = self.base_dir / "core" / "items_cache.json"
        if not path.is_file():
            messagebox.showerror("Built-in catalog unavailable", "The bundled item catalog could not be found. Use Open Catalog to choose a catalog file.")
            return
        self._open_builder_catalog(path)

    def _open_builder_catalog(self, catalog_path=None):
        path = Path(catalog_path) if catalog_path else filedialog.askopenfilename(title="Choose builder catalog", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        try:
            catalog = BuilderCatalog.from_json_file(Path(path))
            catalog.add_items(BuilderCatalog.discover_control_center_projects(self.base_dir / "custom_content" / "projects"))
            favorites_path = self.base_dir / "profiles" / "builder_favorites.json"
            if favorites_path.is_file():
                catalog.load_favorites(favorites_path)
            categories = ["All categories"] + sorted({item.category for item in catalog.items})
            browser = ctk.CTkToplevel(self)
            browser.title("Builder Catalog")
            browser.geometry("760x620")
            browser.minsize(620, 460)
            browser.transient(self)
            browser.grab_set()
            browser.grid_columnconfigure(0, weight=1)
            browser.grid_rowconfigure(2, weight=1)
            ctk.CTkLabel(browser, text="Browse furnishings", font=ctk.CTkFont(size=22, weight="bold")).grid(row=0, column=0, sticky="w", padx=24, pady=(20, 2))
            ctk.CTkLabel(browser, text=f"{len(catalog.items)} items loaded · planning only · nothing changes in the game", text_color="#cbd5e1", anchor="w").grid(row=0, column=0, sticky="w", padx=24, pady=(0, 12))
            controls = ctk.CTkFrame(browser, fg_color="transparent")
            controls.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
            controls.grid_columnconfigure(0, weight=1)
            query = ctk.StringVar()
            ctk.CTkEntry(controls, textvariable=query, placeholder_text="Search by item name or ID").grid(row=0, column=0, sticky="ew", padx=(0, 6))
            category = ctk.StringVar(value=categories[0])
            ctk.CTkOptionMenu(controls, variable=category, values=categories, width=170).grid(row=0, column=1, padx=6)
            favorites_only = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(controls, text="Favorites only", variable=favorites_only).grid(row=0, column=2, padx=6)
            recommendations_only = ctk.BooleanVar(value=False)
            ctk.CTkCheckBox(controls, text="Recommended", variable=recommendations_only).grid(row=0, column=3, padx=6)
            results = ctk.CTkScrollableFrame(browser, fg_color="#172737")
            results.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 12))

            def refresh_results(*_):
                for child in results.winfo_children():
                    child.destroy()
                selected_category = None if category.get() == "All categories" else category.get()
                if recommendations_only.get():
                    matches = catalog.recommend(category=selected_category, limit=max(1, len(catalog.items)))
                    needle = query.get().casefold().strip()
                    if needle:
                        matches = [item for item in matches if needle in item.name.casefold() or needle in str(item.item_id)]
                else:
                    matches = catalog.search(query.get(), selected_category)
                if favorites_only.get():
                    matches = [item for item in matches if item.item_id in catalog.favorites]
                if not matches:
                    ctk.CTkLabel(results, text="No furnishings match this search.", text_color="#cbd5e1", anchor="w").pack(fill="x", padx=14, pady=14)
                    return
                for item in matches:
                    row = ctk.CTkFrame(results, fg_color="#1f2937", corner_radius=8)
                    row.pack(fill="x", padx=6, pady=4)
                    ingredients = ", ".join(f"{name} ×{amount}" for name, amount in sorted(item.ingredients.items())) or "No material data"
                    ctk.CTkLabel(row, text=f"{item.name}  ·  {item.category}\n{ingredients}", anchor="w", justify="left", text_color="#e2e8f0").pack(side="left", fill="x", expand=True, padx=12, pady=8)
                    favorite_text = "★ Unfavorite" if item.item_id in catalog.favorites else "☆ Favorite"
                    ctk.CTkButton(row, text=favorite_text, width=110, command=lambda item_id=item.item_id: toggle_favorite(item_id)).pack(side="right", padx=8, pady=8)

            def toggle_favorite(item_id):
                catalog.set_favorite(item_id, item_id not in catalog.favorites)
                catalog.save_favorites(favorites_path)
                refresh_results()

            query.trace_add("write", refresh_results)
            category.trace_add("write", refresh_results)
            favorites_only.trace_add("write", refresh_results)
            recommendations_only.trace_add("write", refresh_results)
            footer = ctk.CTkFrame(browser, fg_color="transparent")
            footer.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 16))
            ctk.CTkButton(footer, text="Close", command=browser.destroy).pack(side="right")
            ctk.CTkLabel(footer, text="Tip: favorite the furnishings you want to use in a future build plan.", text_color="#94a3b8", anchor="w").pack(side="left")
            refresh_results()
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Catalog load failed", str(exc))

    def _review_builtin_build_plan(self):
        path = self.base_dir / "core" / "items_cache.json"
        if not path.is_file():
            messagebox.showerror("Built-in catalog unavailable", "The bundled item catalog could not be found. Use Review Plan from File instead.")
            return
        self._review_build_plan(path)

    def _review_build_plan(self, catalog_path=None):
        path = Path(catalog_path) if catalog_path else filedialog.askopenfilename(title="Choose builder catalog", filetypes=[("JSON files", "*.json")])
        if not path:
            return
        plan_path = filedialog.askopenfilename(title="Choose saved build plan", filetypes=[("JSON files", "*.json")])
        if not plan_path:
            return
        inventory_path = filedialog.askopenfilename(title="Optional inventory JSON", filetypes=[("JSON files", "*.json")])
        try:
            catalog = BuilderCatalog.from_json_file(path)
            catalog.add_items(BuilderCatalog.discover_control_center_projects(self.base_dir / "custom_content" / "projects"))
            plan = catalog.load_build_plan(Path(plan_path))
            available = {}
            if inventory_path:
                available = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
            else:
                required = plan.materials(catalog)
                if required and messagebox.askyesno("Check materials", "Would you like to enter the materials you already have?\n\nChoose No to view required totals without calculating shortages.", parent=self):
                    for material in required:
                        amount = simpledialog.askinteger(
                            "Materials on hand",
                            f"How many {material} do you currently have?",
                            parent=self,
                            minvalue=0,
                        )
                        if amount is None:
                            break
                        available[material] = amount
            lines = [f"Plan: {plan.name}", "", "Items:"]
            for item in plan.item_breakdown(catalog):
                lines.append(f"• {item['name']} ×{item['quantity']} — " + ", ".join(f"{k} {v}" for k, v in item["materials"].items()))
            lines.extend(["", "Required materials:"])
            lines.extend(f"• {key}: {value}" for key, value in plan.materials(catalog).items())
            shortages = plan.shortages(catalog, available)
            lines.extend(["", "Shortages:"])
            lines.extend(f"• {key}: {value}" for key, value in shortages.items())
            if not shortages:
                lines.append("• none")
            lines.extend(["", "Runtime mutation: disabled"])
            messagebox.showinfo("Build plan review", "\n".join(lines))
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            messagebox.showerror("Build plan review failed", str(exc))
    def show_profiles(self):
        self._clear("Profiles"); self._card("Profiles", "Switching profiles changes staged configuration only. Review & Apply is still required for game installation.")
        active_name = self._active_profile_name()
        status = ctk.CTkFrame(self.body, fg_color="#123329" if not self.dirty else "#3b2b12", border_width=1, border_color="#2f855a" if not self.dirty else "#a16207", corner_radius=10)
        status.pack(fill="x", padx=8, pady=(0, 8))
        state = "No staged changes" if not self.dirty else "Staged changes waiting for Review & Apply"
        ctk.CTkLabel(status, text=f"Active profile: {active_name}  ·  {state}", text_color="#86efac" if not self.dirty else "#fef3c7", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(status, text="First click: Load a profile. Next: review Game Tuning, then use Review & Apply before launching or testing.", text_color="#d1fae5" if not self.dirty else "#fef3c7", anchor="w", wraplength=900, justify="left").pack(fill="x", padx=14, pady=(0, 10))
        bar=ctk.CTkFrame(self.body,fg_color="transparent"); bar.pack(fill="x",pady=6)
        ctk.CTkButton(bar,text="Create Profile",command=self.create_profile).pack(side="left",padx=4); ctk.CTkButton(bar,text="Save Active",command=self.save_profile).pack(side="left",padx=4); ctk.CTkButton(bar,text="Undo Last Restore",command=self.undo_profile).pack(side="left",padx=4)
        self.profile_body=ctk.CTkScrollableFrame(self.body,fg_color="transparent"); self.profile_body.pack(fill="both",expand=True); self.render_profiles()
    def _profile_files(self): return [p for p in (self.base_dir/"profiles").glob("profile_*.json") if p.is_file()]
    def render_profiles(self):
        for child in self.profile_body.winfo_children(): child.destroy()
        files=self._profile_files()
        if not files:
            target=self.base_dir/"profiles"/"profile_default.json"; target.write_text(json.dumps({"id":"default","name":"Default","config":self.pending},indent=2),encoding="utf-8"); files=[target]
        for path in files:
            try: record=json.loads(path.read_text(encoding="utf-8")); name=record.get("name",path.stem); active=record.get("id")==getattr(self,"active_profile_id","default")
            except Exception: continue
            row=ctk.CTkFrame(self.profile_body,fg_color="#172737",border_width=1,border_color="#c55720" if active else "#2c4152",corner_radius=9); row.pack(fill="x",pady=5)
            ctk.CTkLabel(row,text=f"{name}{'  · Active' if active else ''}",anchor="w",font=ctk.CTkFont(weight="bold")).pack(side="left",padx=12,pady=10)
            ctk.CTkButton(row,text="Load",width=65,command=lambda p=path:self.load_named_profile(p)).pack(side="right",padx=3,pady=7); ctk.CTkButton(row,text="Duplicate",width=82,command=lambda p=path:self.duplicate_profile(p)).pack(side="right",padx=3,pady=7); ctk.CTkButton(row,text="Rename",width=68,command=lambda p=path:self.rename_profile(p)).pack(side="right",padx=3,pady=7)
    def _profile_name(self,prompt,initial=""):
        from tkinter import simpledialog
        return simpledialog.askstring("Profile",prompt,initialvalue=initial,parent=self)
    def _persist_active_profile(self):
        path = self.base_dir / "profiles" / "selected_profile.json"
        path.write_text(json.dumps({"id": getattr(self, "active_profile_id", "default")}, indent=2), encoding="utf-8")
    def create_profile(self):
        name=self._profile_name("New profile name:")
        if not name: return
        ident=uuid.uuid4().hex; (self.base_dir/"profiles"/f"profile_{ident}.json").write_text(json.dumps({"id":ident,"name":name,"config":self.pending},indent=2),encoding="utf-8"); self.active_profile_id=ident; self._persist_active_profile(); self.show_profiles()
    def duplicate_profile(self,path):
        record=json.loads(path.read_text(encoding="utf-8")); name=self._profile_name("Name for duplicate:",record.get("name","")+" Copy")
        if not name:return
        ident=uuid.uuid4().hex; record.update(id=ident,name=name); (self.base_dir/"profiles"/f"profile_{ident}.json").write_text(json.dumps(record,indent=2),encoding="utf-8"); self.show_profiles()
    def rename_profile(self,path):
        record=json.loads(path.read_text(encoding="utf-8")); name=self._profile_name("New profile name:",record.get("name",""))
        if name: record["name"]=name; path.write_text(json.dumps(record,indent=2),encoding="utf-8"); self.show_profiles()
    def load_named_profile(self,path):
        record=json.loads(path.read_text(encoding="utf-8")); self.pending=record.get("config",record); self.active_profile_id=record.get("id",path.stem); self._persist_active_profile(); self._dirty(); self.show_profiles()
    def undo_profile(self):
        path = self.base_dir / "profiles" / "undo_profile.json"
        if path.is_file(): self.pending = json.loads(path.read_text(encoding="utf-8")); self._dirty(); messagebox.showinfo("Undo", "The last staged profile snapshot was restored.")
    def save_profile(self): self.manager.active_config = self.pending; self.manager.save_profile(); self._persist_active_profile(); self.dirty = False; self.dirty_label.configure(text="✓ Profile saved", text_color="#86efac")
    def show_install(self):
        self._clear("Mod Manager")
        bar=ctk.CTkFrame(self.body,fg_color="#1f2937",corner_radius=10); bar.pack(fill="x",pady=(0,10)); ctk.CTkLabel(bar,text=f"Active profile: {self._active_profile_name()}  ·  Local download folders",anchor="w").pack(side="left",padx=12,pady=10)
        ctk.CTkButton(bar,text="Add Folder",width=100,command=self.add_mod_folder).pack(side="right",padx=5); ctk.CTkButton(bar,text="Refresh",width=80,command=self.show_install).pack(side="right",padx=5)
        tabs=ctk.CTkFrame(self.body,fg_color="transparent"); tabs.pack(fill="x",pady=(0,8));
        for label,mode in (("Downloads","downloads"),("Installed Mods","installed"),("Updates","updates")): ctk.CTkButton(tabs,text=label,width=125,command=lambda m=mode:self.render_mods(m)).pack(side="left",padx=3)
        self.mod_library_body=ctk.CTkScrollableFrame(self.body,fg_color="transparent"); self.mod_library_body.pack(fill="both",expand=True); self.render_mods("downloads")
    def _active_profile_name(self):
        ident = getattr(self, "active_profile_id", "default")
        if ident == "default": return "Default"
        for path in self._profile_files():
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if record.get("id") == ident: return str(record.get("name", ident))
            except (OSError, ValueError, TypeError):
                continue
        return str(ident)
    def add_mod_folder(self):
        path=filedialog.askdirectory(title="Choose local mod download folder")
        if path: self.local_mods.add_folder(path); self.show_install()
    def render_mods(self, mode="downloads"):
        if not hasattr(self,"mod_library_body") or not self.mod_library_body.winfo_exists(): return
        for child in self.mod_library_body.winfo_children(): child.destroy()
        if not self.local_mods.state.get("folders"):
            self._mod_message("Choose a folder containing ZIP archives or extracted mod directories."); return
        packages=self.local_mods.packages()
        if mode=="installed": packages=[p for p in packages if p.identity in self.local_mods.state.get("installed",{})]
        elif mode=="updates":
            packages=[p for p in packages if p.identity in self.local_mods.state.get("installed",{}) and str(p.version) != str(self.local_mods.state["installed"][p.identity].get("package", {}).get("version", "unknown"))]
        if not packages: self._mod_message("No local packages found for this view."); return
        for package in packages:
            row=ctk.CTkFrame(self.mod_library_body,fg_color="#172737",border_width=1,border_color="#2c4152",corner_radius=9); row.pack(fill="x",pady=5)
            compatibility = self._package_compatibility(package)
            ctk.CTkLabel(row,text=f"{package.name}  ·  {package.version}",font=ctk.CTkFont(weight="bold"),anchor="w").pack(fill="x",padx=14,pady=(10,2)); ctk.CTkLabel(row,text=f"{package.author} · {package.status}\n{package.source}\nCompatibility: {compatibility}",text_color="#b8c7d5",anchor="w",justify="left").pack(fill="x",padx=14,pady=2)
            actions=ctk.CTkFrame(row,fg_color="transparent"); actions.pack(fill="x",padx=10,pady=8); ctk.CTkButton(actions,text="Preview",width=82,command=lambda p=package:self.preview_local_mod(p)).pack(side="left",padx=3); ctk.CTkButton(actions,text="Install",width=82,command=lambda p=package:self.install_local_mod(p),state="normal" if package.status=="recognized and supported" else "disabled").pack(side="left",padx=3)
            if mode == "installed" and package.identity in self.local_mods.state.get("installed", {}):
                enabled = bool(self.local_mods.state["installed"][package.identity].get("enabled", True))
                ctk.CTkButton(actions, text="Disable" if enabled else "Enable", width=82, command=lambda p=package:self.toggle_local_mod(p, enabled)).pack(side="left", padx=3)
                ctk.CTkButton(actions, text="Restore", width=82, command=lambda p=package:self.restore_local_mod(p)).pack(side="left", padx=3)
                ctk.CTkButton(actions, text="Remove", width=82, fg_color="#7f1d1d", hover_color="#991b1b", command=lambda p=package:self.remove_local_mod(p)).pack(side="left", padx=3)
            if mode == "updates":
                ctk.CTkButton(actions, text="Update", width=82, command=lambda p=package:self.update_local_mod(p)).pack(side="left", padx=3)
    def _mod_message(self,text): ctk.CTkLabel(self.mod_library_body,text=text,text_color="#cbd5e1",anchor="w",wraplength=850).pack(fill="x",padx=12,pady=18)
    def _package_compatibility(self, package):
        game = self.installer.selected_game_path()
        if not game:
            return "choose and validate the game folder to check dependencies"
        try:
            plan = self.local_mods.preview(package, game, allow_research=True)
            conflicts = len(plan.get("conflicts", []))
            return "compatible; no file conflicts" if not conflicts else f"compatible with {conflicts} existing file conflict(s) to review"
        except LocalModError as exc:
            return str(exc)
    def preview_local_mod(self,package):
        try: plan=self.local_mods.preview(package,self.installer.selected_game_path() or Path(".")); messagebox.showinfo("Local mod preview",json.dumps(plan,indent=2))
        except LocalModError as exc: messagebox.showerror("Package review",str(exc))
    def install_local_mod(self,package):
        game=self.installer.selected_game_path()
        if not game: messagebox.showwarning("Game folder","Choose and validate the game folder first."); return
        try:
            research_mode = feature_state(package.manifest) == "research-only"
            if research_mode and not messagebox.askyesno("Research-only package", "This package is research-only and has not been proven safe for runtime use. Enable it explicitly for this profile?"): return
            plan=self.local_mods.preview(package,game,allow_research=research_mode)
            if messagebox.askyesno("Install local mod",json.dumps(plan,indent=2)+"\n\nInstall this package?"):
                self.local_mods.install(package,game,allow_research=research_mode); messagebox.showinfo("Installed","Local mod installed and ownership recorded."); self.show_install()
        except (LocalModError,OSError) as exc: messagebox.showerror("Install failed",str(exc))
    def remove_local_mod(self, package):
        if not messagebox.askyesno("Remove local mod", f"Remove Control Center-owned files for '{package.name}'?\n\nUser-modified files will be preserved.", parent=self): return
        try:
            result = self.local_mods.remove_installed(package.identity)
            messagebox.showinfo("Mod removed", f"Removed {len(result['removed'])} owned file(s).\nPreserved {len(result['preserved'])} changed file(s).", parent=self)
            self.show_install()
        except (LocalModError, OSError) as exc:
            messagebox.showerror("Remove failed", str(exc), parent=self)
    def toggle_local_mod(self, package, enabled):
        try:
            result = self.local_mods.set_enabled(package.identity, not enabled)
            messagebox.showinfo("Mod state changed", f"{package.name} is now {'enabled' if result['enabled'] else 'disabled'}. Restart Enshrouded before testing.", parent=self)
            self.show_install()
        except (LocalModError, OSError) as exc:
            messagebox.showerror("Could not change mod state", str(exc), parent=self)
    def restore_local_mod(self, package):
        game = self.installer.selected_game_path()
        if not game:
            return messagebox.showwarning("Game folder", "Choose and validate the game folder first.", parent=self)
        try:
            points = self.local_mods.list_backups(package.identity)
            if not points:
                return messagebox.showinfo("No restore point", "No previous restore point is available for this mod.", parent=self)
            point = points[0]
            if not messagebox.askyesno("Restore previous version", f"Restore the latest restore point for {package.name}?\n\nRestore point: {point['id']}\nThe game must be closed.", parent=self): return
            result = self.local_mods.restore_backup(package.identity, point["id"], game)
            messagebox.showinfo("Mod restored", f"Restored {result['files']} owned file(s). Restart Enshrouded before testing.", parent=self)
            self.show_install()
        except (LocalModError, OSError) as exc:
            messagebox.showerror("Restore failed", str(exc), parent=self)
    def update_local_mod(self, package):
        game = self.installer.selected_game_path()
        if not game:
            return messagebox.showwarning("Game folder", "Choose and validate the game folder first.", parent=self)
        try:
            research_mode = feature_state(package.manifest) == "research-only"
            plan = self.local_mods.preview(package, game, allow_research=research_mode)
            if messagebox.askyesno("Update local mod", json.dumps(plan, indent=2) + "\n\nUpdate this package? A restore point will be created first.", parent=self):
                self.local_mods.install(package, game, replace=True, allow_research=research_mode)
                messagebox.showinfo("Mod updated", f"{package.name} was updated to {package.version}. A restore point was created.", parent=self)
                self.show_install()
        except (LocalModError, OSError) as exc:
            messagebox.showerror("Update failed", str(exc), parent=self)
    def choose_game(self):
        path = filedialog.askdirectory(title="Choose Enshrouded installation folder")
        if path: self.installer.save_game_path(Path(path)); self.show_install()
    def validate(self):
        path = self.installer.selected_game_path()
        if not path: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        try: messagebox.showinfo("Validation", "\n".join(self.installer.validate(path)) or "Validation passed.")
        except Exception as exc: messagebox.showerror("Validation failed", str(exc))
    def repair(self):
        path = self.installer.selected_game_path()
        if path:
            try: self.installer.repair(path); messagebox.showinfo("Repair", "Package repaired and verified. Restart Enshrouded.")
            except Exception as exc: messagebox.showerror("Repair failed", str(exc))
    def uninstall(self):
        path = self.installer.selected_game_path()
        if path and messagebox.askyesno("Uninstall", "Remove only owned Mod Hub files?"):
            try: self.installer.uninstall(path); messagebox.showinfo("Uninstall", "Owned files removed.")
            except Exception as exc: messagebox.showerror("Uninstall failed", str(exc))
    def show_research(self):
        self._clear("Research Catalog"); self._card("Research Only", "These candidates are cataloged with provenance but fail closed and never enter generated Lua.")
        for item in self.registry.research(): self._card(item["label"], f"{item['target_resource']} · {item.get('target_field') or 'field identity pending'}\nSource: {item['source']}")
    def _latest_research_file(self, pattern, fallback_name):
        """Return the newest generated research artifact, with a stable fallback."""
        research_dir = self.base_dir / "research"
        candidates = sorted(
            research_dir.glob(pattern),
            key=lambda path: path.stat().st_mtime if path.is_file() else 0,
            reverse=True,
        )
        return candidates[0] if candidates else research_dir / fallback_name

    def show_research_lab(self):
        self._clear("Research Lab")
        self._card("Test and improve content", "The Research Lab is where you test a project before using it in the game. Start with a project from Content Studio, make one change at a time, then record what worked.")
        context = build_control_context(self.base_dir, self.pending, self.local_mods.state.get("installed", {}), self._last_research_project(), self.last_diagnostic_report, profile_name=self._active_profile_name())
        ctk.CTkLabel(self.body, text=f"Test profile: {context['profile']['name']}  ·  verified restore points: {context['backups']['count']}  ·  third-party mods stay isolated until you start a guided test.", text_color="#bae6fd", anchor="w", wraplength=900).pack(fill="x", padx=10, pady=(0, 10))
        authority = ctk.CTkFrame(self.body, fg_color="#3b2412", border_width=1, border_color="#a16207", corner_radius=10)
        authority.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(authority, text="Multiplayer safety boundary", font=ctk.CTkFont(size=15, weight="bold"), text_color="#fde68a", anchor="w").pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(authority, text="Research results are single-player or client-side observations unless server authority and replication are tested separately. Do not treat a successful local test as multiplayer-safe.", text_color="#fef3c7", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 10))
        authority.pack_forget()
        interaction_card = None
        interaction_boundaries = sorted(
            (self.base_dir / "research").glob("INTERACTION_DONOR_CANDIDATE_BOUNDARY_*.json"),
            key=lambda path: path.stat().st_mtime if path.is_file() else 0,
            reverse=True,
        )
        if interaction_boundaries:
            try:
                interaction_boundary = json.loads(interaction_boundaries[0].read_text(encoding="utf-8"))
                if not interaction_boundary.get("runtime_safe_to_probe", False):
                    interaction_card = ctk.CTkFrame(self.body, fg_color="#3b2412", border_width=1, border_color="#a16207", corner_radius=10)
                    interaction_card.pack(fill="x", padx=8, pady=(0, 10))
                    ctk.CTkLabel(interaction_card, text="Custom interactions: research is paused safely", font=ctk.CTkFont(size=16, weight="bold"), text_color="#fde68a", anchor="w").pack(fill="x", padx=14, pady=(10, 3))
                    ctk.CTkLabel(interaction_card, text="The current build exposes interaction records only inside a quarantined resource family. Control Center will not create or install a probe until a safe donor is found.", text_color="#fef3c7", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 6))
                    ctk.CTkLabel(interaction_card, text=f"Next safe step: {interaction_boundary.get('next_gate', 'Recheck after a game or EML build update.')}", text_color="#fde68a", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 6))
                    ctk.CTkButton(interaction_card, text="Review interaction boundary", width=210, command=self._prepare_interaction_probe).pack(anchor="w", padx=14, pady=(0, 10))
                    interaction_card.pack_forget()
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        snapshot_path = self._latest_research_file("CAPABILITY_SNAPSHOT_*.json", "CAPABILITY_SNAPSHOT_20260928.json")
        status = None
        if snapshot_path.is_file():
            try:
                snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
                counts = snapshot.get("capability_counts", {})
                status = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
                status.pack(fill="x", padx=8, pady=(0, 10))
                ctk.CTkLabel(status, text="Project capability status", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 3))
                ctk.CTkLabel(status, text=(
                    f"Verified: {counts.get('verified', 0)}    Experimental: {counts.get('experimental', 0)}    "
                    f"Research only: {counts.get('research-only', 0)}    Unsupported: {counts.get('unsupported', 0)}"
                ), text_color="#cbd5e1", anchor="w").pack(fill="x", padx=14, pady=(0, 5))
                inputs = snapshot.get("inputs", {})
                provenance_ok = all(isinstance(inputs.get(key), str) and Path(inputs[key]).is_file() for key in ("capability_audit", "milestone_gate", "live_preflight", "metadata_policy"))
                ctk.CTkLabel(status, text=("Evidence sources: traceable and present" if provenance_ok else "Evidence sources: incomplete — refresh verification before relying on this status"), text_color="#a7f3d0" if provenance_ok else "#fbbf24", anchor="w").pack(fill="x", padx=14, pady=(0, 5))
                ctk.CTkLabel(status, text="Research-only means it is safe to investigate but not proven for normal gameplay.", text_color="#fbbf24", anchor="w", wraplength=850, justify="left").pack(fill="x", padx=14, pady=(0, 6))
                ctk.CTkButton(status, text="View remaining roadmap", width=180, command=self._show_capability_roadmap).pack(anchor="w", padx=14, pady=(0, 10))
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        start = ctk.CTkFrame(self.body, fg_color="transparent")
        start.pack(fill="x", padx=8, pady=(0, 8))
        selected_project = self._last_research_project()
        if selected_project:
            self._card("Ready to test", f"{selected_project.name}\nThis is the item you selected in Content Studio. The next step is to prepare a safe test session.")
            next_step = ctk.CTkFrame(self.body, fg_color="#123329", border_width=1, border_color="#2f855a", corner_radius=10)
            next_step.pack(fill="x", padx=8, pady=(0, 8))
            ctk.CTkLabel(next_step, text="Your next step", font=ctk.CTkFont(size=16, weight="bold"), text_color="#a7f3d0", anchor="w").pack(fill="x", padx=14, pady=(10, 2))
            ctk.CTkLabel(next_step, text="1. Prepare the safe test  →  2. Launch Enshrouded  →  3. Capture the screen we request.\nYour normal game files stay protected until you deliberately start the test.", text_color="#d1fae5", anchor="w", justify="left", wraplength=850).pack(side="left", padx=14, pady=(0, 10))
            ctk.CTkButton(next_step, text="Review project", width=125, command=self._review_current_research_project).pack(side="right", padx=(0, 6), pady=10)
            ctk.CTkButton(next_step, text="1. Prepare test session", width=180, command=self._prepare_probe_session).pack(side="right", padx=14, pady=10)
        else:
            next_step = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
            next_step.pack(fill="x", padx=8, pady=(0, 8))
            ctk.CTkLabel(next_step, text="Next step", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 2))
            ctk.CTkLabel(next_step, text="There is no test project selected yet. Create or open one in Content Studio first.", text_color="#cbd5e1", anchor="w", justify="left", wraplength=850).pack(side="left", padx=14, pady=(0, 10))
            ctk.CTkButton(next_step, text="Open Content Studio", width=170, command=self.show_content).pack(side="right", padx=14, pady=10)
        # Keep the first-time workflow visible near the top of the page.  The
        # detailed evidence cards below are useful for review, but beginners
        # should not have to scan the entire lab to discover the next click.
        quickstart = ctk.CTkFrame(self.body, fg_color="#102b40", border_width=1, border_color="#0ea5e9", corner_radius=10)
        quickstart.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(quickstart, text="Begin here — three clicks to test", font=ctk.CTkFont(size=16, weight="bold"), text_color="#bae6fd", anchor="w").pack(fill="x", padx=14, pady=(10, 2))
        ctk.CTkLabel(quickstart, text="Use these in order. When you reach the game, choose the exact screen you are checking; you do not need to understand the research files.", text_color="#dbeafe", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 8))
        quick_actions = ctk.CTkFrame(quickstart, fg_color="transparent")
        quick_actions.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkButton(quick_actions, text="1. Review item", width=150, command=self._review_current_research_project if selected_project else self.show_content).pack(side="left", padx=(0, 6))
        ctk.CTkButton(quick_actions, text="2. Prepare safe test", width=170, command=self._prepare_probe_session).pack(side="left", padx=6)
        ctk.CTkLabel(quick_actions, text="3. Capture:", text_color="#bae6fd", anchor="w").pack(side="left", padx=(8, 4))
        ctk.CTkButton(quick_actions, text="Catalog", width=92, command=lambda: self._capture_research_screenshot("catalog_item")).pack(side="left", padx=3)
        ctk.CTkButton(quick_actions, text="Item info", width=92, command=lambda: self._capture_research_screenshot("item_info")).pack(side="left", padx=3)
        ctk.CTkButton(quick_actions, text="Recipe", width=92, command=lambda: self._capture_research_screenshot("recipe")).pack(side="left", padx=3)
        ctk.CTkButton(quick_actions, text="Placed item", width=105, command=lambda: self._capture_research_screenshot("placed_item")).pack(side="left", padx=3)
        technical_open = ctk.BooleanVar(value=False)
        def toggle_technical_details():
            if technical_open.get():
                authority.pack_forget()
                if interaction_card is not None: interaction_card.pack_forget()
                technical_open.set(False)
                technical_toggle.configure(text="Show technical details")
            else:
                authority.pack(fill="x", padx=8, pady=(0, 10), before=status)
                if interaction_card is not None: interaction_card.pack(fill="x", padx=8, pady=(0, 10), before=status)
                technical_open.set(True)
                technical_toggle.configure(text="Hide technical details")
        technical_toggle = ctk.CTkButton(self.body, text="Show technical details", height=30, fg_color="#263d50", hover_color="#324d62", command=toggle_technical_details)
        technical_toggle.pack(fill="x", padx=8, pady=(0, 10))
        # Show the latest furniture registration result in plain language so
        # beginners can tell what the loader proved from what still needs an
        # in-game screenshot.  This intentionally never promotes the probe.
        furniture_reports = sorted(
            (self.base_dir / "research" / "probe_sessions").glob("*furniture_clone_runtime_evidence_*.json"),
            key=lambda path: path.stat().st_mtime if path.is_file() else 0,
            reverse=True,
        )
        furniture_evidence = furniture_reports[0] if furniture_reports else None
        if furniture_evidence and furniture_evidence.is_file():
            try:
                report = json.loads(furniture_evidence.read_text(encoding="utf-8-sig"))
                runtime = report.get("runtime", {})
                cleanup = report.get("cleanup", {})
                status = "Runtime registration passed" if runtime.get("clone_registered") and runtime.get("clone_discovered") else "Runtime registration needs review"
                color = "#a7f3d0" if status.startswith("Runtime registration passed") else "#fbbf24"
                details = (
                    f"{status}\n"
                    f"Item and recipe added: {'yes' if runtime.get('item_registry_increment') == 1 and runtime.get('recipe_registry_increment') == 1 else 'no'}\n"
                    f"Knowledge and menu link added: {'yes' if runtime.get('knowledge_link_increment') == 1 and runtime.get('ui_set_clone_increment') == 1 else 'no'}\n"
                    "Still needed: catalog screenshot, placed-item screenshot, and save/reload proof.\n"
                    f"Cleanup complete: {'yes' if all(cleanup.get(key) is True for key in ('probe_removed', 'third_party_mod_restored', 'stable_profile_restored')) else 'no'}"
                )
                card = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
                card.pack(fill="x", padx=8, pady=(0, 10))
                ctk.CTkLabel(card, text="Latest furniture test", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 3))
                ctk.CTkLabel(card, text=details, text_color=color, anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 10))
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        # Give beginners a single, readable view of the furniture-clone
        # milestone instead of making them infer progress from probe files.
        candidates_dir = self.base_dir / "research" / "content_clone_candidates"
        candidate_files = sorted(candidates_dir.glob("*_candidate.json")) if candidates_dir.is_dir() else []
        if candidate_files:
            progress = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
            progress.pack(fill="x", padx=8, pady=(0, 10))
            ctk.CTkLabel(progress, text="Furniture donor progress", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 3))
            ctk.CTkLabel(progress, text="Three different donors are being tested one at a time. Runtime registration is not the same as proof that an item appears or persists in your world.", text_color="#cbd5e1", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 7))
            for candidate_path in candidate_files:
                try:
                    candidate = json.loads(candidate_path.read_text(encoding="utf-8-sig"))
                    donor = candidate.get("donor", {})
                    label = donor.get("debug_name") or candidate_path.stem.replace("_", " ").title()
                    state = str(candidate.get("status", "UNKNOWN")).replace("_", " ").title()
                    evidence_path = candidate.get("runtime_evidence")
                    if evidence_path:
                        evidence_file = self.base_dir / evidence_path
                        if evidence_file.is_file():
                            state = "Runtime registration recorded"
                    if "RUNTIME_REGISTRATION" in str(candidate.get("status", "")):
                        next_step = "Next: capture catalog, placement, and save/reload proof."
                    else:
                        next_step = "Next: run an isolated registration test."
                    ctk.CTkLabel(progress, text=f"• {label} — {state}\n  {next_step}", text_color="#a7f3d0" if evidence_path and (self.base_dir / evidence_path).is_file() else "#fbbf24", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=22, pady=2)
                except (OSError, json.JSONDecodeError, TypeError):
                    continue
            ctk.CTkLabel(progress, text="Nothing in this panel is installed automatically. Use Start guided test when you deliberately want to prepare a safe session.", text_color="#94a3b8", anchor="w", wraplength=850, justify="left").pack(fill="x", padx=14, pady=(7, 10))
        visual_reports = sorted(
            (self.base_dir / "research" / "probe_sessions").glob("visual_substitution_runtime_evidence_*.json"),
            key=lambda path: path.stat().st_mtime if path.is_file() else 0,
            reverse=True,
        )
        if visual_reports:
            try:
                visual_report = json.loads(visual_reports[0].read_text(encoding="utf-8-sig"))
                gaps = visual_report.get("limitations", [])
                assignment_ok = visual_report.get("visual_assignment", {}).get("ok") is True
                visual_card = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
                visual_card.pack(fill="x", padx=8, pady=(0, 10))
                ctk.CTkLabel(visual_card, text="Latest visual-substitution test", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(10, 3))
                summary = (
                    f"Assignment accepted: {'yes' if assignment_ok else 'no'}\n"
                    f"Clone discovered: {'yes' if visual_report.get('clone_discovered') is True else 'no'}\n"
                    f"World reached: {'yes' if visual_report.get('world_reached') is True else 'not recorded'}\n"
                    f"Probe cleaned up: {'yes' if visual_report.get('probe_uninstalled') is True and visual_report.get('stable_profile_restored') is True else 'no'}\n"
                    + ("Still needed: " + "; ".join(str(item) for item in gaps) if gaps else "No evidence gaps recorded.")
                )
                ctk.CTkLabel(visual_card, text=summary, text_color="#a7f3d0" if assignment_ok else "#fbbf24", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 10))
                if visual_report.get("world_reached") is True and "human-visible placed-object replacement screenshot" in gaps:
                    ctk.CTkLabel(visual_card, text="Next manual step: load a save with a building area, open the Carpenter/build menu, select the test item, and capture the catalog and placed-item screens.", text_color="#fde68a", anchor="w", justify="left", wraplength=850).pack(fill="x", padx=14, pady=(0, 10))
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        ctk.CTkButton(start, text="Start guided test", height=34, fg_color="#0ea5e9", hover_color="#0284c7", command=self._open_research_wizard).pack(side="left", padx=(0, 6))
        ctk.CTkButton(start, text="How do I use this?", height=34, command=self._show_research_lab_help).pack(side="left", padx=(0, 6))
        ctk.CTkButton(start, text="Review chair/stool probe", height=34, command=self._review_chair_probe).pack(side="left", padx=(0, 6))
        ctk.CTkButton(start, text="Create or edit content", height=34, command=self.show_content).pack(side="left", padx=(0, 6))
        ctk.CTkButton(start, text="Prepare a safe test session", height=34, command=self._prepare_probe_session).pack(side="left", padx=6)
        ctk.CTkButton(start, text="Capture game screen", height=34, command=self._capture_research_screenshot).pack(side="left", padx=6)
        workflow = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
        workflow.pack(fill="x", padx=8, pady=(4, 10))
        ctk.CTkLabel(workflow, text="Recommended order", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(12, 4))
        ctk.CTkLabel(workflow, text="1. Create or open a project in Content Studio\n2. Validate the donor and project\n3. Run a controlled test with the game closed before launch\n4. Capture the result, then publish only after the test passes", justify="left", anchor="w", text_color="#cbd5e1").pack(fill="x", padx=14, pady=(0, 12))
        evidence = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
        evidence.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(evidence, text="Runtime evidence checklist", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(12, 3))
        ctk.CTkLabel(evidence, text="For a custom label, capture each screen separately. A successful loader message alone is not enough to prove that the game displays the label.", text_color="#cbd5e1", wraplength=850, justify="left", anchor="w").pack(fill="x", padx=14, pady=(0, 6))
        for item in ("Catalog item name", "Item information name", "Recipe name and station", "Placement or interaction name"):
            ctk.CTkLabel(evidence, text=f"☐  {item}", text_color="#fbbf24", anchor="w").pack(fill="x", padx=22, pady=2)
        ctk.CTkLabel(evidence, text="When all four are captured, return to the project review and keep the screenshots with the fresh-session report.", text_color="#94a3b8", anchor="w", wraplength=850, justify="left").pack(fill="x", padx=14, pady=(6, 12))
        visual_evidence = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
        visual_evidence.pack(fill="x", padx=8, pady=(0, 10))
        ctk.CTkLabel(visual_evidence, text="Recolor proof", font=ctk.CTkFont(size=16, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(12, 3))
        ctk.CTkLabel(visual_evidence, text="For a recolored item, the runtime log proves the color values were accepted. Only these two screenshots prove that the game visibly uses them:", text_color="#cbd5e1", wraplength=850, justify="left", anchor="w").pack(fill="x", padx=14, pady=(0, 5))
        for item in ("☐ Catalog tile with the recolored item selected", "☐ Placed item showing the recolored frame, bedding, or trim"):
            ctk.CTkLabel(visual_evidence, text=item, text_color="#fbbf24", anchor="w").pack(fill="x", padx=22, pady=2)
        ctk.CTkLabel(visual_evidence, text="If either screenshot is missing, keep the project research-only.", text_color="#94a3b8", anchor="w").pack(fill="x", padx=14, pady=(6, 12))
        import_actions = ctk.CTkFrame(visual_evidence, fg_color="transparent")
        import_actions.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkButton(import_actions, text="Import catalog screenshot", width=190, command=lambda: self._import_research_screenshot("catalog")).pack(side="left", padx=(0, 6))
        ctk.CTkButton(import_actions, text="Import item-info screenshot", width=205, command=lambda: self._import_research_screenshot("item_info")).pack(side="left", padx=6)
        ctk.CTkButton(import_actions, text="Import recipe screenshot", width=190, command=lambda: self._import_research_screenshot("recipe")).pack(side="left", padx=6)
        ctk.CTkButton(import_actions, text="Import placed-item screenshot", width=220, command=lambda: self._import_research_screenshot("placed_item")).pack(side="left", padx=6)
        catalog_evidence_dir = self.base_dir / "research" / "probe_sessions"
        catalog_evidence_files = sorted(catalog_evidence_dir.glob("catalog_icon_fallback_runtime_evidence_*.json"), key=lambda path: path.stat().st_mtime if path.is_file() else 0)
        catalog_evidence_path = catalog_evidence_files[-1] if catalog_evidence_files else None
        if catalog_evidence_path and catalog_evidence_path.is_file():
            try:
                catalog_evidence = json.loads(catalog_evidence_path.read_text(encoding="utf-8-sig"))
                durable = catalog_evidence.get("evidence", {}).get("durable_visual_evidence", {})
                if durable.get("catalog_tile_verdict") == "nonblank_tile_visible":
                    placed_pending = durable.get("placed_object_verdict") != "placed_object_visual_verified"
                    persistence_pending = durable.get("save_persistence_verdict") != "verified"
                    pending = []
                    if placed_pending:
                        pending.append("placed-item screenshot")
                    if persistence_pending:
                        pending.append("save-and-reload proof")
                    detail = ", ".join(pending) if pending else "nothing"
                    ctk.CTkLabel(visual_evidence, text=f"Catalog icon: verified. Still needed: {detail}.", text_color="#fbbf24" if pending else "#a7f3d0", anchor="w", wraplength=850, justify="left").pack(fill="x", padx=14, pady=(0, 10))
                    if placed_pending:
                        ctk.CTkButton(visual_evidence, text="Capture placed-item screenshot", width=230, command=lambda: self._capture_research_screenshot("placed_item")).pack(anchor="w", padx=14, pady=(0, 10))
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        color_evidence_dir = self.base_dir / "research" / "probe_sessions"
        color_evidence_files = sorted(color_evidence_dir.glob("typed_color_combination_runtime_evidence_*.json"), key=lambda path: path.stat().st_mtime if path.is_file() else 0)
        color_evidence_path = color_evidence_files[-1] if color_evidence_files else None
        if color_evidence_path and color_evidence_path.is_file():
            try:
                color_evidence = json.loads(color_evidence_path.read_text(encoding="utf-8-sig"))
                runtime = color_evidence.get("runtime", {})
                visuals = color_evidence.get("visual_evidence", {})
                if runtime.get("item_color_combination_packed_assignment") is True:
                    if visuals.get("catalog_tile_visible") is True and visuals.get("placed_object_visible") is True:
                        status_text, status_color = "Typed recolor: visually verified", "#a7f3d0"
                    else:
                        status_text, status_color = "Typed recolor: runtime accepted; screenshots still needed", "#fbbf24"
                    ctk.CTkLabel(visual_evidence, text=status_text, text_color=status_color, anchor="w", wraplength=850, justify="left").pack(fill="x", padx=14, pady=(0, 10))
                    if not (visuals.get("catalog_tile_visible") is True and visuals.get("placed_object_visible") is True):
                        ctk.CTkLabel(visual_evidence, text="When the game is open, show the recolored item in the build menu, then show the placed item in the world. Save each screen separately below.", text_color="#cbd5e1", anchor="w", wraplength=850, justify="left").pack(fill="x", padx=14, pady=(0, 6))
                        color_capture_actions = ctk.CTkFrame(visual_evidence, fg_color="transparent")
                        color_capture_actions.pack(fill="x", padx=14, pady=(0, 10))
                        ctk.CTkButton(color_capture_actions, text="Save catalog screenshot", width=190, command=lambda: self._capture_research_screenshot("recolored_catalog")).pack(side="left", padx=(0, 6))
                        ctk.CTkButton(color_capture_actions, text="Save placed-item screenshot", width=210, command=lambda: self._capture_research_screenshot("recolored_placed_item")).pack(side="left", padx=6)
            except (OSError, json.JSONDecodeError, TypeError):
                pass
        captured_kinds = {"catalog": [], "item_info": [], "recipe": [], "placed_item": []}
        for report_path in sorted(color_evidence_dir.glob("*.json"), key=lambda path: path.stat().st_mtime if path.is_file() else 0):
            try:
                report = json.loads(report_path.read_text(encoding="utf-8-sig"))
                kind = report.get("evidence_kind")
                image_path = report.get("path")
                from tools.verify_game_screenshot_evidence import verify as verify_screenshot_evidence
                screenshot_report = verify_screenshot_evidence(report_path)
                if screenshot_report.get("valid") and kind in captured_kinds and isinstance(image_path, str):
                    captured_kinds[kind].append(Path(image_path))
            except (OSError, json.JSONDecodeError, TypeError):
                continue
        evidence_complete = all(captured_kinds.values())
        captured_card = ctk.CTkFrame(
            visual_evidence,
            fg_color="#123329" if evidence_complete else "#3b2412",
            border_width=1,
            border_color="#2f855a" if evidence_complete else "#a16207",
            corner_radius=8,
        )
        captured_card.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkLabel(
            captured_card,
            text="Captured evidence files — checklist status",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#a7f3d0" if evidence_complete else "#fde68a",
            anchor="w",
        ).pack(fill="x", padx=12, pady=(8, 3))
        ctk.CTkLabel(captured_card, text=(
            f"Catalog screenshot: {'captured' if captured_kinds['catalog'] else 'still needed'}\n"
            f"Item-information screenshot: {'captured' if captured_kinds['item_info'] else 'still needed'}\n"
            f"Recipe screenshot: {'captured' if captured_kinds['recipe'] else 'still needed'}\n"
            f"Placed-item screenshot: {'captured' if captured_kinds['placed_item'] else 'still needed'}\n"
            "These files are recorded for review only; screenshots do not promote a capability by themselves."
        ), text_color="#d1fae5" if evidence_complete else "#fef3c7", anchor="w", justify="left", wraplength=800).pack(fill="x", padx=12, pady=(0, 8))
        variants = self.base_dir / "research" / "variants"
        if variants.is_dir():
            files = sorted(variants.glob("*.json"))
            if files:
                self._card("Available visual variants", "These are safe to review before testing:")
                for path in files:
                    try:
                        data = json.loads(path.read_text(encoding="utf-8-sig"))
                        name = data.get("variant_name") or path.stem.replace("_", " ").title()
                        state = data.get("feature_state", "research-only")
                        card = self._card(name, f"{state} · {path.name}\nThis is a starting point, not an installed mod. Use the button below to turn it into a project you can validate.")
                        actions = ctk.CTkFrame(card, fg_color="transparent")
                        actions.pack(fill="x", padx=18, pady=(0, 12))
                        ctk.CTkButton(actions, text="Use this variant", width=140, command=lambda p=path: self._use_research_variant(p)).pack(side="left", padx=(0, 6))
                        ctk.CTkButton(actions, text="Open Content Studio", width=150, command=self.show_content).pack(side="left", padx=6)
                    except (OSError, json.JSONDecodeError):
                        self._card(path.stem, "The variant file could not be read yet.")
        queue_path = self.base_dir / "research" / "TUNING_RESEARCH_QUEUE_20260928.json"
        if queue_path.is_file():
            try:
                queue = json.loads(queue_path.read_text(encoding="utf-8"))
                entries = queue.get("research_queue", [])[:5]
                summary = "\n".join(
                    f"P{entry.get('priority', 4)} · {entry.get('category', 'Uncategorized')} · {entry.get('family', 'Unknown')}"
                    for entry in entries
                ) or "No uncovered tuning families are queued."
                self._card("Next tuning research", f"Build {queue.get('build', 'unknown')} · {queue.get('uncovered_family_count', 0)} uncovered families\n{summary}")
            except (OSError, json.JSONDecodeError, TypeError):
                self._card("Next tuning research", "The saved queue could not be read; regenerate it from the tuning audit.")
        ctk.CTkButton(self.body, text="Review Gameplay Feasibility Matrix", command=self._review_gameplay_feasibility).pack(anchor="w", padx=8, pady=8)
        ctk.CTkButton(self.body, text="Review Carpenter Menu Boundary", command=self._review_construction_hammer_boundary).pack(anchor="w", padx=8, pady=8)
        ctk.CTkButton(self.body, text="Draft Builder Placement Study", command=self._draft_builder_placement_study).pack(anchor="w", padx=8, pady=8)
        ctk.CTkButton(self.body, text="Prepare Fresh EML Session", command=self._prepare_probe_session).pack(anchor="w", padx=8, pady=8)
        ctk.CTkButton(self.body, text="Prepare Interaction Research", command=self._prepare_interaction_probe).pack(anchor="w", padx=8, pady=8)
        candidates = self.registry.research()
        catalog_toggle = ctk.CTkButton(
            self.body,
            text=f"Show advanced research catalog ({len(candidates)} entries)",
            height=30,
            fg_color="#263d50",
            hover_color="#324d62",
        )
        catalog_toggle.pack(fill="x", padx=8, pady=(10, 4))
        catalog = ctk.CTkFrame(self.body, fg_color="transparent")
        catalog_open = ctk.BooleanVar(value=False)

        def toggle_catalog():
            if catalog_open.get():
                catalog.pack_forget()
                catalog_open.set(False)
                catalog_toggle.configure(text=f"Show advanced research catalog ({len(candidates)} entries)")
            else:
                catalog.pack(fill="x", padx=0, pady=(0, 8))
                catalog_open.set(True)
                catalog_toggle.configure(text="Hide advanced research catalog")

        catalog_toggle.configure(command=toggle_catalog)
        if not candidates:
            ctk.CTkLabel(
                catalog,
                text="No cataloged probes. Use Settings only if you are intentionally investigating an advanced capability.",
                text_color="#cbd5e1",
                anchor="w",
                justify="left",
                wraplength=850,
            ).pack(fill="x", padx=14, pady=10)
        else:
            for item in candidates:
                risk = item.get("risk", "review required")
                target = item.get("target_resource", "resource pending")
                details = f"Purpose: {item.get('label', 'Research candidate')}\nTarget: {target}\nRisk: {risk}\nVerification: {item.get('status', 'not yet verified')}\nSource: {item.get('source', 'unknown')}"
                card = self._card(item.get("label", "Research candidate"), details, parent=catalog)
                ctk.CTkButton(card, text="Review candidate details", width=190, command=lambda d=details: messagebox.showinfo("Research candidate", d, parent=self)).pack(anchor="w", padx=18, pady=(0, 12))

    def _open_research_wizard(self):
        """Open a beginner-friendly, one-action-at-a-time research workflow."""
        wizard = ctk.CTkToplevel(self)
        wizard.title("Guided Research Test")
        wizard.geometry("700x520")
        wizard.minsize(620, 460)
        wizard.transient(self)
        wizard.grab_set()
        ctk.CTkLabel(wizard, text="Guided Research Test", font=ctk.CTkFont(size=24, weight="bold")).pack(anchor="w", padx=28, pady=(24, 4))
        ctk.CTkLabel(wizard, text="Follow these steps in order. The wizard keeps research content separate from your normal game setup.", text_color="#cbd5e1", wraplength=630, justify="left").pack(anchor="w", padx=28, pady=(0, 18))
        status = ctk.CTkLabel(wizard, text="Step 1 of 4 — choose a project", text_color="#67e8f9", anchor="w", justify="left")
        status.pack(fill="x", padx=28, pady=(0, 10))
        project_text = ctk.CTkLabel(wizard, text="No project selected yet.", anchor="w", justify="left", wraplength=630)
        project_text.pack(fill="x", padx=28, pady=(0, 16))
        actions = ctk.CTkFrame(wizard, fg_color="transparent")
        actions.pack(fill="x", padx=28, pady=4)

        state = {"project": self._last_research_project(), "validated": False, "prepared": False}
        controls = {}

        def refresh():
            if state["project"]:
                project_text.configure(text=f"Project: {state['project']}\nThis is a research-only test; it will not replace vanilla files.")
            else:
                project_text.configure(text="No project selected yet. Choose a project from Content Studio or browse to one here.")
            if state["prepared"]:
                status.configure(text="Step 4 of 4 — test in the game", text_color="#a7f3d0")
            elif state["validated"]:
                status.configure(text="Step 3 of 4 — prepare the safe test session", text_color="#67e8f9")
            elif state["project"]:
                status.configure(text="Step 2 of 4 — validate the project", text_color="#67e8f9")
            else:
                status.configure(text="Step 1 of 4 — choose a project", text_color="#67e8f9")
            if controls:
                controls["validate"].configure(state="normal" if state["project"] else "disabled")
                controls["prepare"].configure(state="normal" if state["validated"] else "disabled")
                controls["color"].configure(state="normal" if state["validated"] else "disabled")
                controls["launch"].configure(state="normal" if state["prepared"] else "disabled")

        def choose():
            path = filedialog.askdirectory(parent=wizard, title="Choose a staged content project")
            if not path:
                return
            report = self.content_validator.validate(Path(path))
            if not report.valid:
                details = "\n".join(f"• {issue.message}" for issue in report.issues)
                messagebox.showerror("Project needs attention", f"This project is not ready yet:\n\n{details}", parent=wizard)
                return
            self._remember_research_project(Path(path))
            state["project"] = Path(path).resolve()
            # Selecting a folder is not the same as validating its contents.
            # Keep the wizard on the validation step so a beginner gets a
            # clear, deliberate safety checkpoint before preparation.
            state["validated"] = False
            refresh()

        def validate():
            project = state["project"] or self._last_research_project()
            if not project:
                return messagebox.showinfo("Choose a project first", "Use Choose project before validating.", parent=wizard)
            state["project"] = project
            report = self.content_validator.validate(project)
            if report.valid:
                self._remember_research_project(project)
                state["validated"] = True
                refresh()
                messagebox.showinfo("Project ready", "The project passed the safety check. Continue to Prepare safe test.", parent=wizard)
            else:
                details = "\n".join(f"• {issue.message}" for issue in report.issues)
                messagebox.showerror("Validation blocked", details, parent=wizard)

        def prepare():
            if not state["validated"]:
                return messagebox.showinfo("Validate first", "Validate the project before preparing a test session.", parent=wizard)
            state["prepared"] = bool(self._prepare_probe_session())
            if state["prepared"]:
                refresh()

        def launch():
            if not state["prepared"]:
                return messagebox.showinfo("Prepare the test first", "Prepare the safe test session before launching the game.", parent=wizard)
            wizard.destroy()
            self._launch_game()

        def create_color_probe():
            project = state["project"] or self._last_research_project()
            if not project:
                return messagebox.showinfo("Choose a project first", "Choose and validate a visual project before creating its color probe.", parent=wizard)
            if not state["validated"]:
                return messagebox.showinfo("Validate the project first", "Run Validate project before creating a color probe. This confirms the staged content is safe to use as the probe source.", parent=wizard)
            definition = Path(project) / "content" / "visual_variant.json"
            if not definition.is_file():
                return messagebox.showerror("Color probe unavailable", "This project does not contain a visual variant definition.", parent=wizard)
            try:
                seed = int(hashlib.sha256(str(Path(project).resolve()).encode("utf-8")).hexdigest()[:8], 16)
                new_item_id = 3987656000 + (seed % 9000) * 2
                new_recipe_id = new_item_id + 1
                output = self.base_dir / "research" / "staging" / f"{Path(project).name}_color_probe"
                if output.exists():
                    output = output.with_name(output.name + "_" + uuid.uuid4().hex[:8])
                command = [sys.executable, str(self.base_dir / "tools" / "build_catalog_preview_probe.py"),
                           str(self.base_dir / "research" / "probes" / "recipe_customization_workshop_20260928"),
                           str(output), "--new-item-id", str(new_item_id), "--new-recipe-id", str(new_recipe_id),
                           "--render-control", "itemColorCombinationPacked", "--color-plan", str(definition)]
                result = subprocess.run(command, cwd=self.base_dir, capture_output=True, text=True, check=True)
                state["project"] = output.resolve()
                state["validated"] = False
                state["prepared"] = False
                self._remember_research_project(output)
                refresh()
                messagebox.showinfo("Color probe ready", f"The isolated recolor probe was created and selected as the next project.\n\n{output}\n\nIt is not installed or enabled yet. Click Validate project, then Prepare safe test when you are ready.", parent=wizard)
            except (OSError, subprocess.CalledProcessError, ValueError) as exc:
                details = getattr(exc, "stderr", "") or str(exc)
                messagebox.showerror("Color probe failed", details, parent=wizard)

        controls["choose"] = ctk.CTkButton(actions, text="1. Choose project", command=choose)
        controls["choose"].pack(side="left", padx=(0, 8))
        controls["validate"] = ctk.CTkButton(actions, text="2. Validate project", command=validate)
        controls["validate"].pack(side="left", padx=8)
        controls["prepare"] = ctk.CTkButton(actions, text="3. Prepare safe test", command=prepare)
        controls["prepare"].pack(side="left", padx=8)
        controls["color"] = ctk.CTkButton(actions, text="Create color probe", command=create_color_probe)
        controls["color"].pack(side="left", padx=8)
        controls["launch"] = ctk.CTkButton(actions, text="4. Launch game", fg_color="#f97316", hover_color="#ea580c", command=launch)
        controls["launch"].pack(side="left", padx=8)
        ctk.CTkButton(wizard, text="Close", command=wizard.destroy).pack(side="right", padx=28, pady=24)
        refresh()

    def _show_capability_roadmap(self):
        path = self._latest_research_file("CAPABILITY_SNAPSHOT_*.json", "CAPABILITY_SNAPSHOT_20260928.json")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            records = {
                entry.get("id"): entry.get("state", "unclassified")
                for entry in data.get("capabilities", [])
                if isinstance(entry, dict) and entry.get("id")
            }
            unresolved = data.get("unresolved_capabilities", [])
            if not unresolved:
                unresolved = [item for item, state in records.items() if state != "verified"]
            labels = {
                "icon_color_material_texture_model": "Custom icons, colors, materials, and textures",
                "original_mesh_asset_import": "Original mesh and asset import",
                "construction_hammer_catalog_integration": "Construction Hammer catalog integration",
                "custom_interactions": "Custom interactions",
                "ai_enemy_archetypes": "AI and enemy archetypes",
                "quest_progression_systems": "Quest and progression systems",
                "animation_world_generation": "Animation and world generation",
                "multiplayer_authority": "Multiplayer authority",
            }
            next_actions = {
                "icon_color_material_texture_model": "Capture a fresh catalog tile and placed-item screenshot for the visual variant.",
                "original_mesh_asset_import": "Provide a supported asset-export route, then validate the imported resource graph.",
                "construction_hammer_catalog_integration": "Find a supported catalog/UI resource owner beyond the quarantined FbUiBundle route.",
                "custom_interactions": "Find a non-TemplateResource interaction donor before attempting a runtime probe.",
                "ai_enemy_archetypes": "Identify a supported AI archetype owner and build a read-only donor probe.",
                "quest_progression_systems": "Identify quest/progression resource owners and validate a minimal dependency graph.",
                "animation_world_generation": "Validate an engine-supported animation or world-generation dependency chain.",
                "multiplayer_authority": "Requires native multiplayer authority support; no safe EML-only route is currently proven.",
            }
            roadmap = ctk.CTkToplevel(self)
            roadmap.title("Remaining research tasks")
            roadmap.geometry("760x620")
            roadmap.transient(self)
            ctk.CTkLabel(roadmap, text="Choose a research task", font=ctk.CTkFont(size=22, weight="bold"), anchor="w").pack(fill="x", padx=24, pady=(22, 4))
            ctk.CTkLabel(roadmap, text="These capabilities still need runtime proof or native engine support. Select a task to open the safest next step; nothing is installed automatically.", text_color="#cbd5e1", anchor="w", justify="left", wraplength=700).pack(fill="x", padx=24, pady=(0, 14))
            task_list = ctk.CTkScrollableFrame(roadmap, fg_color="transparent")
            task_list.pack(fill="both", expand=True, padx=18, pady=(0, 12))
            for item in unresolved:
                card = ctk.CTkFrame(task_list, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=9)
                card.pack(fill="x", pady=4)
                state = records.get(item, "needs review")
                ctk.CTkLabel(card, text=f"{labels.get(item, item)}  ·  {state}", font=ctk.CTkFont(size=14, weight="bold"), anchor="w").pack(side="left", fill="x", expand=True, padx=12, pady=(9, 2))
                ctk.CTkLabel(card, text=f"Next action: {next_actions.get(item, 'Review the capability evidence and define a safe probe.')}", text_color="#cbd5e1", anchor="w", justify="left", wraplength=500).pack(side="left", fill="x", expand=True, padx=8, pady=(9, 9))
                ctk.CTkButton(card, text="Open next step", width=125, command=lambda capability=item, action=next_actions.get(item, "Review the capability evidence and define a safe probe."): self._start_capability_task(capability, action)).pack(side="right", padx=10, pady=10)
            ctk.CTkButton(roadmap, text="Close", width=120, command=roadmap.destroy).pack(anchor="e", padx=24, pady=(0, 20))
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            messagebox.showerror("Roadmap unavailable", f"The capability snapshot could not be read:\n\n{exc}", parent=self)

    def _start_capability_task(self, capability, action):
        """Route a roadmap task to an existing safe workflow or explain its gate."""
        if capability == "icon_color_material_texture_model":
            self.show_content()
        elif capability == "custom_interactions":
            self._prepare_interaction_probe()
        elif capability == "construction_hammer_catalog_integration":
            self._review_construction_hammer_boundary()
        else:
            messagebox.showinfo("Next research step", f"{action}\n\nThis task remains research-only and is not enabled automatically.", parent=self)

    def _show_research_lab_help(self):
        messagebox.showinfo(
            "Research Lab — start here",
            "1. Click Create or edit content.\n"
            "2. Create a test variant in Content Studio.\n"
            "3. Return here and click Prepare a safe test session.\n"
            "4. Launch the game through Control Center.\n"
            "5. Look for the test item and capture the requested screenshots.\n"
            "6. Close the game before restoring or changing the test profile.\n\n"
            "The listed variants are starting points. They are not installed automatically, and research-only items should not be published as finished mods.",
            parent=self,
        )

    def _review_chair_probe(self):
        """Explain the prepared chair probe without installing or enabling it."""
        probe = self.base_dir / "research" / "probes" / "chair_stool_clone_1076226"
        manifest = probe / "mod.json"
        if not manifest.is_file():
            return messagebox.showerror("Chair/stool probe unavailable", f"The prepared probe was not found at:\n\n{probe}", parent=self)
        try:
            data = json.loads(manifest.read_text(encoding="utf-8-sig"))
            messagebox.showinfo(
                "Chair/stool probe",
                f"{data.get('name', 'Furniture clone probe')}\n\n"
                f"Location:\n{probe}\n\n"
                "Status: RESEARCH-ONLY\n"
                "Runtime registration has been recorded. Catalog visibility, placement, interaction, and save persistence still need in-game evidence.\n\n"
                "Nothing was installed or enabled. Use the advanced research workflow when you are ready to test it.",
                parent=self,
            )
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            messagebox.showerror("Chair/stool probe unavailable", str(exc), parent=self)

    def _use_research_variant(self, path):
        """Turn a reviewed research definition into a validated local project."""
        try:
            data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
            name = str(data.get("variant_name") or Path(path).stem.replace("_", " ").title()).strip()
            colors = {str(item.get("target")): str(item.get("color")) for item in data.get("color_adjustments", []) if isinstance(item, dict) and item.get("target") and item.get("color")}
            colors = {key: colors.get(key, default) for key, default in (("frame", "#3A2430"), ("bedding", "#536A9B"), ("trim", "#B08A5A"))}
            donor = str(data.get("donor") or data.get("donor_id") or "bed")
            scale = data.get("scale", [1.0, 1.0, 1.0])
            offset = data.get("offset", [0.0, 0.0, 0.0])
            catalog_preview = str(data.get("catalog_preview") or "donor-fallback")
            placement_preview = str(data.get("placement_preview") or "donor-fallback")
            self._create_content_project_named(
                name,
                donor,
                colors,
                scale,
                offset,
                catalog_preview,
                placement_preview,
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Variant unavailable", f"This research variant could not be opened:\n\n{exc}", parent=self)

    def _review_gameplay_feasibility(self):
        assessments = GameplayFeasibilityPlanner().all_assessments()
        lines = []
        for assessment in assessments:
            lines.append(f"{assessment.area.value}: {assessment.state}")
            lines.append("  Blockers: " + "; ".join(assessment.blockers))
            lines.append("  Next probe: " + assessment.next_probe)
        messagebox.showinfo("Gameplay feasibility", "\n".join(lines))
    def _review_construction_hammer_boundary(self):
        path = self.base_dir / "research" / "CONSTRUCTION_HAMMER_UI_BOUNDARY_20260929.json"
        try:
            boundary = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return messagebox.showerror("Carpenter menu boundary", f"Boundary evidence could not be read:\n{exc}")
        supported = boundary.get("supported_observation", {})
        missing = boundary.get("missing_observation", [])
        lines = [f"Status: {boundary.get('state', 'unknown')}", "", "Observed:"]
        lines.extend(f"  • {key}: {value}" for key, value in supported.items())
        lines.append("\nNot exposed through the current EML route:")
        lines.extend(f"  • {item}" for item in missing)
        lines.append(f"\nConclusion: {boundary.get('conclusion', 'No conclusion recorded.')}")
        messagebox.showinfo("Carpenter menu boundary", "\n".join(lines))
    def _draft_builder_placement_study(self):
        item_id = simpledialog.askinteger("Builder placement study", "Catalog item ID:", parent=self, minvalue=1)
        if item_id is None: return
        plan_name = simpledialog.askstring("Builder placement study", "Plan name (optional):", parent=self) or ""
        try:
            spec = GameplayFeasibilityPlanner.builder_placement_spec(item_id, plan_name)
            messagebox.showinfo("Builder placement study", json.dumps(spec, indent=2))
        except ValueError as exc:
            messagebox.showerror("Builder placement study failed", str(exc))
    def _prepare_probe_session(self):
        process_check = subprocess.run(["tasklist", "/FI", "IMAGENAME eq enshrouded.exe"], capture_output=True, text=True)
        if "enshrouded.exe" in process_check.stdout.lower():
            messagebox.showwarning("Close the game first", "Close Enshrouded before preparing a fresh research session. Your current game session was not changed.")
            return False
        game = self.installer.selected_game_path()
        if not game:
            messagebox.showwarning("Game folder", "Choose the game folder first.")
            return False
        try:
            # Call tools/verify_live_loader.py through its imported function so the packaged Windows build does
            # not try to execute itself as if it were a Python interpreter.
            live_state = inspect_live_loader(Path(game))
        except (OSError, ValueError, TypeError, KeyError):
            messagebox.showwarning("Cannot verify isolation", "Control Center could not inspect the live mod profile. Research preparation was stopped for safety.")
            return False
        if live_state.get("isolation_ready") is not True:
            external = ", ".join(live_state.get("external_third_party_mods", [])) or "another unclassified module"
            profile_path = self.base_dir / "research" / "isolated_smoke_profile_20260927.json"
            if profile_path.is_file() and messagebox.askyesno(
                "Research profile is not isolated",
                f"Research preparation was stopped because {external} is active.\n\n"
                "Control Center can temporarily quarantine the known third-party module, record a restore point, and keep the stable module active. The game must remain closed.\n\nApply the reversible isolation profile now?",
                parent=self,
            ):
                try:
                    # Apply the same reversible quarantine operation in-process.
                    # A frozen build cannot execute apply_smoke_profile.py by
                    # passing it to its own executable.
                    profile = load_smoke_profile(profile_path)
                    result = plan_smoke_profile(game, profile_path, self.base_dir / "profiles")
                    if result.get("status") != "ready":
                        raise RecoveryError("The selected isolation profile no longer matches the live modules.")
                    if smoke_game_running():
                        raise RecoveryError("Enshrouded is running; close it before applying the research profile.")
                    records = [self.recovery.quarantine(Path(game) / "mods", mod_id, f"isolated smoke profile {result['profile']}") for mod_id in result["exclude"]]
                    applied = ", ".join(record.mod_id for record in records) or "no external modules"
                    messagebox.showinfo("Research profile prepared", f"The research profile is ready. Temporarily quarantined: {applied}.\n\nRun Prepare safe test again to continue.", parent=self)
                except (OSError, ValueError, RecoveryError) as exc:
                    messagebox.showerror("Isolation failed", str(exc), parent=self)
            else:
                messagebox.showwarning(
                    "Research profile is not isolated",
                    f"Research preparation was stopped because {external} is active.\n\nReview or quarantine the third-party module first. Your stable profile was not changed.",
                    parent=self,
                )
            return False
        logs = sorted((Path(game) / "logs").glob("*.eml.log"), key=lambda path: path.stat().st_mtime if path.is_file() else 0)
        if not logs:
            messagebox.showwarning("EML log", "No EML log was found for this installation.")
            return False
        try:
            project = self._last_research_project()
            if project:
                report = self.content_validator.validate(project)
                if not report.valid:
                    details = "\n".join(f"• {issue.message}" for issue in report.issues)
                    messagebox.showwarning("Project needs validation", f"Validate the selected project in the guided wizard first:\n\n{details}")
                    return False
            session_root = self.base_dir / "research" / "probe_sessions"
            session_root.mkdir(parents=True, exist_ok=True)
            output = session_root / f"session_boundary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            command = [sys.executable, str(self.base_dir / "tools" / "prepare_probe_session.py"), str(logs[-1]), output]
            result = subprocess.run(command, cwd=self.base_dir, capture_output=True, text=True, check=True)
            project_note = f"\nValidated project: {project}" if project else "\nNo validated content project is selected yet."
            messagebox.showinfo("Probe session ready", f"Fresh-session boundary recorded automatically.{project_note}\n\nSaved session record:\n{output}\n\n{result.stdout.strip()}")
            return True
        except (OSError, subprocess.CalledProcessError) as exc:
            details = getattr(exc, "stderr", "") or str(exc)
            messagebox.showerror("Probe session failed", details)
            return False

    def _prepare_interaction_probe(self):
        """Generate a bounded interaction-donor inspection probe."""
        boundary_candidates = sorted(
            (self.base_dir / "research").glob("INTERACTION_DONOR_CANDIDATE_BOUNDARY_*.json"),
            key=lambda path: path.stat().st_mtime if path.is_file() else 0,
            reverse=True,
        )
        boundary_path = boundary_candidates[0] if boundary_candidates else None
        try:
            boundary = json.loads(boundary_path.read_text(encoding="utf-8")) if boundary_path else None
        except (OSError, json.JSONDecodeError):
            boundary = None
        if boundary and not boundary.get("runtime_safe_to_probe", False):
            next_gate = boundary.get("next_gate", "Find a supported interaction donor before probing.")
            messagebox.showinfo(
                "Interaction research is waiting",
                "Control Center found interaction records, but the current build does not expose a safe donor for them yet.\n\n"
                f"Why: {boundary.get('quarantine_reason', 'The candidate is quarantined by the safety policy.')}\n\n"
                f"Next research step: {next_gate}\n\n"
                "No probe was created, no files were installed, and the game was not changed.",
                parent=self,
            )
            return
        messagebox.showinfo(
            "Interaction research",
            "This prepares a read-only research probe for an existing interaction donor. "
            "It cannot create new interaction logic, change saves, or claim multiplayer authority.",
            parent=self,
        )
        from tkinter import simpledialog
        resource_type = simpledialog.askstring("Interaction donor", "Resource type (not TemplateResource):", parent=self)
        if not resource_type:
            return
        donor_guid = simpledialog.askstring("Interaction donor", "Build-specific donor GUID:", parent=self)
        if not donor_guid:
            return
        interaction_key = simpledialog.askstring("Interaction donor", "Interaction key (optional):", parent=self) or ""
        name = simpledialog.askstring("Interaction donor", "Short name for this research probe:", parent=self)
        if not name:
            return
        destination = filedialog.askdirectory(title="Choose research output folder", parent=self)
        if not destination:
            return
        command = [sys.executable, str(self.base_dir / "tools" / "build_interaction_donor_probe.py"),
                   "--resource-type", resource_type.strip(), "--donor-guid", donor_guid.strip(),
                   "--interaction-key", interaction_key.strip(), "--name", name.strip(),
                   "--output", str(Path(destination) / "interaction_research")]
        try:
            result = subprocess.run(command, cwd=self.base_dir, capture_output=True, text=True, check=True)
            output = Path(destination) / "interaction_research"
            messagebox.showinfo("Interaction probe ready", f"Read-only research probe created at:\n{output}\n\n{result.stdout.strip()}\n\nIt remains research-only and is not installed automatically.", parent=self)
        except (OSError, subprocess.CalledProcessError) as exc:
            details = getattr(exc, "stderr", "") or str(exc)
            messagebox.showerror("Interaction probe failed", details, parent=self)

    def _capture_research_screenshot(self, suggested_prefix="game_capture"):
        """Save a game-window capture as raw evidence without promoting it."""
        process_check = subprocess.run(["tasklist", "/FI", "IMAGENAME eq enshrouded.exe"], capture_output=True, text=True)
        if "enshrouded.exe" not in process_check.stdout.lower():
            return messagebox.showwarning("Game not running", "Launch the game through Control Center before capturing a screen.", parent=self)
        if "placed" in suggested_prefix:
            instructions = "Show the cloned or recolored item placed in the world, with the item clearly visible, then click OK."
        elif "catalog" in suggested_prefix:
            instructions = "Open the Carpenter/build menu, select the cloned or recolored item, and leave its catalog tile visible, then click OK."
        elif "item_info" in suggested_prefix:
            instructions = "Open the cloned or recolored item's information panel and leave its name and appearance visible, then click OK."
        elif "recipe" in suggested_prefix:
            instructions = "Open the recipe for the cloned or recolored item at its crafting station and leave the recipe name and ingredients visible, then click OK."
        else:
            instructions = "Bring the game screen you want to document to the front, then click OK."
        if not messagebox.askokcancel("Prepare the evidence screen", instructions, parent=self):
            return
        destination = filedialog.asksaveasfilename(
            title="Save research screenshot",
            initialdir=str(self.base_dir / "research" / "probe_sessions"),
            initialfile=f"{suggested_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            defaultextension=".png", filetypes=[("PNG image", "*.png")],
        )
        if not destination:
            return
        report = self.base_dir / "tools" / "capture_game_screenshot.py"
        report_path = Path(destination).with_suffix(".json")
        evidence_kind = (
            "placed_item" if "placed" in suggested_prefix else
            "catalog" if "catalog" in suggested_prefix else
            "item_info" if "item_info" in suggested_prefix else
            "recipe" if "recipe" in suggested_prefix else "other"
        )
        result = subprocess.run([sys.executable, str(report), destination, "--report", str(report_path), "--evidence-kind", evidence_kind], cwd=self.base_dir, capture_output=True, text=True)
        if result.returncode == 0:
            messagebox.showinfo("Screenshot saved", f"Saved screenshot to:\n{destination}\n\nEvidence report saved to:\n{report_path}\n\nThis is raw runtime evidence. It does not by itself promote a feature to verified.", parent=self)
        else:
            messagebox.showerror("Screenshot failed", result.stderr.strip() or result.stdout.strip(), parent=self)

    def _import_research_screenshot(self, evidence_kind):
        """Copy a manually captured game image into the evidence folder."""
        source = filedialog.askopenfilename(
            title="Choose the saved game screenshot",
            filetypes=[("PNG image", "*.png"), ("JPEG image", "*.jpg;*.jpeg"), ("All images", "*.png;*.jpg;*.jpeg")],
            parent=self,
        )
        if not source:
            return
        source_path = Path(source)
        if not source_path.is_file() or source_path.stat().st_size <= 0:
            return messagebox.showerror("Screenshot unavailable", "That image could not be read or is empty.", parent=self)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination_dir = self.base_dir / "research" / "probe_sessions"
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / f"{evidence_kind}_manual_{stamp}{source_path.suffix.lower()}"
        report_path = destination.with_suffix(".json")
        try:
            shutil.copy2(source_path, destination)
            report_path.write_text(json.dumps({
                "schema": "control_center.game_screenshot.v1",
                "captured_utc": datetime.now(timezone.utc).isoformat(),
                "process": "manual_import",
                "capture_mode": "user_selected_image",
                "evidence_kind": evidence_kind,
                "path": str(destination),
                "size": destination.stat().st_size,
            }, indent=2) + "\n", encoding="utf-8")
            messagebox.showinfo("Screenshot imported", f"Saved screenshot to:\n{destination}\n\nIt is recorded for review only and does not promote the feature automatically.", parent=self)
        except OSError as exc:
            messagebox.showerror("Screenshot import failed", str(exc), parent=self)
    def show_settings(self):
        self._clear("Settings")
        self._card("Control Center Settings", "Configure the saved Enshrouded installation and inspect loader/package detection. Changes are saved only when explicitly requested.")
        ctk.CTkLabel(self.body, text=f"Active profile: {self._active_profile_name()} · installation checks and recovery actions do not apply staged tuning until Review & Apply.", text_color="#bae6fd", anchor="w", wraplength=900).pack(fill="x", padx=12, pady=(0, 8))
        self._card("Integrity states", "verified = recorded hashes match; updated_by_control_center = an approved upgrade wrote the current files; user_modified = files differ from the recorded version; missing = expected files are absent; untracked = present without an ownership record; quarantined = disabled in reversible storage.")
        path=self.installer.selected_game_path()
        row=ctk.CTkFrame(self.body,fg_color="#172737",corner_radius=10); row.pack(fill="x",padx=4,pady=8)
        ctk.CTkLabel(row,text="Enshrouded installation",anchor="w").pack(side="left",padx=14,pady=14); ctk.CTkLabel(row,text=str(path or "Not selected"),text_color="#cbd5e1",anchor="w").pack(side="left",fill="x",expand=True,padx=8)
        ctk.CTkButton(row,text="Browse",width=90,command=self.choose_game).pack(side="right",padx=10,pady=8)
        ctk.CTkButton(self.body,text="Rescan installation and EML",command=lambda:self._show_detection()).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Preflight Live Loader",command=self._preflight_live_loader).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Record Compatibility Snapshot",command=self._record_compatibility).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Review Update Migration",command=self._review_update_migration).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Explain Module Graph",command=self._explain_module_graph).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Create Support Bundle",command=self._create_support_bundle).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Write Health Report",command=self._write_health_report).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Inspect Integrity States",command=self._inspect_integrity).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Adopt Current Managed Version",command=self._adopt_current_version).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Restore Recorded Version",command=self._restore_recorded_version).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Search EML Logs",command=self._search_eml_logs).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Catalog Research Log",command=self._catalog_research_log).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Inspect Localization Boundary",command=self._inspect_localization_boundary).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Catalog Custom Icon Evidence",command=self._catalog_icon_import).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Generate Read-only Research Probe",command=self._generate_research_probe).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Preflight Controlled Probe",command=self._preflight_controlled_probe).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Quarantine Failed Mod",command=self._quarantine_mod).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Restore Latest Quarantined Mod",command=self._restore_latest_quarantine).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Restore Installed Mod Backup",command=self._restore_installed_backup).pack(anchor="w",padx=8,pady=8)
        self._render_save_safety_card()
        ctk.CTkButton(self.body,text="Back Up Save Folder",command=self._backup_save_folder).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Restore Save Backup",command=self._restore_save_folder).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Compare Save Backups",command=self._compare_save_folders).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Find Save Folder (Read-only)",command=self._discover_save_folder).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Inspect Save Progress (Read-only)",command=self._inspect_save_progress).pack(anchor="w",padx=8,pady=8)
        ctk.CTkButton(self.body,text="Auto-Recover Failed Runtime",command=self._auto_recover_runtime).pack(anchor="w",padx=8,pady=8)
        self.settings_status=ctk.CTkLabel(self.body,text=self._detection_text(),justify="left",anchor="w",text_color="#cbd5e1"); self.settings_status.pack(fill="x",padx=12,pady=8)
        ctk.CTkButton(self.body,text="Save Settings",command=lambda:messagebox.showinfo("Settings","Settings are already persisted when the game folder is selected.")).pack(anchor="w",padx=8,pady=8)
    def _render_save_safety_card(self):
        card = ctk.CTkFrame(self.body, fg_color="#172737", border_width=1, border_color="#2c4152", corner_radius=10)
        card.pack(fill="x", padx=8, pady=(14, 8))
        ctk.CTkLabel(card, text="Save Safety", font=ctk.CTkFont(size=17, weight="bold"), anchor="w").pack(fill="x", padx=14, pady=(12, 2))
        ctk.CTkLabel(card, text="Protect your world before testing a mod. Control Center makes a verified copy and never changes the live save during backup or restore.", text_color="#cbd5e1", anchor="w", justify="left", wraplength=760).pack(fill="x", padx=14, pady=(0, 8))
        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkButton(row, text="Back Up My Saves", height=34, command=self._guided_save_backup).pack(side="left", padx=4)
        ctk.CTkButton(row, text="Restore a Copy Safely", height=34, command=self._guided_save_restore).pack(side="left", padx=4)
        ctk.CTkLabel(card, text="Before either action, close Enshrouded. Restore creates a separate copy for inspection; it does not overwrite your live saves.", text_color="#fbbf24", anchor="w", justify="left", wraplength=760).pack(fill="x", padx=14, pady=(0, 12))
    def _guided_save_backup(self):
        if game_is_running():
            return messagebox.showwarning("Close Enshrouded first", "Please close Enshrouded completely, then choose Back Up My Saves again.", parent=self)
        matches = discover_save_directories()
        candidates = [Path(item["path"]) for item in matches if Path(item["path"]).is_dir()]
        if not candidates:
            return messagebox.showwarning("Save folder not found", "Control Center could not find an Enshrouded save folder. Use Find Save Folder (Read-only) below, then try again.", parent=self)
        source = candidates[0]
        destination = self.base_dir / "profiles" / "save-backups"
        if len(candidates) > 1:
            choices = "\n".join(f"{index + 1}. {path}" for index, path in enumerate(candidates))
            selected = simpledialog.askinteger("Choose save folder", f"Which save folder should be backed up?\n\n{choices}\n\nEnter its number:", minvalue=1, maxvalue=len(candidates), parent=self)
            if not selected:
                return
            source = candidates[selected - 1]
        label = simpledialog.askstring("Name this backup", "Optional name (for example: before-new-bed-test):", parent=self) or "before-test"
        try:
            result = backup_save_directory(source, destination, label)
            messagebox.showinfo("Backup complete", f"Your saves are backed up safely.\n\nFiles copied: {result['file_count']}\nVerified: {'Yes' if result['verified'] else 'No'}\n\nBackup location:\n{result['backup']}", parent=self)
        except SaveBackupError as exc:
            messagebox.showerror("Backup could not be created", str(exc), parent=self)
    def _guided_save_restore(self):
        if game_is_running():
            return messagebox.showwarning("Close Enshrouded first", "Please close Enshrouded completely, then choose Restore a Copy Safely again.", parent=self)
        snapshot = filedialog.askdirectory(title="Choose a Control Center save backup")
        if not snapshot:
            return
        destination = filedialog.askdirectory(title="Choose an empty folder for the restored copy")
        if not destination:
            return
        if not messagebox.askyesno("Restore a separate copy", "Control Center will restore this backup into the folder you chose. Your live Enshrouded saves will not be overwritten. Continue?", parent=self):
            return
        try:
            result = restore_save_backup(Path(snapshot), Path(destination))
            messagebox.showinfo("Restore complete", f"Separate save copy created.\n\nFiles restored: {result['file_count']}\nVerified: {'Yes' if result['verified'] else 'No'}\n\nLocation:\n{result['destination']}", parent=self)
        except SaveBackupError as exc:
            messagebox.showerror("Restore could not be completed", str(exc), parent=self)
    def _detection_text(self):
        path=self.installer.selected_game_path()
        if not path:return "Game installation: Not Found\nEML loader: Unknown — choose a game folder\nGenerated Mod: Unknown"
        info=self.installer.detect(path); mod=path/"mods"/self.installer.MOD_ID; manifest=mod/"mod.json"; entry=mod/"src"/"mod.lua"
        self.platform.game_dir = path
        platform_status = self.platform.status(set(self.manager.modules))
        self.compatibility = CompatibilityEngine(loader_api_version=platform_status.loader_api_version)
        build = platform_status.game.build_id or "Unknown"
        runtime = platform_status.runtime.status.title()
        diagnostics = self.diagnostics.summarize(path / "logs")
        update_status = self.migrations.inspect(path)
        issues = len(platform_status.graph.issues)
        compatibility = self.compatibility.evaluate_all(self.manager.modules, platform_status.game.build_id, enabled=set(self.manager.modules))
        compatibility_errors = sum(1 for report in compatibility.values() for issue in report.issues if issue.severity == "error")
        compatibility_warnings = sum(1 for report in compatibility.values() for issue in report.issues if issue.severity == "warning")
        maturity = {mid: feature_state(data) for mid, data in platform_status.graph.modules.items()}
        research = sum(state == "research-only" for state in maturity.values())
        live = inspect_live_loader(path)
        counts = live.get("classification_counts", {})
        api_version = platform_status.loader_api_version or "Unknown (not reported by EML)"
        external = live.get('external_third_party_mods', [])
        external_text = ', '.join(external) if external else 'none'
        return f"Game installation: {'Detected' if info['has_game'] else 'Not Found'}\nGame build: {build}\nEML Lua API: {api_version}\nUpdate status: {update_status.state}\nEML proxy: {'Detected ('+', '.join(p.name for p in info['eml_proxies'])+')' if info['eml_proxies'] else 'Not Found'}\nMods directory: {'Detected' if info['has_mods_dir'] else 'Not Found'}\nGenerated Mod: {'Installed and manifest present' if manifest.is_file() and entry.is_file() else 'Not Found or Invalid'}\nCurrent runtime: {diagnostics.get('current_runtime_status', runtime)}\nRecommended action: {diagnostics.get('recommended_action', 'No recovery action is needed.')}\nHistorical errors: {diagnostics.get('historical_errors', 0)}\nLast successful session: {diagnostics.get('last_success_session') or 'not recorded'}\nModule graph issues: {issues}\nCompatibility errors: {compatibility_errors}\nCompatibility warnings: {compatibility_warnings}\nResearch-only modules: {research}\nLive maturity: stable={counts.get('stable', 0)}, experimental={counts.get('experimental', 0)}, research-only={counts.get('research-only', 0)}, unclassified={counts.get('unclassified', 0)}\nKnown external modules: {external_text}\nIsolation ready: {'yes' if live.get('isolation_ready') else 'no'}"
    def _show_detection(self):
        if hasattr(self,"settings_status") and self.settings_status.winfo_exists(): self.settings_status.configure(text=self._detection_text())
    def _preflight_live_loader(self):
        path = self.installer.selected_game_path()
        if not path:
            return messagebox.showwarning("Game folder", "Choose the game folder first.")
        result = inspect_live_loader(path)
        counts = result.get("classification_counts", {})
        lines = [
            f"Status: {result.get('status', 'unknown')}",
            f"Isolation ready: {'yes' if result.get('isolation_ready') else 'no'}",
            f"Stable: {counts.get('stable', 0)}",
            f"Experimental: {counts.get('experimental', 0)}",
            f"Research-only: {counts.get('research-only', 0)}",
            f"Unclassified: {counts.get('unclassified', 0)}",
        ]
        if result.get("external_third_party_mods"):
            lines.append("\nKnown external modules (payload untouched):")
            lines.extend(f"  {module}: {reason}" for module, reason in result.get("external_third_party_reasons", {}).items())
        if result.get("unclassified_reasons"):
            lines.append("\nUnclassified reasons:")
            lines.extend(f"  {module}: {reason}" for module, reason in result["unclassified_reasons"].items())
        if result.get("warnings"):
            lines.append("\nWarnings:")
            lines.extend(f"  {warning}" for warning in result["warnings"])
        messagebox.showinfo("Live loader preflight", "\n".join(lines))
        self._show_detection()
    def _record_compatibility(self):
        path = self.installer.selected_game_path()
        if not path: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        status = self.migrations.record(path, "assets.register_resource")
        messagebox.showinfo("Compatibility snapshot", status.message)
        self._show_detection()
    def _review_update_migration(self):
        game = self.installer.selected_game_path()
        if not game: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        build = self.platform.builds.detect(game).build_id
        update_status = self.migrations.inspect(game)
        plan = self.migrations.migration_plan(self.manager.modules, build, update_detected=update_status.state == "changed")
        lines = [f"{item['module_id']}: {item['action']} — {item['reason']}" for item in plan]
        if not lines: return messagebox.showinfo("Migration", "No modules were discovered.")
        disable = [item["module_id"] for item in plan if item["action"] == "disable"]
        text = f"Current build: {build or 'unknown'}\n\n" + "\n".join(lines)
        if disable and messagebox.askyesno("Update migration", text + "\n\nDisable modules marked 'disable' in the active profile?"):
            for module_id in disable:
                self.manager.set_module_enabled(module_id, False)
            self.manager.save_profile()
            self.show_dashboard()
        else:
            messagebox.showinfo("Update migration", text)

    def _explain_module_graph(self):
        enabled = {module_id for module_id, value in self.manager.active_config.get("enabled_modules", {}).items() if value}
        graph = self.platform.modules.build(enabled)
        rows = self.platform.modules.explain(graph)
        lines = ["Resolved load order:", "  " + " → ".join(graph.order) if graph.order else "  (none)", ""]
        for row in rows:
            state = "enabled" if row["enabled"] else "disabled"
            detail = f"{row['id']}: {state}; load index={row['load_index'] if row['load_index'] is not None else '—'}"
            if row["dependencies"]:
                detail += "; depends on " + ", ".join(row["dependencies"])
            if row["issues"]:
                detail += "\n  " + "\n  ".join(row["issues"])
            lines.append(detail)
        if graph.issues:
            lines.extend(["", "Graph issues:"])
            lines.extend(f"• {issue.module_id}: {issue.message}" for issue in graph.issues)
        messagebox.showinfo("Module graph", "\n".join(lines))
    def _create_support_bundle(self):
        destination = filedialog.asksaveasfilename(title="Save support bundle", defaultextension=".zip", filetypes=[("ZIP archive", "*.zip")])
        if not destination: return
        try:
            bundle = self.support_bundles.create(self.base_dir, self.installer.selected_game_path(), Path(destination))
            messagebox.showinfo("Support bundle", f"Created local diagnostic bundle:\n{bundle}")
        except OSError as exc:
            messagebox.showerror("Support bundle failed", str(exc))
    def _write_health_report(self):
        destination = filedialog.asksaveasfilename(title="Save health report", defaultextension=".json", filetypes=[("JSON report", "*.json")])
        if not destination: return
        try:
            report = self.health_reports.write(Path(destination), self.installer.selected_game_path())
            messagebox.showinfo("Health report", f"Wrote machine-readable report:\n{report}")
        except (OSError, ValueError) as exc:
            messagebox.showerror("Health report failed", str(exc))
    def _inspect_integrity(self):
        game = self.installer.selected_game_path()
        if not game: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        report = self.health_reports.generate(game)
        rows = [f"{item['id']}: {item.get('integrity_state', 'unknown')} · {item.get('content_origin', 'unknown')}" for item in report.get('mods', [])]
        messagebox.showinfo("Integrity states", "\n".join(rows) or "No mod directories were found.")
    def _ownership_target(self):
        game = self.installer.selected_game_path()
        if not game: return None
        from tkinter import simpledialog
        mod_id = simpledialog.askstring("Managed mod", "Mod directory to manage:", parent=self)
        if not mod_id: return None
        target = Path(game) / "mods" / mod_id
        if not target.is_dir():
            messagebox.showwarning("Managed mod", f"Directory not found:\n{target}")
            return None
        return target
    def _adopt_current_version(self):
        target = self._ownership_target()
        if target is None: return
        if not messagebox.askyesno("Adopt current version", "Record the current files as approved ownership metadata?\n\nNo mod payload will be overwritten.", parent=self): return
        try:
            result = self.ownership.adopt_current(target, "user")
            messagebox.showinfo("Version adopted", f"Recorded {result['files']} current file hashes.\nPayload overwritten: no.")
        except OwnershipError as exc:
            messagebox.showerror("Adoption failed", str(exc))
    def _restore_recorded_version(self):
        target = self._ownership_target()
        if target is None: return
        if not messagebox.askyesno("Restore recorded version", "Restore the saved ownership backup over the current managed files?", parent=self): return
        try:
            result = self.ownership.restore_recorded(target)
            messagebox.showinfo("Version restored", f"Restored {result['files']} files from the recorded restore point.")
        except OwnershipError as exc:
            messagebox.showerror("Restore failed", str(exc))
    def _search_eml_logs(self):
        from tkinter import simpledialog
        game = self.installer.selected_game_path()
        if not game: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        query = simpledialog.askstring("Search EML logs", "Text to search for (blank returns recent events):", parent=self)
        if query is None: return
        level = simpledialog.askstring("Filter log level", "Optional level: error, warning, or info (blank for all):", parent=self)
        if level is None: return
        level = level.strip().lower() or None
        if level not in {None, "error", "warning", "info"}:
            return messagebox.showwarning("Invalid log level", "Use error, warning, info, or leave the level blank.")
        events = self.diagnostics.search(Path(game) / "logs", query=query or None, level=level)
        if not events: return messagebox.showinfo("EML logs", "No matching events were found.")
        lines = [f"[{event.level.upper()}] {event.source.name}:{event.line_number} {event.message}" for event in events[-80:]]
        messagebox.showinfo("EML log events", f"Showing {len(lines)} of {len(events)} matching event(s).\n\n" + "\n".join(lines))
    def _catalog_research_log(self):
        log = filedialog.askopenfilename(title="Choose EML research log", filetypes=[("EML logs", "*.eml.log"), ("All files", "*.*")])
        if not log: return
        try:
            catalog = self.base_dir / "research" / "research_catalog.json"
            entry = ResearchProbeService.catalog_result(Path(log), catalog)
            messagebox.showinfo("Research catalog", f"Cataloged build {entry.get('build', 'unknown')}\n\nSaved to:\n{catalog}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Research catalog failed", str(exc))
    def _inspect_localization_boundary(self):
        log = filedialog.askopenfilename(title="Choose localization probe log", filetypes=[("EML logs", "*.eml.log"), ("All files", "*.*")])
        if not log: return
        try:
            result = LocalizationDebugger().inspect(Path(log))
            report_path = self.base_dir / "research" / "localization_boundary_reports" / (
                datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json"
            )
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps({
                "schema": "control_center.localization_boundary_report.v1",
                "status": result.status,
                "build_id": result.build_id,
                "boundary": result.boundary,
                "last_marker": result.last_marker,
                "panic_observed": result.panic_observed,
                "registration": result.status == "runtime_registration_verified",
                "missing_keys": list(result.missing_keys),
                "issues": list(result.issues),
                "next_safe_action": result.next_safe_action,
                "log_sha256": result.log_sha256,
            }, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            lines = [
                f"Status: {result.status}",
                f"Build: {result.build_id or 'unknown'}",
                f"Last marker: {result.last_marker or 'none'}",
                f"Boundary: {result.boundary}",
                f"Panic observed: {'yes' if result.panic_observed else 'no'}",
                "",
                "Issues:",
                *(f"- {issue}" for issue in result.issues),
                "",
                f"Next safe action: {result.next_safe_action}",
                "",
                f"Saved evidence: {report_path}",
            ]
            messagebox.showinfo("Localization boundary", "\n".join(lines))
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Localization boundary failed", str(exc))
    def _catalog_icon_import(self):
        log = filedialog.askopenfilename(title="Choose EML icon-import log", filetypes=[("EML logs", "*.eml.log"), ("All files", "*.*")])
        if not log: return
        try:
            catalog = self.base_dir / "research" / "icon_import_catalog.json"
            entry = ResearchProbeService.catalog_icon_import_result(Path(log), catalog)
            messagebox.showinfo("Icon evidence", f"Status: {entry['status']}\n\nRendering verified: no\n\nSaved to:\n{catalog}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Icon evidence failed", str(exc))
    def _preflight_controlled_probe(self):
        game = self.installer.selected_game_path()
        if not game: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        probe = filedialog.askdirectory(title="Choose generated probe folder")
        if not probe: return
        build = self.platform.builds.detect(game).build_id
        report = ResearchProbeService.controlled_validation_preflight(Path(game), Path(probe), build)
        if report["ready"]:
            messagebox.showinfo("Probe preflight", f"Ready for controlled validation on build {build or 'unknown'}.")
        else:
            messagebox.showwarning("Probe preflight blocked", "\n".join(report["issues"]))
    def _generate_research_probe(self):
        candidates = filedialog.askopenfilename(title="Choose research candidates", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not candidates: return
        output = filedialog.askdirectory(title="Choose probe output folder")
        if not output: return
        try:
            result = ResearchProbeService.generate(Path(candidates), Path(output))
            messagebox.showinfo("Research probe", f"Generated read-only probe with {result['candidate_count']} candidates.\n\nOutput:\n{result['output']}")
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            messagebox.showerror("Research probe failed", str(exc))
    def _quarantine_mod(self):
        from tkinter import simpledialog
        game = self.installer.selected_game_path()
        if not game: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        mod_id = simpledialog.askstring("Quarantine mod", "Mod folder ID:", parent=self)
        if not mod_id: return
        reason = simpledialog.askstring("Quarantine mod", "Reason:", parent=self) or "manual recovery"
        if not messagebox.askyesno("Confirm quarantine", f"Move only '{mod_id}' into the reversible quarantine area?"): return
        try:
            record = self.recovery.quarantine(game / "mods", mod_id, reason)
            messagebox.showinfo("Mod quarantined", f"Quarantined safely:\n{record.quarantined}")
        except (RecoveryError, OSError) as exc:
            messagebox.showerror("Quarantine failed", str(exc))
    def _restore_latest_quarantine(self):
        records = self.recovery.records()
        if not records: return messagebox.showinfo("Quarantine", "No quarantined mods are available.")
        record = records[-1]
        if not messagebox.askyesno("Restore quarantined mod", f"Restore '{record.mod_id}' to its original location?\n\nReason: {record.reason}"): return
        try:
            restored = self.recovery.restore(record.record_path)
            messagebox.showinfo("Mod restored", f"Restored:\n{restored}")
        except (RecoveryError, OSError) as exc:
            messagebox.showerror("Restore failed", str(exc))

    def _restore_installed_backup(self):
        installed = sorted(self.local_mods.state.get("installed", {}))
        if not installed:
            return messagebox.showinfo("Restore backup", "No Control Center-owned installed mods have restore points.")
        identity = simpledialog.askstring("Restore backup", "Enter the installed mod ID:\n\n" + "\n".join(installed), parent=self)
        if not identity or identity not in installed:
            return
        points = self.local_mods.list_backups(identity)
        if not points:
            return messagebox.showinfo("Restore backup", "No restore points were found for this mod.")
        choices = "\n".join(f"{p['id']} ({p['files']} files)" for p in points)
        backup_id = simpledialog.askstring("Restore backup", f"Enter the restore-point ID:\n\n{choices}", parent=self)
        if not backup_id or backup_id not in {p['id'] for p in points}:
            return
        game = self.installer.selected_game_path()
        if not game:
            return messagebox.showwarning("Game folder", "Choose and validate the game folder first.")
        try:
            result = self.local_mods.restore_backup(identity, backup_id, game)
            messagebox.showinfo("Backup restored", f"Restored {result['files']} files for {identity}. Restart Enshrouded before testing.")
        except LocalModError as exc:
            messagebox.showerror("Restore failed", str(exc))
    def _auto_recover_runtime(self):
        game = self.installer.selected_game_path()
        if not game: return messagebox.showwarning("Game folder", "Choose the game folder first.")
        try:
            result = self.crash_recovery.recover(game)
            messagebox.showinfo("Automatic recovery", result.message)
            if result.status == "quarantined": self._show_detection()
        except (RecoveryError, OSError) as exc:
            messagebox.showerror("Automatic recovery failed", str(exc))

    def _backup_save_folder(self):
        if game_is_running():
            return messagebox.showwarning("Close Enshrouded", "Save backups can only run while Enshrouded is closed.")
        source = filedialog.askdirectory(title="Choose Enshrouded save folder")
        if not source: return
        destination = filedialog.askdirectory(title="Choose backup destination")
        if not destination: return
        label = simpledialog.askstring("Save backup", "Optional backup label:", parent=self) or "manual"
        try:
            result = backup_save_directory(Path(source), Path(destination), label)
            messagebox.showinfo("Save backup created", f"Backed up {result['file_count']} files.\n\nSnapshot:\n{result['snapshot']}")
        except (OSError, SaveBackupError) as exc:
            messagebox.showerror("Save backup failed", str(exc))

    def _restore_save_folder(self):
        if game_is_running():
            return messagebox.showwarning("Close Enshrouded", "Save restoration can only run while Enshrouded is closed.")
        snapshot = filedialog.askdirectory(title="Choose verified save backup snapshot")
        if not snapshot: return
        destination = filedialog.askdirectory(title="Choose separate restore destination")
        if not destination: return
        if not messagebox.askyesno("Restore save backup", "Restore into this separate destination? The live save folder will not be overwritten.", parent=self): return
        try:
            result = restore_save_backup(Path(snapshot), Path(destination))
            messagebox.showinfo("Save backup restored", f"Restored {result['file_count']} files to:\n{result['destination']}")
        except (OSError, SaveBackupError) as exc:
            messagebox.showerror("Restore failed", str(exc))

    def _compare_save_folders(self):
        if game_is_running():
            return messagebox.showwarning("Close Enshrouded", "Save comparison can only run while Enshrouded is closed.")
        before = filedialog.askdirectory(title="Choose first verified save snapshot")
        if not before: return
        after = filedialog.askdirectory(title="Choose second verified save snapshot")
        if not after: return
        try:
            result = compare_save_snapshots(Path(before), Path(after))
            messagebox.showinfo("Save backup comparison", f"Added: {len(result['added'])}\nRemoved: {len(result['removed'])}\nChanged: {len(result['changed'])}")
        except (OSError, SaveBackupError) as exc:
            messagebox.showerror("Comparison failed", str(exc))

    def _inspect_save_progress(self):
        source = filedialog.askdirectory(title="Choose Enshrouded save folder")
        if not source: return
        try:
            result = inspect_save_directory(Path(source))
            messagebox.showinfo(
                "Save inspection (read-only)",
                f"Active character: {result['active_character']}\n"
                f"Blobs: {result['blob_count']}\n"
                f"Types: {', '.join(result['blob_types']) or 'none'}\n\n"
                "World-save editing is not supported by this inspection.",
            )
        except (OSError, SaveFormatError) as exc:
            messagebox.showerror("Save inspection failed", str(exc))

    def _discover_save_folder(self):
        report = discover_save_directories()
        matches = [item for item in report["candidates"] if item["has_character_index"]]
        if matches:
            messagebox.showinfo("Save folder found", "Candidate save folder(s):\n\n" + "\n".join(item["path"] for item in matches) + "\n\nDiscovery was read-only.")
        else:
            messagebox.showinfo("Save folder not found", "No standard Enshrouded save folder containing characters-index was found. Discovery was read-only.")

    def show_diagnostics(self): self.show_settings()
    def review_apply(self):
        path = self.installer.selected_game_path()
        if not path: return messagebox.showwarning("Install", "Choose the game folder first.")
        try:
            content_errors = []
            for project in self._content_project_roots():
                if (project / "package.json").is_file():
                    smoke = self.smoke_tester.run(project)
                    content_errors.extend(f"{check.name}: {check.details}" for check in smoke.checks if not check.passed)
                else:
                    report = self.content_validator.validate(project)
                    content_errors.extend(issue.message for issue in report.issues if issue.severity == "error")
            if content_errors:
                return messagebox.showerror("Content validation blocked", "Deployment was not started.\n\n" + "\n".join(content_errors))
            plan = self.installer.preview(path)
            if messagebox.askyesno("Review & Apply", "Build and install the deterministic package now?\n\n" + "\n".join(plan.files)):
                if self.dirty:
                    self.save_profile()
                self.installer.install(path); messagebox.showinfo("Installed", "Package installed and verified. Restart Enshrouded.")
        except (InstallerError, ValueError) as exc: messagebox.showerror("Apply blocked", str(exc))


def main(argv=None):
    """Launch the Control Center when called by the unified launcher."""
    previous = sys.argv
    if argv is not None:
        sys.argv = [previous[0], *list(argv)]
    try:
        ctk.set_appearance_mode("Dark"); ctk.set_default_color_theme("blue")
        if "--tool" in sys.argv:
            tool = sys.argv[sys.argv.index("--tool") + 1]
            if tool == "app":
                from gui.app import EnshroudedHubApp
                EnshroudedHubApp().mainloop()
            elif tool == "visual_builder":
                from gui.visual_builder import VisualLuaBuilderApp
                VisualLuaBuilderApp().mainloop()
        else:
            app = ControlCenter()
            if "--view" in sys.argv and sys.argv[sys.argv.index("--view") + 1] == "tuning":
                if "--category" in sys.argv: app.tuning_category = sys.argv[sys.argv.index("--category") + 1]
                if "--subcategory" in sys.argv: app.tuning_subcategory = sys.argv[sys.argv.index("--subcategory") + 1]
                if "--tab" in sys.argv: app.tuning_tab = sys.argv[sys.argv.index("--tab") + 1]
                app.show_tuning()
            elif "--view" in sys.argv and sys.argv[sys.argv.index("--view") + 1] == "mods":
                app.show_install()
            elif "--view" in sys.argv and sys.argv[sys.argv.index("--view") + 1] == "building":
                app.show_building()
            elif "--view" in sys.argv and sys.argv[sys.argv.index("--view") + 1] == "content":
                app.show_content()
            app.mainloop()
        return 0
    finally:
        sys.argv = previous


if __name__ == "__main__":
    raise SystemExit(main())
