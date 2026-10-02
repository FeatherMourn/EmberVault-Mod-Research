from __future__ import annotations
import json
import sys
import traceback
import queue
import threading
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QMainWindow, QPushButton, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget)
from trainer_table import inventory, sha256
from bridge import detect, process_is_enshrouded
from bridge_client import BridgeClient

ROOT = Path(__file__).resolve().parent
TABLE = ROOT.parent / 'Enshrouded_Master_Trainer.CT'
EXPECTED = '0A591301A96C5FDF257564DEC6D53603EEFEC4AD7C79A3677BB7B3ECFA707D30'
STARTUP_LOG = ROOT / 'startup_error.log'

def startup_log(message: str) -> None:
    with STARTUP_LOG.open('a', encoding='utf-8') as stream:
        stream.write(f'[{datetime.now().isoformat(timespec="seconds")}] {message}\n')

class Card(QFrame):
    def __init__(self, title, icon, records, labels, live_records, verified, parent=None):
        super().__init__(parent); self.setObjectName('card')
        box=QVBoxLayout(self); box.setContentsMargins(14,12,14,12); box.setSpacing(6)
        head=QLabel(f'{icon}  {title.upper()}'); head.setObjectName('cardTitle'); box.addWidget(head)
        for record in records[:6]:
            meta=labels.get(record.record_id,{})
            name=meta.get('short_label') or meta.get('display_name') or record.description
            if meta.get('control_type') == 'group' or record.group:
                continue
            live=live_records.get(record.record_id) if verified else None
            if live is None: state='UNVERIFIED'
            elif record.script: state='ACTIVE' if bool(live.get('active')) else 'INACTIVE'
            else: state=('VALUE: '+str(live.get('value'))) if live.get('value') is not None else 'UNREADABLE'
            row=QFrame(); row.setObjectName('recordRow'); lay=QHBoxLayout(row); lay.setContentsMargins(9,6,7,6)
            text=QLabel(name); text.setWordWrap(True); text.setToolTip(record.description); lay.addWidget(text,1)
            control=QPushButton(state); control.setEnabled(False); control.setToolTip(record.description)
            control.setFixedWidth(105); lay.addWidget(control); box.addWidget(row)
        if not records:
            empty=QLabel('No verified records mapped to this category.'); empty.setObjectName('muted'); box.addWidget(empty)

