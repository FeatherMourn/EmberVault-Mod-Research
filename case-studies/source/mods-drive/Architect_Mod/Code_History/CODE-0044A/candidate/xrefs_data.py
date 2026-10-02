import pefile
import struct

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)

func_rva = 0x233C60
target_abs = pe.OPTIONAL_HEADER.ImageBase + func_rva

print("Data XREFs to 0x233C60:")
for section in pe.sections:
    if b'.rdata' in section.Name or b'.data' in section.Name:
        data = section.get_data()
        for i in range(0, len(data) - 8, 8):
            val = struct.unpack('<Q', data[i:i+8])[0]
            if val == target_abs:
                print(f"Found in {section.Name.decode('utf-8').strip('\x00')} at RVA: 0x{section.VirtualAddress + i:X}")

