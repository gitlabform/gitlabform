FROM python:3.12-alpine3.18

COPY ../setup.py /gitlabform/
COPY ../README.md /gitlabform/
COPY ../version /gitlabform/

RUN apk add rust cargo libffi-dev

RUN cd /gitlabform && pip install -e .[test]
