"""
An example consumer that stores all produced information on an SQLite db.
"""

import os
import json
import logging
import argparse
import sqlite3

from hyper.consumer import ZMQConsumer


DB_URI = os.getenv("DB_URI", "citybikes.db")
ZMQ_ADDR = os.getenv("ZMQ_ADDR", "tcp://127.0.0.1:5555")

conn = sqlite3.connect(DB_URI)

cur = conn.cursor()
cur.executescript("""
    CREATE TABLE IF NOT EXISTS networks (
        tag TEXT PRIMARY KEY,
        name TEXT,
        latitude REAL,
        longitude REAL,
        meta BLOB
    ) WITHOUT ROWID;

    CREATE TABLE IF NOT EXISTS stations (
        hash TEXT PRIMARY KEY,
        name TEXT,
        latitude REAL,
        longitude REAL,
        stat BLOB,
        network_tag TEXT
    ) WITHOUT ROWID;
""")
conn.commit()

log = logging.getLogger("consumer")


class SqliteConsumer(ZMQConsumer):
    def handle_message(self, topic, message):
        network = json.loads(message)
        meta = network["meta"]
        log.info("Processing %s", meta)

        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO networks (tag, name, latitude, longitude, meta)
            VALUES (?, ?, ?, ?, json(?))
            ON CONFLICT(tag) DO UPDATE SET
                name=excluded.name,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                meta=json(excluded.meta)
        """,
            (
                network["tag"],
                meta["name"],
                meta["latitude"],
                meta["longitude"],
                json.dumps(meta),
            ),
        )

        conn.commit()

        log.info("[%s] Got %d stations" % (network["tag"], len(network["stations"])))

        data_iter = (
            (
                s["id"],
                s["name"],
                s["latitude"],
                s["longitude"],
                json.dumps(
                    {
                        "bikes": s["bikes"],
                        "free": s["free"],
                        "timestamp": s["timestamp"],
                        "extra": s["extra"],
                    }
                ),
                network["tag"],
            )
            for s in network["stations"]
        )

        cursor.executemany(
            """
            INSERT INTO stations (hash, name, latitude, longitude, stat, network_tag)
            VALUES (?, ?, ?, ?, json(?), ?)
            ON CONFLICT(hash) DO UPDATE SET
                name=excluded.name,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                stat=json(excluded.stat),
                network_tag=excluded.network_tag
        """,
            data_iter,
        )
        conn.commit()
        log.info(
            "[%s] Finished processing %d stations"
            % (network["tag"], len(network["stations"]))
        )


if __name__ == "__main__":
    ZMQ_ADDR = os.getenv("ZMQ_ADDR", "tcp://127.0.0.1:5555")
    ZMQ_TOPIC = os.getenv("ZMQ_TOPIC", "")
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--addr", default=ZMQ_ADDR)
    parser.add_argument("-t", "--topic", default=ZMQ_TOPIC)
    args, _ = parser.parse_known_args()
    consumer = SqliteConsumer(args.addr, args.topic)
    consumer.reader()
