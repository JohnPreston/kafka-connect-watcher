#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""
Models Connect cluster
"""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_connect_watcher.config import Config
from compose_x_common.compose_x_common import keyisset, set_else_none
from copy import deepcopy
from kafka_connect_api.kafka_connect_api import Api, Cluster, Connector
from prometheus_client import Gauge
from error_rules import ErrorHandlingRule


class ConnectCluster:
    """
    The ConnectCluster manages connection and scan of the connectors status execution.
    It also collects metrics about itself.
    """

    def __init__(self, cluster_config: dict):
        if not isinstance(cluster_config, dict):
            raise TypeError("cluster_config must be a dict. Got", type(cluster_config))
        self.definition: dict = cluster_config
        self._orignial_definiton: dict = deepcopy(cluster_config)

        auth = set_else_none("authentication", cluster_config)
        url = set_else_none("url", cluster_config)
        username = set_else_none(
            "username", set_else_none("authentication", cluster_config)
        )
        password = set_else_none(
            "password", set_else_none("authentication", cluster_config)
        )
        if url:
            self._api = Api(
                self.hostname,
                url=url,
                username=username,
                password=password,
            )
        else:
            self._api = Api(
                self.hostname,
                port=int(set_else_none("port", cluster_config, 8083)),
                username=username,
                password=password,
            )
        try:
            self._cluster = Cluster(self.api)
        except Exception as error:
            print(error)

        self.handling_rules: list[ErrorHandlingRule] = [
            ErrorHandlingRule(config)
            for config in set_else_none("error_handling_rules", self.definition)
        ]

    @property
    def hostname(self) -> str:
        return self._definition["hostname"]

    @property
    def api(self) -> Api:
        return self._api

    @property
    def cluster(self) -> Cluster:
        return self._cluster
