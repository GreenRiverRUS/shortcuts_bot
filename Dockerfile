FROM python:3.6

MAINTAINER Vadim Mazaev <vadim.mazaev@gmail.com>

RUN apt-get clean && \
    apt-get update && \
    apt-get install -y \
        apt-utils \
        python-dev \
        vim \
        wget

COPY requirements.txt /
RUN pip3 install -r requirements.txt
COPY src /src

WORKDIR src
CMD python3 main.py
