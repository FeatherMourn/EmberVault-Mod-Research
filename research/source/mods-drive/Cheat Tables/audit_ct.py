from pathlib import Path
import hashlib
import re
import sys
import xml.etree.ElementTree as ET

for raw in sys.argv[1:]:
    path = Path(raw)
    text = path.read_text(encoding="utf-8", errors="replace")
    root = ET.fromstring(text)
    entries = root.findall(".//CheatEntry")
    scripts = [e.findtext("AssemblerScript") or "" for e in entries]
    descriptions = [(e.findtext("Description") or "").strip('"') for e in entries]
    print(f"FILE={path}")
    print(f"SIZE={path.stat().st_size} SHA256={hashlib.sha256(path.read_bytes()).hexdigest()}")
    print(f"ENTRIES={len(entries)} SCRIPTS={sum(bool(s.strip()) for s in scripts)}")
    print(f"ENABLE={sum(s.count('[ENABLE]') for s in scripts)} DISABLE={sum(s.count('[DISABLE]') for s in scripts)}")
    print(f"ALLOC={sum(len(re.findall(r'(?im)^\s*alloc\s*\(', s)) for s in scripts)} DEALLOC={sum(len(re.findall(r'(?im)^\s*dealloc\s*\(', s)) for s in scripts)}")
    print(f"REGSYM={sum(len(re.findall(r'(?im)^\s*registersymbol\s*\(', s)) for s in scripts)} UNREGSYM={sum(len(re.findall(r'(?im)^\s*unregistersymbol\s*\(', s)) for s in scripts)}")
    print("DESCRIPTIONS")
    for i, desc in enumerate(descriptions):
        print(f"{i}: {desc[:240]}")
    print("AOB_LINES")
    for i, script in enumerate(scripts):
        for line in script.splitlines():
            if re.search(r"aobscan|aobscanmodule|assert\s*\(", line, re.I):
                print(f"{i}: {line.strip()[:300]}")
