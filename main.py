import os
import time
from enum import Enum
from abc import ABC, abstractmethod

file = None
lex_head = ' '
lex_peek = ' '
parse_tok = None
found_main = False


class TokenType(Enum):
    TOKEN_EOF = -1,
    TOKEN_IDENTIFIER = 0
    TOKEN_DIGIT = 1,
    TOKEN_LEFT_PAREN = 2
    TOKEN_RIGHT_PAREN = 3
    TOKEN_STAR = 4
    TOKEN_PLUS = 5
    TOKEN_SLASH = 6
    TOKEN_DASH = 7
    TOKEN_IF = 8
    TOKEN_ELIF = 9
    TOKEN_ELSE = 10
    TOKEN_END = 11
    TOKEN_THEN = 12
    TOKEN_DEF = 13
    TOKEN_OR = 14
    TOKEN_AND = 15
    TOKEN_IS = 16
    TOKEN_ISLE = 17
    TOKEN_ISL = 18
    TOKEN_ISGE = 19
    TOKEN_ISG = 20
    TOKEN_ISEQ = 21
    TOKEN_ISNEQ = 22
    TOKEN_STRING = 23
    TOKEN_EQ = 24
    TOKEN_DOT = 25
    TOKEN_COMMA = 26
    TOKEN_BITWISE_OR = 27
    TOKEN_BITWISE_AND = 28
    TOKEN_NOT = 29


class Compiler:

    def __init__(self):
        self.instructions = []


class Opcode(Enum):
    DEF_PROC = 0
    END_PROC = 1
    PUSH_INT = 2
    PUSH_STR = 3
    CALL = 4
    ADD = 5
    SUB = 6


class Token:

    def __init__(self, _type, _data):
        self.type = _type
        self.data = _data


class Instruction:

    def __init__(self, opcode, token=None, value=""):
        self.opcode = opcode
        self.token = token
        self.value = value


class Node(ABC):

    @abstractmethod
    def compile(self, compiler):
        pass


class LogicalExpression(Node):
    def compile(self, compiler):
        pass

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator


class BinaryExpression(Node):

    def compile(self, compiler):
        self.left.compile(compiler)
        self.right.compile(compiler)
        if self.operator.type == TokenType.TOKEN_PLUS:
            compiler.instructions.append(Instruction(Opcode.ADD))
        elif self.operator.type == TokenType.TOKEN_DASH:
            compiler.instructions.append(Instruction(Opcode.SUB))

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator


class UnaryExpression(Node):

    def compile(self, compiler):
        pass

    def __init__(self, exp, operator):
        self.exp = exp
        self.operator = operator


class LiteralExpression(Node):

    def compile(self, compiler):
        if self.token.type == TokenType.TOKEN_STRING:
            compiler.instructions.append(Instruction(Opcode.PUSH_STR, self.token, self.token.data))
        elif self.token.type == TokenType.TOKEN_DIGIT:
            compiler.instructions.append(Instruction(Opcode.PUSH_INT, self.token, self.token.data))

    def __init__(self, token):
        self.token = token


class DefStatement(Node):

    def __init__(self, name, block):
        self.name = name
        self.block = block

    def compile(self, compiler):
        if self.name.data == "main":
            global found_main
            found_main = True
        compiler.instructions.append(Instruction(Opcode.DEF_PROC, self.name, self.name.data))
        for statement in self.block:
            statement.compile(compiler)
        compiler.instructions.append(Instruction(Opcode.END_PROC, self.name, self.name.data))


class CallProcStatement(Node):

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def compile(self, compiler):
        for argument in self.args:
            argument.compile(compiler)
        compiler.instructions.append(Instruction(Opcode.CALL, self.name, self.name.data))


def error(message):
    raise Exception(message)


def parse_advance(expecting=None):
    global parse_tok
    current_tok = parse_tok

    if expecting is not None and current_tok.type != expecting:
        error("Expecting token type %s. Got %s instead." % (expecting.type, current_tok.type))

    parse_tok = next_token()
    if current_tok is None:
        current_tok = parse_tok

    parse_debug()
    return current_tok


