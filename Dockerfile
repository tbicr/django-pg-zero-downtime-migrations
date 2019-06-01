FROM ubuntu:18.04

ENV LC_ALL=C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update
RUN apt-get install -q -y --no-install-recommends software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -q -y --no-install-recommends python3.5 python3.6 python3.7 python3-pip libgdal20
RUN pip3 install setuptools tox

ADD . /app
WORKDIR /app
CMD ["/bin/bash"]
