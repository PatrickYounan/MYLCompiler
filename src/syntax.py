from token import TokenType, Token
from ast import *
from grammar import SyntaxLexer


class SyntaxParser:

    def __init__(self, lexer):
        self.lexer = lexer
        self.token = None

    def parse_advance(self, expecting=None):
        current_tok = self.token

        if expecting is not None and current_tok.type != expecting:
            self.error("Expecting token type %s. Got %s instead." % (expecting.type, current_tok.type))

        self.token = self.lexer.next_token()
        if current_tok is None:
            current_tok = self.token
        return current_tok

    def parse_accept(self, t):
        return True and self.parse_advance() if self.token.type == t else False

    def parse_match(self, t):
        return self.token.type == t

    def parse_token_matches(self, types):
        return self.token.type in types

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

        return IfStatement(condition, then_block, else_block)

    def parse_else_statement(self):
        self.parse_advance()
        block = self.parse_block_statement([TokenType.TOKEN_END])
        return ElseStatement(block)

    def parse_extern_statement(self):
        self.parse_advance()
        including = self.parse_advance(TokenType.TOKEN_IDENTIFIER)
        return ExternStatement(including)

    def parse_statement(self):
        if not self.token or self.token.type == TokenType.TOKEN_EOF:
            return None
        if self.token.type == TokenType.TOKEN_EXTERN:
            return self.parse_extern_statement()
        elif self.token.type == TokenType.TOKEN_DEF:
            return self.parse_def_statement()
        elif self.token.type == TokenType.TOKEN_IDENTIFIER:
            return self.parse_identifier_statement()
        elif self.token.type == TokenType.TOKEN_INT:
            return self.parse_vardecl_statement()
        elif self.token.type == TokenType.TOKEN_IF:
            return self.parse_if_statement()
        elif self.token.type == TokenType.TOKEN_ELSE:
            return self.parse_else_statement()
        return None

    def parse_literal(self):
        return LiteralExpression(self.parse_advance())

    def parse_args_expression(self):
        args = []

        self.parse_advance(TokenType.TOKEN_LEFT_PAREN)

        if self.token.type == TokenType.TOKEN_RIGHT_PAREN:
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
        if self.token.type == TokenType.TOKEN_LEFT_PAREN:
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
            exp = BinaryExpression(exp, right, operator)
        return exp

    def parse_equality(self):
        exp = self.parse_comparison()
        while self.parse_match(TokenType.TOKEN_ISNEQ) or self.parse_match(TokenType.TOKEN_ISEQ):
            operator = self.parse_advance()
            right = self.parse_comparison()
            exp = BinaryExpression(exp, right, operator)
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
