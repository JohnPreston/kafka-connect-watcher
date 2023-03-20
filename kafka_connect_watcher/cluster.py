#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""
Models Connect cluster
"""

from __future__ import annotations

from copy import deepcopy
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_connect_watcher.config import Config

from aws_embedded_metrics.config import get_config
from compose_x_common.compose_x_common import keyisset, set_else_none
from kafka_connect_api.kafka_connect_api import Api, Cluster, Connector
from prometheus_client import Gauge

from kafka_connect_watcher.config import EmfConfig
from kafka_connect_watcher.error_rules import EvaluationRule

emf_config = get_config()


class ConnectCluster:
    """
    The ConnectCluster manages connection and scan of the connectors status execution.
    It also collects metrics about itself.
    """

    def __init__(self, cluster_config: dict, watcher_config: Config):
        if not isinstance(cluster_config, dict):
            raise TypeError("cluster_config must be a dict. Got", type(cluster_config))
        self.definition: dict = cluster_config
        self._orignial_definiton: dict = deepcopy(cluster_config)

        self._name = set_else_none("name", cluster_config)
        self._port = int(set_else_none("port", cluster_config, 8083))
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

        self.handling_rules: list[EvaluationRule] = [
            EvaluationRule(config, watcher_config)
            for config in set_else_none(EvaluationRule.config_key, self.definition)
        ]
        self.metrics_config: dict = set_else_none("metrics", self.definition, {})
        # self.emf_config: dict = set_else_none("aws_emf", self.metrics_config, {})
        self.emf_config: EmfConfig = (
            EmfConfig(self.metrics_config["aws_emf"])
            if keyisset("aws_emf", self.metrics_config)
            else None
        )
        self.prometheus_config: dict = set_else_none(
            "prometheus", self.metrics_config, {}
        )
        self.emf_namespace = None
        self.metrics: dict = {"connectors": {}}

    @property
    def hostname(self) -> str:
        return self.definition["hostname"]

    @property
    def api(self) -> Api:
        return self._api

    @property
    def cluster(self) -> Cluster:
        return self._cluster

    @property
    def name(self) -> str:
        if self._name:
            return self._name
        return f"{self.hostname}_{self.port}"

    @property
    def port(self) -> int:
        return self._port

    def emf_high_resolution(self) -> bool:
        return keyisset("high_resolution_metrics", self.emf_config)
