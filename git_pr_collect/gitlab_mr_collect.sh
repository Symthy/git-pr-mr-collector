#!/bin/bash

source "./docker/docker_exec.sh"

echo "GitLab MR collect tool start."
echo

validate_docker_command
build_and_run_docker_container

# execute collect pull request tool
echo "=== python version ==="
docker exec -it "${DOCKER_CONTAINER_NAME}" python --version
echo "======================"
echo
docker exec -it "${DOCKER_CONTAINER_NAME}" /bin/bash -c "cd src && python collect_github_mr_comments.py `echo $@`"
echo

stop_docker_container

echo "GitLab MR collect tool end. please look under \"out/gitlab\" directory."
