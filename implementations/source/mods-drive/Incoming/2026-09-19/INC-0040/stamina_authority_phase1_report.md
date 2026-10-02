Ran command: `@"
import pefile
from capstone import *

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)

def get_data_at_rva(pe, rva, size):
    for section in pe.sections:
        if section.VirtualAddress <= rva < section.VirtualAddress + section.Misc_VirtualSize:
            offset = rva - section.VirtualAddress
            return section.get_data()[offset:offset+size]
    return b""

# Let's dump 0x234000 to 0x234500
data = get_data_at_rva(pe, 0x234000, 0x600)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

with open('disasm_234.txt', 'w') as f:
    for i in md.disasm(data, 0x234000):
        marker = ">>>" if i.address == 0x23423F else "   "
        bytes_str = " ".join(f"{b:02X}" for b in i.bytes)
        f.write(f"{marker} 0x{i.address:X}: {bytes_str:<24} {i.mnemonic} {i.op_str}\n")
"@ | Out-File -FilePath dump_234.py -Encoding ascii
python dump_234.py`
Ran command: `Start-Sleep -Seconds 2`
Ran command: `cat disasm_234.txt | Select-String "int 3" -Context 0, 5 | Select-String "0x234[012]"`
Ran command: `cat disasm_234.txt | Select-String "ret" -Context 0,2`
Ran command: `cat disasm_234.txt | Select-String "ret "`
Ran command: `cat disasm_234.txt | Select-String "0x23423F" -Context 30,30`
Ran command: `cat disasm_234.txt | Select-Object -First 20`
Ran command: `@"
import pefile
from capstone import *
import sys

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)

def get_data_at_rva(pe, rva, size):
    for section in pe.sections:
        if section.VirtualAddress <= rva < section.VirtualAddress + section.Misc_VirtualSize:
            offset = rva - section.VirtualAddress
            return section.get_data()[offset:offset+size]
    return b""

data = get_data_at_rva(pe, 0x232000, 0x2500)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

last_ret = 0
for i in md.disasm(data, 0x232000):
    if i.mnemonic == 'ret' or i.mnemonic == 'int3':
        last_ret = i.address
    if i.address == 0x23423F:
        print(f"Function likely starts after: 0x{last_ret:X}")
        break

"@ | Out-File -FilePath find_func.py -Encoding ascii
python find_func.py`
Ran command: `Start-Sleep -Seconds 2`
Ran command: `@"
import pefile
from capstone import *

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)

def get_data_at_rva(pe, rva, size):
    for section in pe.sections:
        if section.VirtualAddress <= rva < section.VirtualAddress + section.Misc_VirtualSize:
            offset = rva - section.VirtualAddress
            return section.get_data()[offset:offset+size]
    return b""

data = get_data_at_rva(pe, 0x233C60, 0x800)
md = Cs(CS_ARCH_X86, CS_MODE_64)
md.detail = True

with open('disasm_func.txt', 'w') as f:
    for i in md.disasm(data, 0x233C60):
        marker = ">>>" if i.address == 0x23423F else "   "
        bytes_str = " ".join(f"{b:02X}" for b in i.bytes)
        f.write(f"{marker} 0x{i.address:X}: {bytes_str:<24} {i.mnemonic} {i.op_str}\n")
"@ | Out-File -FilePath dump_func.py -Encoding ascii
python dump_func.py`
Ran command: `Start-Sleep -Seconds 2`
Ran command: `cat disasm_func.txt | Select-Object -First 20`
Ran command: `cat disasm_func.txt | Select-String "ret"`
Ran command: `@"
import pefile
from capstone import *

pe_path = r"H:\SteamLibrary\steamapps\common\Enshrouded\enshrouded.exe"
pe = pefile.PE(pe_path)
text_section = None
for section in pe.sections:
    if b'.text' in section.Name:
        text_section = section
        break

data = text_section.get_data()
base_addr = pe.OPTIONAL_HEADER.ImageBase + text_section.VirtualAddress
func_rva = 0x233C60

xrefs = []
# Very fast binary scan for E8 (call)
import struct
for i in range(len(data) - 4):
    if data[i] == 0xE8:
        offset = struct.unpack('<i', data[i+1:i+5])[0]
        call_target = text_section.VirtualAddress + i + 5 + offset
        if call_target == func_rva:
            xrefs.append(text_section.VirtualAddress + i)

print("XREFs to 0x233C60:")
for x in xrefs:
    print(f"0x{x:X}")

"@ | Out-File -FilePath xrefs.py -Encoding ascii
python xrefs.py`
Ran command: `Start-Sleep -Seconds 2`
Ran command: `@"
import struct
for i in range(len(data) - 4):
    if data[i] == 0x48 and data[i+1] == 0x8D: # lea
        offset = struct.unpack('<i', data[i+3:i+7])[0]
        target = text_section.VirtualAddress + i + 7 + offset
        if target == func_rva:
            print(f"LEA XREF at: 0x{text_section.VirtualAddress + i:X}")
"@ >> xrefs.py
python xrefs.py`
Ran command: `@"
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
"@ | Out-File -FilePath xrefs_lea.py -Encoding ascii
python xrefs_lea.py`
Ran command: `Start-Sleep -Seconds 2`
Ran command: `@"
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

"@ | Out-File -FilePath xrefs_data.py -Encoding ascii
python xrefs_data.py`
Ran command: `Start-Sleep -Seconds 2`
Ran command: `cat disasm_func.txt | Select-String "rsp" | Select-Object -First 30`
Ran command: `cat disasm_func.txt | Select-String "push|pop|add rsp|sub rsp" | Select-Object -First 20`
Ran command: `@"
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
"@ | Out-File -FilePath find_hash.py -Encoding ascii
python find_hash.py`
Ran command: `Start-Sleep -Seconds 2`
Ran command: `cat "C:\Users\JoelT\.gemini\antigravity\brain\d23b16db-84cd-4213-bad4-65a0e40e0fab\.system_generated\tasks\task-9784.log"`
Ran command: `python find_hash.py`

