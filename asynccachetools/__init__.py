# -*- coding: utf-8 -*-
from functools import wraps
import logging
from asyncio import Event
from collections.abc import MutableMapping
from typing import Callable, TypeVar, Any

from cachetools.keys import hashkey

_KEY = TypeVar("_KEY")

_logger = logging.getLogger('asynccachetools')


def acached(cache: MutableMapping[_KEY, Any],
            key: Callable[..., _KEY] = hashkey
            ):
    """
    A wrapper over cachetools for use with asynchronous functions

    Uses event to synchronize the simultaneous execution of coroutines with the same arguments
    """
    # словарь с events, ключи - tuple из названия функции и её аргументов
    events: dict[tuple, Event] = dict()

    def decorator(func):

        @wraps(func)
        async def wrapper(*args, **kwargs):
            k = key(*args, **kwargs)

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