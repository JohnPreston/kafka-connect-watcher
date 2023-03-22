#   SPDX-License-Identifier: MPL-2.0
#   Copyright 2023 John "Preston" Mille <john@ews-network.net>

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from multiprocessing import Queue

from multiprocessing import Queue
from kafka_connect_api.errors import GenericNotFound
from kafka_connect_watcher.logger import LOG


def evaluate_connector_status(queue: Queue) -> None:
    while True:
        if queue.empty():
            break
        else:
            (
                evaluation_rule,
                connect,
                connector,
                running_connectors,
                paused_connectors,
                unassigned_connectors,
                connectors_to_fix,
            ) = queue.get()
        if connect is None:
            break

        connector_metrics: dict = {
            "tasks": len(connector.tasks),
            "running": len(
                [_task for _task in connector.tasks if _task.state == "RUNNING"]
            ),
            "failed": len(
                [_task for _task in connector.tasks if _task.state == "FAILED"]
            ),
            "unassigned": len(
                [_task for _task in connector.tasks if _task.state == "UNASSIGNED"]
            ),
        }
        try:
            if connector.state in ["RUNNING"]:
                if all([task.is_running for task in connector.tasks]):
                    running_connectors += 1
                else:
                    connectors_to_fix.append(connector)
            elif connector.state == "PAUSED":
                paused_connectors += 1
                if evaluation_rule.ignore_paused:
                    connector.cycle_connector()
            elif connector.state == "UNASSIGNED":
                unassigned_connectors += 1
                if not evaluation_rule.ignore_unassigned:
                    connector.cycle_connector()
            else:
                connectors_to_fix.append(connector)
        except GenericNotFound as error:
            LOG.debug(
                "Connector {} not found in connect cluster. {}".format(
                    connector.name,
                    error,
                )
            )
            LOG.error(
                "{} - {}: failed to retrieve status".format(
                    connect.name, connector.name
                )
            )
            unassigned_connectors += 1
            connectors_to_fix.append(connector)
        connect.metrics["connectors"].update({connector.name: connector_metrics})
        queue.task_done()
