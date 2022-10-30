FROM python:3.11-alpine3.16

COPY ../setup.py /gitlabform/
COPY ../README.md /gitlabform/
COPY ../version /gitlabform/
COPY ../CHANGELOG.md /gitlabform/

RUN cd /gitlabform && pip install -e .[test]
