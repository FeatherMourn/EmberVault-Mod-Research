import pefile

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)

text_section = None
for section in pe.sections:
    if b'.text' in section.Name:
        text_section = section
        break

data = text_section.get_data()
import struct

count = 0
for i in range(len(data) - 5):
    # Check for mov reg32, 0x04B6AA8B
    # mov edx, 0x04B6AA8B -> BA 8B AA B6 04
    # mov ecx, 0x04B6AA8B -> B9 8B AA B6 04
    # mov r8d, 0x04B6AA8B -> 41 B8 8B AA B6 04
    
    if data[i:i+5] == b'\xBA\x8B\xAA\xB6\x04' or data[i:i+5] == b'\xB9\x8B\xAA\xB6\x04':
        print(f"Hash 0x04B6AA8B found at RVA 0x{text_section.VirtualAddress + i:X}")
        count += 1
    elif data[i:i+6] == b'\x41\xB8\x8B\xAA\xB6\x04':
        print(f"Hash 0x04B6AA8B found at RVA 0x{text_section.VirtualAddress + i:X}")
        count += 1

print(f"Total hash matches: {count}")
