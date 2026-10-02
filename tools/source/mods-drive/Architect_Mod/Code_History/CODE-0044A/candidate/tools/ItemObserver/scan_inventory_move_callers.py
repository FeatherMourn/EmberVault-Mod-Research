#!/usr/bin/env python3
"""Bounded prototype and caller report for the proven inventory move path."""
import hashlib,json,struct
from pathlib import Path
import capstone,pefile
from capstone.x86 import X86_OP_IMM

RETURNS=(0x38613F,0x38636A,0x3860AC)
TARGET=0x3883C0
def hx(v):return f"0x{v:X}"
root=Path(__file__).resolve().parents[4];exe=root/"enshrouded.exe";data=exe.read_bytes();pe=pefile.PE(data=data,fast_load=True);base=pe.OPTIONAL_HEADER.ImageBase
secs=[(s.Name.rstrip(b"\0").decode(),s.VirtualAddress,s.PointerToRawData,s.SizeOfRawData,s.Misc_VirtualSize) for s in pe.sections]
def off(r):
 for _,v,o,n,z in secs:
  if v<=r<v+max(n,z):return o+r-v
pdata=next(x for x in secs if x[0]==".pdata");funcs=[]
for o in range(pdata[2],pdata[2]+pdata[3]-11,12):
 b,e,u=struct.unpack_from("<III",data,o)
 if b and b<e:funcs.append((b,e,u))
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_64);md.detail=True
rows=[]
for ret in RETURNS:
 f=next(x for x in funcs if x[0]<=ret<x[1]);ins=list(md.disasm(data[off(f[0]):off(f[0])+f[1]-f[0]],base+f[0]));call=next(i for i in ins if i.address-base==ret-5)
 bounded=[]
 for i in ins:
  r=i.address-base
  if ret-0x70<=r<=ret+0x28:
   x={"rva":hx(r),"bytes":bytes(i.bytes).hex(" ").upper(),"instruction":f"{i.mnemonic} {i.op_str}"}
   if i.mnemonic in ("call","jmp") and i.operands and i.operands[0].type==X86_OP_IMM:x["directTargetRva"]=hx(i.operands[0].imm-base)
   bounded.append(x)
 semantics={
  0x38613F:{"rcx":"&result [rbp-0x48]","rdx":"r15 context","r8":"rdi","r9":"resolver return rax","stackArg20":"dword [rbp-0x18]","candidateAmountSource":"ebx from [rbp-0x14]","notes":"On success caller adds EBX to R12D at 0x38614E."},
  0x38636A:{"rcx":"&result [rsp+0x30]","rdx":"rbp context","r8":"rbx","r9":"resolver return rax","stackArg20":"dword [rsp+0x50]","candidateAmountSource":"r13d, bounded by comparisons/cmov at 0x3862FA..0x38630C","notes":"Amount-like R13D is limited by a uint16 input, a resolved limit, and dword [rsp+0x30]."},
  0x3860AC:{"rcx":"&result [rbp-0x48]","rdx":"r15 context","r8":"rdi","r9":"resolver return rax","stackArg20":"dword [rbp-0x18]","candidateAmountSource":"r12d","notes":"On success caller writes R12D to output+4 at 0x3860C3."}
 }[ret]
 rows.append({"observedReturnRva":hx(ret),"callRva":hx(ret-5),"callBytes":bytes(call.bytes).hex(" ").upper(),"callTargetRva":hx(call.operands[0].imm-base),"enclosingFunction":{"beginRva":hx(f[0]),"endRva":hx(f[1]),"unwindRva":hx(f[2])},"argumentSetup":semantics,"boundedDisassembly":bounded})
empty=bytes.fromhex("48 8B C6 C7 46 04 00 00 00 00 C6 06 00");merge=bytes.fromhex("45 01 67 04 C6 06 00 44 3B E7 75 09")
report={"schemaVersion":2,"executableSha256":hashlib.sha256(data).hexdigest().upper(),"targetFunctionRva":hx(TARGET),"prototypeResearch":{"candidateArg1":"RCX result/status output object","candidateArg2":"RDX inventory-access context; copied to RBP and used by lookup helpers","candidateArg3":"R8 packed InventorySlotId-compatible value; copied to RBX","candidateArg4":"R9 resolver record; copied to R14; first dword equals transferred ItemId live","candidateArg5":"caller stack +0x20; copied to EDI; exact semantic role unresolved","candidateArg6":"caller stack +0x28; transfer amount PROVEN by v0.17 live pre/post","destinationResult":"0x387830 decodes candidateArg3, validates slot<8, and returns inventoryBase + slotIndex*0x0C","sourceLookup":"callers 0x385D80 and 0x386180 resolve the other packed slot through 0x386C00 before calling target","r14ConcreteType":"UNSOLVED"},"slotDerivation":{"decodeHelperRva":"0xCBE2B0","packedLayout":"low dword EntityId-compatible; high dword slotIndex-compatible (helper consumes its low byte)","destinationLookupRva":"0x387830","sourceLookupRva":"0x386C00","indexHelperRva":"0xCB4EE0","addressFormula":"base + slotIndex*0x0C","slotBound":"slotIndex < 8","ownership":"UNSOLVED"},"observedCallers":rows,"calleeArgumentFinding":{"candidateAmountRaw":"sixth stack argument: caller [rsp+0x28], observed in callee as dword [rsp+0x88] after its 0x58-byte prologue","candidateAmountStatus":"PROVEN_BUILD_1076226","r14":"callee copies R9 to R14; observed callers supply a resolver return in R9","r14FirstDwordStatus":"PROVEN_BUILD_1076226","r14ConcreteType":"UNSOLVED"},"postObservationSites":[{"path":"empty_destination_initialization","rva":"0x3884E3","bytes":empty.hex(" ").upper(),"occurrenceCount":data.count(empty),"point":"after ItemStack writes and existing bookkeeping call","status":"PROVEN_BUILD_1076226"},{"path":"existing_item_merge","rva":"0x38859F","bytes":merge.hex(" ").upper(),"occurrenceCount":data.count(merge),"point":"count add is replayed before post snapshot; original branches preserved","status":"PROVEN_BUILD_1076226"}],"callerObservedRoles":{"0x38636A":"observed_during_split","0x38613F":"observed_during_move_to_empty","0x3860AC":"observed_during_existing_stack_merge"},"actionClassification":"Roles describe controlled observations, not exclusive function identities.","inventoryTransferActionStatus":"UNSOLVED"}
out=Path(__file__).resolve().parents[2]/"bridge/inventory_move_caller_scan.json";out.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8");print(f"callers={len(rows)} target={TARGET:#x} output={out}")
