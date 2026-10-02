import re

with open("analysis.txt", "r") as f:
    content = f.read()

blocks = content.split("====================================")
results = []
for block in blocks:
    if not block.strip(): continue
    rva_match = re.search(r"RVA: 0x([0-9A-F]+)", block)
    if not rva_match: continue
    rva = rva_match.group(1)
    
    # We want to identify the sequence immediately following the hash call.
    # Usually: call 0xfe5fe0 (or similar lookup).
    # Then some setup, then a read/write to memory.
    
    # Look for writes to [rcx + rdx*4] or [rax + rcx*4] etc.
    lines = block.strip().split("\n")
    writes = []
    reads = []
    maths = []
    has_sub = False
    
    for i, line in enumerate(lines):
        if "mov" in line and "]" in line and "[" in line:
            if "movss" in line or "movsd" in line or "dword ptr" in line:
                if line.split()[1].startswith("mov"):
                    parts = line.split(", ", 1)
                    if len(parts) == 2:
                        dst = parts[0].split(maxsplit=2)[-1]
                        src = parts[1]
                        if "[" in dst: writes.append(line)
                        if "[" in src: reads.append(line)
        if "subss" in line or "addss" in line or "mulss" in line or "maxss" in line or "minss" in line:
            maths.append(line)
            if "subss" in line: has_sub = True
            
    # Classify
    classification = "READ_ONLY"
    if writes and maths:
        if has_sub:
            classification = "DIRECT_WRITE_CANDIDATE (SUB/DECREMENT)"
        else:
            classification = "DIRECT_WRITE_CANDIDATE"
    elif writes and not maths:
        classification = "WRITE_NO_MATH (INITIALIZATION?)"
    
    if len(writes) > 0 or has_sub:
        print(f"--- RVA {rva} ---")
        print(f"Class: {classification}")
        print(f"Math: {len(maths)} ops")
        if maths: print("  " + "\n  ".join(maths[:3]))
        if writes: print("  " + "\n  ".join(writes[:3]))
        print("")
