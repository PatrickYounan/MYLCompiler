from src.compiler import *
from src.token import *
from src.lexer import *
from src.parser import *
import os
import time

path = "../test/test.myl"

start_time = time.time()
lexer = Lexer("%s" % path)

parser = Parser(lexer)
parser.parse_advance()

compiler = Compiler(path.replace(".myl", ".asm"), parser)
compiler.compile(path)

print("%s took %s seconds to compile." % (lexer.file.name, time.time() - start_time))

os.system("nasm -f win64 %s | gcc -o ../program %s" % (compiler.asm_path, compiler.asm_path.replace(".asm", ".obj")))
os.system("..\program")
