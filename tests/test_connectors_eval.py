from queue import Queue
from unittest import Mock

import pytest

from kafka_connect_watcher.connectors_eval import evaluate_connector_status

from .fixtures.mock_config import (
    MockConnectCluster,
    MockConnector,
    MockEvaluationRule,
    MockTask,
)


@pytest.mark.parametrize(
    [
        "connector_states",
        "task_states",
        "len_connectors_to_fix",
        "ignore_unassigned",
        "ignore_paused",
        "cycle_connector",
    ],
    (
        (["FAILED"], ["RUNNING"], 1, False, False, False),
        (["RUNNING"], ["FAILED", "RUNNING"], 1, False, False, False),
        (["RUNNING"], ["UNASSIGNED", "RUNNING"], 0, True, False, False),
        (["RUNNING"], ["UNASSIGNED", "RUNNING"], 1, False, False, False),
        (["RUNNING"], ["RUNNING", "PAUSED"], 0, False, True, False),
        (["RUNNING"], ["PAUSED", "RUNNING"], 1, False, False, False),
        (["PAUSED"], ["RUNNING"], 0, False, True, False),
        (["PAUSED"], ["RUNNING"], 0, False, False, True),
        (["UNASSIGNED"], ["RUNNING"], 0, True, False, False),
        (["UNASSIGNED"], ["RUNNING"], 0, False, False, False),
        (["FAILED", "FAILED"], ["RUNNING"], 2, False, False, False),
    ),
)
def test_evaluate_connector_status(
    mocker,
    connector_states,
    task_states,
    len_connectors_to_fix,
    ignore_unassigned,
    ignore_paused,
    cycle_connector,
):
    connector_queue = Queue()
    rule = MockEvaluationRule(
        ignore_paused=ignore_paused, ignore_unassigned=ignore_unassigned
    )
    connect = MockConnectCluster()
    connectors = []
    connectors_to_fix = []
    for connector_state in connector_states:
        tasks = []
        for task_state in task_states:
            tasks.append(MockTask(state=task_state))
        connectors.append(MockConnector(state=connector_state, tasks=tasks))
    for connector in connectors:
        connector_queue.put(
            [rule, connect, connector, 0, 0, 0, connectors_to_fix],
            False,
        )
    mock_cycle = mocker.patch("fixtures.mock_config.MockConnector.cycle_connector")
    evaluate_connector_status(connector_queue)
    assert len(connectors_to_fix) == len_connectors_to_fix
    if cycle_connector:
        mock_cycle.assert_called_once_with()
