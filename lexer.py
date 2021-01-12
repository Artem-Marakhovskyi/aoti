import re


class Lexeme:
    def __init__(self, marker, value):
        self.marker = marker
        self.value = value

    def __str__(self):
        return '[ %s -> %s]' % (self.marker, self.value)


class Lexer:
    def analyze(self, code: str):
        while len(code) > 0:
            code, lexeme = self.__find_next_lexeme(code)
            self.lexemes.append(lexeme)
        return self.lexemes.copy()

    def __init__(self):
        self.rules = []
        self.lexemes = []
        self.__insert_key_words()
        self.__insert_key_symbols()
        self.__insert_arithmetical_operations()
        self.__insert_assignment()
        self.__insert_variable()

    def __insert_key_words(self):
        self.__append_lexemes(
            ('cycle\s*\(', 'for'),
            ('cond', 'if'),
            ('begin', 'block-start'),
            ('end', 'block-end'),
            ('eq', '=='),
            ('less', '<'),
            ('greater', '>'),
            ('less_eq', '<='),
            ('greater_eq', '>='),
            ('false|False', 'Boolean False'),
            ('true|True', 'Boolean True'))

    def __insert_key_symbols(self):
        self.__append_lexemes(
            ('{', 'array_index_start'),
            ('}', 'array_index_end'),
            ('\(', 'parenthesis_start'),
            ('\)', 'parenthesis_end'),
            ('nl', 'statement-end'),
            ('\,', 'comma'))

    def __insert_arithmetical_operations(self):
        self.__append_lexemes(
            ('\d+', 'number'),
            ('plu', 'plus'),
            ('min', 'minus'),
            ('mul', 'mult'),
            ('div', 'div'),
            ('inc', '++'))

    def __insert_assignment(self):
        self.__append_lexemes(
            ('assign', '='))

    def __insert_variable(self):
        self.__append_lexemes(
            ('[a-zA-Z]+[a-zA-Z0-9]?', 'variable_name'))

    def __append_lexemes(self, *regexes):
        for x in regexes:
            self.rules.append((re.compile(x[0]), x[1]))

    def __find_next_lexeme(self, code) -> (str, Lexeme):
        code = code.strip()
        for rule in self.rules:
            m = rule[0].match(code)
            if m is not None:
                return code[m.span()[1]:], Lexeme(rule[1], code[:m.span()[1]])
        return code[1:], Lexeme('error', code[:1])
