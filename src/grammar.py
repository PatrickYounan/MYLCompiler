from token import TokenType, Token


class SyntaxLexer:

    def __init__(self):
        self.file = None
        self.head = ' '
        self.peek = ' '

    def error(self, message):
        raise Exception(message)

    def lex_advance(self):
        if self.file is not None:
            self.head = self.file.read(1).decode("utf-8")
        else:
            self.error("Lexer Issue: File needs to be set before advancing.")

    def peek_char(self):
        if self.file is not None:
            self.peek = self.file.read(1).decode("utf-8")
            self.file.seek(self.file.tell() - 1)
        else:
            self.error("Lexer Issue: File needs to be set before advancing.")

    def new_token_advance(self, t, data, advances):
        for x in range(0, advances):
            self.lex_advance()
        return Token(t, data)

    def next_identifier(self):
        identifier = ""
        while self.head.isalnum() or self.head == '_':
            identifier += self.head
            self.lex_advance()
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
        elif identifier == "int":
            return Token(TokenType.TOKEN_INT, identifier)

        return Token(TokenType.TOKEN_IDENTIFIER, identifier)

    def next_string(self):
        string = ""
        self.lex_advance()
        while self.head != '"':
            string += self.head
            self.lex_advance()
        self.lex_advance()
        return Token(TokenType.TOKEN_STRING, string)

    def next_digit(self):
        numeral = ""
        decimals = 0
        while self.head.isdigit() or self.head == '.':
            numeral += self.head
            if self.head == '.':
                decimals += 1
            self.lex_advance()

        if decimals > 1:
            error("A number cannot have more than 1 decimal point.")
        return Token(TokenType.TOKEN_DIGIT, numeral)

    def next_token(self):
        while True:
            if not self.head:
                return Token(TokenType.TOKEN_EOF, "")
            if self.head == '"':
                return next_string()
            elif self.head.isalpha() or self.head == '_':
                return self.next_identifier()
            elif self.head.isdigit():
                return self.next_digit()
            elif self.head == '(':
                return self.new_token_advance(TokenType.TOKEN_LEFT_PAREN, "(", 1)
            elif self.head == ')':
                return self.new_token_advance(TokenType.TOKEN_RIGHT_PAREN, ")", 1)
            elif self.head == '*':
                return self.new_token_advance(TokenType.TOKEN_STAR, "*", 1)
            elif self.head == '/':
                return self.new_token_advance(TokenType.TOKEN_SLASH, "/", 1)
            elif self.head == '-':
                return self.new_token_advance(TokenType.TOKEN_DASH, "-", 1)
            elif self.head == '+':
                return self.new_token_advance(TokenType.TOKEN_PLUS, "+", 1)
            elif self.head == ',':
                return self.new_token_advance(TokenType.TOKEN_COMMA, ",", 1)
            elif self.head == '.':
                return self.new_token_advance(TokenType.TOKEN_DOT, ".", 1)
            elif self.head == '=':
                self.lexr_peek()
                return self.new_token_advance(TokenType.TOKEN_ISEQ, "==", 2) if self.peek == '=' else new_token_advance(TokenType.TOKEN_EQ, "=", 1)
            elif self.head == "!":
                self.peek_char()
                return new_token_advance(TokenType.TOKEN_ISNEQ, "!=", 2) if self.peek == '=' else new_token_advance(TokenType.TOKEN_NOT, "!", 1)
            elif self.head == '>':
                self.peek_char()
                return new_token_advance(TokenType.TOKEN_ISGE, ">=", 2) if self.peek == '=' else new_token_advance(TokenType.TOKEN_ISG, ">", 1)
            elif self.head == '<':
                self.peek_char()
                return new_token_advance(TokenType.TOKEN_ISLE, "<=", 2) if self.peek == '=' else new_token_advance(TokenType.TOKEN_ISL, "<", 1)
            elif self.head == '|':
                self.peek_char()
                return new_token_advance(TokenType.TOKEN_OR, "||", 2) if self.peek == '|' else new_token_advance(TokenType.TOKEN_BITWISE_OR, "|", 1)
            elif self.head == '&':
                self.peek_char()
                return new_token_advance(TokenType.TOKEN_AND, "&&", 2) if self.peek == '&' else new_token_advance(TokenType.TOKEN_BITWISE_AND, "&", 1)
            else:
                self.lex_advance()

    def lex_file(self, path):
        self.file = open(path, "rb")
