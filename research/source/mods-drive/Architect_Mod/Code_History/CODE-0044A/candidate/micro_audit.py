import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = next(s for s in pe.sections if b'.text' in s.Name)
data = text_section.get_data()

md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

def disassemble_range(start_rva, end_rva):
    offset_start = start_rva - text_section.VirtualAddress
    length = end_rva - start_rva
    block = data[offset_start:offset_start + length]
    lines = []
    for i in md.disasm(block, start_rva):
        bytes_hex = " ".join(f"{b:02X}" for b in i.bytes)
        lines.append(f"0x{i.address:06X}: {bytes_hex:<24} {i.mnemonic:<10} {i.op_str}")
    return lines

print("=== Disassembling Site A: 0x291590 to 0x2916A0 ===")
for line in disassemble_range(0x291580, 0x2916B0):
    print(line)

print("\n=== Disassembling Site B: 0x2E3D60 to 0x2E3F00 ===")
for line in disassemble_range(0x2E3D60, 0x2E3F10):
    print(line)

