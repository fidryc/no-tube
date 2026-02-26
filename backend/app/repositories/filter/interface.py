from typing import Any, Callable, Union

from app.repositories.filter.enum import Operation

class IFilter:
    _conditions: dict[Operation, Callable]
    def __init__(self, col_title: str, value: Any, operation: Operation):
        self.__col_title = col_title
        self.__value = value
        self.__operation = operation
    
class IExpression:
    def to_expression(self, model: Any): pass
