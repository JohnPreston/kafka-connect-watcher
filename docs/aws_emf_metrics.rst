
.. meta::
    :description: Kafka Connect Watcher
    :keywords: Kafka, Connect, Observability

.. _aws_emf_metrics:

==============================================
AWS Embedded Metrics Format (EMF) Collection
==============================================

If you are running on AWS, you might want to publish the collected metrics to AWS CloudWatch.
To achieve that, the kafka connect watcher uses AWS EMF which will publish logs captured by AWS CloudWatch, and transformed
into metrics automatically.

There are two places where you can configure EMF metrics settings:

* `aws_emf`_ at the root of the configuration file
* `cluster.metrics.aws_emf`_, at the connector level


aws_emf
==========

.. code-block:: yaml

    log_group_name: str
    service_name: str
    service_type: str
    watcher_config:
      enabled: bool
      namespace: str
      dimensions:
        str: str

log_group_name
^^^^^^^^^^^^^^^^

Importance: HIGH

The log group to which the EMF metrics will be published. We recommend to have a **1 day** retention on the log group,
as metrics will be persisted after ingestion, therefore you don't need the additional costs incurred by logs.

service_name
^^^^^^^^^^^^^^

Importance: LOW
Optional setting - used in the metadata of EMF Metric log

service_type
^^^^^^^^^^^^^

Importance: LOW
Optional setting - used in the metadata of EMF Metric log


watcher_config
^^^^^^^^^^^^^^^^^

Configuration that drives the general behaviour of `aws_emf`_

enabled
"""""""""

Importance: HIGH
Default: false

When true, EMF metrics for the watcher (clusters count etc.) are collected and published

namespace
""""""""""""

Importance: HIGH
Default: KafkaConnect/Watcher

Allows you to define the Namespace to which the custom metrics are published.

dimensions
""""""""""""""

Importance: MEDIUM
Optional setting

Arbitrary key/value set (unique keys) that will used as dimensions of the published metrics.
This settings helps with distinguishing metrics if you have multiple instances running.

cluster.metrics.aws_emf
=========================

Settings that drive the EMF metrics collection for a cluster connectors (healthy, failed, unassigned, ignored).

The parameters `namespace`_, `dimensions`_ and `enabled`_ are identical to the ones for the watcher settings.

.. attention::

    The top level `aws_emf`_ settings do not override the cluster level settings.