def parse_accept(t):
    if parse_tok.type == t:
        parse_advance()
        return True
    return False


def parse_match(t):
    return parse_tok.type == t


def parse_debug():
    print("%s %s" % (parse_tok.type, parse_tok.data))


def lex_advance():
    if file is not None:
        global lex_head
        lex_head = file.read(1).decode("utf-8")
    else:
        error("Lexer Issue: File needs to be set before advancing.")


def lexr_peek():
    if file is not None:
        global lex_peek
        lex_peek = file.read(1).decode("utf-8")
        file.seek(file.tell() - 1)
    else:
        error("Lexer Issue: File needs to be set before advancing.")


def new_token_advance(t, data, advances):
    for x in range(0, advances):
        lex_advance()
    return Token(t, data)


def next_identifier():
    identifier = ""
    while lex_head.isalnum() or lex_head == '_':
        identifier += lex_head
        lex_advance()
    if identifier == "def":
        return Token(TokenType.TOKEN_DEF, identifier)
    elif identifier == "else":
        return Token(TokenType.TOKEN_ELSE, identifier)
    elif identifier == "elif":
        return Token(TokenType.TOKEN_ELIF, identifier)
    elif identifier == "if":
        return Token(TokenType.TOKEN_IF, identifier)
    elif identifier == "then":
        return Token(TokenType.TOKEN_THEN, identifier)
    elif identifier == "end":
        return Token(TokenType.TOKEN_END, identifier)

    return Token(TokenType.TOKEN_IDENTIFIER, identifier)


def next_string():
    string = ""
    lex_advance()
    while lex_head != '"':
        string += lex_head
        lex_advance()
    lex_advance()
    return Token(TokenType.TOKEN_STRING, string)


def next_digit():
    numeral = ""
    decimals = 0
    while lex_head.isdigit() or lex_head == '.':
        numeral += lex_head
        if lex_head == '.':
            decimals += 1
        lex_advance()

    if decimals > 1:
        error("A number cannot have more than 1 decimal point.")
    return Token(TokenType.TOKEN_DIGIT, numeral)


def next_token():
    global lex_peek
    while True:
        if not lex_head:
            return Token(TokenType.TOKEN_EOF, "")
        if lex_head == '"':
            return next_string()
        elif lex_head.isalpha() or lex_head == '_':
            return next_identifier()
        elif lex_head.isdigit():
            return next_digit()
        elif lex_head == '(':
            return new_token_advance(TokenType.TOKEN_LEFT_PAREN, "(", 1)
        elif lex_head == ')':
            return new_token_advance(TokenType.TOKEN_RIGHT_PAREN, ")", 1)
        elif lex_head == '*':
            return new_token_advance(TokenType.TOKEN_STAR, "*", 1)
        elif lex_head == '/':
            return new_token_advance(TokenType.TOKEN_SLASH, "/", 1)
        elif lex_head == '-':
            return new_token_advance(TokenType.TOKEN_DASH, "-", 1)
        elif lex_head == '+':
            return new_token_advance(TokenType.TOKEN_PLUS, "+", 1)
        elif lex_head == ',':
            return new_token_advance(TokenType.TOKEN_COMMA, ",", 1)
        elif lex_head == '.':
            return new_token_advance(TokenType.TOKEN_DOT, ".", 1)
        elif lex_head == '=':
            lexr_peek()
            return new_token_advance(TokenType.TOKEN_ISEQ, "==", 2) if lex_peek == '=' else new_token_advance(TokenType.TOKEN_EQ, "=", 1)
        elif lex_head == "!":
            lexr_peek()
            return new_token_advance(TokenType.TOKEN_ISNEQ, "!=", 2) if lex_peek == '=' else new_token_advance(TokenType.TOKEN_NOT, "!", 1)
        elif lex_head == '>':
            lexr_peek()
            return new_token_advance(TokenType.TOKEN_ISGE, ">=", 2) if lex_peek == '=' else new_token_advance(TokenType.TOKEN_ISG, ">", 1)
        elif lex_head == '<':
            lexr_peek()
            return new_token_advance(TokenType.TOKEN_ISLE, "<=", 2) if lex_peek == '=' else new_token_advance(TokenType.TOKEN_ISL, "<", 1)
        elif lex_head == '|':
            lexr_peek()
            return new_token_advance(TokenType.TOKEN_OR, "||", 2) if lex_peek == '|' else new_token_advance(TokenType.TOKEN_BITWISE_OR, "|", 1)
        elif lex_head == '&':
            lexr_peek()
            return new_token_advance(TokenType.TOKEN_AND, "&&", 2) if lex_peek == '&' else new_token_advance(TokenType.TOKEN_BITWISE_AND, "&", 1)
        else:
            lex_advance()


