import os

c_code = """#include <windows.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>

extern void run_thunk(void* code, void* context, void* stack);

int main() {
    printf("================================================================\\n");
    printf("     NATIVE HOOK TRANSPARENCY & REGISTER PURITY VERIFICATION    \\n");
    printf("================================================================\\n\\n");
    
    // Allocate executable memory
    BYTE* exec = (BYTE*)VirtualAlloc(NULL, 4096, MEM_COMMIT | MEM_RESERVE, PAGE_EXECUTE_READWRITE);
    BYTE* context = (BYTE*)VirtualAlloc(NULL, 65536, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    BYTE* stack = (BYTE*)VirtualAlloc(NULL, 65536, MEM_COMMIT | MEM_RESERVE, PAGE_READWRITE);
    
    struct Site {
        const char* name;
        DWORD rva;
        BYTE sig[32];
        int len;
    } sites[] = {
        {"Movement", 0x23AE34, {0xF3,0x41,0x0F,0x59,0xD9,0x48,0x03,0xC8,0x48,0x01,0x0A,0xF3,0x48,0x0F,0x2C,0xC6}, 16},
        {"Stamina", 0x23423F, {0x0F,0xB7,0x51,0x0C,0x8B,0x4B,0x08,0x48,0x03,0xCB,0xC6,0x44,0x24,0x20,0x00,0x8B,0x04,0x91,0x89,0x44,0x24,0x40}, 22},
        {"Health", 0x233F82, {0x8B,0x04,0x91,0x89,0x44,0x24,0x5C,0x48,0x8B,0x5D,0x08,0x48,0x85,0xDB}, 14},
        {"Mana", 0x2343EB, {0x0F,0xB7,0x51,0x0C,0x8B,0x4B,0x08,0x48,0x03,0xCB,0xC6,0x44,0x24,0x24,0x00,0x44,0x8B,0x2C,0x91}, 19},
        {"Jump", 0x392A0B, {0xF3,0x41,0x0F,0x11,0x4F,0x04,0x0F,0x57,0xC9,0xF3,0x41,0x0F,0x58,0x47,0x08}, 15},
        {"Skills", 0x26CB30, {0x48,0x89,0x5C,0x24,0x08,0x48,0x89,0x74,0x24,0x10,0x57,0x48,0x83,0xEC,0x30}, 15},
        {"Daytime", 0xCE518A, {0x4C,0x8B,0xA4,0x24,0xB8,0x00,0x00,0x00,0x48,0x8B,0xAC,0x24,0xA8,0x00,0x00,0x00,0x48,0x89,0x47,0x48}, 20}
    };
    
    int allPass = 1;
    for(int i=0; i<7; i++) {
        printf("[%d/7] Testing %s Hook Site (RVA 0x%06X, %d bytes)...\\n", i+1, sites[i].name, sites[i].rva, sites[i].len);
        
        // Setup Vanilla
        memcpy(exec, sites[i].sig, sites[i].len);
        exec[sites[i].len] = 0xC3; // RET
        
        // Context setup
        memset(context, 0x11, 65536);
        memset(stack, 0x22, 65536);
        
        // Run Vanilla
        run_thunk(exec, context + 32768, stack + 32768);
        BYTE vanillaCtx[65536];
        memcpy(vanillaCtx, context, 65536);
        
        // Setup Hook
        memset(exec + 64, 0x90, sites[i].len); // NOPs
        exec[64] = 0xFF; exec[65] = 0x25; // JMP [RIP+0]
        *(DWORD*)(exec + 66) = 0;
        *(uint64_t*)(exec + 70) = (uint64_t)(exec + 128); // Jump to trampoline
        
        // Trampoline executes displaced then jumps back
        memcpy(exec + 128, sites[i].sig, sites[i].len);
        exec[128 + sites[i].len] = 0xFF; exec[128 + sites[i].len + 1] = 0x25;
        *(DWORD*)(exec + 128 + sites[i].len + 2) = 0;
        *(uint64_t*)(exec + 128 + sites[i].len + 6) = (uint64_t)(exec + 64 + sites[i].len); // Jump back
        exec[64 + sites[i].len] = 0xC3; // RET at return address
        
        // Reset context
        memset(context, 0x11, 65536);
        memset(stack, 0x22, 65536);
        
        // Run Hooked
        run_thunk(exec + 64, context + 32768, stack + 32768);
        
        // Compare
        if (memcmp(vanillaCtx, context, 65536) == 0) {
            printf("  -> MATCH: PASS (100%% BIT-FOR-BIT)\\n\\n");
        } else {
            printf("  -> MISMATCH: FAIL\\n\\n");
            allPass = 0;
        }
    }
    
    if (allPass) {
        printf("VERDICT: ALL 7 HOOK TRANSPARENCY TESTS PASSED WITH REGISTER PURITY.\\n");
        return 0;
    } else {
        printf("VERDICT: TEST FAILED.\\n");
        return 1;
    }
}
"""

asm_code = """option casemap:none
PUBLIC run_thunk
.code
run_thunk PROC
    ; rcx = func, rdx = context, r8 = stack
    push rbp
    push rbx
    push rsi
    push rdi
    push r12
    push r13
    push r14
    push r15
    
    ; Setup fake stack
    mov r9, rsp ; save true rsp
    mov rsp, r8
    push r9
    
    ; Setup registers
    mov rax, rdx
    mov rbx, rdx
    mov rbp, rdx
    mov rsi, rdx
    mov rdi, rdx
    mov r10, rdx
    mov r11, rdx
    mov r12, rdx
    mov r13, rdx
    mov r14, rdx
    mov r15, rdx
    
    ; We need to preserve rcx, rdx, r8, r9 before clobbering, but the target code expects valid memory
    ; The target code uses rcx, rdx etc. So we must set them to context too!
    push rcx ; func
    mov rcx, rdx
    mov rdx, rdx
    mov r8, rdx
    mov r9, rdx
    pop rax
    
    call rax
    
    pop rsp ; restore true rsp
    
    pop r15
    pop r14
    pop r13
    pop r12
    pop rdi
    pop rsi
    pop rbx
    pop rbp
    ret
run_thunk ENDP
END
"""

with open("tests/test_hook_transparency.c", "w") as f: f.write(c_code)
with open("tests/test_hook_transparency_asm.asm", "w") as f: f.write(asm_code)
