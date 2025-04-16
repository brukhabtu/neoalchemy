"""
Cypher keyword constants for Neo4j queries.

This module provides constants and enums for Cypher keywords to avoid
string literals in query building code. Using these constants helps prevent
typos, enables autocompletion, and improves maintainability.
"""

from enum import Enum


class KeywordEnum(str, Enum):
    """Base enum that inherits from str to allow enum values to be used in string context.
    
    This makes the enum members usable directly in string contexts without requiring .value.
    """
    
    def __str__(self):
        """Return the string value of the enum member."""
        return self.value


class ClauseKeyword(KeywordEnum):
    """Keywords for major Cypher clauses."""
    
    MATCH = "MATCH"
    OPTIONAL_MATCH = "OPTIONAL MATCH"
    WHERE = "WHERE"
    RETURN = "RETURN"
    CREATE = "CREATE"
    MERGE = "MERGE"
    DELETE = "DELETE"
    REMOVE = "REMOVE"
    SET = "SET"
    WITH = "WITH"
    UNWIND = "UNWIND"
    ORDER_BY = "ORDER BY"
    SKIP = "SKIP"
    LIMIT = "LIMIT"


class OperatorKeyword(KeywordEnum):
    """Keywords for Cypher operators."""
    
    # Comparison operators
    EQUALS = "="
    NOT_EQUALS = "<>"
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_THAN_EQUALS = ">="
    LESS_THAN_EQUALS = "<="
    
    # String operators
    STARTS_WITH = "STARTS WITH"
    ENDS_WITH = "ENDS WITH"
    CONTAINS = "CONTAINS"
    
    # Collection operators
    IN = "IN"
    ANY_IN = "ANY IN"
    ALL_IN = "ALL IN"
    
    # Null operators
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"


class LogicalKeyword(KeywordEnum):
    """Keywords for logical operations."""
    
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    XOR = "XOR"


class DirectionKeyword(KeywordEnum):
    """Keywords for ordering direction."""
    
    ASC = "ASC"
    DESC = "DESC"


class FunctionKeyword(KeywordEnum):
    """Keywords for Cypher functions."""
    
    # String functions
    TO_LOWER = "toLower"
    TO_UPPER = "toUpper"
    REPLACE = "replace"
    SUBSTRING = "substring"
    TRIM = "trim"
    LEFT = "left"
    RIGHT = "right"
    LTRIM = "lTrim"
    RTRIM = "rTrim"
    SPLIT = "split"
    REVERSE = "reverse"
    
    # Collection functions
    SIZE = "size"
    LENGTH = "length"
    COUNT = "count"
    COLLECT = "collect"
    HEAD = "head"
    LAST = "last"
    REDUCE = "reduce"
    EXTRACT = "extract"
    FILTER = "filter"
    
    # Mathematical functions
    ABS = "abs"
    CEIL = "ceil"
    FLOOR = "floor"
    ROUND = "round"
    SIGN = "sign"
    RAND = "rand"


# Re-export as simple constants for convenience
class CypherKeywords:
    """Constants for commonly used Cypher keywords."""
    
    # Clauses
    MATCH = ClauseKeyword.MATCH
    OPTIONAL_MATCH = ClauseKeyword.OPTIONAL_MATCH
    WHERE = ClauseKeyword.WHERE
    RETURN = ClauseKeyword.RETURN
    WITH = ClauseKeyword.WITH
    ORDER_BY = ClauseKeyword.ORDER_BY
    LIMIT = ClauseKeyword.LIMIT
    SKIP = ClauseKeyword.SKIP
    
    # Operators
    AND = LogicalKeyword.AND
    OR = LogicalKeyword.OR
    NOT = LogicalKeyword.NOT
    
    # Comparison
    EQUALS = OperatorKeyword.EQUALS
    NOT_EQUALS = OperatorKeyword.NOT_EQUALS
    GT = OperatorKeyword.GREATER_THAN
    LT = OperatorKeyword.LESS_THAN
    GTE = OperatorKeyword.GREATER_THAN_EQUALS
    LTE = OperatorKeyword.LESS_THAN_EQUALS
    
    # String
    STARTS_WITH = OperatorKeyword.STARTS_WITH
    ENDS_WITH = OperatorKeyword.ENDS_WITH
    CONTAINS = OperatorKeyword.CONTAINS
    
    # Collection
    IN = OperatorKeyword.IN
    ANY_IN = OperatorKeyword.ANY_IN
    
    # Null
    IS_NULL = OperatorKeyword.IS_NULL
    IS_NOT_NULL = OperatorKeyword.IS_NOT_NULL
    
    # Direction
    ASC = DirectionKeyword.ASC
    DESC = DirectionKeyword.DESC
    
    # Common functions
    COUNT = FunctionKeyword.COUNT
    LENGTH = FunctionKeyword.LENGTH
    TO_LOWER = FunctionKeyword.TO_LOWER
    TO_UPPER = FunctionKeyword.TO_UPPER