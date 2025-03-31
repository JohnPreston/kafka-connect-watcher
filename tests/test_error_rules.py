from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from kafka_connect_watcher.error_rules import AutoCorrectRule, EvaluationRule
from tests.fixtures.mock_config import (
    MockClusterConfig,
    MockConnectCluster,
    MockConnector,
)


@pytest.mark.parametrize(
    ["rule_definition", "connector_name", "expected"],
    (
        ({"exclude_regex": [".*to-exclude.*"]}, "connector-to-exclude-name", False),
        ({"exclude_regex": [".*to-exclude.*"]}, "connector-to-include-name", True),
        ({"include_regex": ".*to-include.*"}, "connector-to-include-name", True),
    ),
)
def test_filter_out_connector(rule_definition, connector_name, expected):
    cluster_config = MockClusterConfig()
    rule = EvaluationRule(rule_definition, {})
    assert rule.filter_out_connector(connector_name, cluster_config) == expected


@pytest.mark.parametrize(
    "config, status_sequence, expected_action, expected_sleep_calls",
    [
        pytest.param(
            {
                "action": "restart",
                "wait_for_status": "30s",
                "max_backoff": 10,
                "max_attempts": 3,
            },
            [
                {"connector": {"state": "FAILED"}, "tasks": [{"state": "FAILED"}]},
                {"connector": {"state": "RUNNING"}, "tasks": [{"state": "RUNNING"}]},
            ],
            "none",
            [30],
            id="recovers-on-second-attempt",
        ),
        pytest.param(
            {
                "action": "restart",
                "wait_for_status": "30s",
                "max_backoff": 50,
                "max_attempts": 3,
            },
            [
                {"connector": {"state": "FAILED"}, "tasks": [{"state": "FAILED"}]},
                {"connector": {"state": "FAILED"}, "tasks": [{"state": "FAILED"}]},
                {"connector": {"state": "FAILED"}, "tasks": [{"state": "FAILED"}]},
            ],
            "restart",
            [30, 50],
            id="fails-all-restart-called",
        ),
        pytest.param(
            {
                "action": "pause",
                "wait_for_status": "30s",
                "max_backoff": 5,
                "max_attempts": 1,
            },
            [
                {"connector": {"state": "FAILED"}, "tasks": [{"state": "FAILED"}]},
            ],
            "pause",
            [],
            id="single-attempt-pause",
        ),
    ],
)
@patch("time.sleep", return_value=None)
def test_backoff_logic_with_mock_connector(
    mock_sleep,
    config,
    status_sequence,
    expected_action,
    expected_sleep_calls,
):
    rule = AutoCorrectRule(config=config, watcher_config={})
    connector = MockConnector()
    connector.config = {"connector.class": "TestClass"}
    connector.cluster.loggers = {"TestClass": True}

    def status_side_effect():
        yield from status_sequence
        while True:
            yield status_sequence[-1]

    type(connector).status = PropertyMock(side_effect=status_side_effect())

    connector.restart = MagicMock()
    connector.pause = MagicMock()
    connector.cycle_connector = MagicMock()

    rule.process(cluster=MockConnectCluster(), connector=connector)

    if expected_action == "restart":
        connector.restart.assert_called_once()
    elif expected_action == "pause":
        connector.pause.assert_called_once()
    else:
        connector.restart.assert_not_called()
        connector.pause.assert_not_called()

    sleep_durations = [call.args[0] for call in mock_sleep.call_args_list]
    backoff_durations = sleep_durations[: len(expected_sleep_calls)]
    assert backoff_durations == expected_sleep_calls
