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
from datetime import datetime as dt
from queue import Queue
from time import sleep

from kafka_connect_watcher.aws_emf import (
    handle_watcher_emf,
    init_emf_config,
    publish_clusters_emf,
)
from kafka_connect_watcher.cluster import ConnectCluster
from kafka_connect_watcher.logger import LOG
from kafka_connect_watcher.threads_settings import NUM_THREADS

FOREVER = 42


class Watcher:
    """
    The Watcher class is the entry point to the program cycling over the different connect cluster, collecting metrics,
    handling exceptions and graceful shutdowns.
    """

    def __init__(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.keep_running: bool = True
        self.connect_clusters_processing_queue = Queue()
        self._threads: list[threading.Thread] = []
        self.metrics: dict = {
            "connect_clusters_total": 0,
            "connect_clusters_healthy": 0,
            "connect_clusters_unhealthy": 0,
        }

    def run(self, config: Config):
        LOG.info("Initializing the watcher")
        clusters: list[ConnectCluster] = [
            ConnectCluster(cluster, config) for cluster in config.config["clusters"]
        ]
        self.metrics.update({"connect_clusters_total": len(clusters)})
        init_emf_config(config)
        LOG.info("Watcher clusters initialized.")
        for _ in range(NUM_THREADS):
            _thread = threading.Thread(
                target=process_cluster,
                daemon=True,
                args=(self.connect_clusters_processing_queue,),
            )
            _thread.start()
            self._threads.append(_thread)
        LOG.info(
            "Watcher threads ({}) initialized. Processing clusters & evaluation rules.".format(
                NUM_THREADS
            )
        )
        try:
            while self.keep_running:
                now = dt.now()
                LOG.info("Clusters processing started")
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
                LOG.info(
                    "Clusters processing finished - {}s".format(
                        (dt.now() - now).total_seconds()
                    )
                )
                if config.emf_watcher_config:
                    handle_watcher_emf(config, self)
                sleep(config.scan_intervals)
                self.metrics.update(
                    {"connect_clusters_healthy": 0, "connect_clusters_unhealthy": 0}
                )
                LOG.debug("Watcher metrics: {}".format(self.metrics))
        except KeyboardInterrupt:
            self.keep_running = False
            LOG.debug("\rExited due to Keyboard interrupt")

    def exit_gracefully(self, pid, pelse):
        print(pid, pelse)
        self.keep_running = False
        exit(0)


def process_error_rules(
    handling_rule, connect_cluster: ConnectCluster, watcher: Watcher
):
    try:
        handling_rule.execute(connect_cluster)
        watcher.metrics["connect_clusters_healthy"] += 1
    except Exception as error:
        watcher.metrics["connect_clusters_unhealthy"] += 1
        LOG.exception(error)
        LOG.error(f"Failed to process the cluster {connect_cluster.name}")
    try:
        if connect_cluster.emf_config:
            publish_clusters_emf(connect_cluster)
    except Exception as error:
        LOG.exception(error)
        LOG.error(f"Failed to export EMF metrics for cluster {connect_cluster.name}")


def process_cluster(queue: Queue):
    while FOREVER:
        if not queue.empty():
            watcher, config, connect_cluster = queue.get()
            if connect_cluster is None:
                break
            for handling_rule in connect_cluster.handling_rules:
                process_error_rules(handling_rule, connect_cluster, watcher)
            queue.task_done()
