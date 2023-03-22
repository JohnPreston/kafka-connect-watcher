
.. meta::
    :description: Kafka Connect Watcher
    :keywords: Kafka, Connect, Observability

##########################################
Kafka Connect Watcher
##########################################

|PYPI_VERSION| |PYPI_LICENSE|

|CODE_STYLE| |TDD|

|BUILD|

---------------------------------------
Actively monitor your Kafka connectors
---------------------------------------

Service that will actively probe and monitor your Kafka connect clusters using the Connect API.
It can report metrics to AWS CloudWatch (Prometheus coming) using `AWS EMF`_ to allow creating alerts
and alarms.

Features
=========

* Scan multiple clusters at once
* Implement different remediation rules
* Include/Exclude lists for connectors to evaluate/ignore

Run / Execute
=================

With docker
------------------

.. code-block::

    docker run --rm -it --network host -v ${PWD}/config.yaml:/config.yaml public.ecr.aws/compose-x/kafka-connect-watcher -c /config.yaml

With python
--------------

.. code-block::

    python -m venv watcher
    source watcher/bin/activate
    pip install pip -U; pip install kafka-connect-watcher
    kafka-connect-watcher -c config.yaml

How does it work?
========================

Provided a configuration file, the watcher will use the Apache Kafka Connect API to query the connectors and evaluate
their status. Based on evaluation rules defined, you get metrics and reporting on the different connectors.
You can also define actions to take in order to help try to recover the connectors, such as restart these.

Install
============

.. code-block:: bash

    # Inside a python virtual environment
    python3 -m venv venv
    source venv/bin/activate
    pip install pip -U
    pip install kafka-connect-watcher

    # For your user only, without virtualenv
    pip install kafka-connect-watcher --user


.. |BUILD| image:: https://codebuild.eu-west-1.amazonaws.com/badges?uuid=eyJlbmNyeXB0ZWREYXRhIjoieURaVkdISTUrZGZjaWFCVlBVN0NJL3VpSzNnVmZsNXlKQnhsZU84YzVxRGpQdTlUQU12WGNaVndESEdTU3FXZ1ZBMnM1OFVOL2MyZTRjcWZzS2owK2pzPSIsIml2UGFyYW1ldGVyU3BlYyI6IkRMSFNTYlFCM1NXbWdhd0wiLCJtYXRlcmlhbFNldFNlcmlhbCI6MX0%3D&branch=main


.. |PYPI_VERSION| image:: https://img.shields.io/pypi/v/kafka-connect-watcher.svg
        :target: https://pypi.python.org/pypi/kafka-connect-watcher

.. |PYPI_LICENSE| image:: https://img.shields.io/pypi/l/kafka-connect-watcher
    :alt: PyPI - License
    :target: https://github.com/compose-x/kafka-connect-watcher/blob/main/LICENSE

.. |PYPI_PYVERS| image:: https://img.shields.io/pypi/pyversions/kafka-connect-watcher
    :alt: PyPI - Python Version
    :target: https://pypi.python.org/pypi/kafka-connect-watcher

.. |PYPI_WHEEL| image:: https://img.shields.io/pypi/wheel/kafka-connect-watcher
    :alt: PyPI - Wheel
    :target: https://pypi.python.org/pypi/kafka-connect-watcher

.. |CODE_STYLE| image:: https://img.shields.io/badge/codestyle-black-black
    :alt: CodeStyle
    :target: https://pypi.org/project/black/

.. |TDD| image:: https://img.shields.io/badge/tdd-pytest-black
    :alt: TDD with pytest
    :target: https://docs.pytest.org/en/latest/contents.html


.. toctree::
    :maxdepth: 1

    requisites
    installation
    configuration_file
    aws_emf_metrics

.. toctree::
    :maxdepth: 1
    :caption: Examples and Help

    examples

.. toctree::
    :titlesonly:
    :maxdepth: 1
    :caption: Modules and Source Code

    modules

Indices and tables
==================
* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. _AWS EMF: https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format_Specification.html
