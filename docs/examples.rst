
.. meta::
    :description: Kafka Connect Watcher
    :keywords: Kafka, Connect, Observability

.. _examples:

================
Examples
================

Test locally
--------------

The very simple configuration below will monitor a connect cluster reachable on ``localhost:8083`` and monitor every
connector in the cluster.

.. code-block:: yaml

    clusters:
      - hostname: localhost
        port: 8083
        metrics:
          aws_emf:
            namespace: KafkaConnect/Watcher
            dimensions:
              Name: my-environment
            enabled: false
        evaluation_rules:
          - include_regex:
              - '(.*)$'
            ignore_paused: true
            auto_correct_actions: []



Enable AWS EMF Metrics collection
-------------------------------------

In the following example, we are collecting monitoring metrics for both the watcher itself, as well as the connectors
of our localhost:8083 cluster.

.. code-block:: yaml

    clusters:
      - hostname: localhost
        port: 8083
        metrics:
          aws_emf:
            namespace: KafkaConnect/Watcher
            dimensions:
              Name: local-cluster
            enabled: true
        evaluation_rules:
          - include_regex:
              - '(.*)$'
            exclude_regex:
              - '(.*)dummy(.*)'
            ignore_paused: true
            auto_correct_actions:
              - action: notify_only
                notify:
                  - target: sns.main_topic

    notification_channels:
      sns:
        main_topic:
          topic_arn: arn:aws:sns:eu-west-1:111111111111:dummy

    aws_emf:
      log_group_name: kafka/connect/watcher/metrics
      service_name: kafka-connect-watcher
      service_type: python
      watcher_config:
        enabled: true
        namespace: KafkaConnect/Watcher
        dimensions:
          name: connect-watcher
