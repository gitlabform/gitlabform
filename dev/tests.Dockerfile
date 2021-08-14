FROM python:3.9-alpine3.14

COPY ../setup.py /gitlabform/
COPY ../README.md /gitlabform/
COPY ../version /gitlabform/

RUN cd /gitlabform && pip install -e .[test]
