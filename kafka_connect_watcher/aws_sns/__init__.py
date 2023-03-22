#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>


"""Manages SNS notifications to report error and status"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from kafka_connect_api.kafka_connect_api import Connector
    from kafka_connect_watcher.cluster import ConnectCluster

from os import path, environ
from jinja2 import (
    Environment,
    BaseLoader,
)
from kafka_connect_api.errors import GenericNotFound
from importlib_resources import files as pkg_files
from botocore.exceptions import ClientError
from datetime import datetime as dt
from compose_x_common.compose_x_common import keyisset, set_else_none
from compose_x_common.aws import get_assume_role_session
from copy import deepcopy
from boto3.session import Session
from kafka_connect_watcher.logger import LOG


class SnsChannel:
    def __init__(self, name: str, definition: dict):
        self.__definition = deepcopy(definition)
        self._definition = definition
        self.name = name
        self.arn = definition["topic_arn"]
        self._templates_definitions: dict = {
            "default": pkg_files("kafka_connect_watcher").joinpath(
                "aws_sns/default.j2"
            ),
            "email": pkg_files("kafka_connect_watcher").joinpath("aws_sns/email.j2"),
            "sms": pkg_files("kafka_connect_watcher").joinpath("aws_sns/sms.j2"),
        }
        self.ignore_errors = keyisset("ignore_errors", self.definition)
        self._messages_templates: dict = {}
        self.import_jinja2_templates()

        self._session = Session()
        self._session_expiry = None

    def __repr__(self):
        return f"sns.{self.name}"

    def import_jinja2_templates(self) -> None:
        if keyisset("template", self.definition):
            self._templates_definitions.update(self.definition["template"])
        for message_type, template_path in self._templates_definitions.items():
            if not path.exists(template_path):
                raise FileNotFoundError(f"Template file not found: {template_path}")
            with open(path.abspath(template_path), "r") as template_file:
                self._messages_templates[message_type] = template_file.read()

    @property
    def messages_templates(self) -> dict:
        """Messages templates"""
        return self._messages_templates

    @property
    def definition(self) -> dict:
        """Initial definition"""
        return self.__definition

    def publish(self, subject: str, message: Union[str, dict]) -> None:
        """Publish message to SNS"""
        if not isinstance(message, (str, dict)):
            raise TypeError(f"message must be str or dict, not {type(message)}")
        client = self.session.client("sns")
        try:
            if isinstance(message, str):
                client.publish(TopicArn=self.arn, Subject=subject, Message=message)
            else:
                client.publish(
                    TopicArn=self.arn,
                    Subject=subject,
                    Message=json.dumps(message),
                    MessageStructure="json",
                )

        except (client.exceptions, ClientError) as error:
            LOG.exception(error)
            LOG.error(f"{self.name} - Failed to send notification to {self.arn}")

    @staticmethod
    def render_message_template(
        template: str,
        cluster_id: str,
        connector_name: str,
        connector_error: str,
    ) -> str:
        jinja_env = Environment(
            loader=BaseLoader(),
            autoescape=True,
            auto_reload=False,
        ).from_string(template)

        content = jinja_env.render(
            env=environ,
            CONNECTOR_NAME=connector_name,
            CONNECT_CLUSTER_ID=cluster_id,
            CONNECT_TRACE_ERROR=connector_error,
        )
        return content

    def send_error_notification(self, cluster: ConnectCluster, connector: Connector):
        """Send error notification"""
        subject = f"Kafka Connect error for {connector.name}"
        messages: dict = {}
        try:
            connector_status = connector.status
        except GenericNotFound:
            connector_status = "Connector does not have any workable status"
        for sns_message_type in self.messages_templates:
            try:
                content = self.render_message_template(
                    self.messages_templates[sns_message_type],
                    cluster.name,
                    connector.name,
                    json.dumps(connector_status),
                )
                messages[sns_message_type] = content
            except Exception as error:
                LOG.exception(error)
                LOG.error(
                    f"Failed to render the Jinja2 template for {sns_message_type}"
                )
                if not self.ignore_errors:
                    raise
        self.publish(subject, messages)

    @property
    def session(self) -> Session:
        """
        Sets the boto3 session up
        If role_arn is set, we assume_role to get the session, and keep track of expiry. If at execution the expiry
        passed, re-assume to a new session and get new credentials.
        Otherwise, use the default Session() set at __init__
        """
        if keyisset("role_arn", self.definition):
            if (
                self._session
                and self._session_expiry
                and (dt.now()) < self._session_expiry
            ):
                return self._session
            else:
                self._session, details = get_assume_role_session(
                    Session(),
                    self.definition["role_arn"],
                    set_else_none(
                        "role_session_name",
                        self.definition,
                        f"KafkaConnectWatcher{self.name}",
                    ),
                    include_full_return=True,
                    DurationSeconds=3600,
                )
                self._session_expiry = details["Credentials"]["Expiration"]
        else:
            return self._session
