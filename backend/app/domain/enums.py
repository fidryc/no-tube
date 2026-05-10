import enum


class Roles(enum.Enum):
    USER = "USER"
    ADMIN = "ADMIN"
    

class ProcessingStatuses(enum.Enum):
    DRAFT = "DRAFT"
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    READY = "READY"
    FAILED = "FAILED"


class Visibility(enum.Enum):
    PUBLIC = "PUBLIC" # доступно всем
    PRIVATE = "PRIVATE" # доступно только владельцу
    SUBSCRIPTION = "SUBSCRIPTION" # доступно владельцу и его платным подписчикам

    
class PaymentStatuses(enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    FAILED = "FAILED"
    