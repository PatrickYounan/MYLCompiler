import time
import os
from src.myl.lexer import Lexer
from src.myl.parser import Parser
from src.myl.compiler import *

compiled_files = {}


def compile_file(path):
    if compiled_files.__contains__(path):
        return None
    start_time = time.time()
    lexer = Lexer("%s" % path)

    parser = Parser(lexer)
    parser.parse_advance()

    compiler = Compiler(path.replace(".myl", ".asm"), parser)
    compiler.compile()
    compiled_files[path] = True
    print("%s took %s seconds to compile." % (lexer.file.name, time.time() - start_time))
    return compiler


def compile_to_exe(compiler):
    os.system("nasm -fwin64 %s | gcc -o program %s" % (compiler.asm_path, compiler.asm_path.replace(".asm", ".obj")))
    os.system("program")
