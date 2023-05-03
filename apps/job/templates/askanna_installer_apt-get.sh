#!/bin/sh

apt-get update && apt-get install --no-install-recommends -y \
    python3 \
    python3-pip \
    curl \
    git \
    unzip \
    tzdata &&
    apt-get clean &&
    rm -rf /var/lib/apt/lists/*

# as a quick note, for a proper install of python, you would
# use a python base image or follow a more official install of python,
# changing this to RUN cd /usr/local/bin
# this just replicates your issue quickly
cd "$(dirname $(which python3))" &&
    ln -s idle3 idle &&
    ln -s pydoc3 pydoc &&
    ln -s $(readlink -f python3-config) python-config

ln -s $(readlink -f python3) python # this will properly alias your python
