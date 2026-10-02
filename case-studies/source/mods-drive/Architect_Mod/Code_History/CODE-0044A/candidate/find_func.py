import pefile
from capstone import *
import sys

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)

def get_data_at_rva(pe, rva, size):
    for section in pe.sections:
        if section.VirtualAddress <= rva < section.VirtualAddress + section.Misc_VirtualSize:
            offset = rva - section.VirtualAddress
            return section.get_data()[offset:offset+size]
    return b""

data = get_data_at_rva(pe, 0x232000, 0x2500)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

last_ret = 0
for i in md.disasm(data, 0x232000):
    if i.mnemonic == 'ret' or i.mnemonic == 'int3':
        last_ret = i.address
    if i.address == 0x23423F:
        print(f"Function likely starts after: 0x{last_ret:X}")
        break