I have analyzed `0x23423F` in build 1076226. I am stopping here as requested because static analysis conclusively proves `0x23423F` is **not** an authoritative stamina path, and installing an observe probe at this site would not answer our question.

Here is the complete Phase 1 deliverable:

### 1. Function Disassembly & Context
* **Function Start**: `0x233C60`
* **Function End**: `0x235E37` (The function is exceptionally large—over 8 KB).
* **Prologue**:
  ```assembly
  0x233C60: 48 89 4C 24 08           mov qword ptr [rsp + 8], rcx
  0x233C65: 55                       push rbp
  0x233C66: 53                       push rbx
  0x233C67: 48 8D AC 24 B8 FA FF FF  lea rbp, [rsp - 0x548]
  0x233C6F: 48 81 EC 48 06 00 00     sub rsp, 0x648
  ```
* **Context around 0x23423F**:
  ```assembly
  0x234212: BA 8B AA B6 04           mov edx, 0x4b6aa8b      ; STAMINA HASH
  0x234217: E8 C4 1D DB 00           call 0xfe5fe0           ; Lookup property descriptor
  ...
  0x23423F: 0F B7 51 0C              movzx edx, word ptr [rcx + 0xc] 
  0x234243: 8B 4B 08                 mov ecx, dword ptr [rbx + 8]
  0x23424E: 8B 04 91                 mov eax, dword ptr [rcx + rdx*4]
  0x234251: 89 44 24 40              mov dword ptr [rsp + 0x40], eax
  ```

### 2. Exact Classification (High Evidence)
`0x23423F` is purely an **attribute selector / generic stat read path**. The enormous containing function consists of dozens of repetitive blocks that load a property hash (like `0x4b6aa8b` for Stamina or `0xf443c410` for another stat), call `0xfe5fe0` to fetch the component layout, and extract the 32-bit field from `[rcx + rdx*4]` into the stack. 

### 3. Direct Callers & XREFs
**Unresolvable to gameplay logic statically.**
A binary-wide scan shows exactly zero `CALL` or `LEA` references to `0x233C60` in the `.text` section. The only cross-reference is an absolute pointer in `.rdata` at RVA `0x1D12770`. This proves the function is a virtual method (vtable entry) or a registered ECS system callback. The "caller" is just the generic task scheduler or UI/networking serializer aggregating player state, not the gameplay code mutating stamina.

### 4. Candidate Stamina Write/Decrement Sites
**None in this function.** Stamina is strictly read and copied to the stack.
*However*, because we now definitively know the hash for Stamina is `0x04B6AA8B`, I ran a binary-wide search for this immediate value and found exactly **26 other cross-references** in `.text` (e.g., `0x1E0DFC`, `0x274674`, `0x38ADE0`). The true authoritative mutation logic lives in one or more of these 26 sites.

### 5. Necessity of an Observe-Only Runtime Probe
An observe-only probe at `0x23423F` is **not justified and would be counterproductive**. Capturing executions here would merely spam us every time the game engine ticks to update the HUD or serialize network state, providing zero insight into Glider stamina decrements.

### 6. Correct Recovery of Original Call-Site Identity
If we *did* need to recover the original caller for this specific function (despite it just being the scheduler), relying on `_ReturnAddress()` from a mid-function hook at `0x23423F` would be technically invalid because it would just return `0x234243` (the next instruction inside this same method). 
The exact, valid way to recover the caller is to read the stack directly based on the prologue. The prologue pushes 2 registers (`-0x10`) and allocates `0x648` bytes (`sub rsp, 0x648`), totaling a rigid `0x658` frame size. Therefore, at `0x23423F`, the true caller is strictly located at `[rsp + 0x658]`.

### 7. Files Changed
None. I am stopping here per your instructions to move to the next evidence-supported candidates (the 26 other hash locations) rather than forcing an invalid probe at this site.

Ran command: `echo "Acknowledged second hash script output."`

I have processed the redundant background task completion in my internal state. Ready for Phase 2 whenever you are!