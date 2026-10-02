import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

pe = pefile.PE(r"H:\\SteamLibrary\\steamapps\\common\\Enshrouded\\enshrouded.exe")
cs = Cs(CS_ARCH_X86, CS_MODE_64)
for rva in (0x1F2E90, 0x26D8D0):
    print(f"--- context near RVA 0x{rva:X} ---")
    for insn in cs.disasm(pe.get_data(rva, 0x220), pe.OPTIONAL_HEADER.ImageBase + rva):
        print(f"RVA+0x{insn.address-pe.OPTIONAL_HEADER.ImageBase:08X}: {insn.bytes.hex(' '):24} {insn.mnemonic} {insn.op_str}")
