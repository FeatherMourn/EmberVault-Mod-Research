import re

with open(r"runtime\native\source\ArchitectCheatCorrelationEntry.asm", "r") as f:
    src = f.read()

# Movement
src = re.sub(r"(cmp dword ptr \[g_cheatSuperSpeed\],1\s+jne @@move_vanilla\s+mulss xmm3,dword ptr \[g_cheatSpeedMul\]\s+cvtsi2ss xmm0,rcx\s+mulss xmm0,dword ptr \[g_cheatSpeedMul\]\s+cvtss2si rcx,xmm0\s+@@move_vanilla:)", r"pushfq\n\1\npopfq", src)

# Stamina
stamina_orig = """cmp dword ptr [g_cheatInfiniteStamina],1
je @@stamina_full_pop
cmp dword ptr [g_cheatFillStaminaPending],0
jle @@stamina_vanilla_pop
dec dword ptr [g_cheatFillStaminaPending]
@@stamina_full_pop:
popfq
jmp @@stamina_full
@@stamina_vanilla_pop:
popfq
\tmov eax,dword ptr [rcx+rdx*4+08h]
\ttest eax,eax
\tjz @@stamina_vanilla
\tmov dword ptr [rcx+rdx*4],eax
\tmov dword ptr [rsp+40h],eax
\tjmp @@stamina_done
@@stamina_vanilla:
\tmov eax,dword ptr [rcx+rdx*4]
\tmov dword ptr [rsp+40h],eax
@@stamina_done:"""

stamina_fix = """pushfq
cmp dword ptr [g_cheatInfiniteStamina],1
je @@stamina_full
cmp dword ptr [g_cheatFillStaminaPending],0
jle @@stamina_vanilla
dec dword ptr [g_cheatFillStaminaPending]
@@stamina_full:
popfq
\tmov eax,dword ptr [rcx+rdx*4+08h]
\ttest eax,eax
\tjz @@stamina_vanilla_2
\tmov dword ptr [rcx+rdx*4],eax
\tmov dword ptr [rsp+40h],eax
\tjmp @@stamina_done
@@stamina_vanilla:
popfq
@@stamina_vanilla_2:
\tmov eax,dword ptr [rcx+rdx*4]
\tmov dword ptr [rsp+40h],eax
@@stamina_done:"""
src = src.replace(stamina_orig, stamina_fix)

# Health
health_orig = """\tcmp dword ptr [g_cheatGodMode],1
\tje @@health_full
\tcmp dword ptr [g_cheatFillHealthPending],0
\tjle @@health_vanilla
\tdec dword ptr [g_cheatFillHealthPending]
@@health_full:
\tmov eax,dword ptr [rcx+rdx*4+08h]
\ttest eax,eax
\tjz @@health_vanilla
\tmov dword ptr [rcx+rdx*4],eax
\tmov dword ptr [rsp+5Ch],eax
\tjmp @@health_displaced
@@health_vanilla:
\tmov eax,dword ptr [rcx+rdx*4]
\tmov dword ptr [rsp+5Ch],eax
@@health_displaced:"""
health_fix = """\tpushfq
\tcmp dword ptr [g_cheatGodMode],1
\tje @@health_full
\tcmp dword ptr [g_cheatFillHealthPending],0
\tjle @@health_vanilla
\tdec dword ptr [g_cheatFillHealthPending]
@@health_full:
\tpopfq
\tmov eax,dword ptr [rcx+rdx*4+08h]
\ttest eax,eax
\tjz @@health_vanilla_2
\tmov dword ptr [rcx+rdx*4],eax
\tmov dword ptr [rsp+5Ch],eax
\tjmp @@health_displaced
@@health_vanilla:
\tpopfq
@@health_vanilla_2:
\tmov eax,dword ptr [rcx+rdx*4]
\tmov dword ptr [rsp+5Ch],eax
@@health_displaced:"""
src = src.replace(health_orig, health_fix)

# Mana
mana_orig = """\tcmp dword ptr [g_cheatInfiniteMana],1
\tje @@mana_full
\tcmp dword ptr [g_cheatFillManaPending],0
\tjle @@mana_vanilla
\tdec dword ptr [g_cheatFillManaPending]
@@mana_full:
\tmov eax,dword ptr [rcx+rdx*4+04h]
\ttest eax,eax
\tjz @@mana_vanilla
\tmov dword ptr [rcx+rdx*4],eax
\tmov r13d,eax
\tjmp @@mana_displaced
@@mana_vanilla:
\tmov r13d,dword ptr [rcx+rdx*4]
@@mana_displaced:"""
mana_fix = """\tpushfq
\tcmp dword ptr [g_cheatInfiniteMana],1
\tje @@mana_full
\tcmp dword ptr [g_cheatFillManaPending],0
\tjle @@mana_vanilla
\tdec dword ptr [g_cheatFillManaPending]
@@mana_full:
\tpopfq
\tmov eax,dword ptr [rcx+rdx*4+04h]
\ttest eax,eax
\tjz @@mana_vanilla_2
\tmov dword ptr [rcx+rdx*4],eax
\tmov r13d,eax
\tjmp @@mana_displaced
@@mana_vanilla:
\tpopfq
@@mana_vanilla_2:
\tmov r13d,dword ptr [rcx+rdx*4]
@@mana_displaced:"""
src = src.replace(mana_orig, mana_fix)

# Craft
src = re.sub(r"(cmp dword ptr \[g_cheatFreeCraft\],1\s+jne @@craft_vanilla\s+mov dword ptr \[rsp\+30h\],00h\s+@@craft_vanilla:)", r"pushfq\n\1\npopfq", src)

# Skills
src = re.sub(r"(cmp dword ptr \[g_cheatSkillPointsActive\],1\s+jne @@skills_vanilla\s+mov r9d,dword ptr \[g_customSkillPoints\]\s+@@skills_vanilla:)", r"pushfq\n\1\npopfq", src)

# Transform
src = re.sub(r"(cmp dword ptr \[g_teleportPending\],0\s+jle @@transform_displaced\s+push r8\s+mov r8,qword ptr \[g_targetPosX\]\s+mov qword ptr \[rdx\+00h\],r8\s+mov r8,qword ptr \[g_targetPosY\]\s+mov qword ptr \[rdx\+08h\],r8\s+mov r8,qword ptr \[g_targetPosZ\]\s+mov qword ptr \[rdx\+10h\],r8\s+pop r8\s+dec dword ptr \[g_teleportPending\]\s+@@transform_displaced:)", r"pushfq\n\1\npopfq", src)

with open(r"runtime\native\source\ArchitectCheatCorrelationEntry.asm", "w") as f:
    f.write(src)
print("ASM Flags patched.")
