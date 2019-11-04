#!/bin/bash
set -ex

./scripts/destroy.sh

docker-compose build

./scripts/start.sh
