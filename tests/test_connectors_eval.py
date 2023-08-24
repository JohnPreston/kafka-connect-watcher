from queue import Queue
import pytest
from fixtures.mock_config import (
    MockEvaluationRule,
    MockConnectCluster,
    MockConnector,
    MockTask,
)
from kafka_connect_watcher.connectors_eval import evaluate_connector_status


@pytest.mark.parametrize(
    [
        "connector_states",
        "task_states",
        "expected_paused",
        "expected_running",
        "expected_unassigned",
        "len_connectors_to_fix",
    ],
    (
        (["FAILED"], ["RUNNING"], 0, 0, 0, 1),
        (["RUNNING"], ["FAILED", "RUNNING"], 0, 0, 0, 1),
        (["FAILED", "FAILED"], ["RUNNING"], 0, 0, 0, 2),
    ),
)
def test_evaluate_connector_status(
    connector_states,
    task_states,
    expected_paused,
    expected_running,
    expected_unassigned,
    len_connectors_to_fix,
):
    connector_queue = Queue()
    rule = MockEvaluationRule()
    connect = MockConnectCluster()
    connectors = []
    connectors_to_fix = []
    paused_connectors: int = 0
    unassigned_connectors: int = 0
    running_connectors: int = 0
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
    evaluate_connector_status(connector_queue)
    assert paused_connectors == expected_paused
    assert running_connectors == expected_running
    assert unassigned_connectors == expected_unassigned
    assert len(connectors_to_fix) == len_connectors_to_fix
