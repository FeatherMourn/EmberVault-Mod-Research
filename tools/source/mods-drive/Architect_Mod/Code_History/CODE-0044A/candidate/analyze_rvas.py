import pefile
from capstone import *
from capstone.x86 import *

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = None
for section in pe.sections:
    if b'.text' in section.Name:
        text_section = section
        break

data = text_section.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

rvas = [
    0x1E0DFC, 0x1E4CB5, 0x1F5731, 0x1F9C57, 0x1FA1BB, 0x1FA22B, 0x210CCC, 0x234212, 
    0x23634A, 0x274674, 0x274ECB, 0x27D224, 0x2915B1, 0x291828, 0x2C829F, 0x2E3D7E, 
    0x2E3DDA, 0x2F1632, 0x2F1AB0, 0x2F1B93, 0x365313, 0x38ADE0, 0x38B36E, 0x38BA06, 
    0x398901, 0x398962
]

print("Analyzing 26 RVAs...")

with open("analysis.txt", "w") as f:
    for rva in rvas:
        f.write(f"\n====================================\n")
        f.write(f"RVA: 0x{rva:X}\n")
        
        # Disassemble 0x100 bytes after the hash instruction
        offset = rva - text_section.VirtualAddress
        block = data[offset:offset+0x100]
        
        insns = list(md.disasm(block, rva))
        writes = 0
        reads = 0
        math = []
        
        for i in insns:
            # simple heuristics
            op_str = i.op_str
            # Check for memory write: destination operand contains a memory reference
            if i.mnemonic.startswith("mov") and ", " in op_str:
                dest, src = op_str.split(", ", 1)
                if "[" in dest and "]" in dest:
                    writes += 1
                elif "[" in src and "]" in src:
                    reads += 1
            if i.mnemonic in ["subss", "addss", "mulss", "divss", "maxss", "minss", "subsd", "addsd"]:
                math.append(i.mnemonic)
                
            f.write(f"0x{i.address:X}: {i.mnemonic:10} {i.op_str}\n")
            
        f.write(f"--> Summary: {reads} reads, {writes} writes, Math: {', '.join(math)}\n")

print("Done")
