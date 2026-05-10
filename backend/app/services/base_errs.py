from enum import Enum


class BaseServiceErrs:
    INVALID_DATA = "INVALID_DATA"
    DB = "DB_ERROR"
    CACHE = "CACHE_ERROR"
    UNKNOWN = "UNKNOWN"