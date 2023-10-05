
.. meta::
    :description: Kafka Connect Watcher
    :keywords: Kafka, Connect, Observability

.. _install:

=============
Installation
=============

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
