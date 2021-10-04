#!/bin/bash

source "./docker/docker_conf.sh"

echo "pr collect tool start."
echo

docker_compose_path=`which docker-compose`
docker_path=`which docker`

if [ -z "${docker_compose_path}" -a -z "${docker_path}" ]; then
  echo "[Error] Nothing docker command. Please install."
  exit 1
fi

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

# execute collect pull request tool
echo "=== python version ==="
docker exec -it python3 python --version
echo "======================"
echo
docker exec -it python3 /bin/bash -c "cd src && python collect_github_pr_review_comments.py `echo $@`"
echo

# container stop
echo "=== START - docker container stop ==="
if [ -n "${docker_compose_path}" ]; then
  docker-compose down
else
  result=`docker stop git_pr_collect_python3`
  if [ $? -eq 0 ]; then
    echo container stop success
  else
    echo "${result}"
  fi
fi
echo "=== END - docker container stop ==="
echo

echo "pr collect tool end. please look under \"out\" directory."
