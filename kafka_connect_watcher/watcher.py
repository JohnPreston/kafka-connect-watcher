#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""
Main entrypoint of the python watcher
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_connect_watcher.config import Config

import signal
from datetime import datetime as dt
from datetime import timedelta as td

from aws_embedded_metrics import metric_scope
from time import sleep
from .cluster import ConnectCluster

from .logger import LOG

FOREVER = 42


class Watcher:
    """
    The Watcher class is the entry point to the program cycling over the different connect cluster, collecting metrics,
    handling exceptions and graceful shutdowns.
    """

    def __init__(self, config: Config):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.keep_running: bool = True

    def run(self, config: Config):
        clusters: list[ConnectCluster] = [ConnectCluster(cluster) for cluster in config.config["clusters"]]
        try:
            while self.keep_running:
                _loop_start = dt.now()
                _output_every = td(seconds=60)
                print("Hello")
                sleep(1)
        except KeyboardInterrupt:
            LOG.debug("\rExited due to Keyboard interrupt")
        except ChildProcessError as error:
            LOG.exception(error)
            LOG.error("One of the observers died.")

    def exit_gracefully(self, pid, pelse):
        print(pid, pelse)
        exit(0)
