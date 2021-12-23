from abc import ABC, abstractmethod


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
        pass


class UnaryExpression(Node):

    def compile(self, compiler):
        pass

    def __init__(self, exp, operator):
        self.exp = exp
        self.operator = operator


class LiteralExpression(Node):

    def compile(self, compiler):
        pass

    def __init__(self, token):
        self.token = token


class VarDeclStatement(Node):

    def __init__(self, var_type, name, expression):
        self.var_type = var_type
        self.name = name
        self.expression = expression

    def compile(self, compiler):
        pass


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

    def __init__(self, name, block):
        self.name = name
        self.block = block

    def compile(self, compiler):
        pass


class CallProcStatement(Node):

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def compile(self, compiler):
        pass
