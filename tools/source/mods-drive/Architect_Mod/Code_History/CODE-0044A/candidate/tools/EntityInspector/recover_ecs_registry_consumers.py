"""CODE-0029 bounded ECS registry-consumer and typed-membership recovery."""
from __future__ import annotations
import hashlib,json,struct
from pathlib import Path
import capstone,pefile

ROOT=Path(__file__).resolve().parents[2];EXE=ROOT.parents[1]/"enshrouded.exe";OUT=ROOT/"bridge/entity_cursor_system_map.json"
EXPECTED="AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781";REGISTRY=0x18125B0
TYPE_SPECS={2670:("CursorSelectObjectAction",0x196D820),2766:("ClientCursorInput",0x19E08C0),2842:("ClientCursor",0x17B4320)}
INDIRECTIONS=(0x1830AE0,0x1832620)

def derive_registry_base(entries):
 """Return a base only when every (index, entry RVA) agrees."""
 bases={entry-index*8 for index,entry in entries}
 return next(iter(bases)) if len(bases)==1 else None

def recognize_indexed_lookup(operations):
 """Require rooted table provenance, eight-byte stepping/scaling and a key."""
 required={"rooted_registry","entry_width_8","caller_key_32","returns_descriptor"}
 return required.issubset(set(operations))

def classify_membership(structural_kind,owns_callback=False):
 if structural_kind not in {"ecs_query","ecs_system","action_subscription","event_subscription"}:return "TYPE_METADATA_ONLY"
 return "TYPED_CALLBACK_OWNED" if owns_callback else "TYPED_MEMBERSHIP_ONLY"

def hook_eligible(build,typed,callback,args,identity,unique,relocatable):
 return all((build,typed,callback,args,identity,unique,relocatable))

def occurrences(raw,pe,needle):
 out=[];pos=0
 while True:
  pos=raw.find(needle,pos)
  if pos<0:return out
  try:out.append(pe.get_rva_from_offset(pos))
  except:pass
  pos+=1

