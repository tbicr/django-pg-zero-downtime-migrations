FROM --platform=linux/amd64 ubuntu:24.04

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -q -y --no-install-recommends software-properties-common git gpg-agent curl && \
    add-apt-repository ppa:deadsnakes/ppa && \
    echo "deb http://apt.postgresql.org/pub/repos/apt noble-pgdg main" > /etc/apt/sources.list.d/pgdg.list && \
    curl -fsSL https://www.postgresql.org/media/keys/ACCC4CF8.asc > /etc/apt/trusted.gpg.d/apt.postgresql.org.asc && \
    apt-get update && \
    apt-get install -q -y --no-install-recommends \
    python3.8 python3.8-distutils \
    python3.9 python3.9-distutils \
    python3.10 python3.10-distutils \
    python3.11 python3.11-distutils \
    python3.12 \
    python3.13 \
    python3-pip \
    libgdal34 \
    postgresql-client-17 && \
    rm -rf /var/lib/apt/lists/* && \
    pip3 install --break-system-packages setuptools tox

ADD . /app
WORKDIR /app
CMD ["/bin/bash"]
