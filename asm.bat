@echo off
gcc -fno-asynchronous-unwind-tables -s -c -o ctest/c.o ctest/c.c
objconv -fnasm ctest/c.o

