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
import threading
from asyncio import get_event_loop, new_event_loop, set_event_loop
from queue import Queue
from time import sleep

from kafka_connect_watcher.aws_emf import init_emf_config, publish_emf
from kafka_connect_watcher.cluster import ConnectCluster
from kafka_connect_watcher.logger import LOG
from kafka_connect_watcher.threads_settings import NUM_THREADS

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
        self.connect_clusters_processing_queue = Queue()
        self._threads: list[threading.Thread] = []

    def run(self, config: Config):
        clusters: list[ConnectCluster] = [
            ConnectCluster(cluster) for cluster in config.config["clusters"]
        ]
        init_emf_config(config)
        for _ in range(NUM_THREADS):
            _thread = threading.Thread(
                target=process_cluster,
                daemon=True,
                args=(self.connect_clusters_processing_queue,),
            )
            _thread.start()
            self._threads.append(_thread)

        try:
            while self.keep_running:
                for connect_cluster in clusters:
                    self.connect_clusters_processing_queue.put(
                        [
                            self,
                            config,
                            connect_cluster,
                        ],
                        False,
                    )
                self.connect_clusters_processing_queue.join()
                sleep(1)
        except KeyboardInterrupt:
            self.keep_running = False
            LOG.debug("\rExited due to Keyboard interrupt")

    def exit_gracefully(self, pid, pelse):
        print(pid, pelse)
        self.keep_running = False
        exit(0)


def process_cluster(queue: Queue):
    while FOREVER:
        if not queue.empty():
            watcher, config, connect_cluster = queue.get()
            if connect_cluster is None:
                break
            for handling_rule in connect_cluster.handling_rules:
                handling_rule.execute(connect_cluster)
            if connect_cluster.emf_enabled():
                try:
                    loop = get_event_loop()
                except RuntimeError:
                    loop = new_event_loop()
                set_event_loop(loop)
                publish_emf(config, connect_cluster)
            queue.task_done()
