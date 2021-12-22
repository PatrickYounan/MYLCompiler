bits 64

section .text
global _main
extern _printf

_main:
 call main
 ret

main:
 push rbp
 mov rbp, rsp
 leave
 ret

