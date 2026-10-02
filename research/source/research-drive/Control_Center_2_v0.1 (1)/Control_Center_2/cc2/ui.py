"""Dependency-free Tkinter front end. All writes stay in CC2 workspace."""
from __future__ import annotations
import json
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from .catalog import CatalogError, index_archives, search_items, get_item, diagnostics
from .planner import plan_new_item, save_plan
from .wizard import detect, approve_eml_config, install_probe, collect, probe_status, runtime_state


class App(tk.Tk):
    def __init__(self, db: Path):
        super().__init__()
        self.db = db
        self.title("Control Center 2 | KFC Custom Content Lab v0.1")
        self.geometry("1100x750")
        self.minsize(760, 540)
        self.selected_guid = None
        self._busy = False
        self.status = tk.StringVar(value="Experimental research build · Never modifies KFC, the original Control Center, or Enshrouded")
        self.kfc = tk.StringVar()
        self.game = tk.StringVar()
        self.last_bundle = None
        self.search_term = tk.StringVar()
        self.slug = tk.StringVar(value="test_stone_clone")
        self.item_name = tk.StringVar(value="Test Stone Clone")
        self.recipe_guid = tk.StringVar()
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        top = ttk.Frame(self, padding=12)
        top.grid(row=0, column=0, sticky="ew")
        top.columnconfigure(1, weight=1)
        ttk.Label(top, text="Local KFC ZIP folder (read-only):").grid(row=0, column=0, sticky="w")
        ttk.Entry(top, textvariable=self.kfc).grid(row=0, column=1, sticky="ew", padx=8)
        ttk.Button(top, text="Browse", command=self.browse_kfc).grid(row=0, column=2)
        self.index_btn = ttk.Button(top, text="Index sources", command=self.start_index)
        self.index_btn.grid(row=0, column=3, padx=6)
        self.tabs = ttk.Notebook(self)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        self.catalog = ttk.Frame(self.tabs, padding=12)
        self.planner = ttk.Frame(self.tabs, padding=12)
        self.health = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.catalog, text="Vanilla catalog")
        self.tabs.add(self.planner, text="New-item research plan")
        self.tabs.add(self.health, text="Diagnostics")
        self._catalog_tab(); self._plan_tab(); self._health_tab()
        ttk.Label(self, textvariable=self.status, padding=(12,8), wraplength=960).grid(row=2, column=0, sticky="ew")

    def _catalog_tab(self):
        self.catalog.columnconfigure(0, weight=1)
        self.catalog.rowconfigure(2, weight=1)
        self.catalog.rowconfigure(4, weight=1)
        row = ttk.Frame(self.catalog)
        row.grid(row=0, column=0, sticky="ew")
        row.columnconfigure(0, weight=1)
        entry = ttk.Entry(row, textvariable=self.search_term)
        entry.grid(row=0, column=0, sticky="ew", padx=(0,8))
        entry.bind("<Return>", lambda e: self.search())
        ttk.Button(row, text="Search", command=self.search).grid(row=0, column=1)
        ttk.Label(self.catalog, text="Choose an item below. Debug names are observed vanilla labels, not localized display text.").grid(row=1, column=0, sticky="w", pady=5)
        columns = ("debug", "id", "category", "registry")
        self.table = ttk.Treeview(self.catalog, columns=columns, show="headings", height=12, selectmode="browse")
        for key,title,width in (("debug","Debug name",380),("id","Numeric ID",110),("category","Category",150),("registry","Registered",90)):
            self.table.heading(key, text=title); self.table.column(key, width=width, stretch=key=="debug")
        self.table.grid(row=2, column=0, sticky="nsew")
        self.table.bind("<<TreeviewSelect>>", self.select_item)
        self.detail = tk.Text(self.catalog, wrap="word", state="disabled", height=12)
        ttk.Label(self.catalog, text="Verified dependency detail:").grid(row=3, column=0, sticky="w", pady=(12,4))
        self.detail.grid(row=4, column=0, sticky="nsew")

    def _plan_tab(self):
        self.planner.columnconfigure(1, weight=1)
        rows = [("Source vanilla GUID", "source_guid"), ("Project slug", "slug"), ("New display name", "item_name"),
                ("Optional producing recipe GUID", "recipe_guid")]
        self.source_guid = tk.StringVar()
        for row,(title,var) in enumerate(rows):
            ttk.Label(self.planner,text=title).grid(row=row,column=0,sticky="w",padx=8,pady=8)
            ttk.Entry(self.planner,textvariable=getattr(self,var)).grid(row=row,column=1,sticky="ew",padx=8,pady=8)
        ttk.Label(self.planner,text="Notes").grid(row=4,column=0,sticky="nw",padx=8,pady=8)
        self.notes = tk.Text(self.planner, height=4, wrap="word")
        self.notes.grid(row=4,column=1,sticky="nsew",padx=8,pady=8)
        ttk.Button(self.planner,text="Preview plan (no game changes)",command=self.preview_plan).grid(row=5,column=1,sticky="w",padx=8,pady=8)
        ttk.Button(self.planner,text="Export plan JSON",command=self.export_plan).grid(row=5,column=1,sticky="e",padx=8,pady=8)
        self.plan_preview = tk.Text(self.planner, height=17, wrap="word", state="disabled")
        self.plan_preview.grid(row=6,column=0,columnspan=2,sticky="nsew",padx=8,pady=8)
        self.planner.rowconfigure(6, weight=1)
        ttk.Label(self.planner,text="Output status: EXPERIMENTAL_NOT_DEPLOYABLE. EML injection is deliberately disabled.").grid(row=7,column=0,columnspan=2,sticky="w",padx=8)

    def _health_tab(self):
        self.health.rowconfigure(2,weight=1)
        self.health.columnconfigure(0,weight=1)
        setup=ttk.Frame(self.health); setup.grid(row=0,column=0,sticky="ew",pady=6); setup.columnconfigure(1,weight=1)
        ttk.Label(setup,text="Enshrouded folder (auto-detected):").grid(row=0,column=0,sticky="w")
        ttk.Entry(setup,textvariable=self.game).grid(row=0,column=1,sticky="ew",padx=8)
        ttk.Button(setup,text="Browse",command=self.browse_game).grid(row=0,column=2)
        buttons=ttk.Frame(self.health); buttons.grid(row=1,column=0,sticky="ew")
        ttk.Button(buttons,text="Check setup",command=self.check_setup).pack(side="left",padx=(0,6))
        ttk.Button(buttons,text="Run Compatibility Test",command=self.prepare_test).pack(side="left",padx=6)
        ttk.Button(buttons,text="Repair Installed Probe",command=self.repair_probe).pack(side="left",padx=6)
        ttk.Button(buttons,text="Retry Compatibility Test",command=self.retry_test).pack(side="left",padx=6)
        ttk.Button(buttons,text="Collect Results",command=self.collect_results).pack(side="left",padx=6)
        ttk.Button(buttons,text="Copy Results",command=self.copy_results).pack(side="left",padx=6)
        self.health_report = tk.Text(self.health,wrap="word",state="disabled")
        self.health_report.grid(row=2,column=0,sticky="nsew")

    @staticmethod
    def replace_text(widget,text):
        widget.configure(state="normal")
        widget.delete("1.0","end")
        widget.insert("end",text)
        widget.configure(state="disabled")

    def browse_kfc(self):
        chosen = filedialog.askdirectory(title="Select local folder containing KFC ZIP exports")
        if chosen:self.kfc.set(chosen)

    def browse_game(self):
        chosen=filedialog.askdirectory(title="Select Enshrouded installation folder")
        if chosen:self.game.set(chosen); self.check_setup()

    def check_setup(self):
        data=detect(Path(self.game.get()) if self.game.get() else None,self.db)
        if data.get('game_root'): self.game.set(data['game_root'])
        lines=["SETUP STATUS",""]
        for key in ('installation','eml_config','base_lua','types_lua','probe','catalog','logs'):
            x=data[key]; lines.append(f"{'PASS' if x.get('available') or x.get('game_log') or x.get('export_directory') else 'MISSING'}  {key}: {x.get('plain_english',x.get('path',''))}")
        self.replace_text(self.health_report,'\n'.join(lines)); self.status.set("Setup check complete; runtime behavior is not proven")

    def prepare_test(self):
        game=Path(self.game.get()).expanduser().resolve() if self.game.get() else None
        if not game or not game.is_dir(): self.check_setup(); messagebox.showerror("Setup required","Choose the Enshrouded installation folder first."); return
        state=probe_status(game/'mods'/'cc2_research_probe')
        if state['status']=='unrelated': messagebox.showerror("Probe installation refused","An unrelated mod occupies cc2_research_probe; it will not be overwritten. Choose a different test setup or remove it manually."); return
        replace=state['status'] in ('outdated','partial')
        prompt="Back up and enable EML export/logging, then install the separate CC2 probe? The original Control Center will not be touched."
        if state['status']=='identical': prompt="Back up and enable EML export/logging? The CC2 probe is already installed and matches this version."
        elif replace: prompt="The existing CC2 probe is %s. Back it up outside the active mods folder, replace it, and enable EML export/logging?" % state['status']
        if not messagebox.askyesno("Explicit approval required",prompt): return
        try:
            cfg=approve_eml_config(game,self.db.parent)
            ins=install_probe(game,self.db.parent,replace=replace)
            self.replace_text(self.health_report,json.dumps({"configuration_backup":cfg,"probe":ins,"next":"Launch Enshrouded, enter a disposable world, then return and click Collect Results."},indent=2))
            self.status.set("Probe staged with explicit approval; launch the game manually")
        except Exception as exc: messagebox.showerror("Compatibility setup blocked",str(exc))

    def collect_results(self):
        game=Path(self.game.get()).expanduser().resolve() if self.game.get() else None
        if not game: self.check_setup(); return
        try:
            self.last_bundle=collect(self.db,game,self.db.parent)
            state=runtime_state(game,self.db)
            self.replace_text(self.health_report,json.dumps({"result":state["plain_english"],"state":state["state"],"bundle":self.last_bundle},indent=2))
            self.status.set(state["plain_english"]+" Console-only output is not runtime proof; use the fallback instructions if needed.")
        except Exception as exc: messagebox.showerror("Collection failed",str(exc))

    def copy_results(self):
        text=self.health_report.get('1.0','end').strip()
        if not text:return
        self.clipboard_clear(); self.clipboard_append(text); self.status.set("Results copied to clipboard")

    def retry_test(self):
        """One-click retry: re-check installed probe/config then collect only CC2 output."""
        game=Path(self.game.get()).expanduser().resolve() if self.game.get() else None
        if not game: self.check_setup(); return
        state=runtime_state(game,self.db)
        self.replace_text(self.health_report,json.dumps(state,indent=2))
        self.status.set("Retry checked: "+state["plain_english"])

    def repair_probe(self):
        game=Path(self.game.get()).expanduser().resolve() if self.game.get() else None
        if not game: self.check_setup(); messagebox.showerror("Setup required","Choose the Enshrouded installation folder first."); return
        state=probe_status(game/'mods'/'cc2_research_probe')
        if state['status']=='identical': self.status.set("Probe already installed; no repair needed"); return
        if state['status']=='unrelated': messagebox.showerror("Repair refused","The installed folder is not recognizably the CC2 probe. It will not be overwritten."); return
        if state['status'] not in ('outdated','partial'): messagebox.showinfo("No installed probe","There is no installed CC2 probe to repair."); return
        if not messagebox.askyesno("Approve probe repair","Back up the outdated/partial CC2 probe outside the active mods directory and install the current bundled probe?"): return
        try:
            result=install_probe(game,self.db.parent,replace=True)
            verified=probe_status(game/'mods'/'cc2_research_probe')
            if verified['status']!='identical': raise RuntimeError("post-repair verification failed: "+json.dumps(verified))
            self.replace_text(self.health_report,json.dumps({"repair":result,"verification":verified},indent=2)); self.status.set("Installed probe repaired and verified")
        except Exception as exc: messagebox.showerror("Probe repair failed",str(exc))

    def start_index(self):
        if self._busy:return
        path=Path(self.kfc.get()).expanduser().resolve()
        if self.db.resolve()==path or path in self.db.resolve().parents:
            messagebox.showerror("Read-only safety","The catalog database cannot live inside the KFC folder.");return
        self._busy=True
        self.index_btn.configure(state="disabled")
        self.status.set("Indexing KFC resource exports…")
        def worker():
            try:
                result=index_archives(path,self.db)
                self.after(0,lambda:self._finished("Indexed: "+", ".join(result["source_archives"])))
            except Exception as e:
                msg=str(e)
                self.after(0,lambda:self._finished("Index failed: "+msg,True))
        threading.Thread(target=worker,daemon=True).start()

    def _finished(self,msg,error=False):
        self._busy=False
        self.index_btn.configure(state="normal")
        self.status.set(msg)
        if error:messagebox.showerror("Control Center 2",msg)
        else:self.search()

    def search(self):
        try:
            found=search_items(self.db,self.search_term.get(),100)
            self.table.delete(*self.table.get_children())
            for x in found:
                self.table.insert("", "end",iid=x["guid"],values=(x["debug_name"] or "(unnamed)",x["item_id"],x["category"],"yes" if x["in_registry"] else "no"))
            self.status.set(f"{len(found)} matching item(s), maximum 100 per query")
        except Exception as exc:self.status.set(str(exc))

    def select_item(self,event=None):
        selected=self.table.selection()
        if not selected:return
        self.selected_guid=selected[0]
        self.source_guid.set(self.selected_guid)
        try:
            d=get_item(self.db,self.selected_guid)
            self.replace_text(self.detail,json.dumps(d,indent=2,ensure_ascii=False))
        except Exception as exc:self.status.set(str(exc))

    def _make_plan(self):
        return plan_new_item(self.db,self.source_guid.get().strip(),slug=self.slug.get().strip(),
                             name=self.item_name.get().strip(),recipe_guid=self.recipe_guid.get().strip() or None,
                             notes=self.notes.get("1.0","end").strip())

    def preview_plan(self):
        try:
            plan=self._make_plan()
            self.replace_text(self.plan_preview,json.dumps(plan,indent=2,ensure_ascii=False))
            self.status.set("Plan preview only. Resource creation is not enabled.")
        except Exception as exc:messagebox.showerror("Plan blocked",str(exc))

    def export_plan(self):
        try:plan=self._make_plan()
        except Exception as exc:messagebox.showerror("Plan blocked",str(exc));return
        base=self.db.parent / "exports"
        base.mkdir(parents=True,exist_ok=True)
        out=filedialog.asksaveasfilename(title="Save experimental research plan",initialdir=base,
                       initialfile=self.slug.get()+"_"+datetime.now().strftime("%Y%m%d_%H%M%S")+".json",defaultextension=".json",filetypes=[("JSON","*.json")])
        if not out:return
        try:
            path=save_plan(plan,Path(out))
            self.status.set("Saved research plan: "+str(path))
        except Exception as exc:messagebox.showerror("Export blocked",str(exc))

    def run_diagnostics(self):
        try:
            data=diagnostics(self.db)
            self.replace_text(self.health_report,json.dumps(data,indent=2,ensure_ascii=False))
            self.status.set("Static diagnostics complete; not in-game proof")
        except Exception as exc:messagebox.showerror("Diagnostics",str(exc))


def launch(db: Path):
    App(db).mainloop()
