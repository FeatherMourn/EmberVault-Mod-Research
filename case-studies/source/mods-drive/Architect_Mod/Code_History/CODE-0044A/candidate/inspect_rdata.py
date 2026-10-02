import pefile

pe = pefile.PE(r'H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe')
rdata = next(s for s in pe.sections if b'.rdata' in s.Name)
offset = 0x1D410F0 - rdata.VirtualAddress
block = rdata.get_data()[offset - 0x100 : offset + 0x200]

# Print strings in block
import re
for m in re.finditer(rb'[A-Za-z0-9_]{4,}', block):
    print(m.group().decode())

