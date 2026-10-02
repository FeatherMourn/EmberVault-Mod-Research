"""Beginner-friendly, explicit-consent diagnostics workflow."""
from __future__ import annotations
import hashlib, json, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
from .catalog import CatalogError, diagnostics

RAKE = "f9abaf9b-060c-470d-a8c3-c7c567ebaa1e"
PROBE = Path(__file__).resolve().parent.parent / "probe_mod" / "CC2_Research_Probe"
PROBE_ID = "cc2_research_probe"
MARKER_PREFIX = "cc2_probe_execution_"

def _hash(p, normalize_text=False):
    if normalize_text:
        return hashlib.sha256(p.read_text(encoding='utf-8').replace('\r\n','\n').replace('\r','\n').encode('utf-8')).hexdigest()
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

def _api_signatures(base: Path) -> dict:
    if not base.is_file(): return {"available":False,"functions":{}}
    text=base.read_text(encoding='utf-8',errors='replace')
    expected={"get_resource":"function AssetManager.get_resource(guid, type, part) end","get_resources_by_type":"function AssetManager.get_resources_by_type(type) end","get_resource_types":"function AssetManager.get_resource_types() end","io.export":"function io.export(path, bytes) end"}
    return {"available":True,"functions":{k:{"declared":v in text,"expected":v} for k,v in expected.items()},"all_verified":all(v in text for v in expected.values())}

def detect(game: Path|None, db: Path) -> dict:
    game = game.resolve() if game else None
    def file_status(p): return {"path":str(p),"available":p.is_file(),"sha256":_hash(p) if p.is_file() else None}
    root = game if game and game.is_dir() else None
    if root is None:
        candidates=[Path(r) for r in ("H:/SteamLibrary/steamapps/common/Enshrouded", "C:/Program Files (x86)/Steam/steamapps/common/Enshrouded")]
        root=next((p for p in candidates if p.is_dir()),None)
    cache=root/'.cache'/'lua' if root else Path('')
    cfg=root/'shroudtopia.json' if root else Path('')
    export_dir=(root/'export') if root else Path('')
    config={}
    if cfg.is_file():
        try: config=json.loads(cfg.read_text(encoding='utf-8'))
        except Exception: config={"_error":"invalid JSON"}
    return {"game_root":str(root) if root else None,
      "installation":{"available":bool(root),"plain_english":"Enshrouded installation found" if root else "Not found; choose the game folder manually."},
      "eml_config":{**(file_status(cfg) if root else {"available":False,"path":None}),"enableLogging":config.get('enableLogging'),"export_directory":config.get('export_directory'),"export_directory_is_configured":isinstance(config.get('export_directory'),str) and bool(config.get('export_directory'))},
      "base_lua":file_status(cache/'base.lua') if root else {"available":False,"path":None},
      "types_lua":file_status(cache/'types.lua') if root else {"available":False,"path":None},
      "api_signatures":_api_signatures(cache/'base.lua') if root else {"available":False,"functions":{}},
      "probe":{"available":(PROBE/'mod.json').is_file() and (PROBE/'src'/'mod.lua').is_file(),"path":str(PROBE)},
      "catalog":{"available":db.is_file(),"path":str(db)},
      "logs":{"game_log":str(root/'enshrouded.log') if root and (root/'enshrouded.log').is_file() else None,"export_directory":str(export_dir) if root else None}}

def _probe_files(root):
    return [p.relative_to(root) for p in root.rglob('*') if p.is_file() and p.name != '__pycache__']

def probe_status(target: Path) -> dict:
    """Classify without writing: absent, identical, outdated, partial, or unrelated."""
    manifest=target/'mod.json'
    if not target.exists(): return {"status":"absent","path":str(target)}
    try: installed=json.loads(manifest.read_text(encoding='utf-8'))
    except Exception: return {"status":"unrelated","reason":"existing folder has no valid mod.json", "path":str(target)}
    if installed.get('id') != PROBE_ID:
        return {"status":"unrelated","reason":"manifest id is not cc2_research_probe", "installed_id":installed.get('id'),"path":str(target)}
    expected=_probe_files(PROBE); missing=[]; changed=[]
    for rel in expected:
        a=target/rel; b=PROBE/rel
        if not a.is_file(): missing.append(str(rel))
        elif _hash(a, True)!=_hash(b, True): changed.append(str(rel))
    return {"status":"partial" if missing else ("outdated" if changed else "identical"),"path":str(target),"missing":missing,"changed":changed,"verified_files":{str(rel):_hash(target/rel,True) for rel in expected if (target/rel).is_file()}}

