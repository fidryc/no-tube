from typing import Any, Union

from sqlalchemy import ColumnElement

from app.repositories.filter.enum import Operation
from app.repositories.filter.interface import IAgregator


class Filter:
    __conditions = {
        Operation.EQ: lambda obj, value: obj == value,
        Operation.NE: lambda obj, value: obj != value,
        Operation.LT: lambda obj, value: obj < value,
        Operation.LE: lambda obj, value: obj <= value,
        Operation.GT: lambda obj, value: obj > value,
        Operation.GE: lambda obj, value: obj >= value,
        Operation.IN: lambda obj, values: obj.in_(values),
        Operation.NOT_IN: lambda obj, values: obj.not_in(values)
    }
    def __init__(self, col_title: str, value: Any, operation: Operation):
        """
        col_title - table column name
        value - value for operation
        operation - operations from enum Operation
        
        example of filter formation: get_by_filters(Filter("id", 5, Operation.EQ)) - line with id = 5
        """
        self.__col_title = col_title
        self.__value = value
        self.__operation = operation
        
    def filter_value(self, obj: Any) -> Union[bool, ColumnElement[bool]]:
        """
        The model is passed from which the attribute passed in col_title is attempted to be taken.
        """
        if not hasattr(obj, self.__col_title):
            return False
        return self.__conditions[self.__operation](getattr(obj, self.__col_title), self.__value)
        
        
class Agregator(IAgregator):
    def __init__(self, *conditions: Union["Or", "And", Filter]):
        self.conditions = conditions
       
        
class Or(Agregator):
    pass

class And(Agregator):
    pass
        
    
