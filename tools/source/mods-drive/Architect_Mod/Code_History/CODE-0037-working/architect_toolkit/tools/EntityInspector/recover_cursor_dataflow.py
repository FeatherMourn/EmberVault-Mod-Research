"""CODE-0028: descriptor-rooted cursor field data-flow recovery (offline only)."""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2];EXE=ROOT.parents[1]/"enshrouded.exe";OUT=ROOT/"bridge/cursor_target_dataflow.json"
EXPECTED="AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
SPECS=(
 {"name":"CursorSelectObjectAction","index":2670,"qualified":"keen::ecs::CursorSelectObjectAction","size":24,"field":"selectedObjectId","offset":8},
 {"name":"ClientCursor","index":2842,"qualified":"keen::ecs::ClientCursor","size":4328,"field":"previousSelectedEntityId","offset":0xC0},
)

def all_find(blob,needle):
 pos=0
 while True:
  pos=blob.find(needle,pos)
  if pos<0:return
  yield pos;pos+=1

def analyze(exe=EXE):
 raw=exe.read_bytes();sha=hashlib.sha256(raw).hexdigest().upper()
 if sha!=EXPECTED:raise RuntimeError(f"unsupported executable SHA-256 {sha}")
 pe=pefile.PE(str(exe),fast_load=False);base=pe.OPTIONAL_HEADER.ImageBase
 text=next(s for s in pe.sections if s.Name.rstrip(b"\0")==b".text");code=pe.get_data(text.VirtualAddress,text.Misc_VirtualSize)
 ranges=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
 def function_at(rva):
  for a,b in ranges:
   if a<=rva<b:return a,b
  return None
 def raw_to_rva(off):
  try:return pe.get_rva_from_offset(off)
  except:return None
 def string_rva(value):
  hits=[]
  for s in pe.sections:
   data=pe.get_data(s.VirtualAddress,s.SizeOfRawData)
   hits += [s.VirtualAddress+i for i in all_find(data,value.encode()+b"\0")]
  return hits
 targets=[]
 for spec in SPECS:
  q=string_rva(spec["qualified"]);f=string_rva(spec["field"])
  if len(q)!=1 or len(f)!=1:raise RuntimeError(f"non-unique metadata string for {spec['name']}: {q} {f}")
  qptr=[raw_to_rva(i) for i in all_find(raw,struct.pack("<Q",base+q[0]))];qptr=[x for x in qptr if x is not None]
  # Generated descriptors consistently own qualified-name relocation at +0x20.
  descriptors=[x-0x20 for x in qptr]
  descriptor=next((x for x in descriptors if struct.unpack("<I",pe.get_data(x+0x40,4))[0]==spec["size"]),None)
  if descriptor is None:raise RuntimeError(f"descriptor not recovered for {spec['name']}")
  fieldptr=[raw_to_rva(i) for i in all_find(raw,struct.pack("<Q",base+f[0]))];fieldptr=[x for x in fieldptr if x is not None]
  refs=[]
  for root in [descriptor,*fieldptr]:
   refs += [raw_to_rva(i) for i in all_find(raw,struct.pack("<Q",base+root))]
  refs=sorted({x for x in refs if x is not None})
  targets.append({**spec,"qualifiedNameRva":q[0],"fieldNameRva":f[0],"descriptorRva":descriptor,"fieldMetadataPointerSites":fieldptr,"metadataReferenceSites":refs})
 # Both exact descriptor references at 0x1817920/0x1817E80 resolve to the
 # same base when indexed by reflection index, proving the primary registry.
 bases=[]
 for t in targets:
  bases += [r-t["index"]*8 for r in t["metadataReferenceSites"]]
 shared=sorted({b for b in bases if bases.count(b)>=2})
 roots={x for t in targets for x in [t["descriptorRva"],*t["fieldMetadataPointerSites"],*t["metadataReferenceSites"]]}|set(shared)
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True;md.skipdata=True
 xrefs=[]
 for ins in md.disasm(code,base+text.VirtualAddress):
  if ins.id==0:continue
  hit=[]
  for op in getattr(ins,"operands",[]):
   if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:
    target=ins.address+ins.size+op.mem.disp-base
    if target in roots:hit.append(target)
   elif op.type==capstone.x86.X86_OP_IMM:
    target=op.imm-base
    if target in roots:hit.append(target)
  if hit:
   rva=ins.address-base;fn=function_at(rva)
   xrefs.append({"instructionRva":rva,"instruction":f"{ins.mnemonic} {ins.op_str}".strip(),"targets":sorted(set(hit)),"functionStartRva":fn[0] if fn else None,"functionEndRva":fn[1] if fn else None})
 functions=[]
 for bounds in sorted({(x["functionStartRva"],x["functionEndRva"]) for x in xrefs if x["functionStartRva"] is not None}):
  a,b=bounds;insns=[];field_access=[]
  for ins in md.disasm(pe.get_data(a,b-a),base+a):
   if ins.id==0:continue
   row={"rva":ins.address-base,"text":f"{ins.mnemonic} {ins.op_str}".strip()};insns.append(row)
   for op in getattr(ins,"operands",[]):
    if op.type==capstone.x86.X86_OP_MEM and op.mem.disp in (8,0xC0):field_access.append({**row,"displacement":op.mem.disp,"access":"write" if ins.operands and ins.operands[0].type==capstone.x86.X86_OP_MEM and ins.operands[0].mem.disp==op.mem.disp else "read_or_address"})
  functions.append({"startRva":a,"endRva":b,"signature":pe.get_data(a,min(16,b-a)).hex(" ").upper(),"metadataXrefs":[x for x in xrefs if x["functionStartRva"]==a],"candidateFieldAccesses":field_access,"disassembly":insns[:160],"classification":"metadata_registry_consumer","gameplayTargetEvidence":"NONE"})
 def hx(v):return f"0x{v:X}" if isinstance(v,int) else v
 encoded=[]
 for t in targets:
  row={k:([hx(x) for x in v] if isinstance(v,list) else hx(v)) for k,v in t.items()}
  row.pop("index")
  row["reflectionIndex"]=t["index"]
  encoded.append(row)
 ef=[]
 for f in functions:
  g=dict(f);g["startRva"]=hx(g["startRva"]);g["endRva"]=hx(g["endRva"])
  for x in g["metadataXrefs"]:
   for k in ("instructionRva","functionStartRva","functionEndRva"):x[k]=hx(x[k])
   x["targets"]=[hx(v) for v in x["targets"]]
  for x in g["candidateFieldAccesses"]:x["rva"]=hx(x["rva"]);x["displacement"]=hx(x["displacement"])
  for x in g["disassembly"]:x["rva"]=hx(x["rva"])
  ef.append(g)
 return {"schema":"architect.cursor_target_dataflow.v1","build":{"revision":1076226,"sha256":sha,"peTimestamp":hx(pe.FILE_HEADER.TimeDateStamp),"imageSize":hx(pe.OPTIONAL_HEADER.SizeOfImage),"supported":True},"scope":{"fields":["CursorSelectObjectAction.selectedObjectId +0x08","ClientCursor.previousSelectedEntityId +0xC0"],"method":"qualified/field string -> generated descriptor -> absolute metadata references -> shared indexed registry -> RIP-relative code xrefs -> bounded function displacement audit"},"targets":encoded,"primaryReflectionRegistry":{"baseRva":hx(shared[0]) if len(shared)==1 else None,"entryWidth":8,"derivation":"descriptorReferenceSite - reflectionIndex * 8","validatedByBothTargets":len(shared)==1},"descriptorRootedFunctions":ef,"result":{"selectedObjectIdProducer":None,"selectedObjectIdConsumer":None,"previousSelectedEntityIdWriter":None,"previousSelectedEntityIdReader":None,"liveClientCursorInstance":None,"hookCandidate":None,"conclusion":"NO_CURSOR_DATAFLOW_CONVERGENCE"},"safety":{"runtimeChanged":False,"hookInstalled":False,"customRaycast":False,"pointerScan":False,"mutation":False},"contradictions":["A displacement match without proven base-object provenance is not field identity.","Generated reflection descriptor and field metadata consumers are registry infrastructure, not evidence of gameplay target production.","No descriptor-rooted function establishes a live ClientCursor instance or target entity lifetime."]}

def main():
 r=analyze();OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(f"wrote {OUT} functions={len(r['descriptorRootedFunctions'])} conclusion={r['result']['conclusion']}")
if __name__=="__main__":main()
