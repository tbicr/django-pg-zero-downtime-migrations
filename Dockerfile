FROM ubuntu:20.04

ENV LC_ALL=C.UTF-8
ENV LANG C.UTF-8

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -q -y --no-install-recommends software-properties-common git
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt-get update
RUN apt-get install -q -y --no-install-recommends python3.6 python3.7 python3.8 python3-pip libgdal26
RUN pip3 install setuptools tox

ADD . /app
WORKDIR /app
CMD ["/bin/bash"]
