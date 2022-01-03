@echo off
nasm -fwin64 test/test.asm | gcc -o run test/test.obj