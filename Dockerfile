FROM python:3.12-alpine

# delete the pip cache because even with `--no-cache-dir` pip still creates ~1.4MB of cache...
RUN cd gitlabform \
    && apk add --no-cache build-base \
    && pip install --no-cache-dir  -e . \
    && rm -rf /root/.cache/pip \
    && apk --purge del build-base

WORKDIR /config

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
