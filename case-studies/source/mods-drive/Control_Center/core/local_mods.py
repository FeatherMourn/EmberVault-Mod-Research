"""Local-only third-party mod library and transactional installer.

Archives are inspected as untrusted data. No executable content is run and
only ZIP and extracted-directory packages are supported by this adapter.
"""
from __future__ import annotations
import configparser, hashlib, json, os, re, shutil, tempfile, time, zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
from .platform_services import feature_state
from .package_service import PackageService

class LocalModError(RuntimeError): pass

@dataclass
class Package:
    identity: str; name: str; version: str; author: str; source: str
    kind: str; status: str; files: list[str]; manifest: dict[str, Any]
    reason: str = ""

def _sha256(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024), b""): h.update(chunk)
    return h.hexdigest()

class LocalModService:
    """Discovery, validation, local installation and safe config editing."""
    MAX_ARCHIVE=512*1024*1024; MAX_EXTRACTED=2*1024*1024*1024; MAX_FILES=10000; MAX_DEPTH=20
    def __init__(self, base_dir: Path, storage: Path|None=None):
        self.base_dir=Path(base_dir); self.storage=Path(storage or (Path(os.environ.get("LOCALAPPDATA", tempfile.gettempdir()))/"EnshroudedModHub"/"local-mods")); self.storage.mkdir(parents=True,exist_ok=True)
        self.state_path=self.storage/"library.json"; self.state=self._load()
    def _load(self):
        try: return json.loads(self.state_path.read_text(encoding="utf-8"))
        except (OSError,ValueError): return {"folders":[],"watch":False,"installed":{},"history":[]}
    def save(self): self.state_path.write_text(json.dumps(self.state,indent=2),encoding="utf-8")
    def set_folders(self, folders): self.state["folders"]=[str(Path(x).resolve()) for x in folders]; self.save()
    def add_folder(self, folder):
        p=str(Path(folder).resolve()); self.state.setdefault("folders",[])
        if p not in self.state["folders"]: self.state["folders"].append(p)
        self.save()
    def packages(self):
        result=[]
        for raw in self.state.get("folders",[]):
            folder=Path(raw)
            if not folder.is_dir(): continue
            for p in sorted(folder.iterdir()):
                if p.is_dir() or p.suffix.lower()==".zip": result.append(self.inspect(p))
        return result
    def inspect(self, source: Path) -> Package:
        source=Path(source); files=[]; manifest={}; kind="directory" if source.is_dir() else "zip"
        try:
            if source.is_dir():
                files=[str(p.relative_to(source)).replace("\\","/") for p in source.rglob("*") if p.is_file()]
                for name in ("mod.json","manifest.json","package.json"):
                    q=source/name
                    if q.is_file(): manifest=json.loads(q.read_text(encoding="utf-8")); break
            else:
                if source.stat().st_size>self.MAX_ARCHIVE: raise LocalModError("Archive exceeds size limit")
                with zipfile.ZipFile(source) as z:
                    seen=set(); total=0
                    for info in z.infolist():
                        n=info.filename.replace("\\","/"); parts=Path(n).parts
                        if n.startswith("/") or ".." in parts or (len(parts)>self.MAX_DEPTH): raise LocalModError(f"Unsafe archive path: {n}")
                        if n.lower() in seen: raise LocalModError(f"Duplicate/case-colliding path: {n}")
                        seen.add(n.lower()); total+=info.file_size
                        if total>self.MAX_EXTRACTED or len(seen)>self.MAX_FILES: raise LocalModError("Archive extraction limits exceeded")
                        if not info.is_dir(): files.append(n)
                        if Path(n).name in ("mod.json","manifest.json","package.json") and not manifest: manifest=json.loads(z.read(info).decode("utf-8"))
        except (OSError,zipfile.BadZipFile,json.JSONDecodeError,LocalModError) as exc:
            return Package(source.stem,source.stem,"unknown","unknown",str(source),kind,"invalid or unsafe",files,{},str(exc))
        identity=str(manifest.get("id") or manifest.get("mod_id") or source.stem).strip()
        name=str(manifest.get("name") or source.stem); version=str(manifest.get("version") or "unknown"); author=str(manifest.get("author") or "unknown")
        supported=bool(manifest.get("loader") in (None,"EML","ember","ember-mod-loader") and any(Path(x).name.lower() in ("mod.json","manifest.json","package.json") for x in files))
        status="recognized and supported" if supported else ("ambiguous package requiring review" if not manifest else "unsupported installation format")
        return Package(identity,name,version,author,str(source),kind,status,files,manifest)
    def preview(self, package: Package, game_dir: Path, allow_research: bool = False):
        if package.status!="recognized and supported": raise LocalModError(f"Package is not installable: {package.status}. {package.reason}")
        if feature_state(package.manifest) == "research-only" and not allow_research:
            raise LocalModError("Package is research-only; explicit research-mode approval is required.")
        requirements = self._dependency_requirements(package.manifest)
        missing = []
        for dependency_id, constraint in requirements:
            manifest_path = Path(game_dir) / "mods" / dependency_id / "mod.json"
            if not manifest_path.is_file():
                missing.append(f"{dependency_id} (missing)")
                continue
            try:
                dependency_manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
                dependency_version = str(dependency_manifest.get("version", ""))
            except (OSError, ValueError):
                missing.append(f"{dependency_id} (invalid manifest)")
                continue
            if constraint and not self._version_satisfies(dependency_version, constraint):
                missing.append(f"{dependency_id} (requires {constraint}, found {dependency_version})")
        if missing:
            raise LocalModError("Missing or incompatible dependencies: " + "; ".join(missing))
        target=Path(game_dir)/"mods"/package.identity
        return {"identity":package.identity,"name":package.name,"version":package.version,"source":package.source,"target":str(target),"files":package.files,"requirements":package.manifest.get("dependencies",[]),"conflicts":[str(target/f) for f in package.files if (target/f).exists()]}

    @staticmethod
    def _dependency_requirements(manifest: dict[str, Any]) -> list[tuple[str, str | None]]:
        raw = manifest.get("dependencies", [])
        if isinstance(raw, dict):
            raw = [raw]
        if not isinstance(raw, list):
            raise LocalModError("Package dependencies must be a list.")
        result: list[tuple[str, str | None]] = []
        for dependency in raw:
            if isinstance(dependency, str):
                dependency_id, constraint = dependency, None
            elif isinstance(dependency, dict):
                dependency_id = str(dependency.get("id", "")).strip()
                constraint = str(dependency.get("version", "")).strip() or None
            else:
                raise LocalModError("Each package dependency must be a string or object.")
            if not dependency_id:
                raise LocalModError("Package dependency is missing an id.")
            if constraint and not re.fullmatch(r"(?:>=|<=|>|<|=)?\s*\d+\.\d+\.\d+", constraint):
                raise LocalModError(f"Unsupported dependency version constraint: {constraint}")
            result.append((dependency_id, constraint))
        return result

    @staticmethod
    def _version_satisfies(version: str, constraint: str) -> bool:
        match = re.fullmatch(r"(>=|<=|>|<|=)?\s*(\d+)\.(\d+)\.(\d+)", constraint)
        candidate = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", version)
        if not match or not candidate:
            return False
        left = tuple(int(value) for value in candidate.groups())
        right = tuple(int(value) for value in match.groups()[1:])
        operator = match.group(1) or "="
        return {">=": left >= right, "<=": left <= right, ">": left > right, "<": left < right, "=": left == right}[operator]
    @staticmethod
    def _running():
        # The production guard always checks the real process.  Tests that use
        # a temporary fake game directory may opt out explicitly so the suite
        # can run while a developer is playing; this flag is never set by the
        # shipped application or installer.
        import os
        if os.environ.get("CONTROL_CENTER_TEST_ALLOW_RUNNING_GAME") == "1":
            return False
        try:
            import subprocess
            output = subprocess.check_output(["tasklist","/FI","IMAGENAME eq Enshrouded.exe"],text=True,stderr=subprocess.DEVNULL)
            return "enshrouded.exe" in output.lower()
        except Exception:
            return True  # fail closed if process state cannot be established
    def install(self, package: Package, game_dir: Path, replace=False, allow_research: bool = False):
        if self._running(): raise LocalModError("Installation is blocked while Enshrouded is running or its state cannot be established.")
        plan=self.preview(package,game_dir,allow_research=allow_research); source=Path(package.source); target=Path(plan["target"]); stage=Path(tempfile.mkdtemp(prefix="mod-",dir=self.storage)); backup=self.storage/"backups"/package.identity/(time.strftime("%Y%m%d-%H%M%S")+f"-{time.time_ns()}"); backup.mkdir(parents=True,exist_ok=True); created=[]
        try:
            if package.kind=="zip":
                with zipfile.ZipFile(source) as z: z.extractall(stage)
                roots=[p for p in stage.iterdir() if p.is_dir()]; root=roots[0] if len(roots)==1 and not (stage/"mod.json").exists() else stage
            else: root=source
            if (root / PackageService.MANIFEST).is_file():
                package_ok, package_errors = PackageService().verify(root)
                if not package_ok:
                    raise LocalModError("Package integrity verification failed: " + "; ".join(package_errors))
            target.mkdir(parents=True,exist_ok=True); hashes={}
            for rel in package.files:
                relp=Path(rel); src=root/relp
                if not src.is_file(): continue
                dst=target/relp
                if dst.exists() and not replace: raise LocalModError(f"Existing file requires explicit replacement approval: {dst}")
                if dst.exists(): (backup/relp).parent.mkdir(parents=True,exist_ok=True); shutil.copy2(dst,backup/relp)
                else: created.append(dst)
                dst.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(src,dst); hashes[str(relp).replace("\\","/")]=_sha256(dst)
            record={"package":asdict(package),"target":str(target),"files":hashes,"backup":str(backup),"enabled":True}; (target/".emh-third-party-owner.json").write_text(json.dumps(record,indent=2),encoding="utf-8"); self.state.setdefault("installed",{})[package.identity]=record; self.state.setdefault("history",[]).append(record); self.save(); return plan
        except Exception:
            for p in created:
                try:p.unlink()
                except OSError:pass
            self._restore(target,backup); raise
        finally: shutil.rmtree(stage,ignore_errors=True)
    def _restore(self,target,backup):
        if backup.is_dir():
            for p in backup.rglob("*"):
                if p.is_file(): q=target/p.relative_to(backup); q.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(p,q)
    def list_backups(self, identity: str) -> list[dict[str, Any]]:
        """List timestamped restore points without exposing files outside storage."""
        root = (self.storage / "backups" / str(identity)).resolve()
        try:
            root.relative_to(self.storage.resolve())
        except ValueError:
            raise LocalModError("Invalid backup identity.")
        if not root.is_dir():
            return []
        result = []
        legacy_files = [item for item in root.iterdir() if item.is_file()]
        if legacy_files:
            result.append({"id": "legacy", "path": str(root), "files": len(legacy_files), "legacy": True})
        import re
        for path in sorted((item for item in root.iterdir() if item.is_dir() and re.fullmatch(r"\d{8}-\d{6}-\d+", item.name)), reverse=True):
            result.append({"id": path.name, "path": str(path), "files": sum(1 for item in path.rglob("*") if item.is_file())})
        return result
    def remove_installed(self, identity: str) -> dict[str, Any]:
        """Remove only an owned deployment, preserving user-modified files."""
        if self._running():
            raise LocalModError("Removal is blocked while Enshrouded is running or its state cannot be established.")
        record = self.state.get("installed", {}).get(identity)
        if not isinstance(record, dict):
            raise LocalModError("No Control Center ownership record exists")
        target = Path(record.get("target", "")).resolve()
        removed, preserved = [], []
        for relative, digest in record.get("files", {}).items():
            current = (target / relative).resolve()
            try:
                current.relative_to(target)
            except ValueError as exc:
                raise LocalModError("Ownership record contains an unsafe path.") from exc
            if current.is_file() and _sha256(current) == digest:
                current.unlink(); removed.append(relative)
            elif current.exists():
                preserved.append(relative)
        owner = target / ".emh-third-party-owner.json"
        try: owner.unlink()
        except OSError: pass
        if target.is_dir():
            for directory in sorted((p for p in target.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                try: directory.rmdir()
                except OSError: pass
            try: target.rmdir()
            except OSError: pass
        self.state.setdefault("installed", {}).pop(identity, None)
        self.save()
        return {"identity": identity, "removed": removed, "preserved": preserved}

    def set_enabled(self, identity: str, enabled: bool) -> dict[str, Any]:
        """Enable or disable an owned mod by moving its whole deployment safely."""
        if self._running():
            raise LocalModError("Enable/disable is blocked while Enshrouded is running or its state cannot be established.")
        record = self.state.get("installed", {}).get(identity)
        if not isinstance(record, dict):
            raise LocalModError("No Control Center ownership record exists")
        target = Path(record.get("target", "")).resolve()
        currently_enabled = bool(record.get("enabled", True))
        if currently_enabled == bool(enabled):
            return {"identity": identity, "enabled": currently_enabled, "target": str(target)}
        disabled_target = target.with_name(target.name + ".disabled")
        if enabled:
            if target.name.endswith(".disabled"):
                disabled_target = target
                target = target.with_name(target.name[:-len(".disabled")])
            if target.exists() or not disabled_target.is_dir():
                raise LocalModError("The disabled deployment cannot be restored safely.")
            disabled_target.rename(target)
        else:
            if not target.is_dir() or disabled_target.exists():
                raise LocalModError("The installed deployment cannot be disabled safely.")
            target.rename(disabled_target)
            target = disabled_target
        record["target"] = str(target); record["enabled"] = bool(enabled)
        self.save()
        return {"identity": identity, "enabled": bool(enabled), "target": str(target)}

    def restore_backup(self, identity: str, backup_id: str, game_dir: Path) -> dict[str, Any]:
        """Restore one owned deployment from a cataloged restore point.

        Only files currently owned by the Control Center may be removed, and
        the game must be stopped. The selected backup must remain beneath the
        service backup root; arbitrary paths and symlinks are rejected.
        """
        if self._running():
            raise LocalModError("Restore is blocked while Enshrouded is running or its state cannot be established.")
        record = self.state.get("installed", {}).get(identity)
        if not isinstance(record, dict):
            raise LocalModError("No Control Center ownership record exists")
        target = Path(record.get("target", "")).resolve()
        if not target.is_dir():
            raise LocalModError("Owned deployment directory is missing.")
        backup_root = (self.storage / "backups" / str(identity)).resolve()
        try:
            backup_root.relative_to(self.storage.resolve())
        except ValueError as exc:
            raise LocalModError("Invalid backup identity.") from exc
        if backup_id == "legacy":
            backup = backup_root
        elif re.fullmatch(r"\d{8}-\d{6}-\d+", str(backup_id)):
            backup = (backup_root / str(backup_id)).resolve()
        else:
            raise LocalModError("Invalid restore-point identifier.")
        try:
            backup.relative_to(backup_root)
        except ValueError as exc:
            raise LocalModError("Backup path escapes the backup root.") from exc
        if not backup.is_dir():
            raise LocalModError("Restore point is missing.")
        files = []
        for source in backup.rglob("*"):
            if source.is_symlink() or (source.exists() and not source.is_file()):
                raise LocalModError("Restore point contains an unsafe entry.")
            if source.is_file():
                relative = source.relative_to(backup)
                destination = (target / relative).resolve()
                try:
                    destination.relative_to(target)
                except ValueError as exc:
                    raise LocalModError("Restore point contains an unsafe path.") from exc
                files.append((source, destination, relative))
        owned = record.get("files", {})
        for relative, digest in owned.items():
            current = (target / relative).resolve()
            try:
                current.relative_to(target)
            except ValueError as exc:
                raise LocalModError("Ownership record contains an unsafe path.") from exc
            if current.is_file() and _sha256(current) == digest and not any(relative == str(item[2]).replace("\\", "/") for item in files):
                current.unlink()
        for source, destination, _ in files:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
        restored = {str(relative).replace("\\", "/"): _sha256(destination) for _, destination, relative in files}
        record["files"] = restored
        record["backup_restored"] = str(backup)
        owner = target / ".emh-third-party-owner.json"
        if files:
            owner.write_text(json.dumps(record, indent=2), encoding="utf-8")
        else:
            # An empty restore point means the owned deployment did not exist
            # at that point. Remove the ownership marker and any directories
            # made empty by the rollback so the loader cannot classify a
            # leftover folder as an unclassified module.
            try:
                owner.unlink()
            except OSError:
                pass
            if target.is_dir():
                for directory in sorted((p for p in target.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                    try:
                        directory.rmdir()
                    except OSError:
                        pass
                try:
                    target.rmdir()
                except OSError:
                    pass
        self.state.setdefault("history", []).append(dict(record))
        self.save()
        return {"identity": identity, "backup_id": backup_id, "target": str(target), "files": len(files)}
    def uninstall(self, identity, game_dir):
        rec=self.state.get("installed",{}).get(identity); 
        if not rec: raise LocalModError("No Control Center ownership record exists")
        target=Path(rec["target"]); owner=target/".emh-third-party-owner.json"
        for rel,digest in rec.get("files",{}).items():
            p=target/rel
            if p.is_file() and _sha256(p)==digest: p.unlink()
        try: owner.unlink()
        except OSError: pass
        # Remove only directories made empty by this uninstall.  Never remove
        # a directory that still contains user or another mod's files.
        if target.is_dir():
            for directory in sorted((p for p in target.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
                try: directory.rmdir()
                except OSError: pass
            try: target.rmdir()
            except OSError: pass
        self.state["installed"].pop(identity,None); self.save()
    def configure_json(self, path: Path, updates: dict[str,Any], backup_dir: Path|None=None):
        path=Path(path); data=json.loads(path.read_text(encoding="utf-8")); old=json.loads(json.dumps(data)); data.update(updates); backup_dir=backup_dir or self.storage/"config-backups"; backup_dir.mkdir(parents=True,exist_ok=True); shutil.copy2(path,backup_dir/(path.name+".bak")); tmp=path.with_suffix(path.suffix+".tmp"); tmp.write_text(json.dumps(data,indent=2)+"\n",encoding="utf-8"); os.replace(tmp,path); return old,data
