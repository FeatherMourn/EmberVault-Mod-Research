import pefile
from capstone import *

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)

def get_data_at_rva(pe, rva, size):
    for section in pe.sections:
        if section.VirtualAddress <= rva < section.VirtualAddress + section.Misc_VirtualSize:
            offset = rva - section.VirtualAddress
            return section.get_data()[offset:offset+size]
    return b""

# Let's dump 0x234000 to 0x234500
data = get_data_at_rva(pe, 0x234000, 0x600)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

with open('disasm_234.txt', 'w') as f:
    for i in md.disasm(data, 0x234000):
        marker = ">>>" if i.address == 0x23423F else "   "
        bytes_str = " ".join(f"{b:02X}" for b in i.bytes)
        f.write(f"{marker} 0x{i.address:X}: {bytes_str:<24} {i.mnemonic} {i.op_str}\n")
