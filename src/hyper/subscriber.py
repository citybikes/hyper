import re
import os
import sys
import logging
import argparse

import zmq


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(stream=sys.stderr)],
    datefmt='%H:%M:%S',
)
log = logging.getLogger("subscriber")


class ZMQSubscriber:
    """ This class can be extended to create subscribers """
    def __init__(self, addr, topic):
        self.addr = addr
        self.topic = topic
        self.ctx = zmq.Context()

    def handle_message(self, topic, message):
        log.info("#%s: %s", topic, message)

    def reader(self):
        socket = self.ctx.socket(zmq.SUB)
        socket.connect(self.addr)
        socket.setsockopt_string(zmq.SUBSCRIBE, "")
        log.info("Waiting for messages on %s/#%s", self.addr, self.topic)

        while True:
            message = socket.recv_string()
            topic, data = message.split(' ', 1)

            if not re.match(self.topic, topic):
                log.debug('%s does not match set topic %s', topic, self.topic)
                continue

            self.handle_message(topic, data)


def main():
    ZMQ_ADDR = os.getenv('ZMQ_ADDR', 'tcp://127.0.0.1:5555')
    ZMQ_TOPIC = os.getenv('ZMQ_TOPIC', '')
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--addr', default=ZMQ_ADDR)
    parser.add_argument('-t', '--topic', default=ZMQ_TOPIC)
    args, _ = parser.parse_known_args()
    subscriber = ZMQSubscriber(args.addr, args.topic)
    subscriber.reader()

if __name__ == "__main__":
    main()
