#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""
Error handling rules
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_connect_api.kafka_connect_api import Connector
    from kafka_connect_watcher.cluster import ConnectCluster
    from kafka_connect_watcher.config import Config

import re
from copy import deepcopy
from queue import Queue
from threading import Thread

from compose_x_common.compose_x_common import (
    get_duration_timedelta,
    keyisset,
    set_else_none,
)

from kafka_connect_watcher.connectors_eval import evaluate_connector_status
from kafka_connect_watcher.logger import LOG
from kafka_connect_watcher.threads_settings import NUM_THREADS
from kafka_connect_watcher.tools import import_regexes


class EvaluationRule:
    """
    Error handling rule
    """

    config_key: str = "evaluation_rules"

    def __init__(self, rule_definition: dict, watcher_config: Config):
        if not isinstance(rule_definition, dict):
            raise TypeError(
                "rule_definition must be a dict. Got", type(rule_definition)
            )
        self.definition = rule_definition
        self._original_definition = deepcopy(rule_definition)
        if not keyisset("include_regex", self.definition):
            LOG.debug("NO INCLUDE REGEX. CONSIDERING ALL CONNECTORS")
            self.include_regexes: list[re.Pattern] = [re.compile(r"(.*)")]
        else:
            self.include_regexes: list[re.Pattern] = import_regexes(
                self.definition["include_regex"]
            )
        if not keyisset("exclude_regex", self.definition):
            LOG.debug("NO exclude REGEX.")
            self.exclude_regexes: list[re.Pattern] = []
        else:
            self.exclude_regexes: list[re.Pattern] = import_regexes(
                self.definition["exclude_regex"]
            )

        self.ignore_paused = keyisset("ignore_paused", self.definition)
        self.ignore_unassigned = keyisset("ignore_unassigned", self.definition)
        self.auto_correct_rules: list[AutoCorrectRule] = [
            AutoCorrectRule(config, watcher_config)
            for config in set_else_none(
                "auto_correct_actions", self.original_config, alt_value=[]
            )
        ]

    @property
    def original_config(self) -> dict:
        return self._original_definition

    def filter_out_connector(self, connector_name: str, cluster: ConnectCluster):
        if self.exclude_regexes:
            for regex in self.exclude_regexes:
                if regex.match(connector_name):
                    LOG.info(
                        f"{cluster.name} - Connector {connector_name} ignored by exclude_regex"
                    )
                    return False
        for regex in self.include_regexes:
            LOG.debug(regex.pattern)
            LOG.debug(regex.match(connector_name))
            if regex.match(connector_name):
                return True

    def execute(self, connect: ConnectCluster) -> None:
        """
        Scans the connectors, matches the ones invalid and not healthy.
        When the connector status is RUNNING, we check all the tasks too to be sure.
        When paused, if we ignore paused connectors, skip
        """
        connectors_total: int = len(connect.cluster.connectors)
        connectors_to_handle: list[Connector] = []
        for connector_name in list(connect.cluster.connectors.keys()):
            if self.filter_out_connector(connector_name, connect):
                connectors_to_handle.append(connect.cluster.connectors[connector_name])
        connectors_to_fix: list[Connector] = []

        connectors_count: int = len(connectors_to_handle)
        ignored_connectors: int = connectors_total - connectors_count
        paused_connectors: int = 0
        unassigned_connectors: int = 0
        running_connectors: int = 0

        connectors_processing_queue = Queue()
        for connector in connectors_to_handle:
            connectors_processing_queue.put(
                [
                    self,
                    connect,
                    connector,
                    running_connectors,
                    paused_connectors,
                    unassigned_connectors,
                    connectors_to_fix,
                ],
                False,
            )
        _processes: list[Thread] = []
        for _ in range(NUM_THREADS):
            __process = Thread(
                target=evaluate_connector_status,
                daemon=True,
                args=(connectors_processing_queue,),
            )
            _processes.append(__process)
            __process.start()
        for _process in _processes:
            _process.join()
        connect.metrics.update(
            {
                "total": connectors_total,
                "ignored": ignored_connectors,
                "count": connectors_count,
                "running": running_connectors,
                "unassigned": unassigned_connectors,
                "failed": len(connectors_to_fix),
            }
        )
        for connector in connectors_to_fix:
            for rule in self.auto_correct_rules:
                rule.process(connect, connector)


class AutoCorrectRule:
    """
    Actions to take when errors are detected.
    """

    def __init__(self, config: dict, watcher_config: Config):
        self._original_config = deepcopy(config)
        self.config = config
        self.action = self.config["action"]
        self.wait_for_status = set_else_none("wait_for_status", self.config, "5s")
        self.on_failure = set_else_none("on_failure", self.config)
        self.notify_targets = set_else_none("notify", self.config)
        self.notification_channels: list = []
        self.map_notify_targets(watcher_config)

    def map_notify_targets(self, watcher_config: Config):
        """Maps the notification_channels to the rule notify targets"""
        for _notify_target in self.notify_targets:
            _target_path = _notify_target["target"]
            if _target_path in watcher_config.notification_channels:
                self.notification_channels.append(
                    watcher_config.notification_channels[_target_path]
                )
            else:
                print(f"{_target_path} not defined in notification_channels")

    @property
    def original_config(self) -> dict:
        return self._original_config

    def process(self, cluster: ConnectCluster, connector: Connector):
        interval_delta = max(
            5, int(get_duration_timedelta(self.wait_for_status).total_seconds())
        )
        try:
            if self.action == "restart":
                connector.restart()
            elif self.action == "pause":
                connector.pause()
            elif self.action == "cycle":
                connector.cycle_connector()
            elif self.action == "notify_only":
                for channel in self.notification_channels:
                    channel.send_error_notification(cluster, connector)

            time.sleep(interval_delta)
            print("Post action status", connector.name, connector.status)
        except Exception as error:
            print(error)
            if self.on_failure:
                log_level_to_set = set_else_none("loglevel", self.on_failure)
                connector_class = set_else_none(
                    "connector.class",
                    connector.config,
                    set_else_none(
                        "class",
                        connector.config,
                    ),
                )
                if (
                    connector.state not in ["RUNNING", "PAUSED"]
                    and log_level_to_set
                    and connector_class in connector.cluster.loggers
                ):
                    connector.cluster.set_logger_log_level(
                        connector_class, log_level_to_set
                    )
