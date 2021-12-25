import os
from src.myl.compiler import *
from src.myl.builder import *

file_compiler = compile_file("test/test.myl")
os.system("nasm -fwin64 %s | gcc -o program %s" % (file_compiler.asm_path, file_compiler.asm_path.replace(".asm", ".obj")))
os.system("program")
