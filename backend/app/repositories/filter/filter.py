from typing import Union
from enum import Enum
from typing import Any

from app.repositories.filter.enum import Operation


class Filter:
    def __init__(self, col_title: str, value: Any, operation: Operation):
        """
        col_title - table column name
        value - value for operation
        operation - operations from enum Operation
        
        example of filter formation: get_by_filters(Filter("id", 5, Operation.EQ)) - line with id = 5
        """
        self.col_title = col_title
        self.value = value
        self.operation = operation


class LogicTypes(Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    
    
class Logic:
    type: LogicTypes
    
    def __init__(self, *conditions: Union["Logic", Filter]):
        self.conditions = conditions
    
class And(Logic):
    type = LogicTypes.AND
    

class Or(Logic):
    type = LogicTypes.OR


class Not(Logic):
    type = LogicTypes.NOT
    
    def __init__(self, condition: Union["Logic", Filter]):
        super().__init__(condition)
