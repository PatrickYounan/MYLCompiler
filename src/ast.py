from abc import ABC, abstractmethod
from compiler import *
from token import TokenType, Token


class Node(ABC):

    @abstractmethod
    def compile(self, compiler):
        pass


class LogicalExpression(Node):

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def compile(self, compiler):
        pass


class BinaryExpression(Node):

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def compile(self, compiler):
        self.left.compile(compiler)
        self.right.compile(compiler)
        compiler.instructions.append(Instruction(Opcode.BINARY_OP, self.operator, self.operator.data))


class UnaryExpression(Node):

    def __init__(self, exp, operator):
        self.exp = exp
        self.operator = operator

    def compile(self, compiler):
        pass


class LiteralExpression(Node):

    def __init__(self, token):
        self.token = token

    def compile(self, compiler):
        if self.token.type == TokenType.TOKEN_DIGIT:
            compiler.instructions.append(Instruction(Opcode.MOV_IMMI, self.token, self.token.data))
        elif self.token.type == TokenType.TOKEN_STRING:
            compiler.instructions.append(Instruction(Opcode.MOV_IMMS, self.token, self.token.data))
        elif self.token.type == TokenType.TOKEN_IDENTIFIER:
            compiler.instructions.append(Instruction(Opcode.LOAD_CONST, self.token, self.token.data))


class VarDeclStatement(Node):

    def __init__(self, var_type, name, expression):
        self.var_type = var_type
        self.name = name
        self.expression = expression

    def compile(self, compiler):
        # Global variables not implemented yet.
        if compiler.scope < 0:
            return

        self.expression.compile(compiler)

        if self.var_type.type == TokenType.TOKEN_INT:
            compiler.instructions.append(Instruction(Opcode.STORE_INT, self.var_type, self.name.data))


class ElseStatement(Node):

    def __init__(self, block):
        self.block = block

    def compile(self, compiler):
        pass


class IfStatement(Node):

    def __init__(self, condition, then_block, else_block):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

    def compile(self, compiler):
        pass


class DefStatement(Node):

    def __init__(self, name, block, def_type):
        self.name = name
        self.block = block
        self.def_type = def_type

    def compile(self, compiler):
        compiler.scope += 1
        compiler.instructions.append(Instruction(Opcode.START_PROC, self.name, self.name.data))
        compiler.instructions.append(Instruction(Opcode.ALLOC_BYTES))

        for statement in self.block:
            statement.compile(compiler)
        compiler.instructions.append(Instruction(Opcode.RES_STACK_PTR))
        compiler.instructions.append(Instruction(Opcode.END_PROC, self.name, self.name.data))
        compiler.scope -= 1


class CallProcStatement(Node):

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def compile(self, compiler):
        for argument in self.args:
            argument.compile(compiler)
            compiler.instructions.append(Instruction(Opcode.PUSH_ARG))
        compiler.instructions.append(Instruction(Opcode.CALL, self.name, self.name.data))


class ExternStatement(Node):

    def __init__(self, name):
        self.name = name

    def compile(self, compiler):
        compiler.instructions.append(Instruction(Opcode.EXTERN, self.name, self.name.data))
