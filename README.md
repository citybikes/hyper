<p align="center">
  <img alt="hyper pub/sub model" width="600px" src="https://github.com/user-attachments/assets/21557297-919e-464a-85e0-af4794a3066c"/>
</p>

# Hyper

Citybikes Hyper is a high-concurrency task scheduling system built for scraping
bike-sharing networks using [pybikes]. Network updates are published over a
ZeroMQ PUB socket, allowing external components to subscribe to live data
updates.

[pybikes]: /pybikes

This project is production ready, but in a beta state. Please report any bugs as an issue on the GitHub repository.

For more information see the guide on the [documentation](https://docs.citybik.es/hyper) website.

## Getting started

### Installation

```shell
pip install git+https://github.com/citybikes/hyper.git
```

### Usage

Start a publisher

```shell
$ hyper publisher
...
15:40:09 | INFO | [velitul] stations 6
15:40:09 | INFO | [velitul] Publishing network:Cykleo:velitul:update
15:40:09 | INFO | [idecycle] stations 14
15:40:09 | INFO | [idecycle] Publishing network:Cykleo:idecycle:update
15:40:09 | INFO | [twisto-velo] stations 21
15:40:09 | INFO | [twisto-velo] Publishing network:Cykleo:twisto-velo:u...
15:40:09 | INFO | [nextbike-leipzig] stations 122
15:40:09 | INFO | [nextbike-leipzig] Publishing network:Nextbike:nextbi...
```

Start a logging subscriber

```shell
$ hyper subscriber
15:40:59.916 | INFO | Waiting for messages on tcp://127.0.0.1:5555/#
15:41:03.498 | INFO | #network:Cykleo:velitul:update: {"tag": "velit ...
15:41:03.526 | INFO | #network:Cykleo:twisto-velo:update: {"tag": ...
```

See [examples/sqlite_subscriber.py] for an example implementation of a
subscriber that stores information on a local SQLite database.

[examples/sqlite_subscriber.py]: examples/sqlite_subscriber.py


## Development

```console
$ pip install -e .
```

## Contributing
Citybikes Hyper is **free, open-source software** licensed under **AGPLv3**.

You can open issues for bugs you've found or features you think are missing. You can also submit pull requests to this repository

**Chat on Matrix**: https://matrix.to/#/#citybikes:matrix.org

## License
Copyright (C) 2024 Awesome Enterprises SL

This program is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with this program. If not, see https://www.gnu.org/licenses/.

