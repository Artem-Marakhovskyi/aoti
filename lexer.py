import re

from token_enum import TokenEnum


class Token:
    def __init__(self, marker, lexeme):
        self.marker = marker
        self.lexeme = lexeme

    def __str__(self):
        return '( %s -> %s)' % (self.marker, self.lexeme)


class Lexer:
    def analyze(self, code: str):
        while len(code) > 0:
            code, token = self.__find_next_token(code)
            self.tokens_found.append(token)
        return self.tokens_found.copy()

    def __init__(self):
        self.lexical_rules = []
        self.tokens_found = []
        self.__insert_key_words()
        self.__insert_key_symbols()
        self.__insert_arithmetical_operations()
        self.__insert_assignment()
        self.__insert_variable()

    def __insert_key_words(self):
        self.__append_lexemes(
            ('cycle\s*\(', TokenEnum.CYCLE_FOR),
            ('cond', TokenEnum.CONDITION_IF),
            ('begin', TokenEnum.BLOCK_START),
            ('end', TokenEnum.BLOCK_END),
            ('eq|less|greater|less_eq|greater_eq', TokenEnum.COMPARABLE),
            ('false|False|true|True', TokenEnum.LITERAL_BOOLEAN))

    def __insert_key_symbols(self):
        self.__append_lexemes(
            ('{', TokenEnum.ARRAY_INDEX_START),
            ('}', TokenEnum.ARRAY_INDEX_END),
            ('\)', TokenEnum.CYCLE_PARENTHESIS_END),
            ('nl', TokenEnum.NEWLINE),
            ('\,', TokenEnum.COMMA))

    def __insert_arithmetical_operations(self):
        self.__append_lexemes(
            ('\d+', TokenEnum.LITERAL_NUMBER),
            ('plu|min|div|mul', TokenEnum.ARITHMETICAL_BINARY),
            ('inc', TokenEnum.ARITHMETICAL_UNARY))

    def __insert_assignment(self):
        self.__append_lexemes(
            ('assign', TokenEnum.ASSIGN))

    def __insert_variable(self):
        self.__append_lexemes(
            ('[a-zA-Z]+[a-zA-Z0-9]?', TokenEnum.VARNAME))

    def __append_lexemes(self, *regexes):
        for x in regexes:
            self.lexical_rules.append((re.compile(x[0]), x[1]))

    def __find_next_token(self, code) -> (str, Token):
        code = code.strip()
        for rule in self.lexical_rules:
            m = rule[0].match(code)
            if m is not None:
                return code[m.span()[1]:], Token(rule[1], code[:m.span()[1]])
        return code[1:], Token(TokenEnum.ERROR, code[:1])
