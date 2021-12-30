from src.token import *
from src.compiler import Instruction, Compiler, Opcode
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


class CompareExpression(Node):

    def __init__(self, left, right, operator):
        self.left = left
        self.right = right
        self.operator = operator

    def compile(self, compiler):
        self.left.compile(compiler)
        compiler.instructions.append(Instruction(Opcode.MOV_TO_REG))
        self.right.compile(compiler)
        compiler.instructions.append(Instruction(Opcode.MOV_TO_REG))
        compiler.instructions.append(Instruction(Opcode.COMPARE_OP, self.operator, self.operator.data))


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
        if self.token.tok_type == TokenType.TOKEN_DIGIT:
            compiler.instructions.append(Instruction(Opcode.MOV_IMMI, self.token, self.token.data))
        elif self.token.tok_type == TokenType.TOKEN_STRING:
            compiler.instructions.append(Instruction(Opcode.MOV_IMMS, self.token, self.token.data))
        elif self.token.tok_type == TokenType.TOKEN_IDENTIFIER:
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

        if self.var_type.tok_type == TokenType.TOKEN_INT:
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
        self.condition.compile(compiler)
        compiler.scope += 1
        compiler.instructions.append(Instruction(Opcode.LABEL))

        for statement in self.then_block:
            statement.compile(compiler)
        compiler.instructions.append(Instruction(Opcode.ENDIF))
        compiler.scope -= 1

        if compiler.scope == 0:
            compiler.instructions.append(Instruction(Opcode.LABEL))


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
            compiler.instructions.append(Instruction(Opcode.MOV_TO_REG))
        compiler.instructions.append(Instruction(Opcode.CALL, self.name, self.name.data))


class IncludeStatement(Node):

    def __init__(self, name):
        self.name = name

    def compile(self, compiler):
        compiler.instructions.append(Instruction(Opcode.INCLUDE, self.name, self.name.data))


class ExternStatement(Node):

    def __init__(self, name):
        self.name = name

    def compile(self, compiler):
        compiler.instructions.append(Instruction(Opcode.EXTERN, self.name, self.name.data))


class Parser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.token = None

    def parse_advance(self, expecting=None):
        current_tok = self.token

        if expecting is not None and current_tok.tok_type != expecting:
            self.error("Expecting token type %s. Got %s instead." % (expecting.tok_type, current_tok.tok_type))

        self.token = self.lexer.next_token()
        if current_tok is None:
            current_tok = self.token
        return current_tok

    def parse_accept(self, t):
        return True and self.parse_advance() if self.token.tok_type == t else False

    def parse_match(self, t):
        return self.token.tok_type == t

    def parse_token_matches(self, types):
        return self.token.tok_type in types

    def parse_block_statement(self, endings):
        statements = []
        while not self.parse_token_matches(endings):
            statements.append(self.parse_statement())
        return statements

    def parse_def_statement(self):
        self.parse_advance()
        name = self.parse_advance(TokenType.TOKEN_IDENTIFIER)
        self.parse_advance(TokenType.TOKEN_LEFT_PAREN)
        # TODO: function arguments.
        self.parse_advance(TokenType.TOKEN_RIGHT_PAREN)

        def_type = None
        if self.parse_accept(TokenType.TOKEN_TYPE_DEFINE):
            def_type = self.parse_advance()

        block = self.parse_block_statement([TokenType.TOKEN_END])
        self.parse_advance(TokenType.TOKEN_END)
        return DefStatement(name, block, def_type)

    def parse_vardecl_statement(self):
        var_type = self.parse_advance()
        name = self.parse_advance(TokenType.TOKEN_IDENTIFIER)
        expression = None
        if self.parse_accept(TokenType.TOKEN_EQ):
            expression = self.parse_expression()
        return VarDeclStatement(var_type, name, expression)

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

    def parse_statement(self):
        if not self.token or self.token.tok_type == TokenType.TOKEN_EOF:
            return None
        if self.token.tok_type == TokenType.TOKEN_EXTERN:
            return self.parse_extern_statement()
        elif self.token.tok_type == TokenType.TOKEN_DEF:
            return self.parse_def_statement()
        elif self.token.tok_type == TokenType.TOKEN_IDENTIFIER:
            return self.parse_identifier_statement()
        elif self.token.tok_type == TokenType.TOKEN_INT:
            return self.parse_vardecl_statement()
        elif self.token.tok_type == TokenType.TOKEN_IF:
            return self.parse_if_statement()
        elif self.token.tok_type == TokenType.TOKEN_ELSE:
            return self.parse_else_statement()
        elif self.token.tok_type == TokenType.TOKEN_INCLUDE:
            return self.parse_include_statement()
        return None

    def parse_literal(self):
        return LiteralExpression(self.parse_advance())

    def parse_args_expression(self):
        args = []

        self.parse_advance(TokenType.TOKEN_LEFT_PAREN)

        if self.token.tok_type == TokenType.TOKEN_RIGHT_PAREN:
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
        if self.token.tok_type == TokenType.TOKEN_LEFT_PAREN:
            return self.parse_proc_call_statement(name)
        return None

    def parse_identifier_literal(self):
        name = self.parse_advance()
        return LiteralExpression(name)

    def parse_primary(self):
        if self.parse_match(TokenType.TOKEN_LEFT_PAREN):
            self.parse_advance()
            exp = self.parse_expression()
            self.parse_advance(TokenType.TOKEN_RIGHT_PAREN)
            return exp
        elif self.parse_match(TokenType.TOKEN_IDENTIFIER):
            return self.parse_identifier_literal()
        elif self.parse_match(TokenType.TOKEN_DIGIT) or self.parse_match(TokenType.TOKEN_STRING):
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

    def parse_expression(self):
        return self.parse_or_expression()
