#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

import argparse
from os import path

from kafka_connect_watcher.config import Config
from kafka_connect_watcher.watcher import Watcher


def start_watcher():
    parser = argparse.ArgumentParser("Kafka Connect Watcher")
    parser.add_argument(
        "-c", "--config-file", help="The input configuration file", required=True
    )

    args = parser.parse_args()

    config = Config(path.abspath(args.config_file))
    watcher = Watcher()
    watcher.run(config)


if __name__ == "__main__":
    start_watcher()
