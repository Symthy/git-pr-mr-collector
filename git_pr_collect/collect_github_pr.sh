#!/bin/bash
echo "pr collect tool start."
echo

docker_compose_path=`which docker-compose`
docker_path=`which docker`

if [ -z "${docker_compose_path}" -a -z "${docker_path}" ]; then
  echo "[Error] Nothing docker command. Please install."
  exit 1
fi
# container build and run
echo "=== START - docker container build and run ==="
if [ -n "${docker_compose_path}" ]; then
  docker-compose build
  docker-compose up -d
elif [ -n "${docker_path}" ]; then
  docker build -f docker/Dockerfile -t python3:latest .
  docker run -d -t -v `pwd`:/work --rm --name python3 python3:latest
fi
echo "=== END - docker container build and run ==="
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
  result=`docker stop python3`
  if [ $? -eq 0 ]; then
    echo container stop success
  else
    echo "${result}"
  fi
fi
echo "=== END - docker container stop ==="
echo

echo "pr collect tool end. please look under \"out\" directory."
