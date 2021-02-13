ARG PY_VERSION
ARG OS_VERSION
FROM python:${PY_VERSION}-${OS_VERSION}
COPY --from=pandoc/core:2.7.2 /usr/bin/pandoc* /usr/bin/
COPY --from=pandoc/core:2.7.2 /usr/lib/libffi* /usr/lib/
RUN apk add --no-cache \
    gmp \
    lua5.3 \
    lua5.3-lpeg
COPY . /gitlabform
RUN cd gitlabform && python setup.py develop
WORKDIR /config