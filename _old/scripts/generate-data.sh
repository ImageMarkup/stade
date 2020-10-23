#!/bin/bash
set -ex

docker-compose exec web python /code/manage.py fakedata
