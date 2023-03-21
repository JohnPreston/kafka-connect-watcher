ARG ARCH=
ARG PY_VERSION=3.9
ARG BASE_IMAGE=public.ecr.aws/docker/library/python:${PY_VERSION}-alpine
ARG LAMBDA_IMAGE=public.ecr.aws/lambda/python:latest

FROM $BASE_IMAGE as builder

WORKDIR /opt
RUN python -m pip install pip -U; python -m pip install poetry
COPY kafka_connect_watcher /opt/kafka_connect_watcher
COPY poetry.lock pyproject.toml README.rst /opt/
RUN poetry build

FROM $BASE_IMAGE
ARG USER_ID=37337
ARG GROUP_ID=37337
ENV USER_ID $USER_ID
ENV GROUP_ID $GROUP_ID
WORKDIR /watcher
RUN addgroup -g ${GROUP_ID} watcher; \
    adduser -D -h /watcher -H -G watcher -u ${USER_ID} watcher
RUN chown -R watcher:watcher /watcher
ENV PATH=/watcher/.local/bin:${PATH}
USER watcher
RUN echo $PATH ; pip install pip -U --no-cache-dir && pip install wheel --no-cache-dir
COPY --from=builder /opt/dist/kafka_connect_watcher-*.whl ${LAMBDA_TASK_ROOT:-/watcher/}/
RUN pip install --user *.whl --no-cache-dir
COPY --chown=watcher:watcher entrypoint.sh /watcher/
ENTRYPOINT ["/watcher/entrypoint.sh"]
