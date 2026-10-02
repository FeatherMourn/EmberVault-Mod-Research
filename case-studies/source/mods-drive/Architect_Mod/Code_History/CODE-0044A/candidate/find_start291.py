import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = next(s for s in pe.sections if b'.text' in s.Name)
data = text_section.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_64)

# scan backwards from 0x291580 to find ret or push rbp
offset = 0x290800 - text_section.VirtualAddress
block = data[offset:offset + 0x1000]

last_func = 0
for i in md.disasm(block, 0x290800):
    if i.mnemonic in ['ret', 'int3']:
        last_func = i.address
    if i.address == 0x2915B1:
        print(f"Function starts after: 0x{last_func:X}")
        break

