FROM python:3.10-alpine3.16

COPY ../setup.py /gitlabform/
COPY ../README.md /gitlabform/
COPY ../version /gitlabform/

RUN cd /gitlabform && pip install -e .[test]
