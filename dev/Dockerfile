FROM python:3.12-alpine3.21
RUN apk add --no-cache \
    gmp \
    lua5.3 \
    lua5.3-lpeg
RUN mkdir gitlabform
COPY . /gitlabform

RUN cd gitlabform \
    && apk add --no-cache build-base \
    && pip install -e . \
    && apk --purge del build-base

WORKDIR /config

RUN addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser
