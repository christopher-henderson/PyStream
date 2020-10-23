# MIT License
#
# Copyright (c) 2020 Christopher Henderson, chris@chenderson.org
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import itertools
from collections.abc import Iterable, Iterator, AsyncIterable, AsyncIterator
from collections import defaultdict
from inspect import iscoroutinefunction

from .._sync.stream import Stream

Enumeration = Stream.Enumeration


# @TODO heck yeah! Typing!
# import typing


##############################
# How to read this file.
##############################


##############################
# MAP
##############################


from builtins import map as ss_map


async def sa_map(f, stream):
    async for x in stream:
        yield f(x)


async def as_map(f, stream):
    for x in stream:
        yield await f(x)


async def aa_map(f, stream):
    async for x in stream:
        yield await f(x)


##############################
# FILTER
##############################

from builtins import filter as ss_filter


async def sa_filter(f, stream):
    async for x in stream:
        if f(x):
            yield x


async def as_filter(f, stream):
    for x in stream:
        if await f(x):
            yield x


async def aa_filter(f, stream):
    async for x in stream:
        if await f(x):
            yield x


##############################
# FILTER_FALSE
##############################

def ss_filter_false(f, stream):
    return ss_filter(lambda x: not f(x), stream)


async def sa_filter_false(f, stream):
    async for x in stream:
        if not f(x):
            yield x


async def as_filter_false(f, stream):
    for x in stream:
        if not await f(x):
            yield x


async def aa_filter_false(f, stream):
    async for x in stream:
        if not await f(x):
            yield x


##############################
# CHAIN
##############################

async def chain(*streams):
    async for x in flatten(streams):
        yield x


##############################
# FLATTEN
##############################


async def s_flatten(streams):
    for stream in streams:
        stream = coerce(stream)
        if is_async_stream(stream):
            async for x in stream:
                yield x
        else:
            for x in stream:
                yield x


async def a_flatten(streams):
    async for stream in streams:
        stream = coerce(stream)
        if is_async_stream(stream):
            async for x in stream:
                yield x
        else:
            for x in stream:
                yield x


##############################
# GROUP_BY
##############################

def ss_group_by(f, stream):
    groups = defaultdict(list)
    for x in stream:
        groups[f(x)].append(x)
    for group in groups.values():
        yield group


async def sa_group_by(f, stream):
    groups = defaultdict(list)
    async for x in stream:
        groups[f(x)].append(x)
    for group in groups.values():
        yield group


async def as_group_by(f, stream):
    groups = defaultdict(list)
    for x in stream:
        groups[await f(x)].append(x)
    for group in groups.values():
        yield group


async def aa_group_by(f, stream):
    groups = defaultdict(list)
    async for x in stream:
        groups[await f(x)].append(x)
    for group in groups.values():
        yield group


##############################
# INSPECT
##############################

def ss_inspect(f, stream):
    for x in stream:
        f(x)
        yield x


async def sa_inspect(f, stream):
    async for x in stream:
        f(x)
        yield x


async def as_inspect(f, stream):
    for x in stream:
        await f(x)
        yield x


async def aa_inspect(f, stream):
    async for x in stream:
        await f(x)
        yield x


##############################
# REPEAT
##############################

def repeat(x):
    while True:
        yield x


##############################
# SKIP_WHILE
##############################


from itertools import dropwhile as ss_skip_while


async def sa_skip_while(f, stream):
    async for x in stream:
        if not f(x):
            yield x
            break
    async for x in stream:
        yield x


async def as_skip_while(f, stream):
    for x in stream:
        if not await f(x):
            yield x
            break
    for x in stream:
        yield x


async def aa_skip_while(f, stream):
    async for x in stream:
        if not await f(x):
            yield x
            break
    async for x in stream:
        yield x


##############################
# TAKE_WHILE
##############################


from itertools import takewhile as ss_take_while


async def sa_take_while(f, stream):
    async for x in stream:
        if f(x):
            yield x
        else:
            break


async def as_take_while(f, stream):
    for x in stream:
        if await f(x):
            yield x
        else:
            break


async def aa_take_while(f, stream):
    async for x in stream:
        if await f(x):
            yield x
        else:
            break


##############################
# ENUMERATE
##############################


from builtins import enumerate as b_enumerate


def s_enumerate(stream):
    return map(lambda x: Enumeration(*x), b_enumerate(stream))


async def a_enumerate(stream):
    count = 0
    async for x in stream:
        yield Enumeration(count, x)
        count += 1

##############################
# SKIP
##############################


def s_skip(stream, limit):
    for _ in range(limit):
        try:
            next(stream)
        except StopIteration:
            break
    for x in stream:
        yield x


async def a_skip(stream, limit):
    for _ in range(limit):
        try:
            await stream.__anext__()
        except StopAsyncIteration:
            break
    async for x in stream:
        yield x


##############################
# TAKE
##############################


def s_take(stream, limit):
    for _ in range(limit):
        try:
            yield next(stream)
        except StopIteration:
            break


async def a_take(stream, limit):
    for _ in range(limit):
        try:
            yield await stream.__anext__()
        except StopAsyncIteration:
            break

##############################
# ZIP
##############################


