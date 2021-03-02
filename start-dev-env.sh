#!/usr/bin/env bash

# Script to build a Docker image and start a Docker container for development purposes only.

SCRIPT=$(readlink -f "$0")
SCRIPT_PATH=$(dirname "${SCRIPT}")

# Build the Docker image.
docker build -f ${SCRIPT_PATH}/Dockerfile -t asmithaxe_ai:dev ${SCRIPT_PATH}

# Start the Docker container.
docker run \
  -it \
  --rm \
  -u $(id -u):$(id -g) \
  -w /workdir \
  -v ${SCRIPT_PATH}:/workdir \
  asmithaxe_ai:dev bash
