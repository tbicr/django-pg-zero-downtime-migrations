FROM --platform=linux/amd64 ubuntu:22.04

ENV LC_ALL=C.UTF-8
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -q -y --no-install-recommends software-properties-common git gpg-agent
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -q -y --no-install-recommends \
    python3.6 \
    python3.7 python3.7-distutils \
    python3.8 python3.8-distutils \
    python3.9 python3.9-distutils \
    python3.10 python3.10-distutils \
    python3.11 python3.11-distutils \
    python3-pip \
    libgdal30
RUN pip3 install setuptools tox

ADD . /app
WORKDIR /app
CMD ["/bin/bash"]
