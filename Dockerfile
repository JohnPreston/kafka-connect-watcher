ARG ARCH=
ARG PY_VERSION=3.9
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:${PY_VERSION}-slim
ARG LAMBDA_IMAGE=public.ecr.aws/lambda/python:latest
FROM $BASE_IMAGE as builder

WORKDIR /opt
COPY kafka_connect_watcher /opt/kafka_connect_watcher
COPY poetry.lock pyproject.toml README.rst /opt/
RUN python -m pip install pip -U; python -m pip install poetry; poetry build

FROM $BASE_IMAGE
RUN groupadd -r watcher -g 37337; \
    useradd -u 37337 -r -g watcher -m -d /watcher -s /sbin/nologin -c "Kafka Connect Watcher" watcher;\
    chown -R watcher:watcher /watcher


ENV PATH=/watcher/.local/bin:${PATH}
COPY --from=builder /opt/dist/kafka_connect_watcher-*.whl ${LAMBDA_TASK_ROOT:-/watcher/}/
WORKDIR /watcher
USER watcher
RUN echo $PATH ; pip install pip -U --no-cache-dir && pip install wheel --no-cache-dir && pip install --user *.whl --no-cache-dir
COPY --chown=watcher:watcher entrypoint.sh /watcher/
ENTRYPOINT ["/watcher/entrypoint.sh"]
