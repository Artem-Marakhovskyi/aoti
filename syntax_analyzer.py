# Поместить '$', затем S в магазин;
# do
# 	{X=верхний символ магазина;
# if (X - терминал)
# 	if (X==InSym)
# 		{удалить X из магазина;
# 		InSym=очередной символ;
# 		}
# 	else {error(); break;}
# else if (X - нетерминал)
# 	if (M[X,InSym]=="X->Y1Y2...Yk")
# 	 {удалить X из магазина;
# 	  поместить Yk,Yk-1,...Y1 в магазин
# 		(Y1 на верхушку);
# 	  вывести правило X->Y1Y2...Yk;
# 	 }
# 	else {error(); break;} /*вход таблицы M пуст*/
#  }
# while (X!='$'); /*магазин пуст*/
# if (InSym != '$') error(); /*Не вся строка прочитана*/
from aifc import Error

from aoti.rules_enum import RulesEnum
from aoti.token_enum import TokenEnum


class SyntaxAnalyzer:
    def __init__(self, input):
        self.stack = LexemeStack()
        self.input = input
        self.rules = SyntaxTable()

    def analyze(self):
        self.stack.push(RulesEnum.STATEMENT)
        while not self.stack.isEmpty():
            stackTop = self.stack.peek()
            if isinstance(stackTop, TokenEnum):
                in_symbol = self.input[0].marker
                if stackTop == in_symbol:
                    self.stack.pop()
                    inp = self.input.pop(0)
                    print('Removed from input & stack: %s' % inp)
                else:
                    raise SyntaxAnalyzerError('Input symbol %s is not matched with stack top %s\r\n%s' % (stackTop, inp, self.getState()))
            else:
                rule = self.rules[stackTop]
                if rule != TokenEnum.ERROR:
                    tkn = self.input[0].marker
                    rule_elements = rule[tkn]
                    self.stack.pop()
                    for x in range(len(rule_elements)):
                        if rule_elements[len(rule_elements) - 1 - x] != RulesEnum.NONE:
                            self.stack.push(rule_elements[len(rule_elements) - 1 - x])
                    rule_applied = 'Rule applied: %s' % (','.join([str(x) for x in rule_elements]))
                    print('Rule applied: %s' % rule_applied)
                else:
                    raise SyntaxAnalyzerError('Syntax error happened.\r\n%s' % (self.getState()))

    def getState(self):
        str_state = 'Stack: '
        for x in self.stack:
            str_state += x
        str_state += '\r\nInput: '
        for x in self.input:
            str_state += str(x) + ', '
        return str_state


class SyntaxTable:
    def __init__(self):
        self.source = {
            RulesEnum.STATEMENT: {
                TokenEnum.CYCLE_FOR: [
                    TokenEnum.CYCLE_FOR,
                    RulesEnum.ASSIGNMENT,
                    TokenEnum.COMMA,
                    RulesEnum.RESULT_STATEMENT,
                    TokenEnum.COMMA,
                    RulesEnum.STATEMENT,
                    TokenEnum.CYCLE_PARENTHESIS_END,
                    TokenEnum.BLOCK_START,
                    RulesEnum.STATEMENT,
                    TokenEnum.BLOCK_END
                ],
                TokenEnum.CONDITION_IF: [
                    TokenEnum.CONDITION_IF,
                    RulesEnum.BINARY_OPERATION,
                    TokenEnum.BLOCK_START,
                    RulesEnum.STATEMENT,
                    TokenEnum.BLOCK_END
                ],
                TokenEnum.BLOCK_START: [
                    TokenEnum.BLOCK_START,
                    RulesEnum.STATEMENT,
                    TokenEnum.BLOCK_END
                ],
                TokenEnum.ARITHMETICAL_UNARY: [
                    TokenEnum.ARITHMETICAL_UNARY,
                    RulesEnum.VARIABLE
                ],
                TokenEnum.NEWLINE: [
                    TokenEnum.NEWLINE,
                    RulesEnum.STATEMENT
                ],
                TokenEnum.VARNAME: [
                    RulesEnum.ASSIGNMENT
                ]
            },
            RulesEnum.ASSIGNMENT: {
                TokenEnum.VARNAME: [
                    RulesEnum.VARIABLE,
                    TokenEnum.ASSIGN,
                    RulesEnum.RESULT_STATEMENT
                ],
            },
            RulesEnum.VARIABLE: {
                TokenEnum.VARNAME: [
                    TokenEnum.VARNAME,
                    RulesEnum.VARIABLE
                ],
                TokenEnum.ARRAY_INDEX_START: [
                    TokenEnum.ARRAY_INDEX_START,
                    RulesEnum.VARIABLE,
                    TokenEnum.ARRAY_INDEX_END
                ],
                TokenEnum.ASSIGN: [RulesEnum.NONE],
                TokenEnum.NEWLINE: [RulesEnum.NONE],
                TokenEnum.BLOCK_END: [RulesEnum.NONE],
            },
            RulesEnum.RESULT_STATEMENT: {
                TokenEnum.LITERAL_BOOLEAN: [
                    TokenEnum.LITERAL_BOOLEAN,
                    RulesEnum.NOT_EMPTY_RESULT_STATEMENT
                ],
                TokenEnum.ARITHMETICAL_UNARY: [
                    TokenEnum.ARITHMETICAL_UNARY,
                    RulesEnum.VARIABLE
                ],
                TokenEnum.COMMA: [
                    RulesEnum.NONE
                ],
                TokenEnum.NEWLINE: [
                    RulesEnum.NONE
                ],
                TokenEnum.VARNAME: [
                    RulesEnum.VARIABLE,
                    RulesEnum.NOT_EMPTY_RESULT_STATEMENT
                ],
                TokenEnum.LITERAL_NUMBER: [
                    TokenEnum.LITERAL_NUMBER,
                    RulesEnum.NOT_EMPTY_RESULT_STATEMENT
                ]
            },
            RulesEnum.NOT_EMPTY_RESULT_STATEMENT: {
                TokenEnum.COMPARABLE: [
                    RulesEnum.BINARY_OPERATION
                ],
                TokenEnum.ARITHMETICAL_BINARY: [
                    RulesEnum.BINARY_OPERATION
                ],
                TokenEnum.CYCLE_PARENTHESIS_END: [RulesEnum.NONE],
                TokenEnum.NEWLINE: [TokenEnum.NEWLINE, RulesEnum.NONE],
                TokenEnum.COMMA: [RulesEnum.NONE]
            },
            RulesEnum.UNARY_OPERATION: {
                TokenEnum.VARNAME: [
                    RulesEnum.UNARY_OPERATION,
                    RulesEnum.VARIABLE
                ]
            },
            RulesEnum.BINARY_OPERATION: {
                TokenEnum.COMPARABLE: [
                    TokenEnum.COMPARABLE,
                    RulesEnum.NOT_EMPTY_RESULT_STATEMENT
                ],
                TokenEnum.ARITHMETICAL_BINARY: [
                    TokenEnum.ARITHMETICAL_BINARY,
                    RulesEnum.NOT_EMPTY_RESULT_STATEMENT
                ]
            }
        }

    def __getitem__(self, item):
        return self.source.get(item, TokenEnum.ERROR)


class LexemeStack:
    def __init__(self):
        self.source = []

    def push(self, x):
        self.source.append(x)

    def peek(self):
        return self.source[-1]

    def pop(self):
        return self.source.pop(-1)

    def isEmpty(self):
        return len(self.source) == 0

    def __iter__(self):
        return iter(self.source)


class SyntaxAnalyzerError(Error):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message

    def __str__(self):
        return self.message
