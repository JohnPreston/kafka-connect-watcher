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
    from kafka_connect_watcher.watcher import Watcher

from asyncio import get_event_loop, new_event_loop, set_event_loop
from copy import deepcopy

from aws_embedded_metrics import metric_scope
from aws_embedded_metrics.config import get_config

from kafka_connect_watcher.logger import LOG

emf_config = get_config()


def init_emf_config(config: Config) -> None:
    try:
        loop = get_event_loop()
    except RuntimeError:
        loop = new_event_loop()
    set_event_loop(loop)
    emf_config.service_name = config.emf_service_name
    emf_config.service_type = config.emf_service_type
    emf_config.log_group_name = config.emf_log_group


@metric_scope
def publish_cluster_metrics(cluster: ConnectCluster, metrics) -> None:
    LOG.info(
        f"{cluster.name} - Publishing Cluster metrics to EMF with Resolution {cluster.emf_config.emf_resolution}",
    )
    LOG.debug(cluster.metrics)
    metrics.reset_dimensions(use_default=False)
    metrics.set_property("ConnectDetails", {"designation": cluster.name})
    dimensions: dict = deepcopy(cluster.emf_config.dimensions)
    dimensions.update({"ConnectCluster": cluster.name})
    metrics.put_dimensions(dimensions)
    for metric_name, value in cluster.metrics.items():
        if not isinstance(value, (int, str)):
            continue
        metrics.put_metric(metric_name, value, None, cluster.emf_config.emf_resolution)


@metric_scope
def publish_connector_metrics(
    cluster: ConnectCluster, connector_name, connector_metrics, metrics
) -> None:
    LOG.debug(
        f"Publishing Cluster Connector metrics to EMF with Resolution {cluster.emf_config.emf_resolution}"
    )
    metrics.set_namespace(cluster.emf_config.namespace)
    metrics.reset_dimensions(use_default=False)
    metrics.set_property("ConnectDetails", {"designation": cluster.name})
    dimensions: dict = deepcopy(cluster.emf_config.dimensions)
    dimensions.update({"ConnectorName": connector_name, "ConnectCluster": cluster.name})
    metrics.put_dimensions(dimensions)
    for _conn_metric_name, _conn_metric_value in connector_metrics.items():
        metrics.put_metric(
            _conn_metric_name,
            _conn_metric_value,
            None,
            cluster.emf_config.emf_resolution,
        )


def publish_clusters_emf(cluster: ConnectCluster) -> None:
    if not cluster.emf_config.enabled:
        return
    try:
        loop = get_event_loop()
    except RuntimeError:
        loop = new_event_loop()
    print("Publish EMF for clusters")
    set_event_loop(loop)
    publish_cluster_metrics(cluster)
    for connector_name, connector_metrics in cluster.metrics["connectors"].items():
        publish_connector_metrics(cluster, connector_name, connector_metrics)


@metric_scope
def publish_watcher_emf_metrics(config: Config, watcher: Watcher, metrics):
    LOG.info(
        f"Publishing Watcher metrics to EMF with Resolution {config.emf_watcher_config.emf_resolution}"
    )
    LOG.debug(watcher.metrics)
    metrics.set_namespace(config.emf_watcher_config.namespace)
    metrics.reset_dimensions(use_default=False)
    metrics.put_dimensions(config.emf_watcher_config.dimensions)
    for _watcher_metric, _watcher_metric_value in watcher.metrics.items():
        metrics.put_metric(
            _watcher_metric,
            _watcher_metric_value,
            None,
            config.emf_watcher_config.emf_resolution,
        )


def handle_watcher_emf(config: Config, watcher: Watcher) -> None:
    if not (config.emf_watcher_config and config.emf_watcher_config.enabled):
        LOG.debug("Watcher metrics to EMF disabled")
        return
    publish_watcher_emf_metrics(config, watcher)
