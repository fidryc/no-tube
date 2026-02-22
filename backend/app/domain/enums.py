import enum


class Roles(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    

class ProcessingStatuses(enum.Enum):
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"

class Visibility(enum.Enum):
    PUBLIC = "PUBLIC" # доступно всем
    PRIVATE = "PRIVATE" # доступно только владельцу
    UNLISTED = "UNLISTED" # доступно по ссылке