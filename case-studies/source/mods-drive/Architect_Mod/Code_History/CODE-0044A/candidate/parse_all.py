import re

with open("analysis.txt", "r") as f:
    content = f.read()

blocks = content.split("====================================")
for block in blocks:
    if not block.strip(): continue
    rva_match = re.search(r"RVA: 0x([0-9A-F]+)", block)
    if not rva_match: continue
    rva = rva_match.group(1)
    
    lines = block.strip().split("\n")
    writes = []
    reads = []
    maths = []
    
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
        if any(m in line for m in ["subss", "addss", "mulss", "maxss", "minss"]):
            maths.append(line)
            
    # Classify
    classification = "READ_ONLY / INDIRECT"
    if writes and maths:
        if any("subss" in m for m in maths):
            classification = "DIRECT_WRITE_CANDIDATE (SUB/DECREMENT)"
        else:
            classification = "DIRECT_WRITE_CANDIDATE (ADD/MATH)"
    elif writes and not maths:
        classification = "WRITE_NO_MATH (INITIALIZATION?)"
        
    print(f"RVA: 0x{rva} | {classification}")
    