def lex_file(path):
    global file
    file = open(path, "rb")


def parse_token_matches(types):
    for t in types:
        if parse_tok.type == t:
            return True
    return False


def parse_block_statement(endings):
    statements = []
    while not parse_token_matches(endings):
        statements.append(parse_statement())
    return statements


def parse_def_statement():
    parse_advance()
    name = parse_advance(TokenType.TOKEN_IDENTIFIER)
    parse_advance(TokenType.TOKEN_LEFT_PAREN)
    parse_advance(TokenType.TOKEN_RIGHT_PAREN)
    block = parse_block_statement([TokenType.TOKEN_END])
    parse_advance(TokenType.TOKEN_END)
    return DefStatement(name, block)


def parse_statement():
    if not parse_tok or parse_tok.type == TokenType.TOKEN_EOF:
        return None
    if parse_tok.type == TokenType.TOKEN_DEF:
        return parse_def_statement()
    elif parse_tok.type == TokenType.TOKEN_IDENTIFIER:
        return parse_identifier_statement()
    return None


def parse_literal():
    return LiteralExpression(parse_advance())


def parse_args_expression():
    args = []

    parse_advance(TokenType.TOKEN_LEFT_PAREN)

    if parse_tok.type == TokenType.TOKEN_RIGHT_PAREN:
        parse_advance()
        return args

    while not parse_match(TokenType.TOKEN_RIGHT_PAREN):
        args.append(parse_expression())
        if not parse_match(TokenType.TOKEN_RIGHT_PAREN):
            parse_advance(TokenType.TOKEN_COMMA)

    parse_advance(TokenType.TOKEN_RIGHT_PAREN)
    return args


def parse_proc_call_statement(name):
    args = parse_args_expression()
    return CallProcStatement(name, args)


def parse_identifier_statement():
    name = parse_advance()
    if parse_tok.type == TokenType.TOKEN_LEFT_PAREN:
        return parse_proc_call_statement(name)
    return None


def parse_identifier_literal():
    name = parse_advance()
    return LiteralExpression(name)


def parse_primary():
    if parse_match(TokenType.TOKEN_LEFT_PAREN):
        parse_advance()
        exp = parse_expression()
        parse_advance(TokenType.TOKEN_RIGHT_PAREN)
        return exp
    elif parse_match(TokenType.TOKEN_IDENTIFIER):
        return parse_identifier_literal()
    elif parse_match(TokenType.TOKEN_DIGIT) or parse_match(TokenType.TOKEN_STRING):
        return parse_literal()
    return None


def parse_unary():
    while parse_match(TokenType.TOKEN_NOT) or parse_match(TokenType.TOKEN_DASH):
        operator = parse_advance()
        right = parse_unary()
        return UnaryExpression(right, operator)
    return parse_primary()


def parse_factor():
    exp = parse_unary()
    while parse_match(TokenType.TOKEN_SLASH) or parse_match(TokenType.TOKEN_STAR):
        operator = parse_advance()
        right = parse_unary()
        exp = BinaryExpression(exp, right, operator)
    return exp


