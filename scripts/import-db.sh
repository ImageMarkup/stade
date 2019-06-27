#!/bin/bash
set -ex

export HEROKU_APP=isic-stade

# stop containers accessing the db
docker-compose stop web worker

docker-compose exec db bash -c "PGPASSWORD=postgres dropdb --if-exists -U postgres -h localhost stade"

PGPASSWORD=postgres heroku pg:pull postgresql-pointy-38139 postgresql://postgres:postgres@localhost:5432/stade

docker-compose restart