class App(QMainWindow):
    def __init__(self):
        startup_log('App construction started')
        super().__init__(); self.setWindowTitle('Enshrouded Master Trainer'); self.resize(1600,900); self.setMinimumSize(1120,680)
        startup_log(f'Loading table: {TABLE}')
        self.records=inventory(TABLE); startup_log(f'Parsed {len(self.records)} table records')
        self.labels=json.loads((ROOT/'trainer_labels.json').read_text(encoding='utf-8')); startup_log('Loaded trainer_labels.json')
        self.live_records={}; self.bridge_verified=False; self.bridge_process_id=0; self.events=[]; self.bridge=BridgeClient(); self.bridge_results=queue.Queue(); self.bridge_busy=False; self._build(); startup_log('Main window widgets constructed'); self._refresh_status(); startup_log('Initial status rendered'); QTimer.singleShot(3000,self._timer); QTimer.singleShot(500,self._poll_bridge)
    def _build(self):
        root=QWidget(); self.setCentralWidget(root); outer=QVBoxLayout(root); outer.setContentsMargins(0,0,0,0); outer.setSpacing(0)
        header=QFrame(); header.setObjectName('header'); header.setMinimumHeight(92); outer.addWidget(header)
        if (ROOT/'dark-fantasy-background.png').is_file():
            bg=QLabel(header); bg.setPixmap(QPixmap(str(ROOT/'dark-fantasy-background.png'))); bg.setScaledContents(True); bg.setGeometry(0,0,1600,92); bg.lower()
        hl=QHBoxLayout(header); hl.setContentsMargins(24,12,24,12)
        brand=QVBoxLayout(); title=QLabel('✦  ENSHROUDED'); title.setObjectName('brand'); sub=QLabel('MASTER TRAINER  ·  v1.0.0'); sub.setObjectName('subtle'); brand.addWidget(title); brand.addWidget(sub); hl.addLayout(brand); hl.addStretch()
        self.status=QLabel(); self.status.setObjectName('status'); hl.addWidget(self.status); self.bridge_status=QLabel('Bridge: unavailable'); self.bridge_status.setObjectName('status'); hl.addWidget(self.bridge_status); self.search=QLineEdit(); self.search.setPlaceholderText('⌕  Search features…'); self.search.setFixedWidth(270); self.search.textChanged.connect(self.render); hl.addWidget(self.search)
        body=QHBoxLayout(); body.setContentsMargins(0,0,0,0); body.setSpacing(0); outer.addLayout(body,1)
        body.addWidget(self.sidebar()); body.addWidget(self.center(),1); body.addWidget(self.rail())
    def sidebar(self):
        w=QFrame(); w.setObjectName('sidebar'); w.setFixedWidth(220); box=QVBoxLayout(w); box.setContentsMargins(10,22,10,15); box.setSpacing(4); box.addWidget(QLabel('NAVIGATION',objectName='muted'))
        for icon,name in [('⌂','Dashboard'),('♟','Player Stats'),('♨','Survival'),('↗','Movement'),('▣','Inventory'),('⚑','Glider'),('⚒','Building'),('⌖','Teleport'),('⚙','Utilities'),('⚙','Settings')]:
            b=QPushButton(f'{icon}   {name}'); b.setObjectName('nav'); b.clicked.connect(self.render); box.addWidget(b)
        box.addStretch(); box.addWidget(QLabel('TABLE IDENTITY',objectName='muted')); box.addWidget(QLabel(f'Enshrouded_Master_Trainer.CT\n{len(self.records)} records\nSHA-256 {sha256(TABLE)[:16]}…',objectName='subtle')); return w
    def center(self):
        self.content=QWidget(); outer=QVBoxLayout(self.content); outer.setContentsMargins(18,18,14,12); outer.setSpacing(8)
        h=QLabel('DASHBOARD'); h.setObjectName('pageTitle'); outer.addWidget(h); outer.addWidget(QLabel('Control your Enshrouded experience · verified records only',objectName='subtle'))
        quick=QFrame(); quick.setObjectName('quick'); q=QHBoxLayout(quick); q.setContentsMargins(10,8,10,8); q.addWidget(QLabel('QUICK TOGGLES',objectName='cardTitle'))
        for name,icon in [('God Mode','♥'),('Infinite Stamina','↯'),('Free Flight','⚑'),('No Fall Damage','◇'),('Creative Building','⚒')]:
            b=QPushButton(f'{icon}  {name}   ·   UNAVAILABLE'); b.setEnabled(False); b.setToolTip('No verified local Cheat Engine bridge is connected.'); q.addWidget(b)
        outer.addWidget(quick)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setFrameShape(QFrame.NoFrame); self.canvas=QWidget(); self.grid=QGridLayout(self.canvas); self.grid.setContentsMargins(0,0,0,0); self.grid.setSpacing(8); self.scroll.setWidget(self.canvas); outer.addWidget(self.scroll,1)
        bottom=QHBoxLayout(); bottom.addWidget(self._bottom_card('⌖  TELEPORT','No verified teleport destinations.'),1); bottom.addWidget(self._bottom_card('◷  RECENT ACTIONS','No verified actions yet.'),1); outer.addLayout(bottom); return self.content
    def _bottom_card(self,title,text):
        c=QFrame(); c.setObjectName('card'); l=QVBoxLayout(c); l.setContentsMargins(14,10,14,10); l.addWidget(QLabel(title,objectName='cardTitle')); l.addWidget(QLabel(text,objectName='muted')); return c
    def rail(self):
        w=QFrame(); w.setObjectName('rail'); w.setFixedWidth(285); box=QVBoxLayout(w); box.setContentsMargins(14,24,14,12); box.addWidget(QLabel('ACTIVE CHEATS',objectName='cardTitle')); self.active_label=QLabel('No verified activations.',objectName='muted'); self.active_label.setWordWrap(True); box.addWidget(self.active_label); box.addSpacing(18); box.addWidget(self._rail_card('PRESETS',['Unavailable until preset validation is implemented.'])); box.addWidget(self._rail_card('SAFETY & INFORMATION',['Use offline or at your own risk.','Game Process: detected state only','Cheat Engine: detected state only','Attachment: unverified'])); box.addStretch(); return w
    def _rail_card(self,title,lines):
        c=QFrame(); c.setObjectName('card'); l=QVBoxLayout(c); l.setContentsMargins(12,12,12,12); l.addWidget(QLabel(title,objectName='cardTitle')); [l.addWidget(QLabel('◆  '+x,objectName='muted')) for x in lines]; return c
    def render(self):
        while self.grid.count(): self.grid.takeAt(0).widget().deleteLater()
        groups={n:[] for n in ['Player Stats','Survival','Movement','Inventory','Glider','Building']}; query=self.search.text().lower()
        for r in self.records:
            m=self.labels.get(r.record_id,{}); name=m.get('display_name',r.description); category=m.get('category')
            if category in groups and query in (name+' '+r.description).lower(): groups[category].append(r)
        for i,(name,icon) in enumerate([('Player Stats','♥'),('Survival','♨'),('Movement','↗'),('Inventory','▣'),('Glider','⚑'),('Building','⚒')]): self.grid.addWidget(Card(name,icon,groups[name],self.labels,self.live_records,self.bridge_verified),i//3,i%3)
    def _refresh_status(self):
        s=detect(); attached=process_is_enshrouded(self.bridge_process_id) if self.bridge_verified else False; self.status.setText(f'Game: {"ON" if s.game else "OFF"}  ·  Cheat Engine: {"ON" if s.cheat_engine else "OFF"}  ·  Attached: {"VERIFIED" if attached else "UNVERIFIED"}'); self.render()
    def _poll_bridge(self):
        if not self.bridge_busy:
            self.bridge_busy=True
            expected=[{'id':r.record_id,'description':r.description} for r in self.records]
            def work():
                try: self.bridge_results.put(self.bridge.call('hello',{'expected_records':expected},timeout=1.0))
                finally: self.bridge_busy=False
            threading.Thread(target=work,daemon=True).start()
        while not self.bridge_results.empty():
            result=self.bridge_results.get()
            if result.ok and result.payload.get('table_verified'):
                self.bridge_verified=True; self.bridge_process_id=int(result.payload.get('process_id') or 0); self.live_records=result.payload.get('records') or {}; self.bridge_status.setText('Bridge: connected · table verified'); active=[self.labels.get(k,{}).get('short_label',v.get('description','')) for k,v in self.live_records.items() if v.get('active')]; self.active_label.setText('\n'.join('● '+x for x in active[:8]) or 'No verified activations.'); self.render()
            else:
                self.bridge_verified=False; self.bridge_process_id=0; self.live_records={}; self.bridge_status.setText('Bridge: '+(result.error or 'unavailable')); self.active_label.setText('No verified activations.'); self.render()
        QTimer.singleShot(3000,self._poll_bridge)
    def _timer(self): self._refresh_status(); QTimer.singleShot(3000,self._timer)

def main() -> int:
    startup_log(f'Startup entered; cwd={Path.cwd()}; executable={sys.executable}')
    app=QApplication(sys.argv); startup_log('QApplication created')
    app.setStyleSheet('''QWidget{background:#071520;color:#dcebf1;font-family:"Segoe UI";}#header{background:#0b1b28;}#sidebar{background:#0b1d2a;}#rail{background:#0a1924;}#brand{color:#e5b15a;font-size:26px;font-weight:700;}#pageTitle{font-size:30px;font-weight:700;}#status,.subtle{color:#9bb3bf;font-size:11px;}#card,#quick{background:#0d2230;border:1px solid #214456;border-radius:4px;}#cardTitle{color:#4fe0ed;font-size:13px;font-weight:700;}#recordRow{background:#102a39;border-radius:3px;}#muted{color:#8fa9b5;}QPushButton{background:#173545;color:#dcebf1;border:1px solid #2d5365;border-radius:4px;padding:7px;}QPushButton:disabled{color:#71808a;background:#132936;border-color:#1d3b49;}QPushButton#nav{border:0;text-align:left;padding:9px;background:#102e40;}QPushButton#nav:hover{background:#31504d;}QLineEdit{background:#132d3c;border:1px solid #31566a;padding:8px;color:#dcebf1;}QScrollArea{background:#071520;}''')
    window=App(); startup_log('Main window constructed; calling show()'); window.show(); window.raise_(); window.activateWindow(); app.processEvents(); startup_log(f'Window state: visible={window.isVisible()} exposed={window.windowHandle().isExposed() if window.windowHandle() else False}'); startup_log('Entering app.exec()')
    result=app.exec(); startup_log(f'app.exec() returned {result}'); return result

if __name__=='__main__':
    try:
        sys.exit(main())
    except Exception:
        details=traceback.format_exc(); startup_log('STARTUP FAILURE\n'+details)
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(None,'Enshrouded Master Trainer startup failure',f'Startup failed. Details were written to:\n{STARTUP_LOG}\n\n{details}')
        except Exception:
            pass
        raise
