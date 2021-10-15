#!/bin/bash

source "./docker/docker_conf.sh"

if [ ! -e "./conf/github_access_token.txt" ]; then
  touch ./conf/github_access_token.txt
fi
if [ ! -e "./conf/gitlab_access_token.txt" ]; then
  touch ./conf/gitlab_access_token.txt
fi
if [ ! -e "./conf/target_github_repository.conf" ]; then
  cp ./conf/target_github_repository.conf.model ./conf/target_github_repository.conf
fi
if [ ! -e "./conf/target_gitlab_project.conf" ]; then
  cp ./conf/target_gitlab_project.conf.model ./conf/target_gitlab_project.conf
fi

docker_compose_path=`which docker-compose`
docker_path=`which docker`

if [ -z "${docker_compose_path}" -a -z "${docker_path}" ]; then
  echo "[Error] Nothing docker command. Please install."
  exit 1
fi

echo "=== START - docker image build ==="
if [ -n "${docker_compose_path}" ]; then
  docker-compose build
elif [ -n "${docker_path}" ]; then
  docker build -f docker/Dockerfile -t ${DOCKER_IMAGE_NAME} .
fi
echo "=== END - docker image build ==="