def install_probe(game: Path, workspace: Path, *, replace: bool=False) -> dict:
    target=game/'mods'/PROBE_ID
    state=probe_status(target)
    if state['status']=='identical': return {**state,"installed":False,"message":"Probe already installed","continue":True}
    if state['status']=='unrelated': raise CatalogError("refusing to overwrite unrelated mod at %s (%s)" % (target,state['reason']))
    if state['status'] in ('outdated','partial') and not replace:
        raise CatalogError("existing CC2 probe is %s; explicit replacement approval is required" % state['status'])
    backup=None
    if target.exists():
        backup=workspace/'backups'/('probe_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        backup.parent.mkdir(parents=True,exist_ok=True); shutil.copytree(target,backup)
        shutil.rmtree(target)
    target.parent.mkdir(parents=True,exist_ok=True); shutil.copytree(PROBE,target)
    return {"status":"installed" if not backup else "replaced","installed":True,"path":str(target),"backup":str(backup) if backup else None,"continue":True}

def runtime_state(game: Path, db: Path) -> dict:
    """Classify runtime evidence; existence alone is never execution proof."""
    d=detect(game,db); target=game/'mods'/PROBE_ID; ps=probe_status(target)
    export=Path(d['logs'].get('export_directory') or '')
    markers=sorted(export.glob(MARKER_PREFIX+'*.json'), key=lambda p:p.stat().st_mtime, reverse=True) if export.is_dir() else []
    log=Path(d['logs']['game_log']) if d['logs'].get('game_log') else None
    text=log.read_text(encoding='utf-8',errors='replace') if log and log.is_file() else ''
    executed='[CC2 OBSERVE]' in text
    invalid_markers=[]
    for p in markers:
        try: json.loads(p.read_text(encoding='utf-8'))
        except Exception: invalid_markers.append(str(p))
    if ps['status']=='absent': state='probe_not_installed'
    elif ps['status'] in ('unrelated','partial'): state='probe_not_installed'
    elif ps['status']=='outdated': state='probe_outdated'
    elif invalid_markers: state='export_created_collection_failed'
    elif markers: state='complete_success'
    elif executed: state='executed_export_failed'
    else: state='installed_execution_unconfirmed'
    return {"state":state,"plain_english":{"probe_not_installed":"The CC2 probe is not installed correctly.","probe_outdated":"The installed CC2 probe is outdated and needs repair.","installed_execution_unconfirmed":"The probe matches, but no CC2 execution marker was found.","executed_export_failed":"The probe ran, but no CC2 export was created.","export_created_collection_failed":"A CC2 export exists, but CC2 could not read it as a valid report.","complete_success":"CC2 probe execution and export were confirmed."}[state],"probe":ps,"markers":[str(p) for p in markers],"invalid_markers":invalid_markers,"console_or_log_execution_seen":executed,"export_directory":str(export) if export else None,"eml_export_configured":d['eml_config'].get('export_directory_is_configured',False),"game_log":str(log) if log else None}

def approve_eml_config(game: Path, workspace: Path) -> dict:
    cfg=game/'shroudtopia.json'
    if not cfg.is_file(): raise CatalogError("EML configuration not found")
    data=json.loads(cfg.read_text(encoding='utf-8'))
    backup=workspace/'backups'/('shroudtopia_'+datetime.now().strftime('%Y%m%d_%H%M%S')+'.json')
    backup.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(cfg,backup)
    data['enableLogging']=True; data['export_directory']=data.get('export_directory','export'); data['active']=True
    cfg.write_text(json.dumps(data,indent=2)+"\n",encoding='utf-8')
    return {"backup":str(backup),"config":str(cfg),"export_directory":data['export_directory']}

def collect(db: Path, game: Path, workspace: Path) -> dict:
    root=detect(game,db); runtime=runtime_state(game,db); export=Path(root['logs']['export_directory'])
    files=[]
    if export.is_dir(): files=sorted(export.glob('*'),key=lambda p:p.stat().st_mtime,reverse=True)[:20]
    log=Path(root['logs']['game_log']) if root['logs']['game_log'] else None
    report={"timestamp_utc":datetime.now(timezone.utc).isoformat(),"detected":root,"runtime":runtime,"static_catalog":diagnostics(db) if db.is_file() else None,"probe_runtime":runtime['state'],"checks":{"probe_execution":runtime['state'],"rake_lookup":"UNSOLVED","resource_counts":"UNSOLVED","api_presence":"UNSOLVED","build_identification":"UNSOLVED","missing_evidence":[] if runtime['state']=='complete_success' else ["launch Enshrouded with probe","enter disposable world","return logs/export"]}}
    out=workspace/'diagnostics'; out.mkdir(parents=True,exist_ok=True); stamp=datetime.now().strftime('%Y%m%d_%H%M%S'); j=out/f'cc2_diagnostics_{stamp}.json'; md=out/f'cc2_diagnostics_{stamp}.md'; z=out/f'cc2_diagnostics_{stamp}.zip'
    j.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    md.write_text('# Control Center 2 Diagnostics\n\nRuntime probe evidence is not collected until Enshrouded is launched.\n\n'+json.dumps(report['checks'],indent=2),encoding='utf-8')
    with zipfile.ZipFile(z,'w',zipfile.ZIP_DEFLATED) as a:
        a.write(j,j.name); a.write(md,md.name)
        for p in ([log] if log else [])+files:
            if p and p.is_file() and p.stat().st_size < 25*1024*1024: a.write(p,'evidence/'+p.name)
    return {"report":str(j),"summary":str(md),"zip":str(z),"export_candidates":[str(x) for x in files],"game_log":str(log) if log else None}
