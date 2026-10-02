import pefile
from capstone import *
from capstone.x86 import *

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = next(s for s in pe.sections if b'.text' in s.Name)
data = text_section.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

rvas = [
    0x1E0DFC, 0x1E4CB5, 0x1F5731, 0x1F9C57, 0x1FA1BB, 0x1FA22B, 0x210CCC, 0x234212, 
    0x23634A, 0x274674, 0x274ECB, 0x27D224, 0x2915B1, 0x291828, 0x2C829F, 0x2E3D7E, 
    0x2E3DDA, 0x2F1632, 0x2F1AB0, 0x2F1B93, 0x365313, 0x38ADE0, 0x38B36E, 0x38BA06, 
    0x398901, 0x398962
]

results = []
for rva in rvas:
    offset = rva - text_section.VirtualAddress - 0x10
    block = data[offset:offset+0x200]
    insns = list(md.disasm(block, rva - 0x10))
    
    # find the instruction that reads from the property offset (e.g. mov ..., [rcx + rdx*4])
    # or writes to it (mov [rcx + rdx*4], ...)
    
    has_read = False
    has_write = False
    write_insn = None
    math_ops = []
    
    for i in insns:
        if i.address < rva: continue
        op_str = i.op_str
        # Check memory accesses
        if "[" in op_str and "]" in op_str and ("*4" in op_str or "+ 0xc" in op_str or "+ 0x10" in op_str):
            if i.mnemonic.startswith("mov"):
                dst, src = op_str.split(", ", 1)
                if "[" in dst and "]" in dst and "*4" in dst:
                    has_write = True
                    write_insn = i
                elif "[" in src and "]" in src and "*4" in src:
                    has_read = True
        if i.mnemonic in ["subss", "addss", "mulss", "minss", "maxss"]:
            math_ops.append(i.mnemonic)

    cls = "UNKNOWN"
    if has_read and has_write:
        cls = "DIRECT_WRITE_CANDIDATE"
    elif has_read and not has_write:
        cls = "READ_ONLY"
    elif has_write and not has_read:
        cls = "WRITE_ONLY (INITIALIZATION)"
    else:
        # maybe accessed differently
        cls = "INDIRECT_OR_UNKNOWN"
        
    results.append(f"0x{rva:X} | {cls} | Math: {len(math_ops)}")
    if has_write and write_insn:
        results.append(f"  -> Write: {write_insn.mnemonic} {write_insn.op_str}")

with open("summary_candidates.txt", "w") as f:
    f.write("\n".join(results))

