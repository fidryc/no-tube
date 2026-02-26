from typing import Any, Union

from app.repositories.filter.enum import Operation

class Filter:
    # example
    __conditions = {
        Operation.EQ: lambda obj, value: obj == value,
        Operation.NE: lambda obj, value: obj != value,
        Operation.LT: lambda obj, value: obj < value,
        Operation.LE: lambda obj, value: obj <= value,
        Operation.GT: lambda obj, value: obj >= value,
        Operation.GE: lambda obj, value: obj > value,
        Operation.IN: lambda obj, values: obj in values,
        Operation.NOT_IN: lambda obj, values: obj not in values
    }
    def __init__(self, col_title: str, value: Any, operation: Operation):
        self.__col_title = col_title
        self.__value = value
        self.__operation = operation
        
    def filter_value(self, obj: Any) -> Union[bool, Any]: pass
    
    
class IAgregator:
    def __init__(self, *conditions: Union["IOr", "IAnd", Filter]): pass
    
    
class IOr(IAgregator):
    pass


class IAnd(IAgregator):
    pass