async def zip(*streams):
    streams = [coerce(stream) for stream in streams]
    while True:
        try:
            group = list()
            for stream in streams:
                group.append(await stream.__anext__() if is_async_stream(stream) else next(stream))
            yield tuple(group)
        except StopIteration:
            break
        except StopAsyncIteration:
            break

##############################
# POOL
##############################


def s_pool(stream, size):
    p = list()
    for x in stream:
        p.append(x)
        if len(p) == size:
            yield p
            p = list()
    if len(p) != 0:
        yield p


async def a_pool(stream, size):
    p = list()
    async for x in stream:
        p.append(x)
        if len(p) == size:
            yield p
            p = list()
    if len(p) != 0:
        yield p


##############################
# SORT
##############################

s_sort = sorted


async def a_sort(stream):
    for x in sorted([x async for x in stream]):
        yield x


##############################
# REVERSE
##############################


def s_reverse(stream):
    for x in reversed([x for x in stream]):
        yield x


async def a_reverse(stream):
    for x in reversed([x async for x in stream]):
        yield x


##############################
# DISTINCT
##############################

def s_distinct(stream):
    seen = set()
    for x in stream:
        if x in seen:
            continue
        seen.add(x)
        yield x


async def a_distinct(stream):
    seen = set()
    async for x in stream:
        if x in seen:
            continue
        seen.add(x)
        yield x


##############################
# DISTINCT_WITH
##############################

def ss_distinct_with(f, stream):
    seen = set()
    for x in stream:
        h = f(x)
        if h in seen:
            continue
        seen.add(h)
        yield x


async def sa_distinct_with(f, stream):
    seen = set()
    async for x in stream:
        h = f(x)
        if h in seen:
            continue
        seen.add(h)
        yield x


async def as_distinct_with(f, stream):
    seen = set()
    for x in stream:
        h = await f(x)
        if h in seen:
            continue
        seen.add(h)
        yield x


async def aa_distinct_with(f, stream):
    seen = set()
    async for x in stream:
        h = await f(x)
        if h in seen:
            continue
        seen.add(h)
        yield x


##############################
# FOR_EACH
##############################


def ss_for_each(f, stream):
    for x in stream:
        f(x)
        yield


async def as_for_each(f, stream):
    for x in stream:
        await f(x)
        yield


async def sa_for_each(f, stream):
    async for x in stream:
        f(x)
        yield


async def aa_for_each(f, stream):
    async for x in stream:
        await f(x)
        yield


##############################
# STEP_BY
##############################


def s_step_by(stream, step):
    return itertools.islice(stream, 0, None, step)


async def a_step_by(stream, step):
    c = 0
    async for x in stream:
        if c % step == 0:
            yield x
        c += 1


##############################
# UTILS
##############################


def is_async_stream(stream):
    return isinstance(stream, AsyncIterator) or isinstance(stream, AsyncIterable)


def coerce(stream):
    if isinstance(stream, AsyncIterator):
        return stream
    if isinstance(stream, AsyncIterable):
        return stream.__aiter__()
    if isinstance(stream, Iterator):
        return stream
    if isinstance(stream, Iterable):
        return stream.__iter__()
    else:
        raise TypeError


def factory(s, a):
    def inner(stream, *args):
        stream = coerce(stream)
        if is_async_stream(stream):
            return a(stream, *args)
        return s(stream, *args)

    return inner


def higher_order_factory(ss, sa, _as, aa):
    def inner(f, stream):
        f_is_async = iscoroutinefunction(f)
        stream_is_async = is_async_stream(stream)
        if not f_is_async and not stream_is_async:
            return ss(f, stream)
        elif not f_is_async and stream_is_async:
            return sa(f, stream)
        elif f_is_async and not stream_is_async:
            return _as(f, stream)
        elif f_is_async and stream_is_async:
            return aa(f, stream)
        else:
            raise TypeError
    return inner


##############################
# FINAL_EXPORT_ALIASES
##############################


chain = chain
distinct = factory(s_distinct, a_distinct)
distinct_with = higher_order_factory(ss_distinct_with, sa_distinct_with, as_distinct_with, aa_distinct_with)
enumerate = factory(s_enumerate, a_enumerate)
filter = higher_order_factory(ss_filter, sa_filter, as_filter, aa_filter)
filter_false = higher_order_factory(ss_filter_false, sa_filter_false, as_filter_false, aa_filter_false)
flatten = factory(s_flatten, a_flatten)
for_each = higher_order_factory(ss_for_each, sa_for_each, as_for_each, aa_for_each)
group_by = higher_order_factory(ss_group_by, sa_group_by, as_group_by, aa_group_by)
inspect = higher_order_factory(ss_inspect, sa_inspect, as_inspect, aa_inspect)
map = higher_order_factory(ss_map, sa_map, as_map, aa_map)
pool = factory(s_pool, a_pool)
reverse = factory(s_reverse, a_reverse)
skip_while = higher_order_factory(ss_skip_while, sa_skip_while, as_skip_while, aa_skip_while)
skip = factory(s_skip, a_skip)
sort = factory(s_sort, a_sort)
step_by = factory(s_step_by, a_step_by)
take_while = higher_order_factory(ss_take_while, sa_take_while, as_take_while, aa_take_while)
take = factory(s_take, a_take)
