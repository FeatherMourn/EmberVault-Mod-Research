from __future__ import annotations
import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from trainer_table import Record, inventory, sha256
from bridge import detect

EXPECTED_HASH = '0A591301A96C5FDF257564DEC6D53603EEFEC4AD7C79A3677BB7B3ECFA707D30'
ROOT = Path(__file__).resolve().parent
DEFAULT_TABLE = ROOT.parent / 'Enshrouded_Master_Trainer.CT'
CONFIG = ROOT / 'trainer_gui.json'
BG='#071520'; PANEL='#0d2230'; PANEL2='#102a39'; BORDER='#214456'; TEXT='#dcebf1'; MUTED='#8fa9b5'; TEAL='#4fe0ed'; AMBER='#f6a23a'

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Enshrouded Master Trainer'); self.geometry('1600x900'); self.minsize(1120,680); self.configure(bg=BG)
        self.records=[]; self.table=None; self.events=[]; self.search=tk.StringVar(); self.search.trace_add('write',lambda *_:self.render_dashboard()); self._build(); self.load_table(self._configured_table()); self.after(1200,self.refresh_status)
    def label(self,p,text,color=TEXT,size=10,bold=False,**kw): return tk.Label(p,text=text,fg=color,bg=kw.pop('bg',p.cget('bg')),font=('Segoe UI',size,'bold' if bold else 'normal'),**kw)
    def button(self,p,text,command,state='normal',accent=False): return tk.Button(p,text=text,command=command,state=state,relief='flat',bd=0,bg=AMBER if accent else PANEL2,fg='#09151c' if accent else TEXT,activebackground='#e9bd68',font=('Segoe UI',9,'bold'),padx=8,pady=6)
    def _build(self):
        h=tk.Frame(self,bg='#0b1b28',height=78);h.pack(fill='x');h.pack_propagate(False);b=tk.Frame(h,bg='#0b1b28');b.pack(side='left',padx=22);self.label(b,'✦  ENSHROUDED',TEAL,22,True,bg='#0b1b28').pack(anchor='w',pady=(11,0));self.label(b,'MASTER TRAINER  ·  v1.0.0',MUTED,9,bg='#0b1b28').pack(anchor='w')
        self.status=self.label(h,'Game: OFF  ·  Cheat Engine: OFF  ·  Attached: NO',TEXT,9,bg='#0b1b28');self.status.pack(side='right',padx=24);s=tk.Frame(h,bg='#132d3c',highlightthickness=1,highlightbackground=BORDER);s.pack(side='right',padx=16,pady=18);self.label(s,'⌕',TEAL,16,True,bg='#132d3c').pack(side='left');tk.Entry(s,textvariable=self.search,width=28,relief='flat',bg='#132d3c',fg=TEXT,insertbackground=TEXT,font=('Segoe UI',10)).pack(side='left',padx=6)
        body=tk.Frame(self,bg=BG);body.pack(fill='both',expand=True);self.sidebar=tk.Frame(body,bg='#0b1d2a',width=220);self.sidebar.pack(side='left',fill='y');self.sidebar.pack_propagate(False);self.main=tk.Frame(body,bg=BG);self.main.pack(side='left',fill='both',expand=True);self.rail=tk.Frame(body,bg='#0a1924',width=286);self.rail.pack(side='right',fill='y');self.rail.pack_propagate(False);self._sidebar();self._rail();self.render_dashboard()
    def _sidebar(self):
        self.label(self.sidebar,'NAVIGATION',MUTED,9,True,bg='#0b1d2a').pack(anchor='w',padx=18,pady=(26,10))
        for icon,text in [('⌂','Dashboard'),('♟','Player Stats'),('♨','Survival'),('↗','Movement'),('▣','Inventory'),('⚑','Glider'),('⚒','Building'),('⌖','Teleport'),('⚙','Utilities'),('⚙','Settings')]:
            self.button(self.sidebar,f'{icon}   {text}',self.show_page).pack(fill='x',padx=9,pady=2)
        self.label(self.sidebar,'TABLE IDENTITY',MUTED,9,True,bg='#0b1d2a').pack(anchor='w',padx=18,pady=(28,5));self.table_info=self.label(self.sidebar,'Loading…',MUTED,8,anchor='w',justify='left',wraplength=180,bg='#0b1d2a');self.table_info.pack(fill='x',padx=18);self.button(self.sidebar,'▣  Open Different CT',self.choose_table).pack(fill='x',padx=12,pady=18)
    def _rail(self):
        self.label(self.rail,'ACTIVE CHEATS',TEAL,11,True,bg='#0a1924').pack(anchor='w',padx=16,pady=(28,8));self.label(self.rail,'No verified activations',MUTED,9,anchor='w',bg='#0a1924').pack(fill='x',padx=16,pady=(0,18));self._rail_box('PRESETS',['Survival+ (Balanced)','Creative Mode','Exploration','Combat Prep']);self._rail_box('SAFETY & INFORMATION',['Use at your own risk.','Game Process: detected state only','Cheat Engine: detected state only','Activation bridge: unavailable'])
    def _rail_box(self,title,lines):
        box=tk.Frame(self.rail,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);box.pack(fill='x',padx=12,pady=8);self.label(box,title,TEAL,10,True,bg=PANEL).pack(anchor='w',padx=12,pady=(12,7));
        for line in lines:self.label(box,('▶ ' if title=='PRESETS' else '◆ ')+line,TEXT if title=='PRESETS' else MUTED,9,anchor='w',bg=PANEL).pack(fill='x',padx=12,pady=5)
    def _card(self,p,title,icon,records):
        c=tk.Frame(p,bg=PANEL,highlightthickness=1,highlightbackground=BORDER);c.pack(side='left',fill='both',expand=True,padx=5,pady=5);self.label(c,f'{icon}  {title.upper()}',TEAL,10,True,bg=PANEL).pack(anchor='w',padx=14,pady=(12,8))
        for r in records[:5]:
            row=tk.Frame(c,bg=PANEL2);row.pack(fill='x',padx=10,pady=3);self.label(row,r.description[:34],TEXT,9,anchor='w',bg=PANEL2).pack(side='left',fill='x',expand=True,padx=8,pady=6);self.button(row,'OFF',lambda rec=r:self._unavailable(rec),'disabled').pack(side='right',padx=6,pady=3)
        if not records:self.label(c,'No matching records in verified CT.',MUTED,9,anchor='w',bg=PANEL).pack(anchor='w',padx=14,pady=10)
    def render_dashboard(self):
        for w in self.main.winfo_children():w.destroy()
        self.label(self.main,'DASHBOARD',TEXT,24,True,bg=BG).pack(anchor='w',padx=18,pady=(22,0));self.label(self.main,'Verified records from the original table · controls remain safe while disconnected',MUTED,10,bg=BG).pack(anchor='w',padx=18,pady=(0,8))
        q=tk.Frame(self.main,bg=BG);q.pack(fill='x',padx=14,pady=7)
        for name,val in [('QUICK TOGGLES','0 active'),('TABLE RECORDS',str(len(self.records))),('VERIFIED STATE','Disconnected')]:
            x=tk.Frame(q,bg=PANEL2,highlightthickness=1,highlightbackground=BORDER);x.pack(side='left',fill='x',expand=True,padx=5);self.label(x,'◆  '+name,TEAL,10,True,bg=PANEL2).pack(anchor='w',padx=12,pady=(10,3));self.label(x,val,TEXT,14,True,bg=PANEL2).pack(anchor='w',padx=12,pady=(0,10))
        grid=tk.Frame(self.main,bg=BG);grid.pack(fill='both',expand=True,padx=14);groups={}
        for r in self.records:
            if self.search.get().lower() not in r.description.lower():continue
            d=r.description.lower();key='Player Stats' if any(x in d for x in ['health','mana','stamina','attribute','vital']) else 'Survival' if any(x in d for x in ['hunger','thirst','temperature','survival']) else 'Movement' if any(x in d for x in ['speed','jump','fall','flight','glide']) else 'Inventory' if any(x in d for x in ['item','stack','durability','weight']) else 'Building' if any(x in d for x in ['build','craft']) else 'Utilities';groups.setdefault(key,[]).append(r)
        for i,(n,ic) in enumerate([('Player Stats','♥'),('Survival','♨'),('Movement','↗'),('Inventory','▣'),('Glider','⚑'),('Building','⚒')]):self._card(grid,n,ic,groups.get(n,[])).grid(row=i//2,column=i%2,sticky='nsew')
        for i in range(2):grid.grid_columnconfigure(i,weight=1)
        for i in range(3):grid.grid_rowconfigure(i,weight=1)
        bottom=tk.Frame(self.main,bg=BG);bottom.pack(fill='x',padx=14,pady=5);self._card(bottom,'Teleport','⌖',groups.get('Utilities',[])[:3]);self._card(bottom,'Recent Actions','◷',[])
    def _configured_table(self):
        try:return Path(json.loads(CONFIG.read_text()).get('table',str(DEFAULT_TABLE)))
        except (OSError,ValueError,TypeError):return DEFAULT_TABLE
    def load_table(self,path):
        if not path.is_file():return self._event('Table not found: '+str(path))
        actual=sha256(path)
        if path.resolve()==DEFAULT_TABLE.resolve() and actual!=EXPECTED_HASH:return self._event('HASH MISMATCH — table not loaded.')
        try:self.records=inventory(path);self.table=path
        except Exception as e:return self._event('CT parse failed: '+str(e))
        self.table_info.configure(text=f'{path.name}\n{len(self.records)} records\nSHA-256 {actual[:16]}…');self._event(f'Loaded {len(self.records)} records');self.render_dashboard()
    def refresh_status(self):
        s=detect();self.status.configure(text=f'Game: {"ON" if s.game else "OFF"}  ·  Cheat Engine: {"ON" if s.cheat_engine else "OFF"}  ·  Attached: NO');self.after(3000,self.refresh_status)
    def choose_table(self):
        p=filedialog.askopenfilename(filetypes=[('Cheat Engine Table','*.CT')])
        if p:self.load_table(Path(p));CONFIG.write_text(json.dumps({'table':p},indent=2))
    def show_page(self):self.render_dashboard()
    def _unavailable(self,r):messagebox.showinfo('Unavailable',f'{r.description}\n\nDisabled: no verified Cheat Engine bridge is connected.')
    def _event(self,text):self.events.append(text)

if __name__=='__main__':App().mainloop()
