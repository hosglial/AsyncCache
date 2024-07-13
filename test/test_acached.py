# -*- coding: utf-8 -*-
import asyncio
from unittest.mock import AsyncMock

import pytest
from cachetools import LRUCache
from cachetools.keys import hashkey

from asynccachetools import acached


async def long_foo():
    await asyncio.sleep(1)


long_mock = AsyncMock()
long_mock.side_effect = long_foo


@pytest.mark.asyncio
async def test_all_args_caching():
    long_mock.reset_mock()

    @acached(LRUCache(maxsize=128))
    async def foo(_arg1, _arg2):
        await long_mock()

    await foo(1, 1)
    await foo(1, 1)

    long_mock.assert_called_once()


@pytest.mark.asyncio
async def test_single_arg_caching():
    long_mock.reset_mock()

    @acached(LRUCache(maxsize=128), key=lambda _arg1, _arg2: hashkey(_arg1))
    async def foo(_arg1, _arg2):
        await long_mock()

    await foo(1, 1)
    await foo(1, 2)

    long_mock.assert_called_once()


@pytest.mark.asyncio
async def test_simultanious_calls():
    long_mock.reset_mock()

    @acached(LRUCache(maxsize=128), key=lambda _arg1, _arg2: hashkey(_arg1))
    async def foo(_arg1, _arg2):
        await long_mock()

    tasks = [foo(1, 1) for _ in range(100)]

    await asyncio.gather(*tasks)

    long_mock.assert_called_once()
