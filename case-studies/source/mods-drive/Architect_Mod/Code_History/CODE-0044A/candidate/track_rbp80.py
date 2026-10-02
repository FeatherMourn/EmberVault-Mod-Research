import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = next(s for s in pe.sections if b'.text' in s.Name)
data = text_section.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_64)

# Disassemble from 0x291200 to 0x291680
offset_start = 0x291200 - text_section.VirtualAddress
block = data[offset_start:offset_start + 0x500]

print("Scanning for [rbp - 0x80] in 0x291200..0x291680:")
for i in md.disasm(block, 0x291200):
    if "0x80" in i.op_str and "rbp" in i.op_str:
        print(f"0x{i.address:06X}: {i.mnemonic:<10} {i.op_str}")

