from enum import Enum


class RulesEnum(Enum):
    STATEMENT = 0,
    ASSIGNMENT = 1,
    VARIABLE = 3,
    INDEX = 4,
    RESULT_STATEMENT = 5,
    NOT_EMPTY_RESULT_STATEMENT = 6,
    UNARY_OPERATION = 7,
    BINARY_OPERATION = 8,
    NONE = 9