def parse_term():
    exp = parse_factor()
    while parse_match(TokenType.TOKEN_DASH) or parse_match(TokenType.TOKEN_PLUS):
        operator = parse_advance()
        right = parse_factor()
        exp = BinaryExpression(exp, right, operator)
    return exp


def parse_comparison():
    exp = parse_term()
    while parse_match(TokenType.TOKEN_ISG) or parse_match(TokenType.TOKEN_ISGE) or parse_match(TokenType.TOKEN_ISL) or parse_match(TokenType.TOKEN_ISLE):
        operator = parse_advance()
        right = parse_term()
        exp = BinaryExpression(exp, right, operator)
    return exp


def parse_equality():
    exp = parse_comparison()
    while parse_match(TokenType.TOKEN_ISNEQ) or parse_match(TokenType.TOKEN_ISEQ):
        operator = parse_advance()
        right = parse_comparison()
        exp = BinaryExpression(exp, right, operator)
    return exp


def parse_and_expression():
    exp = parse_equality()

    while parse_match(TokenType.TOKEN_AND):
        operator = parse_advance()
        right = parse_equality()
        exp = LogicalExpression(exp, right, operator)
    return exp


def parse_or_expression():
    exp = parse_and_expression()

    while parse_match(TokenType.TOKEN_OR):
        operator = parse_advance()
        right = parse_and_expression()
        exp = LogicalExpression(exp, right, operator)
    return exp


def parse_expression():
    return parse_or_expression()


def write_section(asm_file, strings):
    for t in strings:
        asm_file.write(t)
    asm_file.write("\n")


if __name__ == '__main__':
    start_time = time.time()

    lex_file("test.myl")
    compiler = Compiler()

    parse_advance()

    while True:
        node = parse_statement()
        if node is None:
            break
        node.compile(compiler)

    strings = {}

    setup = []
    data = []
    text = []
    code = []

    asm_file = open("test.asm", "w")

    setup.append("bits 64\n")

    text.append("section .text\n")
    text.append("global _main\n")
    text.append("extern _printf\n")

    if found_main:
        code.append("_main:\n")
        code.append(" call main\n")
        code.append(" ret\n\n")

    constants = 0

    for instruction in compiler.instructions:
        if instruction.opcode == Opcode.DEF_PROC:
            code.append(instruction.token.data + ":\n")
            code.append(" push rbp\n")
            code.append(" mov rbp, rsp\n")
        elif instruction.opcode == Opcode.END_PROC:
            code.append(" leave\n")
            code.append(" ret\n")
        elif instruction.opcode == Opcode.ADD:
            code.append(" pop rdx\n")
            code.append(" pop rbx\n")
            code.append(" add rdx, rbx\n")
            code.append(" push rdx\n")
        elif instruction.opcode == Opcode.SUB:
            code.append(" pop rbx\n")
            code.append(" pop rdx\n")
            code.append(" sub rdx, rbx\n")
            code.append(" push rdx\n")
        elif instruction.opcode == Opcode.CALL:
            code.append(" call %s\n" % instruction.value)
        elif instruction.opcode == Opcode.PUSH_INT:
            code.append(" push %s\n" % instruction.value)
        elif instruction.opcode == Opcode.PUSH_STR:
            if strings.__contains__(instruction.value):
                string = strings[instruction.value]
                code.append(" push %s\n" % string)
            else:
                string = "lc%d" % constants
                strings[instruction.value] = string
                data.append("%s: db \"%s\", 10, 0\n" % (string, instruction.value))
                code.append(" push %s\n" % string)
                constants += 1

    write_section(asm_file, setup)

    if len(data) > 0:
        asm_file.write("section .data\n")
        write_section(asm_file, data)

    write_section(asm_file, text)
    write_section(asm_file, code)
    asm_file.close()

    if found_main:
        os.system("nasm -fwin32 test.asm | gcc -o test test.obj")

    print("Took %s seconds to compile." % (time.time() - start_time))
