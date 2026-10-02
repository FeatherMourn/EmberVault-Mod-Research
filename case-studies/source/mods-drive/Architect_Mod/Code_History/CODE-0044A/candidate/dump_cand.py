import pefile
from capstone import *
from capstone.x86 import *

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = next(s for s in pe.sections if b'.text' in s.Name)
data = text_section.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

def dump_block(rva):
    print(f"\n--- Disassembly for 0x{rva:X} ---")
    offset = rva - text_section.VirtualAddress - 0x20
    block = data[offset:offset+0x100]
    for i in md.disasm(block, rva - 0x20):
        print(f"0x{i.address:X}: {i.mnemonic:10} {i.op_str}")

dump_block(0x2E3DDA)
dump_block(0x2F1632)
