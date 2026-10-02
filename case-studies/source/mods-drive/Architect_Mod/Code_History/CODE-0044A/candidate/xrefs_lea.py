import pefile
import struct

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = None
for section in pe.sections:
    if b'.text' in section.Name:
        text_section = section
        break

data = text_section.get_data()
func_rva = 0x233C60

print("LEA XREFs to 0x233C60:")
for i in range(len(data) - 7):
    if data[i] == 0x48 and data[i+1] == 0x8d: # lea reg, [rip + offset]
        offset = struct.unpack('<i', data[i+3:i+7])[0]
        target = text_section.VirtualAddress + i + 7 + offset
        if target == func_rva:
            print(f"0x{text_section.VirtualAddress + i:X}")
