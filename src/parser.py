from src.token import *
from src.compiler import Compiler, Instruction, Opcode, Function
from abc import ABC, abstractmethod
from llvmlite import ir, binding


class Node(ABC):

    @abstractmethod
    def eval(self, compiler):
        pass


class LogicalExpression(Node):

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def eval(self, compiler):
        pass


class TernaryExpression(Node):

    def __init__(self, condition, then_exp, else_exp):
        self.condition = condition
        self.then_exp = then_exp
        self.else_exp = else_exp

    def eval(self, compiler):
        pass


class CompareExpression(Node):

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def eval(self, compiler):
        pass


class BinaryExpression(Node):

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def eval(self, compiler):
        self.left.eval(compiler)
        self.right.eval(compiler)

        if self.operator.kind == TokenType.TOKEN_PLUS:
            compiler.add(Instruction(Opcode.ADD))
        elif self.operator.kind == TokenType.TOKEN_DASH:
            compiler.add(Instruction(Opcode.SUB))
        elif self.operator.kind == TokenType.TOKEN_STAR:
            compiler.add(Instruction(Opcode.MUL))
        elif self.operator.kind == TokenType.TOKEN_SLASH:
            compiler.add(Instruction(Opcode.DIV))


class UnaryExpression(Node):

    def __init__(self, exp, operator):
        self.exp = exp
        self.operator = operator

    def eval(self, compiler):
        compiler.state = self.operator.data
        self.exp.eval(compiler)
        if self.operator.kind == TokenType.TOKEN_NOT:
            compiler.add(Instruction(Opcode.NOT))
        compiler.state = ""


class LiteralExpression(Node):

    def __init__(self, token):
        self.token = token

    def eval(self, compiler):
        if self.token.kind == TokenType.TOKEN_DIGIT:
            compiler.add(Instruction(Opcode.MOV_INT_CONST, self.token, self.token.data if compiler.state != "-" else "-%s" % self.token.data))
        elif self.token.kind == TokenType.TOKEN_IDENTIFIER:
            compiler.add(Instruction(Opcode.LOAD_VAR, self.token, self.token.data))
        elif self.token.kind == TokenType.TOKEN_STRING:
            compiler.add(Instruction(Opcode.LOAD_STRING, self.token, self.token.data))
        elif self.token.kind == TokenType.TOKEN_DECIMAL:
            compiler.add(Instruction(Opcode.MOV_FLOAT_CONST, self.token, self.token.data if compiler.state != "-" else "-%s" % self.token.data))


class VarStatement(Node):

    def __init__(self, var_type, name, expression):
        self.var_type = var_type
        self.name = name
        self.expression = expression

    def eval(self, compiler):
        self.expression.eval(compiler)
        if self.var_type.kind == TokenType.TOKEN_INT8:
            compiler.add(Instruction(Opcode.STORE_INT8, self.var_type, self.name.data))
        elif self.var_type.kind == TokenType.TOKEN_INT16:
            compiler.add(Instruction(Opcode.STORE_INT16, self.var_type, self.name.data))
        elif self.var_type.kind == TokenType.TOKEN_INT32:
            compiler.add(Instruction(Opcode.STORE_INT32, self.var_type, self.name.data))
        elif self.var_type.kind == TokenType.TOKEN_INT64:
            compiler.add(Instruction(Opcode.STORE_INT64, self.var_type, self.name.data))
        elif self.var_type.kind == TokenType.TOKEN_FLOAT64:
            compiler.add(Instruction(Opcode.STORE_FLOAT64, self.var_type, self.name.data))


class ElseStatement(Node):

    def __init__(self, block):
        self.block = block

    def eval(self, compiler):
        pass


class IfStatement(Node):

    def __init__(self, condition, then_block, else_block):
        self.condition = condition
        self.then_block = then_block
        self.else_block = else_block

    def eval(self, compiler):
        pass


class DefStatement(Node):

    def __init__(self, name, block, def_type, public):
        self.name = name
        self.block = block
        self.def_type = def_type
        self.public = public

    def eval(self, compiler):
        compiler.functions[self.name.data] = Function(self.name.data, self.def_type.kind if self.def_type is not None else None)
        compiler.add(Instruction(Opcode.START_PROC if not self.public else Opcode.START_PUB_PROC, self.def_type, self.name.data))
        compiler.add(Instruction(Opcode.SETUP_STACK))
        for statement in self.block:
            statement.eval(compiler)
        compiler.add(Instruction(Opcode.CLOSE_STACK))
        compiler.add(Instruction(Opcode.END_PROC, self.name, self.name.data))


class CallProcStatement(Node):

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def eval(self, compiler):
        for expression in self.args:
            expression.eval(compiler)
            compiler.add(Instruction(Opcode.PUSH_ARGUMENT))
        compiler.add(Instruction(Opcode.CALL, self.name, self.name.data))


