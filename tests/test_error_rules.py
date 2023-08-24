import pytest
from kafka_connect_watcher.error_rules import EvaluationRule
from tests.fixtures.mock_config import MockClusterConfig

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
