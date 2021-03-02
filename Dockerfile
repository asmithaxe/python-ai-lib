FROM python:3.8-slim

# Update the OS and install any utilities that are required.
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq \
    && apt-get upgrade -y \
    && pip3 install --upgrade pip
RUN pip3 install build

WORKDIR /workdir
