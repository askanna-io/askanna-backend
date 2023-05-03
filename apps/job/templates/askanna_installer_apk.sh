#!/bin/sh

apk update \
    && apk add --no-cache \
    python3 py3-pip \
    && apk add curl \
    && apk add git \
    && apk add unzip \
    && apk add tzdata

# as a quick note, for a proper install of python, you would
# use a python base image or follow a more official install of python,
# changing this to RUN cd /usr/local/bin
# this just replicates your issue quickly
cd "$(dirname $(which python3))" \
    && ln -s idle3 idle \
    && ln -s pydoc3 pydoc \
    && ln -s python3 python \ # this will properly alias your python
    && ln -s python3-config python-config
