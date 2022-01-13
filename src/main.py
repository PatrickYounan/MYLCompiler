from src.compiler import Compiler
from src.lexer import *
from src.parser import *
import os
import time


path = "../test/test.myl"

start_time = time.time()
lexer = Lexer("%s" % path)

parser = Parser(lexer)
parser.parse_advance()

compiler = Compiler(parser)
asm = path.replace(".myl", ".asm")
obj = asm.replace(".asm", ".obj")
compiler.compile(asm)

os.system("nasm -fwin64 %s | gcc -o ../run %s" % (asm, obj))

print("%s took %s seconds to compile." % (lexer.file.name, time.time() - start_time))
