import functools
from typing import Any, Awaitable, Callable, Coroutine, ParamSpec, TypeVar

from app.repositories.exceptions import BaseRepositoryException
from app.services.base_errs import BaseServiceErrs
from app.services.exception import BaseServiceException

P = ParamSpec("P")
R = TypeVar("R")

import functools
from typing import Awaitable, Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

def get_handler(
    service_exc: type[BaseServiceException],
) -> Callable[
    [str],
    Callable[
        [Callable[P, Awaitable[R]]],
        Callable[P, Awaitable[R]]
    ]
]:

    def add_context(
        context: str = "Without context",
    ) -> Callable[
        [Callable[P, Awaitable[R]]],
        Callable[P, Awaitable[R]]
    ]:

        def exc_handler(
            func: Callable[P, Awaitable[R]]
        ) -> Callable[P, Awaitable[R]]:

            @functools.wraps(func)
            async def wrapper(
                *args: P.args,
                **kwargs: P.kwargs
            ) -> R:
                try:
                    return await func(*args, **kwargs)

                except BaseRepositoryException as e:
                    raise service_exc(
                        f"{context}: DB err",
                        err=BaseServiceErrs.DB
                    ) from e

                except BaseServiceException:
                    raise

                except Exception as e:
                    print(e)
                    raise service_exc(
                        f"{context}: Unknown err",
                        err=BaseServiceErrs.UNKNOWN
                    ) from e

            return wrapper

        return exc_handler

    return add_context