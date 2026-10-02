"""Offline, fail-closed CODE-0027 targeting evidence compiler."""
from __future__ import annotations
import hashlib, json, struct
from pathlib import Path
import pefile

ROOT=Path(__file__).resolve().parents[2]
EXE=ROOT.parents[1]/"enshrouded.exe"
TYPES=ROOT.parents[1]/".cache"/"types.json"
OUT=ROOT/"bridge"/"entity_inspector_static_map.json"
EXPECTED_SHA="AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
EXPECTED_TIMESTAMP=0x6A4236C8
EXPECTED_IMAGE_SIZE=0x2DA7000
TARGETS=(
 (2670,"keen::ecs::CursorSelectObjectAction",24,{"selectedObjectId":8}),
 (2766,"keen::ecs::ClientCursorInput",160,{}),
 (2842,"keen::ecs::ClientCursor",4328,{"hoveredVoxelMaterialId":138,"previousSelectedEntityId":192}),
 (710,"keen::ecs::TargetEntity",4,{"targetId":0}),
 (711,"keen::ecs::TargetPosition",12,{"targetPosition":0}),
 (3418,"keen::ecs::DebugHitResult",44,{}),
 (3697,"keen::ecs::InteractionQuery",20,{}),
)

def _fields(record):
 return {name:int(value["dataOffset"]) for name,value in record.get("structFields",{}).items()}

def analyze(exe=EXE,types=TYPES):
 sha=hashlib.sha256(exe.read_bytes()).hexdigest().upper()
 pe=pefile.PE(str(exe),fast_load=True)
 build={"revision":1076226,"sha256":sha,"expectedSha256":EXPECTED_SHA,"peTimestamp":f"0x{pe.FILE_HEADER.TimeDateStamp:08X}","imageSize":f"0x{pe.OPTIONAL_HEADER.SizeOfImage:X}"}
 build["supported"]=(sha==EXPECTED_SHA and pe.FILE_HEADER.TimeDateStamp==EXPECTED_TIMESTAMP and pe.OPTIONAL_HEADER.SizeOfImage==EXPECTED_IMAGE_SIZE)
 raw=json.loads(types.read_text(encoding="utf-8")); records=raw["types"]; candidates=[]
 for index,name,size,required in TARGETS:
  record=records[index]; fields=_fields(record)
  valid=record.get("qualifiedName")==name and int(record.get("size",-1))==size and all(fields.get(k)==v for k,v in required.items())
  candidates.append({"reflectionIndex":index,"qualifiedName":name,"size":size,"fields":fields,"layoutValidated":valid,"liveInstanceProven":False,"producerRvas":[],"consumerRvas":[],"hookEligible":False,"contradiction":"Reflection metadata does not identify a live instance, producer, lifetime, or target publication boundary."})
 return {"schema":"architect.entity_inspector_static_map.v1","analysisMode":"offline_static_only","build":build,"priorityOrder":["interaction/highlight target","build/selection target","combat/use target","camera/physics raycast","custom validated raycast"],"selectedVanillaPath":{"family":"ClientCursor / CursorSelectObjectAction","status":"STATIC_LAYOUT_CANDIDATE_ONLY","rva":None,"signature":None,"evidence":"selectedObjectId and previousSelectedEntityId are reflected identity-shaped fields","limitation":"No live ECS component instance or producer/consumer function boundary is independently validated."},"candidates":candidates,"resultLayout":{"entityId":None,"resourceId":None,"runtimePointer":None,"type":None,"name":None,"position":None,"rotation":None,"authority":"UNKNOWN","components":[]},"hookSafety":{"canonicalBuildMatch":build["supported"],"exactSignature":False,"uniqueMatch":False,"understoodFunctionBoundary":False,"understoodArguments":False,"relocatableOverwrite":False,"cleanUninstallPath":False,"install":False},"findings":{"stableIdentity":"UNSOLVED","transform":"UNSOLVED","componentEnumeration":"UNSOLVED","authorityNetwork":"UNSOLVED","classification":"UNKNOWN","playerSynergy":"No validated relation to local/remote player ECS identity.","buildingSynergy":"Cursor reflection exposes building-oriented state but no validated target owner or live identity."},"captureBounds":{"records":64,"bytes":262144},"mutationCommands":[],"conclusion":"NO_SAFE_TARGET_PATH_CONVERGENCE"}

def main():
 result=analyze();OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8");print(f"wrote {OUT} conclusion={result['conclusion']}")
if __name__=="__main__":main()
