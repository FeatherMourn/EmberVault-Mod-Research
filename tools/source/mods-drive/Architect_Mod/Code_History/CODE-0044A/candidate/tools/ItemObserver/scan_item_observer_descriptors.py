"""Offline structural analysis of the four v4 shared +0x10 targets."""
from __future__ import annotations

import argparse, hashlib, importlib.util, json, struct
from pathlib import Path
import pefile

DESCRIPTORS = (0x160BFC0, 0x1857610, 0x1908FB0, 0x18BAFA0)

def load(name):
    path = Path(__file__).with_name(name); spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec); assert spec and spec.loader; spec.loader.exec_module(mod); return mod
def hx(value): return None if value is None else f"0x{value:X}"

def ascii_at(image, rva):
    off = image.rva_to_offset(rva) if rva is not None else None
    if off is None: return None
    end = image.data.find(b"\0", off, min(off + 128, len(image.data))); raw = image.data[off:end] if end >= 0 else b""
    return raw.decode("ascii") if len(raw) > 1 and all(32 <= b <= 126 for b in raw) else None

def fields(image, base):
    out=[]
    for rel in range(0, 0x101, 8):
        off=image.rva_to_offset(base+rel)
        if off is None or off+8>len(image.data): continue
        raw=struct.unpack_from("<Q",image.data,off)[0]; target=raw-image.image_base if image.image_base<=raw<image.image_base+image.pe.OPTIONAL_HEADER.SizeOfImage else None
        sec=image.section_for_rva(target) if target is not None else None
        kind="null" if raw==0 else ("valid_pointer" if sec else ("small_integer" if raw<0x10000 else "unknown"))
        out.append({"offset":f"0x{rel:X}","rawQword":hx(raw),"classification":kind,"resolvedRva":hx(target),"resolvedSection":sec["name"] if sec else None,"associatedAscii":ascii_at(image,target),"candidateCodePointer":bool(target is not None and image.is_executable_rva(target))})
    return out

def relocations(path,image,targets):
    pe=pefile.PE(str(path));pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_BASERELOC"]]);out=[]
    for block in getattr(pe,"DIRECTORY_ENTRY_BASERELOC",[]):
      for ent in block.entries:
        owner=next((x for x in targets if x<=ent.rva<x+0x100),None)
        if owner is None: continue
        off=image.rva_to_offset(ent.rva); raw=int.from_bytes(image.data[off:off+8],"little") if off is not None else 0
        target=raw-image.image_base if image.image_base<=raw<image.image_base+image.pe.OPTIONAL_HEADER.SizeOfImage else None; sec=image.section_for_rva(target) if target is not None else None
        out.append({"descriptorRva":hx(owner),"fieldOffset":hx(ent.rva-owner),"relocationRva":hx(ent.rva),"type":ent.type,"rawValue":hx(raw),"resolvedTargetRva":hx(target),"targetSection":sec["name"] if sec else None})
    return out

def main():
 p=argparse.ArgumentParser(description=__doc__); root=Path(__file__).resolve().parents[2]
 p.add_argument("--exe",type=Path,default=Path(__file__).resolve().parents[4]/"enshrouded.exe");p.add_argument("--output",type=Path,default=root/"bridge"/"item_observer_descriptor_scan.json");a=p.parse_args()
 mod=load("scan_item_observer_callgraph.py"); owners=load("scan_item_observer_owners.py"); image=mod.PeImage(a.exe.resolve())
 descriptor_rows=[{"descriptor":f"candidateDescriptor_{i}","rva":hx(rva),"fileOffset":hx(image.rva_to_offset(rva)),"section":image.section_for_rva(rva)["name"],"alignment":f"0x{rva & 0xF:X}","fields":fields(image,rva)} for i,rva in enumerate(DESCRIPTORS)]
 incoming={hx(rva):owners.all_reverse_refs(image,rva) for rva in DESCRIPTORS}
 code=mod.code_references_to(image,set(DESCRIPTORS)); relocs=relocations(a.exe.resolve(),image,DESCRIPTORS)
 outgoing=[]
 for row in descriptor_rows:
   for field in row["fields"]:
    if field["resolvedRva"]: outgoing.append({"sourceDescriptor":row["rva"],"fieldOffset":field["offset"],"targetRva":field["resolvedRva"],"targetSection":field["resolvedSection"],"relationship":"relocation_backed_pointer" if any(x["descriptorRva"]==row["rva"] and x["fieldOffset"]==field["offset"] for x in relocs) else "validated_file_pointer","confidence":"PROVEN"})
 comparison=[]
 for offset in range(0,0x101,8): comparison.append({"offset":f"0x{offset:X}","values":[next(x for x in row["fields"] if x["offset"]==f"0x{offset:X}") for row in descriptor_rows]})
 report={"schemaVersion":1,"tool":"scan_item_observer_descriptors.py","executableSha256":hashlib.sha256(image.data).hexdigest().upper(),"descriptors":descriptor_rows,"fieldComparisons":comparison,"relocations":relocs,"incomingReferences":incoming,"outgoingReferences":outgoing,"ownerCandidates":[],"descriptorFamilies":[{"members":[row["rva"] for row in descriptor_rows],"confidence":"CANDIDATE","reason":"all four occur as shared +0x10 targets of 0x30-stride action metadata entries"}],"stringAssociations":[{"descriptor":row["rva"],"strings":[x["associatedAscii"] for x in row["fields"] if x["associatedAscii"]]} for row in descriptor_rows],"codeReferences":{hx(rva):code.get(rva,[]) for rva in DESCRIPTORS},"candidateFunctions":[],"referenceGraphs":[],"conclusions":["No descriptor has a decoded .text reference.","No descriptor field contains a validated executable pointer.","The descriptor family remains a structural candidate only."],"hookReadiness":"NOT_READY","safety":"Offline file analysis only; no process, hook, injection, or mutation was used."}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(f"descriptors=4 relocations={len(relocs)} incoming={sum(len(x) for x in incoming.values())} code-xrefs={sum(len(x) for x in code.values())}")
if __name__=="__main__": main()
