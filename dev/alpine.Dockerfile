FROM python:3.9-alpine3.14
COPY --from=pandoc/core:2.7.2 /usr/bin/pandoc* /usr/bin/
COPY --from=pandoc/core:2.7.2 /usr/lib/libffi* /usr/lib/
RUN apk add --no-cache \
    gmp \
    lua5.3 \
    lua5.3-lpeg
RUN mkdir gitlabform
COPY . /gitlabform

RUN cd gitlabform \
    && apk add --no-cache build-base \
    && python setup.py develop \
    && apk --purge del build-base

WORKDIR /config