class CallProcExpression(Node):

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def eval(self, compiler):
        for expression in self.args:
            expression.eval(compiler)
            compiler.add(Instruction(Opcode.PUSH_ARGUMENT))
        compiler.add(Instruction(Opcode.CALL, self.name, self.name.data))


class IncludeStatement(Node):

    def __init__(self, name):
        self.name = name

    def eval(self, compiler):
        pass


class ExternStatement(Node):

    def __init__(self, name):
        self.name = name

    def eval(self, compiler):
        compiler.add(Instruction(Opcode.EXTERN, self.name, self.name.data))


class ReturnStatement(Node):

    def __init__(self, expression):
        self.expression = expression

    def eval(self, compiler):
        if self.expression:
            self.expression.eval(compiler)
        compiler.add(Instruction(Opcode.RETURN))


class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.token = None

    def parse_advance(self, expecting=None):
        current_tok = self.token

        if expecting is not None and current_tok.kind != expecting:
            self.error("Expecting token type %s. Got %s instead." % (expecting.kind, current_tok.kind))

        self.token = self.lexer.next_token()
        if current_tok is None:
            current_tok = self.token
        return current_tok

    def parse_accept(self, t):
        return True and self.parse_advance() if self.token.kind == t else False

    def parse_match(self, t):
        return self.token.kind == t

    def parse_token_matches(self, types):
        return self.token.kind in types

    def parse_block_statement(self, endings):
        statements = []
        while not self.parse_token_matches(endings):
            statements.append(self.parse_statement())
        return statements

    def parse_pub_def_statement(self):
        self.parse_advance()
        name = self.parse_advance(TokenType.TOKEN_IDENTIFIER)
        self.parse_advance(TokenType.TOKEN_LEFT_PAREN)
        # TODO: function arguments.
        self.parse_advance(TokenType.TOKEN_RIGHT_PAREN)

        def_type = None
        if self.parse_accept(TokenType.TOKEN_COLON):
            def_type = self.parse_advance()

        block = self.parse_block_statement([TokenType.TOKEN_END])
        self.parse_advance(TokenType.TOKEN_END)
        return DefStatement(name, block, def_type, True)

    def parse_def_statement(self):
        self.parse_advance()
        name = self.parse_advance(TokenType.TOKEN_IDENTIFIER)
        self.parse_advance(TokenType.TOKEN_LEFT_PAREN)
        # TODO: function arguments.
        self.parse_advance(TokenType.TOKEN_RIGHT_PAREN)

        def_type = None
        if self.parse_accept(TokenType.TOKEN_COLON):
            def_type = self.parse_advance()

        block = self.parse_block_statement([TokenType.TOKEN_END])
        self.parse_advance(TokenType.TOKEN_END)
        return DefStatement(name, block, def_type, False)

    def parse_var_statement(self):
        var_type = self.parse_advance()
        name = self.parse_advance(TokenType.TOKEN_IDENTIFIER)
        expression = None
        if self.parse_accept(TokenType.TOKEN_EQ):
            expression = self.parse_expression()
        return VarStatement(var_type, name, expression)

    def parse_if_statement(self):
        self.parse_advance()
        condition = self.parse_expression()
        self.parse_advance(TokenType.TOKEN_THEN)
        then_block = self.parse_block_statement([TokenType.TOKEN_ELIF, TokenType.TOKEN_ELSE, TokenType.TOKEN_END])
        else_block = None

        if self.parse_match(TokenType.TOKEN_ELSE):
            else_block = self.parse_statement()
        else:
            self.parse_advance()

        return IfStatement(condition, then_block, else_block)

    def parse_else_statement(self):
        self.parse_advance()
        return ElseStatement(self.parse_block_statement([TokenType.TOKEN_END]))

    def parse_extern_statement(self):
        self.parse_advance()
        return ExternStatement(self.parse_advance(TokenType.TOKEN_IDENTIFIER))

    def parse_include_statement(self):
        self.parse_advance()
        return IncludeStatement(self.parse_advance(TokenType.TOKEN_STRING))

    def parse_return_statement(self):
        self.parse_advance()
        expression = None
        if not self.parse_match(TokenType.TOKEN_END):
            expression = self.parse_expression()
        return ReturnStatement(expression)

    def parse_statement(self):
        if not self.token or self.token.kind == TokenType.TOKEN_EOF:
            return None
        if self.parse_match(TokenType.TOKEN_EXTERN):
            return self.parse_extern_statement()
        elif self.parse_match(TokenType.TOKEN_DEF):
            return self.parse_def_statement()
        elif self.parse_match(TokenType.TOKEN_PUB):
            self.parse_advance()
            if self.parse_match(TokenType.TOKEN_DEF):
                return self.parse_pub_def_statement()
            raise Exception("Error. pub can only be used with a def token.")
        elif self.parse_match(TokenType.TOKEN_IDENTIFIER):
            return self.parse_identifier_statement()
        elif self.parse_token_matches([TokenType.TOKEN_INT8, TokenType.TOKEN_INT16, TokenType.TOKEN_INT32, TokenType.TOKEN_INT64, TokenType.TOKEN_FLOAT64]):
            return self.parse_var_statement()
        elif self.parse_match(TokenType.TOKEN_IF):
            return self.parse_if_statement()
        elif self.parse_match(TokenType.TOKEN_ELSE):
            return self.parse_else_statement()
        elif self.parse_match(TokenType.TOKEN_INCLUDE):
            return self.parse_include_statement()
        elif self.parse_match(TokenType.TOKEN_RETURN):
            return self.parse_return_statement()
        return None

    def parse_literal(self):
        return LiteralExpression(self.parse_advance())

    def parse_args_expression(self):
        args = []

        self.parse_advance(TokenType.TOKEN_LEFT_PAREN)

        if self.token.kind == TokenType.TOKEN_RIGHT_PAREN:
            self.parse_advance()
            return args

        while not self.parse_match(TokenType.TOKEN_RIGHT_PAREN):
            args.append(self.parse_expression())
            if not self.parse_match(TokenType.TOKEN_RIGHT_PAREN):
                self.parse_advance(TokenType.TOKEN_COMMA)

        self.parse_advance(TokenType.TOKEN_RIGHT_PAREN)
        return args

    def parse_proc_call_statement(self, name):
        args = self.parse_args_expression()
        return CallProcStatement(name, args)

    def parse_identifier_statement(self):
        name = self.parse_advance()
        if self.token.kind == TokenType.TOKEN_LEFT_PAREN:
            return self.parse_proc_call_statement(name)
        return None

    def parse_identifier_literal(self):
        name = self.parse_advance()
        if self.parse_match(TokenType.TOKEN_LEFT_PAREN):
            args = self.parse_args_expression()
            return CallProcExpression(name, args)
        return LiteralExpression(name)

    def parse_primary(self):
        if self.parse_match(TokenType.TOKEN_LEFT_PAREN):
            self.parse_advance()
            exp = self.parse_expression()
            self.parse_advance(TokenType.TOKEN_RIGHT_PAREN)
            return exp
        elif self.parse_match(TokenType.TOKEN_IDENTIFIER):
            return self.parse_identifier_literal()
        elif self.parse_token_matches([TokenType.TOKEN_DIGIT, TokenType.TOKEN_STRING, TokenType.TOKEN_DECIMAL]):
            return self.parse_literal()
        return None

    def parse_unary(self):
        while self.parse_match(TokenType.TOKEN_NOT) or self.parse_match(TokenType.TOKEN_DASH):
            operator = self.parse_advance()
            right = self.parse_unary()
            return UnaryExpression(right, operator)
        return self.parse_primary()

    def parse_factor(self):
        exp = self.parse_unary()
        while self.parse_match(TokenType.TOKEN_SLASH) or self.parse_match(TokenType.TOKEN_STAR):
            operator = self.parse_advance()
            right = self.parse_unary()
            exp = BinaryExpression(exp, right, operator)
        return exp

    def parse_term(self):
        exp = self.parse_factor()
        while self.parse_match(TokenType.TOKEN_DASH) or self.parse_match(TokenType.TOKEN_PLUS):
            operator = self.parse_advance()
            right = self.parse_factor()
            exp = BinaryExpression(exp, right, operator)
        return exp

    def parse_comparison(self):
        exp = self.parse_term()
        while self.parse_match(TokenType.TOKEN_ISG) or self.parse_match(TokenType.TOKEN_ISGE) or self.parse_match(TokenType.TOKEN_ISL) or self.parse_match(TokenType.TOKEN_ISLE):
            operator = self.parse_advance()
            right = self.parse_term()
            exp = CompareExpression(exp, right, operator)
        return exp

    def parse_equality(self):
        exp = self.parse_comparison()
        while self.parse_match(TokenType.TOKEN_ISNEQ) or self.parse_match(TokenType.TOKEN_ISEQ):
            operator = self.parse_advance()
            right = self.parse_comparison()
            exp = CompareExpression(exp, right, operator)
        return exp

    def parse_and_expression(self):
        exp = self.parse_equality()

        while self.parse_match(TokenType.TOKEN_AND):
            operator = self.parse_advance()
            right = self.parse_equality()
            exp = LogicalExpression(exp, right, operator)
        return exp

    def parse_or_expression(self):
        exp = self.parse_and_expression()

        while self.parse_match(TokenType.TOKEN_OR):
            operator = self.parse_advance()
            right = self.parse_and_expression()
            exp = LogicalExpression(exp, right, operator)
        return exp

    def parse_ternary_if_expression(self):
        condition = self.parse_expression()
        self.parse_advance(TokenType.TOKEN_QUESTION)
        then_expression = self.parse_expression()
        self.parse_advance(TokenType.TOKEN_COLON)
        else_expression = self.parse_expression()
        return TernaryExpression(condition, then_expression, else_expression)

    def parse_expression(self):
        if self.parse_match(TokenType.TOKEN_IF):
            self.parse_advance()
            return self.parse_ternary_if_expression()
        return self.parse_or_expression()
