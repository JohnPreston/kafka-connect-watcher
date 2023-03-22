#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

"""Manages different channels of communications"""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from compose_x_common.compose_x_common import keyisset

if TYPE_CHECKING:
    from kafka_connect_watcher.config import Config

from copy import deepcopy

from kafka_connect_watcher.aws_sns import SnsChannel


class Notifications:
    def __init__(self, notifications_def: dict):
        self._definition = deepcopy(notifications_def)
        self.sns_channels: dict[str, SnsChannel] = {}

        if keyisset("sns", self.definition):
            for name, definition in self.definition["sns"].items():
                channel = SnsChannel(name, definition)
                self.sns_channels[name] = channel

    @property
    def definition(self) -> dict:
        return self._definition
