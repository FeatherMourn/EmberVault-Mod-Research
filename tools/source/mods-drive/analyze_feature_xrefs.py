"""Read-only candidate finder; string references are not gameplay-hook proof."""
from pathlib import Path
import re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP

EXE = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe")
TERMS = (b"health", b"stamina", b"mana", b"oxygen", b"glider", b"durability", b"inventory", b"teleport")
pe = pefile.PE(str(EXE), fast_load=False)
image_base = pe.OPTIONAL_HEADER.ImageBase
rdata = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".rdata")
rva0 = rdata.VirtualAddress
raw = pe.get_data(rva0, rdata.Misc_VirtualSize)
needles = {}
for m in re.finditer(rb"[ -~]{5,}", raw):
    value = m.group(0).lower()
    if any(t in value for t in TERMS):
        needles[image_base + rva0 + m.start()] = value[:100]

text = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
code = pe.get_data(text.VirtualAddress, text.Misc_VirtualSize)
cs = Cs(CS_ARCH_X86, CS_MODE_64)
cs.detail = True
hits = []
for insn in cs.disasm(code, image_base + text.VirtualAddress):
    for op in insn.operands:
        if op.type == X86_OP_MEM and op.mem.base == X86_REG_RIP:
            target = insn.address + insn.size + op.mem.disp
            if target in needles:
                hits.append((insn.address, target, insn.mnemonic, insn.op_str, needles[target]))

print(f"STRING_CANDIDATES={len(needles)}")
print(f"RIP_RELATIVE_XREFS={len(hits)}")
for address, target, mnemonic, operands, value in hits[:200]:
    print(f"0x{address:X} -> 0x{target:X} {mnemonic} {operands} | {value.decode('ascii','replace')}")
print("STATUS=STATIC_CANDIDATES_ONLY")
