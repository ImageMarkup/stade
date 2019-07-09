#!/bin/bash
set -ex

export HEROKU_APP=isic-stade

# stop containers accessing the db
docker-compose stop web worker

docker-compose exec db bash -c "PGPASSWORD=postgres dropdb --host localhost --username postgres --if-exists stade && createdb --host localhost --username postgres stade"

docker-compose exec db bash -c \
"pg_dump --format=custom --no-privileges $(heroku config:get DATABASE_URL)"\
" | PGPASSWORD=postgres pg_restore --host localhost --username postgres --format=custom --no-privileges --no-owner --dbname=stade"

docker-compose restart
