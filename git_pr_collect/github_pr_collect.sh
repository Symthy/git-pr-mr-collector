#!/bin/bash

source "./docker/docker_conf.sh"

echo "Github PR collect tool start."
echo

validate_docker_command
build_and_run_docker_container

# execute collect pull request tool
echo "=== python version ==="
docker exec -it "${DOCKER_CONTAINER_NAME}" python --version
echo "======================"
echo
docker exec -it "${DOCKER_CONTAINER_NAME}" /bin/bash -c "cd src && python collect_github_pr_review_comments.py `echo $@`"
echo

stop_docker_container

echo "Github PR collect tool end. Please look under \"out/github\" directory."
