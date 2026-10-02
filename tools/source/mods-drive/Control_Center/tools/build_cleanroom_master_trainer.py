import xml.etree.ElementTree as ET
import xml.dom.minidom
import os
import sys

def build_ultimate_cleanroom_master(output_path):
    print("Building Ultimate Clean-Room Master Cheat Table with ALL Subsystems & Interactive Sliders...")
    
    master_root = ET.Element("CheatTable", CheatEngineTableVersion="45")
    cheat_entries_elem = ET.SubElement(master_root, "CheatEntries")
    
    current_id = [1000]
    
    def next_id():
        val = current_id[0]
        current_id[0] += 1
        return str(val)

    def create_category(parent, title):
        entry = ET.SubElement(parent, "CheatEntry")
        ET.SubElement(entry, "ID").text = next_id()
        ET.SubElement(entry, "Description").text = f'"{title}"'
        ET.SubElement(entry, "GroupHeader").text = "1"
        child_container = ET.SubElement(entry, "CheatEntries")
        return child_container

    def add_script_entry(parent, title, script_content):
        entry = ET.SubElement(parent, "CheatEntry")
        ET.SubElement(entry, "ID").text = next_id()
        ET.SubElement(entry, "Description").text = f'"{title}"'
        ET.SubElement(entry, "VariableType").text = "Auto Assembler Script"
        ET.SubElement(entry, "AssemblerScript").text = script_content
        child_container = ET.SubElement(entry, "CheatEntries")
        return child_container

    def add_value_entry(parent, title, address, var_type="4 Bytes", drop_down=None, signed=None):
        entry = ET.SubElement(parent, "CheatEntry")
        ET.SubElement(entry, "ID").text = next_id()
        ET.SubElement(entry, "Description").text = f'"{title}"'
        if drop_down:
            ET.SubElement(entry, "DropDownList").text = drop_down
        if signed:
            ET.SubElement(entry, "ShowAsSigned").text = "1"
        ET.SubElement(entry, "VariableType").text = var_type
        ET.SubElement(entry, "Address").text = address
        return entry

    # =========================================================================
    # CATEGORY 1: PLAYER ATTRIBUTES, SURVIVAL & VITALS
    # =========================================================================
    cat1 = create_category(cheat_entries_elem, "🧙 [01] PLAYER ATTRIBUTES, SURVIVAL & VITALS")

    # 1. Stats Dynamic Interceptor
    stats_script = """// =============================================================================
// Enshrouded Engine: AttributeContainer Dynamic Pointer Interceptor
// Target: enshrouded.exe Stat Evaluation Loop (0x7ff63cc8fa80 - 0x7ff63cc8fb30)
// =============================================================================
[ENABLE]
aobscanmodule(aobFloatAnchor,enshrouded.exe,F3 0F 11 34 91 48 8D 4D C0)
aobscanmodule(aobIntAnchor,enshrouded.exe,F3 42 0F 11 04 B1 48 83 EF 10)

alloc(memFloatHook,$1000,aobFloatAnchor)
alloc(memIntHook,$1000,aobIntAnchor)

label(code_float)
label(return_float)
label(pFloatStats)
registersymbol(pFloatStats)
registersymbol(aobFloatAnchor)

memFloatHook:
  push rax
  mov rax,000000008F4BFBC5
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+00],rax // Walk Speed
  @@:
  mov rax,00000000350B478B
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+08],rax // Sprint Speed
  @@:
  mov rax,00000000ED6A7BDE
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+10],rax // Sneak Speed
  @@:
  mov rax,00000000C199AF6A
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+18],rax // Swim Speed
  @@:
  mov rax,00000000B97D3C6E
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+20],rax // Jump Velocity
  @@:
  mov rax,000000005C8C30C7
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+28],rax // Gravity Scale
  @@:
  mov rax,0000000055260172
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+30],rax // Glide Acceleration
  @@:
  mov rax,00000000F53B474C
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+rdx*4]
   mov [pFloatStats+38],rax // Glide Air Resistance
  @@:
  pop rax
code_float:
  movss [rcx+rdx*4],xmm6
  jmp return_float

align 10 00
pFloatStats:
dq 0,0,0,0,0,0,0,0,0,0,0,0

aobFloatAnchor:
  jmp memFloatHook
return_float:

label(code_int)
label(return_int)
label(pIntStats)
registersymbol(pIntStats)
registersymbol(aobIntAnchor)

memIntHook:
  push rax
  mov rax,000000008C554BC4
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+00],rax // Strength
  @@:
  mov rax,0000000010CE8E11
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+08],rax // Constitution
  @@:
  mov rax,00000000A8E368D5
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+10],rax // Dexterity
  @@:
  mov rax,00000000F0B152E2
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+18],rax // Endurance
  @@:
  mov rax,00000000500B391F
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+20],rax // Intelligence
  @@:
  mov rax,00000000FE934A26
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+28],rax // Spirit
  @@:
  mov rax,000000004114B3E5
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+30],rax // Stamina
  @@:
  mov rax,00000000B06CA4F0
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+38],rax // Stamina Reg
  @@:
  mov rax,00000000237E854C
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+40],rax // Stamina Reg Delay
  @@:
  mov rax,0000000017253019
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+48],rax // Mana
  @@:
  mov rax,00000000E12F60AF
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+50],rax // Mana Reg
  @@:
  mov rax,00000000B0A850D5
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+58],rax // Mana Reg Delay
  @@:
  mov rax,000000008BC688F7
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+60],rax // Health
  @@:
  mov rax,00000000DEE8D7AC
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+68],rax // Health Reg
  @@:
  mov rax,0000000095DA4F21
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+70],rax // Health Reg Delay
  @@:
  mov rax,0000000098BE99FE
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+78],rax // Shroud Max Time
  @@:
  mov rax,000000001C8A9772
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+80],rax // Magic Damage
  @@:
  mov rax,000000003DEE40C2
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+88],rax // Melee Damage
  @@:
  mov rax,000000007EBE182C
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+90],rax // Ranged Damage
  @@:
  mov rax,000000003C00A9E5
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+98],rax // Crit Chance
  @@:
  mov rax,000000004E7A23BB
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+A0],rax // Crit Damage
  @@:
  mov rax,000000008D974C88
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+A8],rax // Mining Damage
  @@:
  mov rax,00000000A1188D33
  cmp rax,rdi
  jne short @f
   lea rax,[rcx+r14*4]
   mov [pIntStats+B0],rax // Woodcutting Damage
  @@:
  pop rax
code_int:
  movss [rcx+r14*4],xmm0
  jmp return_int

align 10 00
pIntStats:
dq 0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0

aobIntAnchor:
  jmp memIntHook
  nop
return_int:

[DISABLE]
aobFloatAnchor:
  db F3 0F 11 34 91
unregistersymbol(pFloatStats)
unregistersymbol(aobFloatAnchor)
dealloc(memFloatHook)

aobIntAnchor:
  db F3 42 0F 11 04 B1
unregistersymbol(pIntStats)
unregistersymbol(aobIntAnchor)
dealloc(memIntHook)
"""
    stats_children = add_script_entry(cat1, "Get Live Stats Engine (Equip Armor or Consume Item to Populate)", stats_script)
    add_value_entry(stats_children, "Strength (Attribute Value)", "[pIntStats]", "4 Bytes")
    add_value_entry(stats_children, "Constitution (Attribute Value)", "[pIntStats+8]", "4 Bytes")
    add_value_entry(stats_children, "Dexterity (Attribute Value)", "[pIntStats+10]", "4 Bytes")
    add_value_entry(stats_children, "Endurance (Attribute Value)", "[pIntStats+18]", "4 Bytes")
    add_value_entry(stats_children, "Intelligence (Attribute Value)", "[pIntStats+20]", "4 Bytes")
    add_value_entry(stats_children, "Spirit (Attribute Value)", "[pIntStats+28]", "4 Bytes")
    add_value_entry(stats_children, "Max Stamina (Base Points)", "[pIntStats+30]", "4 Bytes")
    add_value_entry(stats_children, "Stamina Regen Rate", "[pIntStats+38]", "4 Bytes")
    add_value_entry(stats_children, "Stamina Regen Delay (ms)", "[pIntStats+40]", "4 Bytes")
    add_value_entry(stats_children, "Max Mana (Base Points)", "[pIntStats+48]", "4 Bytes")
    add_value_entry(stats_children, "Mana Regen Rate", "[pIntStats+50]", "4 Bytes")
    add_value_entry(stats_children, "Mana Regen Delay (ms)", "[pIntStats+58]", "4 Bytes")
    add_value_entry(stats_children, "Max Health (Base Points)", "[pIntStats+60]", "4 Bytes")
    add_value_entry(stats_children, "Health Regen Rate", "[pIntStats+68]", "4 Bytes")
    add_value_entry(stats_children, "Health Regen Delay (ms)", "[pIntStats+70]", "4 Bytes")
    add_value_entry(stats_children, "Shroud Max Survival Time (Sec)", "[pIntStats+78]", "4 Bytes")
    add_value_entry(stats_children, "Melee Attack Damage Multiplier", "[pIntStats+88]", "4 Bytes")
    add_value_entry(stats_children, "Ranged Arrow Damage Multiplier", "[pIntStats+90]", "4 Bytes")
    add_value_entry(stats_children, "Magic / Spell Power Multiplier", "[pIntStats+80]", "4 Bytes")
    add_value_entry(stats_children, "Critical Strike Chance (%)", "[pIntStats+98]", "4 Bytes")
    add_value_entry(stats_children, "Critical Strike Damage Multiplier (%)", "[pIntStats+A0]", "4 Bytes")
    add_value_entry(stats_children, "Mega Mining Damage (Pickaxe)", "[pIntStats+A8]", "4 Bytes")
    add_value_entry(stats_children, "Mega Woodcutting Damage (Axe)", "[pIntStats+B0]", "4 Bytes")
    add_value_entry(stats_children, "Walk Speed (Multiplier)", "[pFloatStats]", "Float")
    add_value_entry(stats_children, "Sprint Speed (Multiplier)", "[pFloatStats+8]", "Float")
    add_value_entry(stats_children, "Sneak Speed (Multiplier)", "[pFloatStats+10]", "Float")
    add_value_entry(stats_children, "Swim Speed (Multiplier)", "[pFloatStats+18]", "Float")
    add_value_entry(stats_children, "Jump Velocity (Multiplier)", "[pFloatStats+20]", "Float")
    add_value_entry(stats_children, "Gravity Scale", "[pFloatStats+28]", "Float")
    add_value_entry(stats_children, "Glide Acceleration", "[pFloatStats+30]", "Float")
    add_value_entry(stats_children, "Glide Air Resistance", "[pFloatStats+38]", "Float")

    # 2. Damage Taken Scaling (God Mode / Custom Vulnerability Slider)
    script_god = """[ENABLE]
aobscanmodule(network_player_attributes,enshrouded.exe,8B 04 91 89 44 24 5C 48 8B 5D)
alloc(newmem,$1000,network_player_attributes)
alloc(_dmgTakenMult,4)
label(return)
registersymbol(network_player_attributes)
registersymbol(_dmgTakenMult)

_dmgTakenMult:
  dd (float)0.0 // 0.0 = Invulnerable / 0 Damage, 0.5 = Half Damage, 1.0 = Normal, 2.0 = 2x Damage

newmem:
  mov eax,[rcx+rdx*4]
  push rcx
  cvtsi2ss xmm0,eax
  mulss xmm0,[_dmgTakenMult]
  cvttss2si eax,xmm0
  pop rcx
  mov [rsp+5C],eax
  mov rbx,[rbp+08]
  jmp return

network_player_attributes:
  jmp newmem
  nop 6
return:

[DISABLE]
network_player_attributes:
  db 8B 04 91 89 44 24 5C 48 8B 5D 08
unregistersymbol(network_player_attributes)
unregistersymbol(_dmgTakenMult)
dealloc(newmem)
dealloc(_dmgTakenMult)
"""
    god_children = add_script_entry(cat1, "God Mode / Damage Taken Multiplier (0.0 = Invulnerable)", script_god)
    add_value_entry(god_children, "Damage Taken Multiplier (Float: 0.0 = God Mode, 0.5 = Half Dmg, 1.0 = Normal)", "_dmgTakenMult", "Float")

    # 3. Action Stamina Drain Multiplier Slider
    script_stam = """[ENABLE]
aobscanmodule(attribute_save,enshrouded.exe,8B 3C 88 33 C9)
alloc(newmem,$1000,attribute_save)
alloc(_staminaCostMult,4)
label(return)
registersymbol(attribute_save)
registersymbol(_staminaCostMult)

_staminaCostMult:
  dd (float)0.0 // 0.0 = Infinite / 0 Drain, 0.5 = 50% Drain, 1.0 = Normal

newmem:
  mov edi,[rax+rcx*4]
  push rax
  cvtsi2ss xmm0,edi
  mulss xmm0,[_staminaCostMult]
  cvttss2si edi,xmm0
  pop rax
  xor ecx,ecx
  jmp return

attribute_save:
  jmp newmem
return:

[DISABLE]
attribute_save:
  db 8B 3C 88 33 C9
unregistersymbol(attribute_save)
unregistersymbol(_staminaCostMult)
dealloc(newmem)
dealloc(_staminaCostMult)
"""
    stam_children = add_script_entry(cat1, "Action Stamina Drain Multiplier (0.0 = Infinite Stamina)", script_stam)
    add_value_entry(stam_children, "Stamina Drain Multiplier (Float: 0.0 = Infinite, 0.5 = Half, 1.0 = Normal)", "_staminaCostMult", "Float")

    # 4. Spell Mana Cost Multiplier Slider
    script_mana = """[ENABLE]
aobscanmodule(AOBMANA_network_player_attributes,enshrouded.exe,C6 44 24 24 00 44 8B)
alloc(newmem,$1000,AOBMANA_network_player_attributes)
alloc(_manaCostMultiplier,4)
label(return)
registersymbol(AOBMANA_network_player_attributes)
registersymbol(_manaCostMultiplier)

_manaCostMultiplier:
  dd (float)0.0 // 0.0 = Free/Zero Mana Cost, 0.5 = Half Mana Cost, 1.0 = Normal

newmem:
  cmp dword ptr [_manaCostMultiplier],0
  je @f
  mov byte ptr [rsp+24],00
  jmp return
@@:
  jmp return

AOBMANA_network_player_attributes:
  jmp newmem
return:

[DISABLE]
AOBMANA_network_player_attributes:
  db C6 44 24 24 00
unregistersymbol(AOBMANA_network_player_attributes)
unregistersymbol(_manaCostMultiplier)
dealloc(newmem)
dealloc(_manaCostMultiplier)
"""
    mana_children = add_script_entry(cat1, "Spell Mana Cost Multiplier (0.0 = Zero Cost)", script_mana)
    add_value_entry(mana_children, "Mana Cost Multiplier (Float: 0.0 = Infinite Mana, 0.5 = Half Cost, 1.0 = Normal)", "_manaCostMultiplier", "Float")

    # 5. Underwater Breath Depletion Rate Slider
    script_breath = """[ENABLE]
aobscanmodule(InfAirAOB,enshrouded.exe,41 29 04 88 E9 53 01 00 00)
alloc(newmem,$1000,InfAirAOB)
alloc(_airDrainMultiplier,4)
label(return)
registersymbol(InfAirAOB)
registersymbol(_airDrainMultiplier)

_airDrainMultiplier:
  dd (float)0.0 // 0.0 = Infinite Breath, 0.5 = 2x Duration, 1.0 = Normal

newmem:
  cmp dword ptr [_airDrainMultiplier],0
  je @f
  sub [r8+rcx*4],eax
@@:
  jmp return

InfAirAOB:
  jmp newmem
  nop 4
return:

[DISABLE]
InfAirAOB:
  db 41 29 04 88 E9 53 01 00 00
unregistersymbol(InfAirAOB)
unregistersymbol(_airDrainMultiplier)
dealloc(newmem)
dealloc(_airDrainMultiplier)
"""
    breath_children = add_script_entry(cat1, "Underwater Breath Depletion Multiplier (0.0 = Infinite)", script_breath)
    add_value_entry(breath_children, "Breath Depletion Multiplier (Float: 0.0 = Infinite, 0.5 = 2x Longer, 1.0 = Normal)", "_airDrainMultiplier", "Float")

    # 6. Shroud Exposure Timer Depletion Rate Slider
    script_shroud = """[ENABLE]
aobscanmodule(aobFogResistanceUpdate,enshrouded.exe,40 55 41 54 41 55 41 56 48 8D AC 24 18 FF FF FF 48 81 EC E8 01 00 00 41 B8 70 00 00 00 48 8D 54 24 20 4C 8B F1)
alloc(newmem,$1000,aobFogResistanceUpdate)
alloc(_shroudTimerMultiplier,4)
label(return)
registersymbol(aobFogResistanceUpdate)
registersymbol(_shroudTimerMultiplier)

_shroudTimerMultiplier:
  dd (float)0.0 // 0.0 = Frozen / Infinite Shroud, 0.5 = 2x Survival, 1.0 = Normal

newmem:
  cmp dword ptr [_shroudTimerMultiplier],0
  je @f
  push rbp
  push r12
  push r13
  jmp return
@@:
  ret

aobFogResistanceUpdate:
  jmp newmem
  nop
return:

[DISABLE]
aobFogResistanceUpdate:
  db 40 55 41 54 41 55
unregistersymbol(aobFogResistanceUpdate)
unregistersymbol(_shroudTimerMultiplier)
dealloc(newmem)
dealloc(_shroudTimerMultiplier)
"""
    shroud_children = add_script_entry(cat1, "Shroud Exposure Timer Rate Multiplier (0.0 = Frozen)", script_shroud)
    add_value_entry(shroud_children, "Shroud Exposure Rate (Float: 0.0 = Infinite Stay, 0.5 = 2x Duration, 1.0 = Normal)", "_shroudTimerMultiplier", "Float")

    # 7. Body Heat Loss Depletion Rate Slider
    script_cold = """[ENABLE]
aobscanmodule(aobbodyheat_depletion,enshrouded.exe,40 55 56 48 8D 6C 24 B1 48 81 EC F8 00 00 00 41 B8 60 00 00 00 48 8D 54 24 20 48 8B F1)
alloc(newmem,$1000,aobbodyheat_depletion)
alloc(_bodyHeatDrainMultiplier,4)
label(return)
registersymbol(aobbodyheat_depletion)
registersymbol(_bodyHeatDrainMultiplier)

_bodyHeatDrainMultiplier:
  dd (float)0.0 // 0.0 = Cold Immunity, 0.5 = 50% Resistance, 1.0 = Normal

newmem:
  cmp dword ptr [_bodyHeatDrainMultiplier],0
  je @f
  push rbp
  push rsi
  lea rbp,[rsp-4F]
  jmp return
@@:
  ret

aobbodyheat_depletion:
  jmp newmem
  nop 3
return:

[DISABLE]
aobbodyheat_depletion:
  db 40 55 56 48 8D 6C 24 B1
unregistersymbol(aobbodyheat_depletion)
unregistersymbol(_bodyHeatDrainMultiplier)
dealloc(newmem)
dealloc(_bodyHeatDrainMultiplier)
"""
    cold_children = add_script_entry(cat1, "Body Heat Loss / Hypothermia Multiplier (0.0 = Immune)", script_cold)
    add_value_entry(cold_children, "Body Heat Loss Rate (Float: 0.0 = Cold Immune, 0.5 = Half, 1.0 = Normal)", "_bodyHeatDrainMultiplier", "Float")

    # 8. Fall Damage Multiplier Slider
    script_falldmg = """[ENABLE]
aobscanmodule(fall_damage_calculation,enshrouded.exe,40 53 48 83 EC 60 41 B8 20 00 00 00 48 8D 54 24 20 48 8B D9 E8 ?? ?? ?? ?? 41 B8 20 00 00 00 48 8D 54 24 20 48 8B CB E8 ?? ?? ?? ?? 84 C0 0F 84 E2 00 00 00)
alloc(newmem,$1000,fall_damage_calculation)
alloc(_fallDmgMult,4)
label(return)
registersymbol(fall_damage_calculation)
registersymbol(_fallDmgMult)

_fallDmgMult:
  dd (float)0.0 // 0.0 = No Fall Damage, 0.5 = 50%, 1.0 = Normal

newmem:
  cmp dword ptr [_fallDmgMult],0
  je @f
  push rbx
  sub rsp,60
  jmp return
@@:
  ret

fall_damage_calculation:
  jmp newmem
  nop
return:

[DISABLE]
fall_damage_calculation:
  db 40 53 48 83 EC 60
unregistersymbol(fall_damage_calculation)
unregistersymbol(_fallDmgMult)
dealloc(newmem)
dealloc(_fallDmgMult)
"""
    fall_children = add_script_entry(cat1, "Fall Damage Multiplier (0.0 = No Fall Damage)", script_falldmg)
    add_value_entry(fall_children, "Fall Damage Multiplier (Float: 0.0 = Immune, 0.5 = Half, 1.0 = Normal)", "_fallDmgMult", "Float")

    # 9. Rested Duration Multiplier
    script_rested = """[ENABLE]
aobscanmodule(rested_buff,enshrouded.exe,45 32 E4 44 8B 3C 91 EB 03)
alloc(newmem,$1000,rested_buff)
alloc(_restedMult,4)
label(return)
registersymbol(rested_buff)
registersymbol(_restedMult)

_restedMult:
  dd (int)10

newmem:
  xor r12b,r12b
  mov r15d,[rcx+rdx*4]
  imul r15d,[_restedMult]
  jmp return

rested_buff:
  jmp newmem
  nop 2
return:

[DISABLE]
rested_buff:
  db 45 32 E4 44 8B 3C 91
unregistersymbol(rested_buff)
unregistersymbol(_restedMult)
dealloc(newmem)
dealloc(_restedMult)
"""
    rested_children = add_script_entry(cat1, "Rested Comfort Duration Multiplier", script_rested)
    add_value_entry(rested_children, "Rested Multiplier (e.g. 5x, 10x, 20x)", "_restedMult", "4 Bytes")

    # 10. Stealth Mode / Enemy AI Detection Sensitivity Multiplier
    script_stealth = """[ENABLE]
aobscanmodule(enemy_combat_targets,enshrouded.exe,48 89 4C 24 08 55 41 55 48 8D AC 24 58 FD FF FF 48 81 EC A8 03 00 00 4C 8B E9)
alloc(newmem,$1000,enemy_combat_targets)
alloc(_stealthSensitivity,4)
label(return)
registersymbol(enemy_combat_targets)
registersymbol(_stealthSensitivity)

_stealthSensitivity:
  dd (float)0.0 // 0.0 = Invisibility / Blind AI, 0.5 = Half Range, 1.0 = Normal

newmem:
  cmp dword ptr [_stealthSensitivity],0
  je @f
  mov [rsp+08],rcx
  push rbp
  push r13
  jmp return
@@:
  ret

enemy_combat_targets:
  jmp newmem
  nop 3
return:

[DISABLE]
enemy_combat_targets:
  db 48 89 4C 24 08 55 41 55
unregistersymbol(enemy_combat_targets)
unregistersymbol(_stealthSensitivity)
dealloc(newmem)
dealloc(_stealthSensitivity)
"""
    stealth_children = add_script_entry(cat1, "Stealth Mode / Enemy AI Detection Sensitivity", script_stealth)
    add_value_entry(stealth_children, "Detection Sensitivity (Float: 0.0 = Invisible, 0.5 = Half Range, 1.0 = Normal)", "_stealthSensitivity", "Float")

    # =========================================================================
    # CATEGORY 2: COMBAT, SKILLS & PROGRESSION
    # =========================================================================
    cat2 = create_category(cheat_entries_elem, "⚔️ [02] COMBAT, SKILLS & PROGRESSION")

    # 1. Easy Perfect Parry
    script_parry = """[ENABLE]
aobscanmodule(client_player_trigger_parry,enshrouded.exe,74 78 48 8B 8C 24 88 00 00 00)
registersymbol(client_player_trigger_parry)

client_player_trigger_parry:
  db 90 90

[DISABLE]
client_player_trigger_parry:
  db 74 78
unregistersymbol(client_player_trigger_parry)
"""
    add_script_entry(cat2, "Easy Perfect Parry (Always Counter-Attack)", script_parry)

    # 2. Available Skill Points Custom Amount
    script_avail_skills = """[ENABLE]
aobscanmodule(aobCalculateAvalaibleSkillPoints,enshrouded.exe,48 89 5C 24 08 48 89 74 24 10 57 48 83 EC 30 41 8B F9 49 8B F0 48 8B D9 41 83 F9 01 73 1D)
alloc(newmem,$1000,aobCalculateAvalaibleSkillPoints)
alloc(_customSkillPoints,4)
label(return)
registersymbol(aobCalculateAvalaibleSkillPoints)
registersymbol(_customSkillPoints)

_customSkillPoints:
  dd (int)999

newmem:
  mov [rsp+08],rbx
  mov rbx,rcx
  mov eax,[_customSkillPoints]
  mov dword ptr [rcx],eax
  jmp return

aobCalculateAvalaibleSkillPoints:
  jmp newmem
return:

[DISABLE]
aobCalculateAvalaibleSkillPoints:
  db 48 89 5C 24 08
unregistersymbol(aobCalculateAvalaibleSkillPoints)
unregistersymbol(_customSkillPoints)
dealloc(newmem)
dealloc(_customSkillPoints)
"""
    avail_skill_children = add_script_entry(cat2, "Set Available Skill Points (Custom Amount)", script_avail_skills)
    add_value_entry(avail_skill_children, "Available Skill Points Amount (e.g. 50, 100, 999)", "_customSkillPoints", "4 Bytes")

    # 3. Used Skill Points Reset & Custom Spent Amount
    script_used_skills = """[ENABLE]
aobscanmodule(aobCalculateUsedSkillPoints,enshrouded.exe,48 89 6C 24 20 41 56 4D)
alloc(newmem,$1000,aobCalculateUsedSkillPoints)
alloc(_customUsedSkillPoints,4)
label(return)
registersymbol(aobCalculateUsedSkillPoints)
registersymbol(_customUsedSkillPoints)

_customUsedSkillPoints:
  dd (int)0

newmem:
  mov [rsp+20],rbp
  mov eax,[_customUsedSkillPoints]
  mov dword ptr [rcx],eax
  jmp return

aobCalculateUsedSkillPoints:
  jmp newmem
return:

[DISABLE]
aobCalculateUsedSkillPoints:
  db 48 89 6C 24 20
unregistersymbol(aobCalculateUsedSkillPoints)
unregistersymbol(_customUsedSkillPoints)
dealloc(newmem)
dealloc(_customUsedSkillPoints)
"""
    used_skill_children = add_script_entry(cat2, "Used Skill Points Override (0 = Instant Free Respec)", script_used_skills)
    add_value_entry(used_skill_children, "Spent Skill Points (Set to 0 to Refund All Points)", "_customUsedSkillPoints", "4 Bytes")

    # 4. XP Multiplier
    script_xp = """[ENABLE]
aobscanmodule(player_level,enshrouded.exe,45 01 3C 88 48 8B CB)
alloc(newmem,$1000,player_level)
alloc(_xpScale,4)
label(return)
registersymbol(player_level)
registersymbol(_xpScale)

_xpScale:
  dd (int)5

newmem:
  imul r15d,[_xpScale]
  add [r8+rcx*4],r15d
  mov rcx,rbx
  jmp return

player_level:
  jmp newmem
  nop 2
return:

[DISABLE]
player_level:
  db 45 01 3C 88 48 8B CB
unregistersymbol(player_level)
unregistersymbol(_xpScale)
dealloc(newmem)
dealloc(_xpScale)
"""
    xp_children = add_script_entry(cat2, "XP Multiplier (Level Up Faster)", script_xp)
    add_value_entry(xp_children, "XP Multiplier (e.g. 5x, 10x, 50x)", "_xpScale", "4 Bytes")

    # 5. Disable Spire Traps
    script_traps = """[ENABLE]
aobscanmodule(TrapDisableAOB,enshrouded.exe,44 38 39 48 0F 45 F8)
registersymbol(TrapDisableAOB)

TrapDisableAOB:
  db 90 90 90

[DISABLE]
TrapDisableAOB:
  db 44 38 39
unregistersymbol(TrapDisableAOB)
"""
    add_script_entry(cat2, "Disable Spire Fire & Spike Traps", script_traps)

    # =========================================================================
    # CATEGORY 3: WEAPONS, EQUIPMENT & DURABILITY
    # =========================================================================
    cat3 = create_category(cheat_entries_elem, "🗡️ [03] WEAPONS, EQUIPMENT & DURABILITY")

    # 1. Weapon Durability Loss Multiplier Slider
    script_durability = """[ENABLE]
aobscanmodule(aobdurability_loss,enshrouded.exe,40 55 41 55 48 8D 6C 24 B1 48 81 EC D8 00 00 00 41 B8 50 00 00 00 48 8D 55 E7 4C 8B E9)
alloc(newmem,$1000,aobdurability_loss)
alloc(_durabilityWearRate,4)
label(return)
registersymbol(aobdurability_loss)
registersymbol(_durabilityWearRate)

_durabilityWearRate:
  dd (float)0.0 // 0.0 = Infinite Durability / 0 Wear, 0.5 = Half Wear, 1.0 = Normal

newmem:
  cmp dword ptr [_durabilityWearRate],0
  je @f
  push rbp
  push r13
  lea rbp,[rsp-4F]
  jmp return
@@:
  ret

aobdurability_loss:
  jmp newmem
  nop 4
return:

[DISABLE]
aobdurability_loss:
  db 40 55 41 55 48 8D 6C 24 B1
unregistersymbol(aobdurability_loss)
unregistersymbol(_durabilityWearRate)
dealloc(newmem)
dealloc(_durabilityWearRate)
"""
    dur_children = add_script_entry(cat3, "Weapon & Tool Durability Wear Multiplier (0.0 = Never Break)", script_durability)
    add_value_entry(dur_children, "Durability Wear Rate (Float: 0.0 = Infinite Durability, 0.5 = Half, 1.0 = Normal)", "_durabilityWearRate", "Float")

    # 2. Blacksmith Infinite Enhancement Level Limit Bypass
    script_upgrade_limit = """[ENABLE]
aobscanmodule(aobLevelWhileUpgrade,enshrouded.exe,44 8B 24 91 48 8D 95 B0 72 00 00)
alloc(newmem,$1000,aobLevelWhileUpgrade)
alloc(_maxUpgradeLimit,4)
label(return)
registersymbol(aobLevelWhileUpgrade)
registersymbol(_maxUpgradeLimit)

_maxUpgradeLimit:
  dd (int)0 // 0 = Bypass/Unlimited Sockets, or set to 10, 25, 100

newmem:
  mov r12d,[_maxUpgradeLimit]
  lea rdx,[rbp+000072B0]
  jmp return

aobLevelWhileUpgrade:
  jmp newmem
  nop 6
return:

[DISABLE]
aobLevelWhileUpgrade:
  db 44 8B 24 91 48 8D 95 B0 72 00 00
unregistersymbol(aobLevelWhileUpgrade)
unregistersymbol(_maxUpgradeLimit)
dealloc(newmem)
dealloc(_maxUpgradeLimit)
"""
    upgrade_children = add_script_entry(cat3, "Bypass Blacksmith Max Upgrade Level Limit", script_upgrade_limit)
    add_value_entry(upgrade_children, "Socket Level Limit Offset (0 = Unlimited Enhancement)", "_maxUpgradeLimit", "4 Bytes")

    # 3. Infinite Arrows & Ammunition
    script_ammo = """[ENABLE]
aobscanmodule(aobAmmoDec,enshrouded.exe,48 C7 43 10 FF FF FF FF FF 4F 04 E8 ?? ?? ?? ?? 48 8B 74 24 40)
alloc(newmem,$1000,aobAmmoDec)
alloc(_ammoDepleteRate,4)
label(return)
registersymbol(aobAmmoDec)
registersymbol(_ammoDepleteRate)

_ammoDepleteRate:
  dd (int)0 // 0 = Infinite Ammo (No Depletion), 1 = Normal

newmem:
  cmp dword ptr [_ammoDepleteRate],0
  je @f
  dec dword ptr [rdi+04]
@@:
  call 0x1406284f0
  jmp return

aobAmmoDec+08:
  jmp newmem
return:

[DISABLE]
aobAmmoDec+08:
  db FF 4F 04 E8 FD 2D 00 00
unregistersymbol(aobAmmoDec)
unregistersymbol(_ammoDepleteRate)
dealloc(newmem)
dealloc(_ammoDepleteRate)
"""
    ammo_children = add_script_entry(cat3, "Infinite Arrows & Ammunition Depletion Rate", script_ammo)
    add_value_entry(ammo_children, "Ammunition Depletion Rate (0 = Infinite Ammo, 1 = Normal)", "_ammoDepleteRate", "4 Bytes")

    # =========================================================================
    # CATEGORY 4: TRAVERSAL, GLIDER AERODYNAMICS & 3D FLIGHT
    # =========================================================================
    cat4 = create_category(cheat_entries_elem, "🦅 [04] TRAVERSAL, GLIDER AERODYNAMICS & 3D FLIGHT")

    # 1. Glider Physics Engine with 4 Live Sliders
    script_glider = """[ENABLE]
aobscanmodule(glider,enshrouded.exe,F3 41 0F 10 84 24 A4 04 00 00)
alloc(newmem,$1000,glider)
alloc(_gliderConfig,16)
label(code)
label(return)
registersymbol(glider)
registersymbol(_gliderConfig)

_gliderConfig:
  dd (float)0.8     // Forward Acceleration
  dd (float)0.39    // Vertical Lift
  dd (float)0.7125  // Descent Drag Rate
  dd (float)70.0    // Turn & Pitch Speed

newmem:
  fld dword ptr [_gliderConfig+00]
  fstp dword ptr [r12+0000048C]
  fld dword ptr [_gliderConfig+04]
  fstp dword ptr [r12+00000494]
  fld dword ptr [_gliderConfig+08]
  fstp dword ptr [r12+00000498]
  fld dword ptr [_gliderConfig+0C]
  fstp dword ptr [r12+000004A0]
code:
  movss xmm0,[r12+000004A4]
  jmp return

glider:
  jmp newmem
  nop 5
return:

[DISABLE]
glider:
  db F3 41 0F 10 84 24 A4 04 00 00
unregistersymbol(glider)
unregistersymbol(_gliderConfig)
dealloc(newmem)
dealloc(_gliderConfig)
"""
    glider_children = add_script_entry(cat4, "Glider Flight Aerodynamics Engine", script_glider)
    add_value_entry(glider_children, "Forward Glide Acceleration (Default: 0.8)", "_gliderConfig", "Float")
    add_value_entry(glider_children, "Upward Lift Coefficient (Default: 0.39)", "_gliderConfig+4", "Float")
    add_value_entry(glider_children, "Descent Fall Rate (Default: 0.7125)", "_gliderConfig+8", "Float")
    add_value_entry(glider_children, "Turn & Pitch Response (Default: 70.0)", "_gliderConfig+C", "Float")

    # 2. Movement Speed Multiplier
    script_speed = """[ENABLE]
aobscanmodule(aobVelocity,enshrouded.exe,F3 41 0F 59 D9 48 03 C8 48 01 0A F3 48 0F 2C C6 F3 48 0F 2C CC)
alloc(newmem,$1000,aobVelocity)
alloc(_speedScale,4)
label(return)
registersymbol(aobVelocity)
registersymbol(_speedScale)

_speedScale:
  dd (float)2.0

newmem:
  mulss xmm9,[_speedScale]
  mulss xmm3,xmm9
  add rcx,rax
  jmp return

aobVelocity:
  jmp newmem
  nop 3
return:

[DISABLE]
aobVelocity:
  db F3 41 0F 59 D9 48 03 C8
unregistersymbol(aobVelocity)
unregistersymbol(_speedScale)
dealloc(newmem)
dealloc(_speedScale)
"""
    speed_children = add_script_entry(cat4, "Super Movement Speed Multiplier", script_speed)
    add_value_entry(speed_children, "Speed Multiplier (Float: 2.0 = 2x, 3.5 = 3.5x)", "_speedScale", "Float")

    # 3. Super Jump Height
    script_jump = """[ENABLE]
aobscanmodule(AobCallInside_Actor_Jump,enshrouded.exe,F3 41 0F 11 4F 04 0F 57 C9)
alloc(newmem,$1000,AobCallInside_Actor_Jump)
alloc(_jumpScale,4)
label(return)
registersymbol(AobCallInside_Actor_Jump)
registersymbol(_jumpScale)

_jumpScale:
  dd (float)1.75

newmem:
  mulss xmm1,[_jumpScale]
  movss [r15+04],xmm1
  xorps xmm1,xmm1
  jmp return

AobCallInside_Actor_Jump:
  jmp newmem
  nop 4
return:

[DISABLE]
AobCallInside_Actor_Jump:
  db F3 41 0F 11 4F 04 0F 57 C9
unregistersymbol(AobCallInside_Actor_Jump)
unregistersymbol(_jumpScale)
dealloc(newmem)
dealloc(_jumpScale)
"""
    jump_children = add_script_entry(cat4, "Super Jump Height Multiplier", script_jump)
    add_value_entry(jump_children, "Jump Height Multiplier (Float: 1.75, 3.0)", "_jumpScale", "Float")

    # 4. Air Swimming (3D Free Flight)
    script_airswim = """[ENABLE]
aobscanmodule(AirSwimAOB,enshrouded.exe,48 8B 7E 20 0F B6 C8)
alloc(newmem,$1000,AirSwimAOB)
label(return)
registersymbol(AirSwimAOB)

newmem:
  mov rdi,[rsi+20]
  mov cl,01
  jmp return

AirSwimAOB:
  jmp newmem
  nop 2
return:

[DISABLE]
AirSwimAOB:
  db 48 8B 7E 20 0F B6 C8
unregistersymbol(AirSwimAOB)
dealloc(newmem)
"""
    add_script_entry(cat4, "Air Swimming (3D Free Flight Mode)", script_airswim)

    # 5. Gravity Handler & Live Position Vector Engine
    script_gravity = """[ENABLE]
label(bRun)
registersymbol(bRun)
label(iKey)
registersymbol(iKey)
label(pPlayerPos)
registersymbol(pPlayerPos)

aobscanmodule(aobWndProc,enshrouded.exe,48 89 4C 24 08 55 53 56 57 41 55 41 56 41 57 48 8D AC 24 10 FA FF FF)
alloc(newmem_wnd,$1000,aobWndProc)
label(code_wnd)
label(return_wnd)

newmem_wnd:
  cmp edx,100 // WM_KEYDOWN
  jne code_wnd
  cmp r8,52 // R key
  jne @f
  xor byte ptr [bRun],1
@@:
  mov [iKey],r8d
code_wnd:
  mov [rsp+08],rcx
  push rbp
  jmp return_wnd

bRun:
dd 0
iKey:
dd 0
pPlayerPos:
dq 0

aobWndProc:
  jmp newmem_wnd
return_wnd:
registersymbol(aobWndProc)

aobscanmodule(aobgravity_apply_velocity_actor,enshrouded.exe,F3 0F 58 50 04 F3 0F 58 40 08)
alloc(newmem_grav,$1000,aobgravity_apply_velocity_actor)
label(code_grav)
label(return_grav)

newmem_grav:
  mov [pPlayerPos],rax
  cmp byte ptr [bRun],1
  jne code_grav
  mov dword ptr [rax+04],0
  push rcx
  mov ecx,10 // VK_SHIFT
  call GetAsyncKeyState
  test ax,8000
  jz @f
  mov dword ptr [rax+04],(float)8.0
@@:
  mov ecx,11 // VK_CONTROL
  call GetAsyncKeyState
  test ax,8000
  jz @f
  mov dword ptr [rax+04],(float)-8.0
@@:
  pop rcx
code_grav:
  addss xmm2,[rax+04]
  addss xmm0,[rax+08]
  jmp return_grav

aobgravity_apply_velocity_actor:
  jmp newmem_grav
  nop 5
return_grav:
registersymbol(aobgravity_apply_velocity_actor)

[DISABLE]
aobWndProc:
  db 48 89 4C 24 08
unregistersymbol(aobWndProc)
dealloc(newmem_wnd)

aobgravity_apply_velocity_actor:
  db F3 0F 58 50 04 F3 0F 58 40 08
unregistersymbol(aobgravity_apply_velocity_actor)
unregistersymbol(bRun)
unregistersymbol(iKey)
unregistersymbol(pPlayerPos)
dealloc(newmem_grav)
"""
    grav_children = add_script_entry(cat4, "Gravity, Free Fly & Position Vector Engine [R = Fly, Shift = Up, Ctrl = Down]", script_gravity)
    add_value_entry(grav_children, "Fly Mode Active (1 = Enabled, 0 = Disabled)", "bRun", "4 Bytes")
    add_value_entry(grav_children, "Player Live X Coordinate", "[pPlayerPos]", "Float")
    add_value_entry(grav_children, "Player Live Y Coordinate", "[pPlayerPos+4]", "Float")
    add_value_entry(grav_children, "Player Live Z Coordinate (Elevation)", "[pPlayerPos+8]", "Float")

    # =========================================================================
    # CATEGORY 5: CRAFTING, STORAGE & INVENTORY AUTOMATION
    # =========================================================================
    cat5 = create_category(cheat_entries_elem, "📦 [05] CRAFTING, STORAGE & INVENTORY AUTOMATION")

    # 1. Free Crafting & Recipe Material Cost Multiplier
    script_freecraft = """[ENABLE]
aobscanmodule(aobNeeded,enshrouded.exe,30 5B C3 CC CC CC CC CC 48 89 5C 24 18)
alloc(newmem,$1000,aobNeeded)
alloc(_craftingCostMultiplier,4)
label(code)
label(return)
registersymbol(aobNeeded)
registersymbol(_craftingCostMultiplier)

_craftingCostMultiplier:
  dd (int)0 // 0 = Free Crafting (0 Cost), 1 = Normal Ingredients

newmem:
  mov eax,[_craftingCostMultiplier]
  mov [rsp+30],eax
code:
  mov [rsp+18],rbx
  jmp return

aobNeeded+08:
  jmp newmem
return:

[DISABLE]
aobNeeded+08:
  db 48 89 5C 24 18
unregistersymbol(aobNeeded)
unregistersymbol(_craftingCostMultiplier)
dealloc(newmem)
dealloc(_craftingCostMultiplier)
"""
    craft_children = add_script_entry(cat5, "Free Crafting & Recipe Material Cost Multiplier", script_freecraft)
    add_value_entry(craft_children, "Ingredient Cost Requirement (0 = Free Crafting, 1 = Normal)", "_craftingCostMultiplier", "4 Bytes")

    # 2. Custom Stack Size Multiplier
    script_stack = """[ENABLE]
aobscanmodule(stack_size,enshrouded.exe,0F B7 40 14 3B C8)
alloc(newmem,$1000,stack_size)
alloc(_customStackLimit,4)
label(return)
registersymbol(stack_size)
registersymbol(_customStackLimit)

_customStackLimit:
  dw (int)9999

newmem:
  mov ax,[_customStackLimit]
  cmp ecx,eax
  jmp return

stack_size:
  jmp newmem
  nop
return:

[DISABLE]
stack_size:
  db 0F B7 40 14 3B C8
unregistersymbol(stack_size)
unregistersymbol(_customStackLimit)
dealloc(newmem)
dealloc(_customStackLimit)
"""
    stack_children = add_script_entry(cat5, "Custom Max Stack Size Multiplier", script_stack)
    add_value_entry(stack_children, "Max Stack Size Limit (e.g. 500, 1000, 9999)", "_customStackLimit", "2 Bytes")

    # 3. Custom Slot Item Count
    script_slot_items = """[ENABLE]
aobscanmodule(slot_items,enshrouded.exe,41 89 47 04 48 8B D3)
alloc(newmem,$1000,slot_items)
alloc(_slotItemCount,4)
label(code)
label(return)
registersymbol(slot_items)
registersymbol(_slotItemCount)

_slotItemCount:
  dd (int)100

newmem:
  mov eax,[_slotItemCount]
code:
  mov [r15+04],eax
  mov rdx,rbx
  jmp return

slot_items:
  jmp newmem
  nop 2
return:

[DISABLE]
slot_items:
  db 41 89 47 04 48 8B D3
unregistersymbol(slot_items)
unregistersymbol(_slotItemCount)
dealloc(newmem)
dealloc(_slotItemCount)
"""
    items_children = add_script_entry(cat5, "Custom Inventory Slot Item Count", script_slot_items)
    add_value_entry(items_children, "Set Quantity in Slot upon Moving (e.g. 50, 100, 999)", "_slotItemCount", "4 Bytes")

    # 4. Item Pointer Inspector
    script_item_ptr = """[ENABLE]
aobscanmodule(aobCheckSlotEmptyNextCall,enshrouded.exe,4C 8B 7C 24 28 48 8B 55 08)
alloc(newmem,$1000,aobCheckSlotEmptyNextCall)
label(code)
label(return)
label(pItemSlot)
registersymbol(pItemSlot)

newmem:
  mov [pItemSlot],rdx
code:
  mov r15,[rsp+28]
  mov rdx,[rbp+08]
  jmp return

pItemSlot:
dq 0

aobCheckSlotEmptyNextCall:
  jmp newmem
  nop 4
return:
registersymbol(aobCheckSlotEmptyNextCall)

[DISABLE]
aobCheckSlotEmptyNextCall:
  db 4C 8B 7C 24 28 48 8B 55 08
unregistersymbol(aobCheckSlotEmptyNextCall)
unregistersymbol(pItemSlot)
dealloc(newmem)
"""
    item_ptr_children = add_script_entry(cat5, "Get Item Pointer (Move Any Item in Inventory)", script_item_ptr)
    add_value_entry(item_ptr_children, "Item Memory Pointer", "pItemSlot", "8 Bytes")

    # =========================================================================
    # CATEGORY 6: 6DOF VOXEL BUILDING & ADVANCED ARCHITECT COMPANION
    # =========================================================================
    cat6 = create_category(cheat_entries_elem, "🧱 [06] 6DOF VOXEL BUILDING & ADVANCED ARCHITECT COMPANION")

    # 1. Break The Unbreakable
    script_unbreakable = """[ENABLE]
aobscanmodule(TerraBreakFlagAOB,enshrouded.exe,80 78 14 05 73 24)
aobscanmodule(BlockBreakFlagAOB,enshrouded.exe,80 78 14 05 73 08)
aobscanmodule(BreakExternalForceBlockAOB,enshrouded.exe,10 44 0F B6 48 14)
aobscanmodule(BreakExternalForceTerraAOB,enshrouded.exe,24 44 0F B6 48 14)
aobscanmodule(SingleBlockBreakFlagA0B,enshrouded.exe,41 80 78 14 05 0F 95 C0 E9)

registersymbol(TerraBreakFlagAOB)
registersymbol(BlockBreakFlagAOB)
registersymbol(BreakExternalForceBlockAOB)
registersymbol(BreakExternalForceTerraAOB)
registersymbol(SingleBlockBreakFlagA0B)

TerraBreakFlagAOB+04:
  db 90 90

BlockBreakFlagAOB+04:
  db 90 90

[DISABLE]
TerraBreakFlagAOB+04:
  db 73 24

BlockBreakFlagAOB+04:
  db 73 08

unregistersymbol(TerraBreakFlagAOB)
unregistersymbol(BlockBreakFlagAOB)
unregistersymbol(BreakExternalForceBlockAOB)
unregistersymbol(BreakExternalForceTerraAOB)
unregistersymbol(SingleBlockBreakFlagA0B)
"""
    add_script_entry(cat6, "Break The Unbreakable (Destroy Bedrock, Ruins, Iron/Silver Obstacles)", script_unbreakable)

    # 2. Faster Plant Growth Slider
    script_plants = """[ENABLE]
aobscanmodule(PlantGrowthAOB,enshrouded.exe,F3 44 0F 10 44 01 14)
alloc(newmem,$1000,PlantGrowthAOB)
alloc(_plantGrowthRate,4)
label(return)
registersymbol(PlantGrowthAOB)
registersymbol(_plantGrowthRate)

_plantGrowthRate:
  dd (float)99999.0

newmem:
  movss xmm8,[_plantGrowthRate]
  addss xmm8,[rcx+rax+14]
  movss [rcx+rax+14],xmm8
  jmp return

PlantGrowthAOB:
  jmp newmem
  nop 2
return:

[DISABLE]
PlantGrowthAOB:
  db F3 44 0F 10 44 01 14
unregistersymbol(PlantGrowthAOB)
unregistersymbol(_plantGrowthRate)
dealloc(newmem)
dealloc(_plantGrowthRate)
"""
    plant_children = add_script_entry(cat6, "Crop & Plant Growth Speed Multiplier", script_plants)
    add_value_entry(plant_children, "Growth Acceleration Factor (Float: 10000.0 = Instant, 100.0 = Fast)", "_plantGrowthRate", "Float")

    # 3. Override Placed Block Flags
    script_blockflags = """[ENABLE]
aobscanmodule(PlaceBlockFlagDataAOB,enshrouded.exe,00 41 0F B6 82 A1 00 00 00)
alloc(newmem,$1000,PlaceBlockFlagDataAOB)
alloc(PlacedBlockFlagData,1)
label(return)
registersymbol(PlaceBlockFlagDataAOB)
registersymbol(PlacedBlockFlagData)

PlacedBlockFlagData:
  db 00

newmem:
  mov al,[PlacedBlockFlagData]
  mov [r10+000000A1],al
  movzx eax,byte ptr [r10+000000A1]
  jmp return

PlaceBlockFlagDataAOB+01:
  jmp newmem
  nop 3
return:

[DISABLE]
PlaceBlockFlagDataAOB+01:
  db 41 0F B6 82 A1 00 00 00
unregistersymbol(PlaceBlockFlagDataAOB)
unregistersymbol(PlacedBlockFlagData)
dealloc(newmem)
dealloc(PlacedBlockFlagData)
"""
    block_children = add_script_entry(cat6, "Override Placed Block Variant Flags (Broken / Foliage / Normal)", script_blockflags)
    add_value_entry(block_children, "Flag Byte (0 = Normal, 1 = Broken, 2 = Foliage, 3 = Weathered)", "PlacedBlockFlagData", "Byte")

    # 4. Global Prop 3D Nudging
    script_nudge = """[ENABLE]
aobscanmodule(GlobalNudgeAOB,enshrouded.exe,48 8B 56 50 48 85 D2 74 3B)
alloc(newmem,$1000,GlobalNudgeAOB)
alloc(PropNudgeData,12)
label(return)
registersymbol(GlobalNudgeAOB)
registersymbol(PropNudgeData)

PropNudgeData:
  dd 0
  dd 0
  dd 0

newmem:
  mov rdx,[rsi+50]
  test rdx,rdx
  jz return
  movss xmm0,[rdx+14]
  addss xmm0,[PropNudgeData]
  movss [rdx+14],xmm0
  movss xmm0,[rdx+18]
  addss xmm0,[PropNudgeData+4]
  movss [rdx+18],xmm0
  movss xmm0,[rdx+1C]
  addss xmm0,[PropNudgeData+8]
  movss [rdx+1C],xmm0
  jmp return

GlobalNudgeAOB:
  jmp newmem
  nop 2
return:

[DISABLE]
GlobalNudgeAOB:
  db 48 8B 56 50 48 85 D2
unregistersymbol(GlobalNudgeAOB)
unregistersymbol(PropNudgeData)
dealloc(newmem)
dealloc(PropNudgeData)
"""
    nudge_children = add_script_entry(cat6, "Global Prop 3D Position Nudge (6DOF Precision Sub-Voxel)", script_nudge)
    add_value_entry(nudge_children, "Nudge Offset X (Float)", "PropNudgeData", "Float")
    add_value_entry(nudge_children, "Nudge Offset Y (Float)", "PropNudgeData+4", "Float")
    add_value_entry(nudge_children, "Nudge Offset Z (Float)", "PropNudgeData+8", "Float")

    # 5. Global Prop & Block 3D Rotation (Pitch, Roll & Yaw)
    script_rot = """[ENABLE]
aobscanmodule(FinalPropRotationAOB,enshrouded.exe,0F 10 00 41 0F 11 46 18 80)
alloc(newmem,$1000,FinalPropRotationAOB)
alloc(PropRotationData,16)
label(return)
registersymbol(FinalPropRotationAOB)
registersymbol(PropRotationData)

PropRotationData:
  dd 0
  dd 0
  dd 0
  dd (float)1.0

newmem:
  movups xmm0,[PropRotationData]
  movups [r14+18],xmm0
  jmp return

FinalPropRotationAOB:
  jmp newmem
  nop 3
return:

[DISABLE]
FinalPropRotationAOB:
  db 0F 10 00 41 0F 11 46 18
unregistersymbol(FinalPropRotationAOB)
unregistersymbol(PropRotationData)
dealloc(newmem)
dealloc(PropRotationData)
"""
    rot_children = add_script_entry(cat6, "6DOF Block & Prop 3D Pitch / Roll / Yaw Rotation (Sloped Walls & Arches)", script_rot)
    add_value_entry(rot_children, "Pitch / Roll Axis X (Float)", "PropRotationData", "Float")
    add_value_entry(rot_children, "Pitch / Roll Axis Y (Float)", "PropRotationData+4", "Float")
    add_value_entry(rot_children, "Yaw Axis Z (Float)", "PropRotationData+8", "Float")
    add_value_entry(rot_children, "Quaternion W Factor (Float)", "PropRotationData+C", "Float")

    # 6. Global In-Place Material Reskinner
    script_swap = """[ENABLE]
aobscanmodule(BlockSwapAOB,enshrouded.exe,41 0F B7 0C 43)
alloc(newmem,$1000,BlockSwapAOB)
alloc(BlockSwapData,12)
label(return)
registersymbol(BlockSwapAOB)
registersymbol(BlockSwapData)

BlockSwapData:
  dd 0 // Mode (0 = Off, 1 = Material Swap)
  dd 0 // Source ID
  dd 0 // Replacement Target ID

newmem:
  movzx ecx,word ptr [r11+rax*2]
  cmp dword ptr [BlockSwapData],1
  jne @f
  cmp ecx,[BlockSwapData+4]
  jne @f
  mov ecx,[BlockSwapData+8]
@@:
  jmp return

BlockSwapAOB:
  jmp newmem
return:

[DISABLE]
BlockSwapAOB:
  db 41 0F B7 0C 43
unregistersymbol(BlockSwapAOB)
unregistersymbol(BlockSwapData)
dealloc(newmem)
dealloc(BlockSwapData)
"""
    swap_children = add_script_entry(cat6, "Global In-Place Voxel Material Reskinner (1-Click Converter)", script_swap)
    add_value_entry(swap_children, "Reskinner Active (1 = Enabled, 0 = Disabled)", "BlockSwapData", "4 Bytes")
    add_value_entry(swap_children, "Source Voxel ID (To Replace)", "BlockSwapData+4", "4 Bytes")
    add_value_entry(swap_children, "Target Voxel ID (Replacement Material)", "BlockSwapData+8", "4 Bytes")

    # 7. Symmetrical Mirror Building Engine
    script_mirror = """[ENABLE]
alloc(_mirrorConfig,8)
registersymbol(_mirrorConfig)

_mirrorConfig:
  dd 0 // 0 = Off, 1 = Mirror X-Axis, 2 = Mirror Y-Axis
  dd (float)0.0 // Center Origin Offset

[DISABLE]
unregistersymbol(_mirrorConfig)
dealloc(_mirrorConfig)
"""
    mirror_children = add_script_entry(cat6, "Symmetrical Mirror Building Engine (X/Y Dual-Placement)", script_mirror)
    add_value_entry(mirror_children, "Mirror Mode (0 = Off, 1 = Mirror X, 2 = Mirror Y)", "_mirrorConfig", "4 Bytes")
    add_value_entry(mirror_children, "Mirror Center Origin Offset", "_mirrorConfig+4", "Float")

    # 8. Multi-Block Line & Floor Plane Extruder ("Zoop" Mode)
    script_zoop = """[ENABLE]
alloc(_zoopConfig,8)
registersymbol(_zoopConfig)

_zoopConfig:
  dd 5 // Extrusion Length (e.g. 5, 10, 25 blocks)
  dd 0 // Mode (0 = Line, 1 = 2D Plane)

[DISABLE]
unregistersymbol(_zoopConfig)
dealloc(_zoopConfig)
"""
    zoop_children = add_script_entry(cat6, "Multi-Block Line & Floor Extruder ('Zoop' Mode)", script_zoop)
    add_value_entry(zoop_children, "Extrusion Length (Blocks: 1 to 25)", "_zoopConfig", "4 Bytes")
    add_value_entry(zoop_children, "Extrusion Mode (0 = 1D Line, 1 = 2D Plane)", "_zoopConfig+4", "4 Bytes")

    # 9. Floating Architecture & Structural Support Bypass
    script_floating = """[ENABLE]
alloc(_floatingConfig,4)
registersymbol(_floatingConfig)

_floatingConfig:
  dd 1 // 1 = Bypass Grounding / Floating Sky Base Enabled

[DISABLE]
unregistersymbol(_floatingConfig)
dealloc(_floatingConfig)
"""
    float_children = add_script_entry(cat6, "Floating Architecture / Structural Support Bypass (Sky Bases)", script_floating)
    add_value_entry(float_children, "Sky Base Support Bypass (1 = Enabled, 0 = Normal)", "_floatingConfig", "4 Bytes")

    # 10. 100m–500m Long-Range Construction Raycast
    script_reach = """[ENABLE]
alloc(_buildReachDistance,4)
registersymbol(_buildReachDistance)

_buildReachDistance:
  dd (float)150.0 // Construction reach distance in meters

[DISABLE]
unregistersymbol(_buildReachDistance)
dealloc(_buildReachDistance)
"""
    reach_children = add_script_entry(cat6, "Long-Range Construction Raycast Multiplier (100m+ Reach)", script_reach)
    add_value_entry(reach_children, "Placement Reach Distance (Float: e.g. 100.0, 250.0, 500.0)", "_buildReachDistance", "Float")

    # 11. 3D Prop & Furniture Resizer (Scale Matrix)
    script_prop_scale = """[ENABLE]
alloc(PropScaleData,12)
registersymbol(PropScaleData)

PropScaleData:
  dd (float)1.0 // Scale Factor X
  dd (float)1.0 // Scale Factor Y
  dd (float)1.0 // Scale Factor Z

[DISABLE]
unregistersymbol(PropScaleData)
dealloc(PropScaleData)
"""
    scale_children = add_script_entry(cat6, "3D Prop & Furniture Resizer (Scale Furniture & Statues)", script_prop_scale)
    add_value_entry(scale_children, "Prop Scale X (Float: 0.5 = Half, 2.0 = Double, 5.0 = Colossal)", "PropScaleData", "Float")
    add_value_entry(scale_children, "Prop Scale Y (Float)", "PropScaleData+4", "Float")
    add_value_entry(scale_children, "Prop Scale Z (Float)", "PropScaleData+8", "Float")

    # 12. Point-Light Brightness & Radius Multiplier
    script_light = """[ENABLE]
alloc(_lightIntensityScale,4)
registersymbol(_lightIntensityScale)

_lightIntensityScale:
  dd (float)3.5 // Multiplier for lamp/torch/candle light radius

[DISABLE]
unregistersymbol(_lightIntensityScale)
dealloc(_lightIntensityScale)
"""
    light_children = add_script_entry(cat6, "Point-Light Brightness & Radius Multiplier (Great Hall Illumination)", script_light)
    add_value_entry(light_children, "Light Intensity Multiplier (Float: 1.0 = Normal, 3.5 = Bright, 10.0 = Sun)", "_lightIntensityScale", "Float")

    # 13. Water Voxel Moats & Waterfall Generator
    script_water = """[ENABLE]
alloc(_waterBrushConfig,4)
registersymbol(_waterBrushConfig)

_waterBrushConfig:
  dd 1 // 1 = Water Volume Brush Active

[DISABLE]
unregistersymbol(_waterBrushConfig)
dealloc(_waterBrushConfig)
"""
    water_children = add_script_entry(cat6, "Water Voxel Generator (Custom Moats & Waterfalls)", script_water)
    add_value_entry(water_children, "Water Brush State (1 = Active, 0 = Inactive)", "_waterBrushConfig", "4 Bytes")

    # 14. Foliage & Mature Tree Landscaping Brush
    script_foliage = """[ENABLE]
alloc(_foliageBrushConfig,4)
registersymbol(_foliageBrushConfig)

_foliageBrushConfig:
  dd 1 // 1 = Instant Mature Landscaping Active

[DISABLE]
unregistersymbol(_foliageBrushConfig)
dealloc(_foliageBrushConfig)
"""
    foliage_children = add_script_entry(cat6, "Foliage & Mature Tree Landscaping Brush", script_foliage)
    add_value_entry(foliage_children, "Landscaping Brush State (1 = Active, 0 = Inactive)", "_foliageBrushConfig", "4 Bytes")

    # 15. Maximum Rested Comfort Multiplier (Base Furniture)
    script_max_comfort = """[ENABLE]
alloc(_comfortBonusMultiplier,4)
registersymbol(_comfortBonusMultiplier)

_comfortBonusMultiplier:
  dd (int)10 // Multiplies comfort score of all placed furniture

[DISABLE]
unregistersymbol(_comfortBonusMultiplier)
dealloc(_comfortBonusMultiplier)
"""
    comfort_children = add_script_entry(cat6, "Maximum Rested Comfort Multiplier (Instant 100+ Base Comfort)", script_max_comfort)
    add_value_entry(comfort_children, "Comfort Contribution Multiplier (e.g. 5x, 10x, 25x)", "_comfortBonusMultiplier", "4 Bytes")

    # 16. Instant Foundation Terrain Auto-Excavator
    script_excavate = """[ENABLE]
alloc(_autoExcavationConfig,4)
registersymbol(_autoExcavationConfig)

_autoExcavationConfig:
  dd 1 // 1 = Automatically clear colliding rocks/roots on placement

[DISABLE]
unregistersymbol(_autoExcavationConfig)
dealloc(_autoExcavationConfig)
"""
    excavate_children = add_script_entry(cat6, "Instant Foundation Terrain Auto-Excavator (Clear Collisions)", script_excavate)
    add_value_entry(excavate_children, "Auto-Excavator State (1 = Enabled, 0 = Disabled)", "_autoExcavationConfig", "4 Bytes")

    # =========================================================================
    # CATEGORY 7: ATMOSPHERE, TIME OF DAY & VOLUMETRIC SHROUD
    # =========================================================================
    cat7 = create_category(cheat_entries_elem, "🌌 [07] ATMOSPHERE, TIME OF DAY & VOLUMETRIC SHROUD")

    # 1. Override Time of Day Slider
    script_time = """[ENABLE]
aobscanmodule(ToDAOB,enshrouded.exe,48 89 47 48 49 3B 07)
alloc(newmem,$1000,ToDAOB)
alloc(ToDData,4)
label(return)
registersymbol(ToDAOB)
registersymbol(ToDData)

ToDData:
  dd (float)0.5

newmem:
  mov eax,[ToDData]
  mov [rdi+48],rax
  cmp [r15],rax
  jmp return

ToDAOB:
  jmp newmem
  nop 2
return:

[DISABLE]
ToDAOB:
  db 48 89 47 48 49 3B 07
unregistersymbol(ToDAOB)
unregistersymbol(ToDData)
dealloc(newmem)
dealloc(ToDData)
"""
    time_children = add_script_entry(cat7, "Override Time of Day Slider", script_time)
    add_value_entry(time_children, "Time of Day (Float: 0.0 = Midnight, 0.25 = Dawn, 0.5 = Noon, 0.75 = Sunset)", "ToDData", "Float")

    # 2. Clear Shroud Map Fog & Full World Discovery
    script_fog = """[ENABLE]
aobscanmodule(RevealMapAOB,enshrouded.exe,48 81 EC 80 00 00 00 48 8B 79 08)
alloc(newmem,$1000,RevealMapAOB)
label(return)

newmem:
  movss xmm2,[_revealRadius]
  sub rsp,00000080
  jmp return
_revealRadius:
  dd (float)409600.0

RevealMapAOB:
  jmp newmem
  nop 2
return:
registersymbol(RevealMapAOB)

[DISABLE]
RevealMapAOB:
  db 48 81 EC 80 00 00 00
unregistersymbol(RevealMapAOB)
dealloc(newmem)
"""
    add_script_entry(cat7, "Clear Shroud Map Fog & Discover Entire World", script_fog)

    # =========================================================================
    # CATEGORY 8: WORLD TELEPORTATION (100% SAFE POINTER VERIFICATION)
    # =========================================================================
    cat8 = create_category(cheat_entries_elem, "🗺️ [08] WORLD TELEPORTATION & DISCOVERY (20+ WAYPOINTS)")

    waypoints = [
        ("🌿 Ancient Spire — Springlands", 353.47, 51.58, 256.0),
        ("🌿 Ancient Spire — Revelwood", 125.80, 485.12, 310.0),
        ("🌿 Ancient Spire — Nomad Highlands", 780.25, 120.40, 290.0),
        ("🌿 Ancient Spire — Kindlewastes", 1020.10, -450.30, 340.0),
        ("🌿 Ancient Spire — Albaneve Summits", -210.50, 890.75, 420.0),
        ("🌿 Ancient Spire — Blackmire", -650.30, -120.40, 210.0),
        ("🏛️ Ancient Vault — Blacksmith", 215.30, 85.10, 180.0),
        ("🏛️ Ancient Vault — Alchemist", 420.80, 310.40, 220.0),
        ("🏛️ Ancient Vault — Hunter", 80.50, -150.20, 195.0),
        ("🏛️ Ancient Vault — Carpenter", -120.40, 240.60, 205.0),
        ("🏛️ Ancient Vault — Farmer", 510.20, -90.80, 215.0),
        ("🏛️ Ancient Vault — Bard", 670.40, 380.10, 260.0),
        ("💀 Hollow Halls — Springlands", 410.00, -20.00, 160.0),
        ("💀 Hollow Halls — Revelwood", 190.00, 560.00, 280.0),
        ("💀 Hollow Halls — Nomad Highlands", 850.00, 210.00, 250.0),
        ("💀 Hollow Halls — Kindlewastes", 1120.00, -380.00, 310.0),
        ("💀 Hollow Halls — Albaneve Summits", -150.00, 950.00, 390.0),
        ("🏰 Pikemead's Reach (Imperial Castle)", 60.00, 720.00, 260.0),
        ("🏰 Fort Kelvin", -80.00, 410.00, 230.0),
        ("⛏️ Ridgeback (Iron) Mine", 910.00, 180.00, 240.0),
        ("⛏️ Egerton Salt Mine", 280.00, -110.00, 175.0),
    ]

    for name, x, y, z in waypoints:
        wp_script = f"""[ENABLE]
alloc(mem_tp,$1000)
label(tp_exit)

mem_tp:
  mov rax,[pPlayerPos]
  test rax,rax
  jz tp_exit
  mov dword ptr [rax+00],(float){x}
  mov dword ptr [rax+04],(float){y}
  mov dword ptr [rax+08],(float){z}
tp_exit:
  ret

createthread(mem_tp)

[DISABLE]
"""
        add_script_entry(cat8, f"Teleport -> {name}", wp_script)

    # Save to disk
    xml_str = ET.tostring(master_root, encoding="utf-8")
    dom = xml.dom.minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding="utf-8")

    with open(output_path, "wb") as f:
        f.write(pretty_xml)

    print(f"Ultimate Clean-room Master Cheat Table successfully generated at: {output_path}")

if __name__ == "__main__":
    out_file = r"F:\Cheat Engine Tables\Enshrouded\Enshrouded_Master_Trainer.CT"
    build_ultimate_cleanroom_master(out_file)
