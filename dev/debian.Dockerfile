FROM python:3.10-bullseye
RUN apt-get update \
    && apt-get install -y pandoc \
    && apt-get clean
COPY . /gitlabform
RUN cd gitlabform && python setup.py develop
WORKDIR /config
