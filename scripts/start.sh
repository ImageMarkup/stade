#!/bin/bash
set -ex

docker-compose up --detach
docker-compose ps
