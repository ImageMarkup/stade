#!/bin/bash
set -ex

docker-compose up --detach
until curl -s -o /dev/null http://127.0.0.1:8000; do sleep 5; done
docker-compose exec web python /code/manage.py migrate

docker-compose ps

echo "Index: http://localhost:8000"
echo "Admin: http://localhost:8000/admin"
