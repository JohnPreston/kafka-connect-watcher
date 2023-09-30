import json
from os import path

import pytest
import yaml

from kafka_connect_watcher.config import Config


@pytest.mark.parametrize(
    ["config_path", "expected"],
    (
        (
            "test_config.yaml",
            {
                "clusters": [
                    {
                        "hostname": "localhost",
                        "port": 8083,
                        "interval": 5,
                        "evaluation_rules": [
                            {"auto_correct_actions": [{"action": "restart"}]},
                            {
                                "auto_correct_actions": [
                                    {
                                        "action": "pause",
                                        "notify": [{"target": "sns.main_topic"}],
                                    }
                                ]
                            },
                        ],
                    }
                ],
                "notification_channels": {
                    "sns": {
                        "main_topic": {
                            "topic_arn": "arn:aws:sns:eu-west-1:123456789:test-sns-topic"
                        }
                    }
                },
            },
        ),
    ),
)
def test_config_parsing(config_path, expected):
    actual = Config(path.abspath(f"tests/fixtures/configs/{config_path}"))
    assert actual.config == expected
