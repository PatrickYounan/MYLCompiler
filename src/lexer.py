from src.token import TokenType, Token


class Lexer:

    def __init__(self, path):
        self.file = open(path, "rb")
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
        elif identifier == "i8":
            return Token(TokenType.TOKEN_INT8, identifier)
        elif identifier == "i16":
            return Token(TokenType.TOKEN_INT16, identifier)
        elif identifier == "i32":
            return Token(TokenType.TOKEN_INT32, identifier)
        elif identifier == "i64":
            return Token(TokenType.TOKEN_INT64, identifier)
        elif identifier == "double":
            return Token(TokenType.TOKEN_DOUBLE, identifier)
        elif identifier == "float":
            return Token(TokenType.TOKEN_FLOAT, identifier)
        elif identifier == "extern":
            return Token(TokenType.TOKEN_EXTERN, identifier)
        elif identifier == "include":
            return Token(TokenType.TOKEN_INCLUDE, identifier)
        elif identifier == "return":
            return Token(TokenType.TOKEN_RETURN, identifier)
        elif identifier == "pub":
            return Token(TokenType.TOKEN_PUB, identifier)

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
                return self.next_string()
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
                self.peek_char()
                return self.new_token_advance(TokenType.TOKEN_ISEQ, "==", 2) if self.peek == '=' else self.new_token_advance(TokenType.TOKEN_EQ, "=", 1)
            elif self.head == "!":
                self.peek_char()
                return self.new_token_advance(TokenType.TOKEN_ISNEQ, "!=", 2) if self.peek == '=' else self.new_token_advance(TokenType.TOKEN_NOT, "!", 1)
            elif self.head == '>':
                self.peek_char()
                return self.new_token_advance(TokenType.TOKEN_ISGE, ">=", 2) if self.peek == '=' else self.new_token_advance(TokenType.TOKEN_ISG, ">", 1)
            elif self.head == '<':
                self.peek_char()
                return self.new_token_advance(TokenType.TOKEN_ISLE, "<=", 2) if self.peek == '=' else self.new_token_advance(TokenType.TOKEN_ISL, "<", 1)
            elif self.head == '|':
                self.peek_char()
                return self.new_token_advance(TokenType.TOKEN_OR, "||", 2) if self.peek == '|' else self.new_token_advance(TokenType.TOKEN_BITWISE_OR, "|", 1)
            elif self.head == '&':
                self.peek_char()
                return self.new_token_advance(TokenType.TOKEN_AND, "&&", 2) if self.peek == '&' else self.new_token_advance(TokenType.TOKEN_BITWISE_AND, "&", 1)
            elif self.head == ':':
                return self.new_token_advance(TokenType.TOKEN_COLON, ":", 1)
            elif self.head == '?':
                return self.new_token_advance(TokenType.TOKEN_QUESTION, "?", 1)
            elif self.head == ":":
                return self.new_token_advance(TokenType.TOKEN_COLON, ":", 1)
            else:
                self.lex_advance()
