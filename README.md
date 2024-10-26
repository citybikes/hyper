# citybikes-hyper

Citybikes Hyper is the next-generation framework for executing pybikes by
leveraging zmq pubsub, asyncio queues and threadpool executors.

## Installation

```console
pip install .
```

## Usage

A producer script schedules pybikes tasks and publishes updated networks as
a JSON message over a ZMQ PUB socket.

```
$ python -m hyper.producer
...
15:40:09 | INFO | [velitul] stations 6
15:40:09 | INFO | [velitul] Publishing network:Cykleo:velitul:update
15:40:09 | INFO | [idecycle] stations 14
15:40:09 | INFO | [idecycle] Publishing network:Cykleo:idecycle:update
15:40:09 | INFO | [twisto-velo] stations 21
15:40:09 | INFO | [twisto-velo] Publishing network:Cykleo:twisto-velo:update
15:40:09 | INFO | [nextbike-leipzig] stations 122
15:40:09 | INFO | [nextbike-leipzig] Publishing network:Nextbike:nextbike-leipzig:update
```

Results can be retrieved over a ZMQ SUB socket. For example, by using the
log consumer

```
$ python -m hyper.consumer
15:40:59.916 | INFO | Waiting for messages on tcp://127.0.0.1:5555/#
15:41:03.498 | INFO | #network:Cykleo:velitul:update: {"tag": "velitul", ...
15:41:03.526 | INFO | #network:Cykleo:twisto-velo:update: {"tag": ...
...
```

See [examples/sqlite_consumer.py] for an example implementation of a consumer
that stores produced information on a local SQLite database.

```
$ python examples/sqlite_consumer.py
16:44:03.629 | INFO | Waiting for messages on tcp://127.0.0.1:5555/#
16:44:10.712 | INFO | Processing {'name': 'Vélitul', 'city': 'Laval', ...
16:44:10.714 | INFO | [velitul] Got 6 stations
16:44:10.715 | INFO | [velitul] Finished processing 6 stations
16:44:10.728 | INFO | Processing {'name': 'IDEcycle', 'city': 'Pau', ...
16:44:10.728 | INFO | [idecycle] Got 14 stations
16:44:10.729 | INFO | [idecycle] Finished processing 14 stations
```

```
$ sqlite3 citybikes.db
SQLite version 3.43.2 2023-10-10 13:08:14
Enter ".help" for usage hints.
sqlite> select count(*) from networks;
674
sqlite> select count(*) from stations;
70735
sqlite>
```

[examples/sqlite_consumer.py]: examples/sqlite_consumer.py

## Configuration

The producer is highly customizable to configure how each pybikes network is
scheduled, by pattern matching network identifiers. For example:

```python
from hyper.config import Config
from hyper.producer import DEFAULTS

schedule = Config(DEFAULTS, {
    # Run updates every 3 minutes
    ".*": {
        "interval": 180,
    },
    # Set a different interval for all GBFS networks
    "pybikes.gbfs::.*": {
        "interval": 300,
    },
    # The following changes only affects network with tag 'citi-bike-nyc'
    "pybikes.gbfs::citi-bike-nyc": {
        # add a 10s jitter between scheduled requests
        "jitter": 10,
        # scraper opts for this network
        "scraper": {
            "user-agent": "Agent 700",
            "requests_timeout": 42,
        }
    },
    "pybikes.nextbike::.*": {
        # use a different queue for nextbike
        "queue": "nextbike",
    }
})

queues = [
    # Default queue with 100 workers
    ("default", 100),
    # Use 50 workers on this queue
    ("nextbike", 50),
]
```

Pass the configuration file to the producer

```console
python -m hyper.producer -c config.py
```

For a full list of configuration options, see [defaults]

[defaults]: src/hyper/producer.py#L28

## Development

```console
pip install -e .
```
