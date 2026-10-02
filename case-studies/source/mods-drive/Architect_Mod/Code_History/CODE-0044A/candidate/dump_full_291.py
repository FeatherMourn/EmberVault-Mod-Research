import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_64

pe = pefile.PE(r'H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe')
text_section = next(s for s in pe.sections if b'.text' in s.Name)
data = text_section.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_64)

# Disassemble 0x2912F0 to 0x29170A
start_rva = 0x2912F0
end_rva = 0x291710
offset = start_rva - text_section.VirtualAddress
block = data[offset:offset + (end_rva - start_rva)]

with open('full_291.txt', 'w') as f:
    for i in md.disasm(block, start_rva):
        bytes_hex = ' '.join(f'{b:02X}' for b in i.bytes)
        f.write(f'0x{i.address:06X}: {bytes_hex:<24} {i.mnemonic:<10} {i.op_str}\n')

print('Wrote full_291.txt')
