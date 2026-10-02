"""Static-only triage for the current executable; never writes process memory."""
from pathlib import Path
import hashlib
import re
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64
from capstone.x86_const import X86_OP_MEM, X86_REG_RIP

EXE = Path(r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe")
TERMS = (b"health", b"stamina", b"mana", b"xp", b"durability", b"fall", b"jump", b"speed", b"oxygen", b"shroud", b"heat", b"craft")
pe = pefile.PE(str(EXE), fast_load=False)
base = pe.OPTIONAL_HEADER.ImageBase
print("FILE", EXE)
print("SHA256", hashlib.sha256(EXE.read_bytes()).hexdigest().upper())
print("IMAGE_BASE", hex(base), "ENTRY_RVA", hex(pe.OPTIONAL_HEADER.AddressOfEntryPoint))
for section in pe.sections:
    name = section.Name.rstrip(b"\0").decode("ascii", "replace")
    print("SECTION", name, hex(section.VirtualAddress), hex(section.Misc_VirtualSize), hex(section.SizeOfRawData))

rdata = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".rdata")
rva = rdata.VirtualAddress
blob = pe.get_data(rva, rdata.Misc_VirtualSize)
strings = []
for m in re.finditer(rb"[ -~]{5,}", blob):
    value = m.group(0)
    low = value.lower()
    if any(t in low for t in TERMS):
        strings.append((base + rva + m.start(), m.start(), value[:120]))
print("TERM_STRINGS", len(strings))

text_section = next(s for s in pe.sections if s.Name.rstrip(b"\0") == b".text")
code = pe.get_data(text_section.VirtualAddress, text_section.Misc_VirtualSize)
cs = Cs(CS_ARCH_X86, CS_MODE_64)
cs.detail = True
hits = []
for insn in cs.disasm(code, base + text_section.VirtualAddress):
    for operand in insn.operands:
        if operand.type == X86_OP_MEM and operand.mem.base == X86_REG_RIP:
            target = insn.address + insn.size + operand.mem.disp
            for addr, offset, value in strings:
                if addr <= target < addr + len(value):
                    hits.append((insn.address, target, insn.mnemonic, insn.op_str, value))
                    break
print("RIP_RELATIVE_TERM_XREFS", len(hits))
for address, target, mnemonic, operands, value in hits[:300]:
    print(f"CANDIDATE 0x{address:X} -> 0x{target:X} {mnemonic} {operands} | {value.decode('ascii','replace')}")
print("STATUS Needs evidence: runtime value scans and access/write traces unavailable")
