import asyncio
from unittest.mock import Mock, AsyncMock

import pytest

from hyper.scheduler import Scheduler


@pytest.mark.asyncio
async def test_task_scheduling():
    scheduler = Scheduler()
    tasks = [Mock() for _ in range(10)]
    for t in tasks:
        scheduler.enqueue(t)
    scheduler.start()
    await asyncio.sleep(0)
    scheduler.shutdown()
    assert all((t.called for t in tasks))


@pytest.mark.asyncio
async def test_task_scheduling_multiple_queues():
    scheduler = Scheduler(('foo', 10), ('bar', 10), ('baz', 0))
    tasks_foo = [Mock() for _ in range(10)]
    for t in tasks_foo:
        scheduler.enqueue(t, queue='foo')

    tasks_bar = [Mock() for _ in range(10)]
    for t in tasks_bar:
        scheduler.enqueue(t, queue='bar')

    tasks_baz = [Mock() for _ in range(10)]
    for t in tasks_baz:
        scheduler.enqueue(t, queue='baz')

    scheduler.start()
    await asyncio.sleep(0)
    scheduler.shutdown()

    assert all((t.called for t in tasks_foo))
    assert all((t.called for t in tasks_bar))
    assert all((not t.called for t in tasks_baz))


@pytest.mark.asyncio
# XXX look into https://docs.python.org/3/library/unittest.mock.html#unittest.mock.AsyncMock
async def test_task_callback():
    async def some_task():
        return 42

    async def cb(result, * args, ** kwargs):
        pass

    async def eb(err, * args, ** kwargs):
        pass

    task = AsyncMock(some_task)
    scheduler = Scheduler()
    cbmock = AsyncMock(cb)
    ebmock = AsyncMock(eb)
    scheduler.enqueue(task, callback=cbmock, errback=ebmock)
    scheduler.start()
    await asyncio.sleep(0)
    scheduler.shutdown()

    assert task.called
    assert cbmock.called


@pytest.mark.asyncio
# XXX look into https://docs.python.org/3/library/unittest.mock.html#unittest.mock.AsyncMock
async def test_task_errback():
    async def some_task():
        return 42

    async def cb(result, * args, ** kwargs):
        pass

    async def eb(err, * args, ** kwargs):
        pass

    task = AsyncMock(some_task, side_effect=Exception())
    scheduler = Scheduler()
    cbmock = AsyncMock(cb)
    ebmock = AsyncMock(eb)
    scheduler.enqueue(task, callback=cbmock, errback=ebmock)

    scheduler.start()
    await asyncio.sleep(0)
    scheduler.shutdown()
    assert task.called
    assert ebmock.called
