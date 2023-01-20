#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""
Error handling rules
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_connect_api.kafka_connect_api import Cluster, Connector

import re
from time import sleep
from datetime import datetime as dt
from copy import deepcopy
from compose_x_common.compose_x_common import (
    set_else_none,
    keyisset,
    get_duration_timedelta,
)

from kafka_connect_watcher.tools import import_regexes


class ErrorHandlingRule:
    """
    Error handling rule
    """

    def __init__(self, rule_definition: dict):
        if not isinstance(rule_definition, dict):
            raise TypeError(
                "rule_definition must be a dict. Got", type(rule_definition)
            )
        self.definition = rule_definition
        self._original_definition = deepcopy(rule_definition)
        if not keyisset("include_regex", self.definition):
            print("NO INCLUDE REGEX. CONSIDERING ALL CONNECTORS")
            self.include_regexes: list[re.Pattern] = [re.compile(r"(.*)")]
        else:
            self.include_regexes: list[re.Pattern] = import_regexes(
                self.definition["include_regexes"]
            )
        if not keyisset("exclude_regex", self.definition):
            print("NO exclude REGEX.")
            self.exclude_regexes: list[re.Pattern] = []
        else:
            self.exclude_regexes: list[re.Pattern] = import_regexes(
                self.definition["exclude_regexes"]
            )

        self.ignore_paused = keyisset("ignore_paused", self.definition)
        self.ignore_unassigned = keyisset("ignore_unassigned", self.definition)
        self.auto_correct_rules: list[AutoCorrectRule] = [
            AutoCorrectRule(config)
            for config in set_else_none("auto_correct", self.original_config)
        ]

    @property
    def original_config(self) -> dict:
        return self._original_definition

    def filter_out_connector(self, connector_name: str):
        print(connector_name)
        if self.exclude_regexes:
            for regex in self.exclude_regexes:
                if regex.match(connector_name):
                    print(f"Connector {connector_name} ignored by blacklist")
                    return False
        for regex in self.include_regexes:
            if regex.match(connector_name):
                return True

    def execute(self, cluster: Cluster) -> None:
        """
        Scans the connectors, matches the ones invalid and not healthy.
        When the connector status is RUNNING, we check all the tasks too to be sure.
        When paused, if we ignore paused connectors, skip
        """
        connectors_to_handle: list[Connector] = []
        for connector_name in list(cluster.connectors.keys()):
            if self.filter_out_connector(connector_name):
                connectors_to_handle.append(cluster.connectors[connector_name])
        connectors_to_fix: list[Connector] = []
        for connector in connectors_to_handle:
            if connector.state in ["RUNNING"]:
                if all([task.is_running for task in connector.tasks]):
                    continue
                else:
                    connectors_to_fix.append(connector)
                    continue
            elif connector.state == "PAUSED" and not self.ignore_paused:
                connector.cycle_connector()
            elif connector.state == "UNASSIGNED" and not self.ignore_unassigned:
                connector.cycle_connector()
            else:
                connectors_to_fix.append(connector)

        for connector in connectors_to_fix:
            for rule in self.auto_correct_rules:
                rule.process(connector)


class AutoCorrectRule:
    """
    Actions to take when errors are detected.
    """

    def __init__(self, config: dict):
        self._original_config = deepcopy(config)
        self.config = config
        self.action = self.config["action"]
        self.wait_for_status = set_else_none("wait_for_status", self.config, "5s")
        self.on_failure = set_else_none("on_failure", self.config)
        self.notify_targets = set_else_none("notify", self.config)

    @property
    def original_config(self) -> dict:
        return self._original_config

    def process(self, connector: Connector):
        interval_delta = max(
            2, int(get_duration_timedelta(self.wait_for_status).total_seconds())
        )
        if self.action == "restart":
            connector.restart()
        elif self.action == "pause":
            connector.pause()
        elif self.action == "cycle":
            connector.cycle_connector()
        time.sleep(interval_delta)
        print("Post action status", connector.name, connector.status)

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
