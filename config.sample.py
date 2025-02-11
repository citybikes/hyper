import os

from citybikes.hyper.config import Config

PROXY_HOST = os.getenv("PROXY_HOST", "localhost")
PROXY_PORT = os.getenv("PROXY_PORT", "8080")

defaults = {
    # update interval in seconds: int
    "interval": 180,
    # add a random component to execution time
    "jitter": 0,
    # set run concurrency
    "concurrency": {
        # per network (for async networks)
        "network": 20,
        # whole system (number of concurrent networks of this class)
        "system": None,
    },
    "enabled": True,
    "scraper": {
        "requests_timeout": 11,
        "retry": False,
        "retry_opts": {},
        "proxy_enabled": False,
        "ssl_verification": True,
        "proxies": {
            "http": "http://%s:%s" % (PROXY_HOST, PROXY_PORT),
            "https": "http://%s:%s" % (PROXY_HOST, PROXY_PORT),
        },
    },
}

schedule = Config(
    defaults, {
        ".*": {
            "enabled": False,
        },
        ".*bicing.*": {
            "enabled": True,
        }
    },
)

queues = [
    ("default", 100),
]
