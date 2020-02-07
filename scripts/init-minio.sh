#!/bin/bash
set -ex

docker run --rm -it --network stade_default --entrypoint /bin/sh minio/mc -c '
/usr/bin/mc config host add minio http://minio:9000 minioAdminAccessKey minioAdminSecretKey \
&& /usr/bin/mc mb -ignore-existing minio/stade \
&& /usr/bin/mc admin user add minio stadeAccessKey stadeSecretKey \
&& /usr/bin/mc admin policy set minio readwrite user=stadeAccessKey'
