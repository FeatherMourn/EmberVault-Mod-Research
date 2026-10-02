import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

path = r"H:\\SteamLibrary\\steamapps\\common\\Enshrouded\\enshrouded.exe"
rva = 0x1F3014
pe = pefile.PE(path)
data = pe.get_data(rva - 24, 96)
cs = Cs(CS_ARCH_X86, CS_MODE_64)
for insn in cs.disasm(data, pe.OPTIONAL_HEADER.ImageBase + rva - 24):
    print(f"RVA+0x{insn.address - pe.OPTIONAL_HEADER.ImageBase:08X}: {insn.bytes.hex(' '):24} {insn.mnemonic} {insn.op_str}")
