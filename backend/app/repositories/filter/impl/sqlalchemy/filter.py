from sqlalchemy import and_, not_, or_
from typing import Any

from app.repositories.filter.enum import Operation
from app.repositories.filter.interface import IExpression, IFilter


class Filter(IFilter, IExpression):
    _conditions = {
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
    
    def to_expression(self, model):
        """
        The model is passed from which the attribute passed in col_title is attempted to be taken.
        """
        if not hasattr(model, self.__col_title):
            raise AttributeError(f"Model {model} has no column '{self.__col_title}'")
        return self._conditions[self.__operation](getattr(model, self.__col_title), self.__value)
        
class Logic(IExpression):
    _op = None
    def __init__(self, *conditions: IExpression):
        self.conditions: list[IExpression] = conditions
   
    def to_expression(self, model):
        return self._op(*[cond.to_expression(model=model) for cond in self.conditions])
       
        
class Or(Logic):
    _op = staticmethod(or_)


class And(Logic):
    _op = staticmethod(and_)


class Not(IExpression):
    _op = staticmethod(not_)
    
    def __init__(self, condition: IExpression):
        self.condition: IExpression = condition
    
    def to_expression(self, model):
        return self._op(self.condition.to_expression(model=model))
        
    
