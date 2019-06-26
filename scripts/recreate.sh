#!/bin/bash
set -ex

./scripts/stop.sh

sudo rm -rf .docker/{pgdata,uploads}

docker-compose build

./scripts/start.sh
