"""Offline CODE-0024 GameSettings reflection and executable-anchor mapper."""
from __future__ import annotations
import hashlib, json, struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXE = ROOT.parents[1] / "enshrouded.exe"
TYPES = ROOT.parents[1] / ".cache" / "types.json"
OUT = ROOT / "bridge" / "game_settings_static_map.json"
EXPECTED_SHA = "AF2F5A1227911D8AA06B3908D6BD0211838211CAE14EA91099CB57D0DF990781"
TARGETS = (2702, 2703, 2784, 3410, 4308, 4309, 4311)

def build() -> dict:
    import pefile
    exe_hash = hashlib.sha256(EXE.read_bytes()).hexdigest().upper()
    pe = pefile.PE(str(EXE), fast_load=False)
    text = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text").get_data()
    raw = json.loads(TYPES.read_text(encoding="utf-8")); rows = raw.get("types", raw)
    by_index = {int(x["index"]): x for x in rows}
    types = []
    for index in TARGETS:
        row = by_index[index]
        hashes = {k: row.get(k) for k in ("nameHash", "impactHash", "qualifiedHash", "internalHash")}
        hits = {k: text.count(struct.pack("<I", int(v))) for k,v in hashes.items() if v is not None}
        types.append({"index":index,"qualifiedName":row["qualifiedName"],"size":row["size"],"hashes":hashes,"textImmediateHits":hits})
    settings = by_index[2702]
    fields = [{"name":name,"offset":value["dataOffset"],"typeIndex":value["type"],"classification":"UNAVAILABLE","candidateMode":"LIVE","readback":False,"revert":False} for name,value in settings["structFields"].items()]
    return {"schemaVersion":1,"build":{"revision":1076226,"sha256":exe_hash,"fingerprintMatches":exe_hash==EXPECTED_SHA,"peTimestamp":f"0x{pe.FILE_HEADER.TimeDateStamp:08X}","imageSize":f"0x{pe.OPTIONAL_HEADER.SizeOfImage:08X}"},"reflection":{"sha256":hashlib.sha256(TYPES.read_bytes()).hexdigest().upper(),"types":types},"fields":fields,"runtime":{"authoritativeOwner":"UNSOLVED","dispatch":"UNSOLVED","authority":"UNSOLVED","versionMonotonicity":"UNSOLVED","changedEventDelivery":"UNSOLVED","readback":"UNSOLVED","persistence":"UNSOLVED","mutationEnabled":False,"firstMutationCandidate":"factoryProductionSpeedFactor","candidateRationale":"High-signal and reversible only after the shared dispatch/readback/restore path is proven.","installProbe":False,"reason":"No unique semantic native boundary or authoritative readback path was recovered."}}

def main() -> None:
    result=build(); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(f"wrote {OUT} fields={len(result['fields'])} installProbe={result['runtime']['installProbe']}")
if __name__ == "__main__": main()
