import asyncio
import logging

from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor

from apscheduler.schedulers.asyncio import AsyncIOScheduler

log = logging.getLogger('scheduler')


class Scheduler:
    """ This class can schedule tasks that get queued and executed. It does
    use native queues instead of whatever APScheduler provides, thus using
    the scheduler only for scheduling """

    def __init__(self, * qworkers):
        if len(qworkers) == 0:
            qworkers = [('default', 10)]

        self.queues = {}
        self.qworkers = qworkers

        for queues, workers in self.qworkers:
            queues = [queues] if not isinstance(queues, list) else queues
            for queue in queues:
                self.queues.setdefault(queue, asyncio.Queue())

        self.scheduler = AsyncIOScheduler()
        self.workers = []

    @staticmethod
    async def default_callback(result, * args, ** kwargs):
        return result

    @staticmethod
    async def default_errback(error, * args, ** kwargs):
        log.error(error)

    def start(self):
        for queues, n in self.qworkers:
            queues = [queues] if not isinstance(queues, list) else queues
            for i in range(n):
                t = asyncio.create_task(self.worker(f'worker-{i}', queues))
                self.workers.append(t)

        self.scheduler.start()

    def shutdown(self):
        log.info("Shutting down")

        for w in self.workers:
            w.cancel()

        self.scheduler.shutdown()


    def schedule(self, f, * args, callback=None, errback=None, queue='default',
                 ** kwargs):
        def fun(): self.enqueue(f, callback, errback, queue)
        return self.scheduler.add_job(fun, * args, ** kwargs)


    def enqueue(self, f, callback=None, errback=None, queue='default'):
        callback = callback or self.default_callback
        errback = errback or self.default_errback
        self.queues[queue].put_nowait((f, callback, errback))


    @asynccontextmanager
    async def get_item(self, queues):
        """gets the first available item in any of the queues"""
        while True:
            for queue in queues:
                q = self.queues[queue]
                try:
                    item = q.get_nowait()
                    try:
                        yield queue, * item
                    finally:
                        q.task_done()
                    return
                except asyncio.queues.QueueEmpty:
                    continue
            await asyncio.sleep(1)


    async def worker(self, name, queues):
        while True:
            try:
                async with self.get_item(queues) as item:
                    queue, f, callback, errback = item
                    try:
                        result = await f()
                        await callback(
                            result,
                            * getattr(f, 'args', []),
                            ** getattr(f, 'keywords', {})
                        )

                    except Exception as err:
                        await errback(
                            err,
                            * getattr(f, 'args', []),
                            ** getattr(f, 'keywords', {})
                        )
            except Exception as e:
                log.exception(e)


    async def wait(self):
        # wait until workers finish (killed)
        await asyncio.gather(*self.workers, return_exceptions=True)


    def qsize(self, queue=None):
        if not queue:
            return {qn: q.qsize() for qn, q in self.queues.items()}
        return self.queues[queue].qsize()



class AsyncExecutor:
    def __init__(self, loop, n_workers):
        self.loop = loop
        self.executor = ThreadPoolExecutor(max_workers=n_workers)

    async def run_async(self, f, * args):
        res = await self.loop.run_in_executor(self.executor, f, * args)
        return res
