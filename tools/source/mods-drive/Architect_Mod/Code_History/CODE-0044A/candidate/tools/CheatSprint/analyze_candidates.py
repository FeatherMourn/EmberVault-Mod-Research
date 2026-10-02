"""CODE-0032 offline remap audit for the first reversible F7 cheat sprint."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path

BUILD=1076226
SHA256="AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
PE_TIMESTAMP=0x6A4236C8
IMAGE_SIZE=0x02DA7000
CANDIDATES=(
 ("camera.fov.live","Camera FOV",None,None,"RESOURCE","No external mechanism and no live owner/consumer/readback chain."),
 ("movement.speed.live","Movement speed acquisition","0F 10 00 F2 0F 10 48 10 48 8B 44 24 40",0x2CBB33,"NATIVE_HOOK","Velocity-object acquisition is not a stable scalar owner."),
 ("movement.speed.live","Movement speed arithmetic","F3 41 0F 59 D9 48 03 C8 48 01 0A F3 48 0F 2C C6 F3 48 0F 2C CC",0x23AE34,"NATIVE_HOOK","Planar integration patch lacks local-player correlation and scalar readback."),
 ("player.stamina.full","Full stamina","0F B7 51 0C 8B 4B 08 48 03 CB C6 44 24 20 00 8B 04 91 89 44 24 40 EB 09 C6 44 24 20 16",0x23423F,"NATIVE_HOOK","Dynamic indexed cell and +8 sibling semantics require runtime correlation."),
 ("player.stamina.full","Full stamina generic reader","8B 3C 88 33 C9",0x27D8CF,"NATIVE_HOOK","Selector absent; writing 999 could affect an arbitrary indexed attribute."),
 ("player.mana.full","Full mana","C6 44 24 24 00 44 8B",0x2343F5,"NATIVE_HOOK","Sibling-field maximum semantics and authoritative readback are unproven."),
 ("item.durability.no_loss","No durability loss","44 01 2C 91 48 8D 4D B7",0x331A7A,"NATIVE_HOOK","Old patch reverses a delta and may persist item changes."),
)

def parse_pe(data):
 pe=struct.unpack_from("<I",data,0x3C)[0]
 return struct.unpack_from("<I",data,pe+8)[0],struct.unpack_from("<I",data,pe+0x50)[0]

def analyze(exe):
 data=Path(exe).read_bytes(); timestamp,image_size=parse_pe(data); digest=hashlib.sha256(data).hexdigest().upper()
 exact=digest==SHA256 and timestamp==PE_TIMESTAMP and image_size==IMAGE_SIZE; rows=[]
 for target_id,feature,signature,expected_rva,backend,reason in CANDIDATES:
  needle=bytes.fromhex(signature) if signature else b""
  offsets=[] if not needle else [i for i in range(len(data)) if data.startswith(needle,i)]
  # Revision 1076226 .text starts at raw 0x400 and RVA 0x1000.
  rvas=[x+0xC00 for x in offsets]
  rows.append({"targetId":target_id,"feature":feature,"backend":backend,"signature":signature,
   "expectedRva":None if expected_rva is None else f"0x{expected_rva:X}","matchCount":len(offsets),
   "observedRvas":[f"0x{x:X}" for x in rvas],"signatureAtExpectedRva":expected_rva in rvas if signature else False,
   "evidenceStatus":"CURRENT_BUILD_STATIC_CANDIDATE" if signature and exact and len(offsets)==1 and expected_rva in rvas else "INSUFFICIENT_EVIDENCE",
   "result":"REJECTED","reason":reason})
 return {"schema":"architect.first_cheat_sprint.v1","taskId":"CODE-0032","primaryResult":"NO_SAFE_MUTATION_CANDIDATE_FOUND",
  "build":{"revision":BUILD,"sha256":digest,"peTimestamp":f"0x{timestamp:08X}","imageSize":f"0x{image_size:08X}","exactMatch":exact},
  "candidateCount":len(rows),"acceptedCandidate":None,"namedTargetsRegistered":[],"mutationMasterGateChanged":False,
  "runtimeBehaviorChanged":False,"candidates":rows,
  "blockingReason":"No candidate has a deterministic live owner, original scalar model, immediate authoritative readback, and verified scalar restoration path.",
  "nextRuntimeExperiment":"Observe-only correlate the movement and stamina hook contexts before designing any mutation."}

def main():
 root=Path(__file__).resolve().parents[2]; p=argparse.ArgumentParser()
 p.add_argument("--exe",type=Path,default=root.parents[1]/"enshrouded.exe")
 p.add_argument("--output",type=Path,default=root/"bridge"/"first_cheat_sprint.json"); a=p.parse_args()
 result=analyze(a.exe); a.output.parent.mkdir(parents=True,exist_ok=True)
 a.output.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
 print(f"result={result['primaryResult']} candidates={result['candidateCount']} exactBuild={result['build']['exactMatch']}")
 return 0
if __name__=="__main__": raise SystemExit(main())
