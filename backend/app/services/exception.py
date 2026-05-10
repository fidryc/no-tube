from app.services.base_errs import BaseServiceErrs


class BaseServiceException(Exception):
    def __init__(self, *args, err: BaseServiceErrs = BaseServiceErrs.UNKNOWN, **kwargs):
        super().__init__(*args, **kwargs)
        self.err = err