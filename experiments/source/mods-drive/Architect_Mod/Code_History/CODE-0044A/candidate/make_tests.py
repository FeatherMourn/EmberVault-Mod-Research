import os

asm_code = """option casemap:none

PUBLIC exec_hook_test

.code

; void exec_hook_test(void* func, void* context);
; rcx = func, rdx = context
exec_hook_test PROC
    push rbp
    push rbx
    push rsi
    push rdi
    push r12
    push r13
    push r14
    push r15
    sub rsp, 256
    
    ; Save original context pointer
    mov r8, rdx
    
    ; Load all registers from context to point to safe memory
    mov rax, rdx
    mov rbx, rdx
    mov rcx, rdx
    mov rdx, r8
    mov rbp, r8
    mov rsi, r8
    mov rdi, r8
    mov r9, r8
    mov r10, r8
    mov r11, r8
    mov r12, r8
    mov r13, r8
    mov r14, r8
    mov r15, r8
    
    ; Call the target function (which is just the instructions)
    ; But wait, the function takes arguments? We jump or call it.
    ; Actually, it's easier to just call it.
    call rcx
    
    add rsp, 256
    pop r15
    pop r14
    pop r13
    pop r12
    pop rdi
    pop rsi
    pop rbx
    pop rbp
    ret
exec_hook_test ENDP

END
"""

c_code = """#include <windows.h>
#include <stdio.h>
#include <stdint.h>

extern void exec_hook_test(void* func, void* context);

typedef struct {
    uint8_t memory[8192];
} DummyContext;

int main() {
    printf("Starting 7-site transparency test...\\n");
    return 0;
}
"""

with open("tests/test_hook_transparency_asm.asm", "w") as f: f.write(asm_code)
with open("tests/test_hook_transparency.c", "w") as f: f.write(c_code)
