#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""
Configuration loader
"""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime as dt
from json import JSONDecodeError, loads
from os import path
from typing import Union

import yaml
from aws_embedded_metrics.storage_resolution import StorageResolution
from compose_x_common.compose_x_common import get_duration, keyisset, set_else_none
from importlib_resources import files as pkg_files
from jsonschema import RefResolver, validate

try:
    from yaml import Loader
except ImportError:
    from yaml import CLoader as Loader

from kafka_connect_watcher.aws_sns import SnsChannel
from kafka_connect_watcher.logger import LOG


class Config:
    """
    Represents the configuration & settings from the execution.
    """

    def __init__(
        self, config_file_path: str = None, configuration: Union[dict, str] = None
    ):
        if not configuration and not config_file_path:
            raise ValueError(
                "You must specify either the configuration or the path to it."
            )
        if not configuration and config_file_path:
            with open(path.abspath(config_file_path), "r") as config_fd:
                configuration = yaml.load(config_fd.read(), Loader=Loader)
        elif not config_file_path and not isinstance(configuration, (str, dict)):
            raise TypeError(
                "configuration must be a string or dict. Got", type(configuration)
            )
        if configuration and isinstance(configuration, str):
            try:
                configuration = loads(configuration)
            except JSONDecodeError:
                configuration = yaml.load(configuration, Loader=Loader)
        self._config: dict = {}
        self.config = configuration
        self._original_config = deepcopy(configuration)
        self.emf_config = set_else_none("aws_emf", self.config)
        self.emf_log_group = set_else_none(
            "log_group_name", self.emf_config, "kafka/connect/watcher/metrics"
        )
        self.emf_service_name = set_else_none(
            "service_name", self.emf_config, "kafka-connect-watcher"
        )
        self.emf_service_type = set_else_none("service_type", self.emf_config, "python")
        self.emf_watcher_config = (
            EmfConfig(self.emf_config["watcher_config"])
            if keyisset("watcher_config", self.emf_config)
            else None
        )
        self.scan_intervals = self.set_scan_intervals()
        self.notification_channels: dict = {}
        if keyisset("notification_channels", self.config):
            for channel_name, channel_definition in self.config[
                "notification_channels"
            ].items():
                if channel_name == "sns":
                    for (
                        sns_channel_name,
                        sns_channel_definition,
                    ) in channel_definition.items():
                        self.notification_channels[
                            f"{channel_name}.{sns_channel_name}"
                        ] = SnsChannel(sns_channel_name, sns_channel_definition)
                else:
                    LOG.warning("Channel {} is not supported.".format(channel_name))

    def __repr__(self):
        return json.dumps(self.original_config)

    @property
    def config(self) -> dict:
        return self._config

    @config.setter
    def config(self, config: dict) -> None:
        source = pkg_files("kafka_connect_watcher").joinpath("watcher-config.spec.json")
        resolver = RefResolver(f"file://{path.abspath(path.dirname(source))}/", None)
        validate(
            config,
            loads(source.read_text()),
            resolver=resolver,
        )
        for cluster in config["clusters"]:
            interval_string = set_else_none("interval", cluster, "15s")
            interval_delta = get_duration(interval_string)
            now = dt.now()
            cluster["interval"] = max(
                2, int(((now + interval_delta) - now).total_seconds())
            )
        self._config = config

    @property
    def original_config(self) -> dict:
        return self._original_config

    def set_scan_intervals(self) -> int:
        intervals_value = set_else_none("watch_interval", self.config, 60)
        if isinstance(intervals_value, str):
            interval_delta = get_duration(intervals_value)
            now = dt.now()
            return max(2, int(((now + interval_delta) - now).total_seconds()))
        else:
            return max([2, intervals_value])


class EmfConfig:
    def __init__(self, config: dict):
        self.enabled: bool = keyisset("enabled", config)
        self.namespace = config["namespace"]
        self.emf_resolution = (
            StorageResolution.HIGH
            if keyisset("high_resolution_metrics", config)
            else StorageResolution.STANDARD
        )
        self.dimensions = set_else_none("dimensions", config, {})
