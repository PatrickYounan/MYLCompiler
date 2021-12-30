import enum
from enum import Enum


class TokenType(enum.IntEnum):
    TOKEN_EOF = -1
    TOKEN_IDENTIFIER = 0
    TOKEN_DIGIT = 1
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
    TOKEN_INT = 30
    TOKEN_DOUBLE = 31
    TOKEN_FLOAT = 32
    TOKEN_TYPE_DEFINE = 33
    TOKEN_EXTERN = 34
    TOKEN_INCLUDE = 35


class Token:

    def __init__(self, _type, _data):
        self.tok_type = _type
        self.data = _data
