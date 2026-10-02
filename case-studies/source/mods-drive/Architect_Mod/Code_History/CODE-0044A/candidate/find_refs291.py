import pefile
import struct

pe = pefile.PE(r'H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe')
text_section = next(s for s in pe.sections if b'.text' in s.Name)
data = text_section.get_data()
func_rva = 0x2912F0

print('Searching callers/refs to 0x2912F0...')
for i in range(len(data) - 4):
    if data[i] == 0xE8:
        offset = struct.unpack('<i', data[i+1:i+5])[0]
        if text_section.VirtualAddress + i + 5 + offset == func_rva:
            print(f'CALL at RVA: 0x{text_section.VirtualAddress + i:X}')

# Also search .rdata for pointers to 0x2912F0
target_abs = pe.OPTIONAL_HEADER.ImageBase + func_rva
for section in pe.sections:
    if b'.rdata' in section.Name or b'.data' in section.Name:
        sdata = section.get_data()
        for i in range(0, len(sdata) - 8, 8):
            val = struct.unpack('<Q', sdata[i:i+8])[0]
            if val == target_abs:
                print(f'Pointer in {section.Name.decode().strip(chr(0))} at RVA: 0x{section.VirtualAddress + i:X}')
