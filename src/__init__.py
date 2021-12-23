import os
import time
import ast
from token import TokenType, Token
from grammar import SyntaxLexer
from syntax import SyntaxParser
from compiler import Compiler

if __name__ == '__main__':
    start_time = time.time()

    lexer = SyntaxLexer()
    lexer.lex_file("test/test.myl")

    parser = SyntaxParser(lexer)
    parser.parse_advance()

    compiler = Compiler()

    while True:
        node = parser.parse_statement()
        if node is None:
            break
        node.compile(compiler)

    print("Compilation took %s seconds." % (time.time() - start_time))
