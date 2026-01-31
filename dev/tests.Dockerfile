FROM python:3.12-alpine

COPY ../pyproject.toml /gitlabform/
COPY ../README.md /gitlabform/
COPY ../LICENSE /gitlabform/

RUN apk add rust cargo libffi-dev

RUN cd /gitlabform && pip install -e .[test]
