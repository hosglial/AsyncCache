# -*- coding: utf-8 -*-
from functools import wraps
import logging
from asyncio import Event
from collections.abc import MutableMapping
from typing import Callable, TypeVar, Any, Hashable, Optional

from cachetools.keys import hashkey

_KEY = TypeVar("_KEY")
_HashableTuple = tuple[Hashable, ...]

_logger = logging.getLogger('asynccachetools')


def acached(cache: MutableMapping[_KEY, Any],
            key: Callable[..., _KEY] = hashkey,
            events: Optional[dict[_HashableTuple, Event]] = None
            ):
    """
    A wrapper over cachetools for use with asynchronous functions

    Uses event to synchronize the simultaneous execution of coroutines with the same arguments
    """
    if events is None:
        events = dict()

    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)

            # if ellipsis in args or kwargs - caching disabled
            if ... in args or ... in kwargs.values():
                return await func(*args, **kwargs)

            try:
                if k in events:  # if k present in events, wait for another coroutine to complete
                    await events[k].wait()

                result = cache[k]  # cache hit
                _logger.debug(f'Value of {func.__name__} with args {k} found in cache')

            except KeyError:  # cache miss
                _logger.debug(f'Value of {func.__name__} with args {k} not found in cache, executing')

                events[k] = Event()  # event is put into the dictionary, the other coroutines stand by.

                result = await func(*args, **kwargs)

                cache[k] = result
            finally:
                if k in events:  # setting event, then delete it
                    events[k].set()
                    del events[k]

            return result

        return wrapper

    return decorator
