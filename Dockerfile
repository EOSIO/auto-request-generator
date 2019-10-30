FROM ubuntu:18.04

RUN apt-get update && apt-get install -y python3 python3-pip

RUN mkdir /request_generator

COPY request_generator/* /request_generator/
COPY requirements.txt /requirements.txt
COPY setup.py /setup.py
COPY test.py /test.py

RUN pip3 install -r /requirements.txt