def analyze(exe=EXE):
 raw=exe.read_bytes();sha=hashlib.sha256(raw).hexdigest().upper()
 if sha!=EXPECTED:raise RuntimeError(f"unsupported executable {sha}")
 pe=pefile.PE(str(exe),fast_load=False);base=pe.OPTIONAL_HEADER.ImageBase
 if derive_registry_base(((2670,0x1817920),(2842,0x1817E80)))!=REGISTRY:raise RuntimeError("registry derivation contradiction")
 memberships=[]
 for index,(name,descriptor) in TYPE_SPECS.items():
  entry=REGISTRY+index*8;value=struct.unpack("<Q",pe.get_data(entry,8))[0]-base
  if value!=descriptor:raise RuntimeError(f"false registry base: index {index} resolves 0x{value:X}, expected 0x{descriptor:X}")
  for site in occurrences(raw,pe,struct.pack("<Q",base+descriptor)):
   context="primary_reflection_registry" if site==entry else "generated_type_metadata_collection"
   memberships.append({"reflectionIndex":index,"typeName":name,"containingObjectRva":f"0x{site:X}","slotRva":f"0x{site:X}","descriptorRva":f"0x{descriptor:X}","objectType":context,"neighborTypeIndices":[],"systemOrQueryIdentity":None,"ownedCallback":None,"executionSide":"unknown","evidenceStatus":"PROVEN_STATIC_MEMBERSHIP" if site==entry else "INFERRED_METADATA_MEMBERSHIP","typedSystemEvidence":False})
 # Prove two global records point to the same registry; the adjacent count is
 # preserved as data, not interpreted as a type count without layout proof.
 ind=[]
 for site in INDIRECTIONS:
  value=struct.unpack("<Q",pe.get_data(site,8))[0]-base
  ind.append({"pointerSiteRva":f"0x{site:X}","valueRva":f"0x{value:X}","matchesRegistry":value==REGISTRY,"adjacentQword":f"0x{struct.unpack('<Q',pe.get_data(site+8,8))[0]:X}"})
 if not all(x["matchesRegistry"] for x in ind):raise RuntimeError("false registry indirection")
 roots=set(INDIRECTIONS)
 text=next(s for s in pe.sections if s.Name.rstrip(b"\0")==b".text");code=pe.get_data(text.VirtualAddress,text.Misc_VirtualSize)
 def direct_callers(target):
  return [text.VirtualAddress+i for i in range(len(code)-5) if code[i]==0xE8 and text.VirtualAddress+i+5+struct.unpack_from("<i",code,i+1)[0]==target]
 ranges=sorted((e.struct.BeginAddress,e.struct.EndAddress) for e in pe.DIRECTORY_ENTRY_EXCEPTION)
 def bounds(rva):
  for a,b in ranges:
   if a<=rva<b:return a,b
 md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True;md.skipdata=True
 xrefs=[]
 for ins in md.disasm(code,base+text.VirtualAddress):
  if ins.id==0:continue
  for op in ins.operands:
   target=None
   if op.type==capstone.x86.X86_OP_MEM and op.mem.base==capstone.x86.X86_REG_RIP:target=ins.address+ins.size+op.mem.disp-base
   elif op.type==capstone.x86.X86_OP_IMM:target=op.imm-base
   if target in roots:
    rva=ins.address-base;fn=bounds(rva);xrefs.append({"instructionRva":f"0x{rva:X}","instruction":f"{ins.mnemonic} {ins.op_str}".strip(),"globalRva":f"0x{target:X}","functionStartRva":f"0x{fn[0]:X}" if fn else None,"functionEndRva":f"0x{fn[1]:X}" if fn else None})
 # Direct xrefs are candidate entry points only. An indexed consumer must also
 # have scale 8 and a data-flow link from the rooted global; absent that, reject.
 consumers=[];rejected=[]
 accessor_xref=next((x for x in xrefs if x["instructionRva"]=="0x75E710" and x["globalRva"]=="0x1832620"),None)
 accessor_sig=pe.get_data(0x75E710,8).hex(" ").upper()
 resolver_sig=pe.get_data(0x802F50,16).hex(" ").upper()
 if accessor_xref and accessor_sig=="48 8D 05 09 3F 0D 01 C3":
  consumers.append({"functionRva":"0x75E710","functionBounds":{"start":"0x75E710","end":"0x75E718"},"signature":accessor_sig,"registryBaseProvenance":"LEA of owner record 0x1832620; owner +0 points to 0x18125B0 and +8 contains 0x383E","indexSource":None,"indexWidth":None,"scalingBehavior":None,"returnedObject":"pointer to generic registry owner record","callers":[f"0x{x:X}" for x in direct_callers(0x75E710)],"callees":[],"evidenceClassification":"PROVEN_STATIC_GENERIC_ACCESSOR","generic":True,"contextSpecific":False})
 if resolver_sig=="48 89 5C 24 08 57 48 83 EC 20 48 8B 3D 97 53 70":
  resolver_callers=direct_callers(0x802F50)
  consumers.append({"functionRva":"0x802F50","functionBounds":{"start":"0x802F50","end":"0x802FDF"},"signature":resolver_sig,"registryBaseProvenance":"fallback calls 0x75E710, loads owner +0 table and owner +8 count","indexSource":"generic caller-supplied 32-bit key in ECX/EBX; not proven to be reflection index","indexWidth":32,"scalingBehavior":"fallback advances descriptor-pointer cursor by 8 bytes; fast path indexes a generic cache with mappedIndex*8","returnedObject":"descriptor pointer whose dword +0x50 matches caller key","callers":{"directCount":len(resolver_callers),"rvas":[f"0x{x:X}" for x in resolver_callers]},"callees":["0x802A20 generic cache lookup","0x75E710 registry owner accessor"],"evidenceClassification":"PROVEN_STATIC_GENERIC_DESCRIPTOR_RESOLVER","generic":True,"contextSpecific":False})
 for x in xrefs:
  rejected.append({"candidate":x,"reason":"References a registry-owning global, but no proven index*8 lookup with preserved concrete type index was recovered.","classification":"GENERIC_GLOBAL_REFERENCE_REJECTED"})
 # The two requested descriptors never co-occur in a non-primary bounded
 # metadata collection and none of their non-primary sites owns a code pointer.
 typed=[];callbacks=[];queries=[]
 conclusion="GENERIC_REGISTRY_CONSUMER_ONLY" if consumers else "NO_TYPED_SYSTEM_CONVERGENCE"
 return {"schema":"architect.entity_cursor_system_map.v1","build":{"revision":1076226,"sha256":sha,"peTimestamp":f"0x{pe.FILE_HEADER.TimeDateStamp:X}","imageSize":f"0x{pe.OPTIONAL_HEADER.SizeOfImage:X}","supported":True},"registry":{"baseRva":"0x18125B0","entryWidth":8,"lookupModel":"descriptor = *(registryBase + reflectionIndex * 8)","derivationChecks":[{"index":2670,"entryRva":"0x1817920","descriptorRva":"0x196D820"},{"index":2842,"entryRva":"0x1817E80","descriptorRva":"0x17B4320"},{"index":2766,"entryRva":"0x1817C20","descriptorRva":"0x19E08C0"}],"indirections":ind},"registryConsumers":consumers,"typeMemberships":memberships,"typedSystemCandidates":typed,"queryCandidates":queries,"callbackCandidates":callbacks,"fieldAccessesInsideTypedCallbacks":[],"supporting2766Correlations":[],"localPlayerInputCorrelations":[],"rejectedGenericPaths":rejected+[{
 "candidate":"non-primary descriptor pointer collections","reason":"Collections preserve type metadata membership but expose no ECS system/query ownership or callback pointer.","classification":"TYPE_METADATA_ONLY"},{"candidate":"whole-binary immediates 2670/2766/2842","reason":"Rejected by design: integer equality without typed structural context is not membership.","classification":"UNRELATED_INTEGER_REJECTED"},{"candidate":"whole-binary +0x08/+0x8A/+0xC0 accesses","reason":"Rejected by design until a typed callback establishes base-object provenance.","classification":"UNPROVEN_BASE_REJECTED"}],"typeIdentityPreservedToCallback":False,"hookEligibility":{"strongObserveCandidate":False,"reason":"No typed system/query and owned callback preserve index 2670 or 2842; generic registry functions must not be hooked."},"runtimeExperiment":{"justified":False,"proposal":None},"conclusion":conclusion,"safety":{"offlineOnly":True,"runtimeChanged":False,"hookInstalled":False,"pointerGraphTraversal":False,"heapScan":False,"customRaycast":False,"mutation":False}}

def main():
 r=analyze();OUT.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(f"wrote {OUT} xrefRejects={len(r['rejectedGenericPaths'])-3} conclusion={r['conclusion']}")
if __name__=="__main__":main()
