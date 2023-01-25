#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""
AWS EMF Publishing management for cluster & connectors
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from kafka_connect_watcher.cluster import ConnectCluster
    from kafka_connect_watcher.config import Config

from copy import deepcopy

from aws_embedded_metrics import metric_scope
from aws_embedded_metrics.config import get_config
from aws_embedded_metrics.logger.metrics_logger import MetricsLogger
from aws_embedded_metrics.logger.metrics_logger_factory import create_metrics_logger

emf_config = get_config()


def init_emf_config(config: Config) -> None:
    emf_config.service_name = config.emf_service_name
    emf_config.service_type = config.emf_service_type
    emf_config.log_group_name = config.emf_log_group


@metric_scope
def publish_cluster_metrics(config: Config, cluster: ConnectCluster, metrics) -> None:
    print(cluster.name, "Publishing Cluster metrics to EMF")
    metrics.reset_dimensions(use_default=False)
    metrics.set_property("ConnectDetails", {"designation": cluster.name})
    dimensions: dict = deepcopy(cluster.emf_config["dimensions"])
    dimensions.update({"ConnectCluster": cluster.name})
    metrics.put_dimensions(dimensions)
    for metric_name, value in cluster.metrics.items():
        if not isinstance(value, (int, str)):
            continue
        metrics.put_metric(metric_name, value, None)


@metric_scope
def publsh_connector_metrics(
    config: Config, cluster: ConnectCluster, connector_name, connector_metrics, metrics
) -> None:
    print("Publishing Cluster Connector metrics to EMF")

    metrics.set_namespace(cluster.emf_config["namespace"])
    metrics.reset_dimensions(use_default=False)
    metrics.set_property("ConnectDetails", {"designation": cluster.name})
    dimensions: dict = deepcopy(cluster.emf_config["dimensions"])
    dimensions.update({"ConnectorName": connector_name, "ConnectCluster": cluster.name})
    metrics.put_dimensions(dimensions)
    for _conn_metric_name, _conn_metric_value in connector_metrics.items():
        metrics.put_metric(_conn_metric_name, _conn_metric_value, None)


def publish_emf(config: Config, cluster: ConnectCluster) -> None:
    publish_cluster_metrics(config, cluster)
    for connector_name, connector_metrics in cluster.metrics["connectors"].items():
        publsh_connector_metrics(config, cluster, connector_name, connector_metrics)
