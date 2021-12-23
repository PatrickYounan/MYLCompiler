import os
import time
import ast
from token import TokenType, Token
from grammar import SyntaxLexer
from syntax import SyntaxParser
from compiler import Compiler

start_time = time.time()

lexer = SyntaxLexer()
lexer.lex_file("test/test.myl")

parser = SyntaxParser(lexer)
parser.parse_advance()

compiler = Compiler("test/test.asm", parser)
compiler.compile()

print("\nCompilation took %s seconds." % (time.time() - start_time))
