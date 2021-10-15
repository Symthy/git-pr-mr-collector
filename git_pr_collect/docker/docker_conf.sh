#!/bin/bash

# constant
DOCKER_IMAGE_NAME="git_pr_collect_python3:latest"
DOCKER_CONTAINER_NAME="git_pr_collect_python3"

docker_compose_path=`which docker-compose`
docker_path=`which docker`

function validate_docker_command() {


  if [ -z "${docker_compose_path}" -a -z "${docker_path}" ]; then
    echo "[Error] Nothing docker command. Please install."
    exit 1
  fi
}

function build_and_run_docker_container() {
  docker_image=`docker image ls -q ${DOCKER_IMAGE_NAME}`

  # container build and run
  echo "=== START - docker container run ==="
  if [ -n "${docker_compose_path}" ]; then
    if [ -z "${docker_image}" ]; then
      docker-compose build
    fi
    docker-compose up -d
  elif [ -n "${docker_path}" ]; then
    if [ -z "${docker_image}" ]; then
      docker build -f docker/Dockerfile -t "${DOCKER_IMAGE_NAME}" .
    fi
    docker run -d -t -v `pwd`:/work --rm --name "${DOCKER_CONTAINER_NAME}" "${DOCKER_IMAGE_NAME}"
  fi
  echo "=== END - docker container run ==="
  echo
}

function stop_docker_container() {
  # container stop
  echo "=== START - docker container stop ==="
  if [ -n "${docker_compose_path}" ]; then
    docker-compose down
  else
    result=`docker stop "${DOCKER_CONTAINER_NAME}"`
    if [ $? -eq 0 ]; then
      echo "container stop success"
    else
      echo "${result}"
    fi
  fi
  echo "=== END - docker container stop ==="
  echo
}