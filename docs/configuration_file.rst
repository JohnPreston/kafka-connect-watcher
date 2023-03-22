
.. meta::
    :description: Kafka Connect Watcher
    :keywords: Kafka, Connect, Observability

.. _configuration_file_syntax:

==============================================
Configuration file syntax and settings
==============================================

The configuration files passed as inputs to the kafka-connect-watcher are going to be evaluated and checked with `jsonschema`_
which validates the structure and validity of the input.

Below is the JSON schema definition, found in `kafka_connect_watcher/watcher-config.spec.json`_

.. jsonschema:: ../kafka_connect_watcher/watcher-config.spec.json

Definition
-----------

.. literalinclude:: ../kafka_connect_watcher/watcher-config.spec.json

.. _jsonschema: https://python-jsonschema.readthedocs.io/en/stable/
.. _kafka_connect_watcher/watcher-config.spec.json: https://github.com/JohnPreston/kafka-connect-watcher/blob/main/kafka_connect_watcher/watcher-config.spec.json
