FROM python:3.13-alpine3.22

COPY ../pyproject.toml /gitlabform/
COPY ../README.md /gitlabform/
COPY ../LICENSE /gitlabform/

RUN apk add rust cargo libffi-dev

RUN cd /gitlabform && pip install -e .[test]
