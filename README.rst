
===========================================
Kafka Connect Watcher
===========================================

Service that will actively probe and monitor your Kafka connect clusters using the Connect API.
It can report metrics to AWS CloudWatch (Prometheus coming) using `AWS EMF`_ to allow creating alerts
and alarms.

Features
=========

* Scan multiple clusters at once
* Implement different remediation rules
* Include/Exclude lists for connectors to evaluate/ignore

Roadmap
=========

* Prometheus support
* Multiple channels of alerts (i.e. webhooks)


Systems recommendations
------------------------------

When using multiple clusters, we recommend to provide multiple CPUs to the service as it
has multi-threading enabled, allowing for parallel processing of clusters & their respective connectors.


.. _AWS EMF: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
