import os
import sys
import signal
import logging
import asyncio
import argparse
import traceback
from collections import Counter
from functools import partial, wraps
from datetime import datetime

import zmq
import zmq.asyncio

from requests.adapters import HTTPAdapter

from pybikes import PyBikesScraper, get as pybikes_get
from pybikes.data import _traverse_lib
from pybikes.utils import keys
from pybikes.contrib import TSTCache

from hyper import __version__ as version
from hyper.srv import AdminServer
from hyper.scheduler import Scheduler, AsyncExecutor
from hyper.config import Config, read_config


DEFAULTS = {
    # update interval in seconds: int
    "interval": 180,
    # use default queue
    "queue": "default",
    # add a random component to execution time
    "jitter": 0,
    "concurrency": {
        "network": 20,
        "system": None,
    },
    "enabled": True,
    "scraper": {
        "user_agent": f"pybikes - hyper {version}",
        "requests_timeout": 11,
        "retry": False,
        "retry_opts": {},
        "proxy_enabled": False,
        "ssl_verification": True,
        "proxies": {},
    },
}

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
N_WORKERS_PYBIKES = int(os.getenv('N_WORKERS_PYBIKES', 100))
N_WORKERS_QUEUE = int(os.getenv('N_WORKERS_QUEUE', 100))
CONFIG_FILE = os.getenv('HYPER_CONFIG', None)
ZMQ_LISTEN = os.getenv('ZMQ_LISTEN', 'tcp://127.0.0.1:5555')


logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stderr)],
    datefmt="%H:%M:%S",
)

# apscheduler is very loggy
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARN)
logging.getLogger('apscheduler.scheduler').setLevel(logging.WARN)

log = logging.getLogger("producer")

# XXX needed for pool exhaustion
adapter = HTTPAdapter(
    pool_connections=N_WORKERS_PYBIKES,
    pool_maxsize=N_WORKERS_QUEUE
)


def bound(fun, sem):
    @wraps(fun)
    async def _wrap(* args, ** kwargs):
        async with sem:
            r = await fun(* args, ** kwargs)
        return r
    return _wrap


async def run(config):
    schedule = config['schedule']
    s = Scheduler(* config['queues'])
    loop = asyncio.get_running_loop()
    executor = AsyncExecutor(loop, N_WORKERS_PYBIKES)
    admin = AdminServer()

    errors = {'counts': Counter(), 'traceback': {}}

    # Create a ZeroMQ context and socket for PUB
    zmq_context = zmq.asyncio.Context()
    zmq_socket = zmq_context.socket(zmq.PUB)
    zmq_socket.bind(ZMQ_LISTEN)

    async def cb(network, * args, ** kwargs):
        log.info("[%s] stations %d", network.tag, len(network.stations))
        channel = f"network:{network.__class__.__name__}:{network.tag}:update"
        log.info("[%s] Publishing %s", network.tag, channel)
        message = f"{channel} {network.to_json()}"
        await zmq_socket.send_string(message)

    async def eb(error, network, scraper, settings):
        errors['counts'][network.tag] += 1
        errors["traceback"].setdefault(
            network.tag, "".join(traceback.format_exception(error)[-2:])
        )

        log.error("[%s] %s", network.tag, error)

        # # XXX
        # # next time try using a proxy if a proxy can be used
        # scraper.proxy_enabled = True

    def shutdown():
        s.shutdown()
        admin.stop()

    async def update_station(network, station, scraper, settings):
        await executor.run_async(station.update, scraper)
        return station

    async def update_network(network, scraper, settings):
        await executor.run_async(network.update, scraper)

        if not network.sync:
            sem = asyncio.BoundedSemaphore(settings['concurrency']['network'])
            fun = bound(update_station, sem)
            futures = [fun(network, station, scraper, settings)
                       for station in network.stations]

            log.info("[%s] Waiting for %d futures", network.tag, len(futures))
            await asyncio.gather(* futures)
            log.info("[%s] Done for %d futures", network.tag, len(futures))

        return network

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    cache = TSTCache(delta=60)
    semaphores = {}

    # XXX: add 'randomization' of instances so 'concurrent' systems are
    # eventually executed on a different order, ie:
    # tasks = [nextbike, nextbike, nextbike, bicing ...]
    # becomes
    # tasks = [nextbike, bicing, velib, ..., nextbike]

    for mod, cls, i_data in _traverse_lib():
        try:
            instance = pybikes_get(i_data['tag'], key=getattr(keys, mod))
        except Exception as e:
            log.error("[%s] %s", i_data['tag'], e)
            continue

        settings = schedule[instance]

        if not settings['enabled']:
            log.debug("[%s] disabled, ignoring", instance.tag)
            continue

        interval = settings['interval']
        jitter = settings['jitter']
        scraper = PyBikesScraper(** settings['scraper'])
        # XXX still needed here?
        scraper.session.mount('http://', adapter)
        scraper.session.mount('https://', adapter)

        method = update_network

        concurrency = settings['concurrency']['system']
        queue = settings.get('queue', 'default')

        if instance.unifeed:
            scraper.cachedict = cache
            # XXX
            concurrency = 1 if concurrency is None else concurrency
            # queue = settings.get('queue', 'unifeed')

        if concurrency is not None:
            sem = semaphores.setdefault(
                instance.__class__.__name__,
                asyncio.BoundedSemaphore(concurrency)
            )
            method = bound(update_network, sem)

        fun = partial(method, instance, scraper, settings)

        s.schedule(
            fun, 'interval', seconds=interval, jitter=jitter,
            name=schedule.__transform_key__(instance),
            next_run_time=datetime.now(),
            misfire_grace_time=interval,
            callback=cb, errback=eb, queue=queue,
        )

    s.start()

    # start C&C server in a separate thread
    admin.start({
        'scheduler': s,
        'config': config,
        'errors': errors,
    })
    await s.wait()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', type=argparse.FileType('r'))
    args, _ = parser.parse_known_args()

    if args.config:
        config = read_config(args.config)
    elif CONFIG_FILE:
        config = read_config(open(CONFIG_FILE))
    else:
        config = {
            'schedule': Config(DEFAULTS, {}),
            'queues': [('default', 100)],
        }

    asyncio.run(run(config))


if __name__ == "__main__":
    main()
