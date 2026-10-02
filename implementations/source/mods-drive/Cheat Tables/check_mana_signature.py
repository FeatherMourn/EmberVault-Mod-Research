import pefile

pe = pefile.PE(r"H:\\SteamLibrary\\steamapps\\common\\Enshrouded\\enshrouded.exe")
text = pe.sections[0].get_data()
start = 0x1F2F50 - pe.sections[0].VirtualAddress
end = 0x1F3009 - pe.sections[0].VirtualAddress
pattern = text[start:end]
hits = []
i = text.find(pattern)
while i >= 0:
    hits.append(pe.sections[0].VirtualAddress + i)
    i = text.find(pattern, i + 1)
print("LENGTH", len(pattern))
print("PATTERN", pattern.hex(" "))
print("MATCH_COUNT", len(hits))
print("RVA_MATCHES", [hex(x) for x in hits])
