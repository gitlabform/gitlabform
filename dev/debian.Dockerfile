ARG PY_VERSION
ARG OS_VERSION
FROM python:${PY_VERSION}-${OS_VERSION}
RUN apt-get update \
    && apt-get install -y pandoc \
    && apt-get clean
COPY . /gitlabform
RUN cd gitlabform && python setup.py develop
WORKDIR /config