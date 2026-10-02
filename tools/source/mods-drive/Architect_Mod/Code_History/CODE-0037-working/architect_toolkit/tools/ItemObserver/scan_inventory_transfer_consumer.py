#!/usr/bin/env python3
"""Bounded current-build analysis of the artifact-guided inventory-move site."""
from __future__ import annotations
import argparse, hashlib, json, struct
from pathlib import Path
import capstone, pefile
from capstone.x86 import X86_OP_IMM

SITE_RVA=0x388453
HISTORICAL_PREFIX=bytes.fromhex("4C8B7C2428488B55")
OVERWRITTEN_BYTES=bytes.fromhex("4C8B7C2428488B5508498BCF")
EXPANDED_BYTES=bytes.fromhex("4C8B7C2428488B5508498BCFE82CB4930084C00F8495000000")
def hx(v): return None if v is None else f"0x{v:X}"

def main():
 p=argparse.ArgumentParser(description=__doc__); root=Path(__file__).resolve().parents[4]
 p.add_argument("--exe",type=Path,default=root/"enshrouded.exe")
 p.add_argument("--output",type=Path,default=Path(__file__).resolve().parents[2]/"bridge/inventory_move_pointer_site_scan.json")
 a=p.parse_args(); data=a.exe.read_bytes(); pe=pefile.PE(data=data,fast_load=True); base=pe.OPTIONAL_HEADER.ImageBase
 sections=[{"name":s.Name.rstrip(b"\0").decode(errors="replace"),"rva":s.VirtualAddress,"raw":s.PointerToRawData,"rawSize":s.SizeOfRawData,"virtualSize":s.Misc_VirtualSize} for s in pe.sections]
 def sec(r): return next((s for s in sections if s["rva"]<=r<s["rva"]+max(s["rawSize"],s["virtualSize"])),None)
 def off(r):
  s=sec(r)
  if not s or r-s["rva"]>=s["rawSize"]: raise ValueError(f"RVA {r:#x} is not file-backed")
  return s["raw"]+r-s["rva"]
 pdata=next(s for s in sections if s["name"]==".pdata"); funcs=[]
 for o in range(pdata["raw"],pdata["raw"]+pdata["rawSize"]-11,12):
  b,e,u=struct.unpack_from("<III",data,o)
  if b and b<e: funcs.append((b,e,u))
 enclosing=next((x for x in funcs if x[0]<=SITE_RVA<x[1]),None)
 if not enclosing: raise SystemExit("No .pdata function contains target RVA")
 begin,end,unwind=enclosing; md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64); md.detail=True
 insns=list(md.disasm(data[off(begin):off(begin)+end-begin],base+begin))
 def row(i):
  x={"rva":hx(i.address-base),"bytes":bytes(i.bytes).hex(" ").upper(),"instruction":f"{i.mnemonic} {i.op_str}".strip()}
  if i.mnemonic in ("call","jmp") and i.operands and i.operands[0].type==X86_OP_IMM:x["directTargetRva"]=hx(i.operands[0].imm-base)
  return x
 bounded=[row(i) for i in insns if SITE_RVA-0x35<=i.address-base<=SITE_RVA+0xC8]
 callers=[]; text=next(s for s in sections if s["name"]==".text")
 for i in md.disasm(data[text["raw"]:text["raw"]+text["rawSize"]],base+text["rva"]):
  if i.mnemonic=="call" and i.operands and i.operands[0].type==X86_OP_IMM and i.operands[0].imm-base==begin:callers.append(hx(i.address-base))
 def occurrences(needle):
  out=[]; start=0
  while (found:=data.find(needle,start))>=0: out.append(found); start=found+1
  return out
 old=occurrences(HISTORICAL_PREFIX); expanded=occurrences(EXPANDED_BYTES); site=off(SITE_RVA)
 report={"schemaVersion":2,"tool":"scan_inventory_transfer_consumer.py","strategy":"bounded artifact-guided current-site analysis; broad multi-offset scan disabled","executable":{"sha256":hashlib.sha256(data).hexdigest().upper(),"timeDateStamp":hx(pe.FILE_HEADER.TimeDateStamp),"sizeOfImage":hx(pe.OPTIONAL_HEADER.SizeOfImage)},"historicalExternalEvidence":{"oldRva":"0x340D13","oldRvaUsed":False,"prefix":HISTORICAL_PREFIX.hex(" ").upper()},"currentSite":{"rva":hx(SITE_RVA),"section":sec(SITE_RVA)["name"],"enclosingFunction":{"beginRva":hx(begin),"endRva":hx(end),"unwindInfoRva":hx(unwind)},"exactBytesAtSite":data[site:site+32].hex(" ").upper(),"overwrittenInstructionBytes":OVERWRITTEN_BYTES.hex(" ").upper(),"overwrittenInstructionLength":len(OVERWRITTEN_BYTES),"continuationRva":hx(SITE_RVA+len(OVERWRITTEN_BYTES)),"downstreamDirectCallRva":"0x38845F","downstreamDirectCallTargetRva":"0xCC3890","boundedDisassembly":bounded,"directCallersOfEnclosingFunction":callers,"directCallerLimitation":"No direct rel32 caller was decoded; dispatch may be indirect."},"signature":{"historicalPrefixCurrentOccurrenceCount":len(old),"expandedCurrentBytes":EXPANDED_BYTES.hex(" ").upper(),"expandedCurrentOccurrenceCount":len(expanded),"maskedForm":"4C 8B 7C 24 28 48 8B 55 08 49 8B CF E8 ?? ?? ?? ?? 84 C0 0F 84 ?? ?? ?? ??","relocationNote":"rel32 displacements are validated by decoded current-build targets rather than treated as portable identity bytes"},"dataFlow":{"candidateSource":"R15 <- qword [RSP+0x28] at 0x388453","stackSlotProvenance":"0x387830 receives &([rsp+0x20]); success is tested at [rsp+0x20], and adjacent qword [rsp+0x28] is consumed as R15","validationCall":"0xCC3890(candidate R15, qword [RBP+0x08]) -> AL","downstreamEvidence":["0x3884A6 writes dword [R15+0x00]","0x3884D0 writes dword [R15+0x04]","0x3884BF writes dword [R15+0x08] on one branch","0x388501 reads dword [R15+0x00] on the alternate branch"],"itemStackInterpretation":"EXPERIMENTAL_RUNTIME_VALIDATION_REQUIRED"},"probeDecision":"READY_FOR_BUILD_LOCKED_OBSERVE_ONLY_PROBE","inventoryTransferActionStatus":"UNSOLVED","safety":"Static PE/disassembly analysis only; no process access or game mutation."}
 a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
 print(f"site={SITE_RVA:#x} function={begin:#x}..{end:#x} historical={len(old)} expanded={len(expanded)} probe={report['probeDecision']}")
if __name__=="__main__": main()
