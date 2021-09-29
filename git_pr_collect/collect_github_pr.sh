#!/bin/bash
echo "pr collect tool start."
echo

# container build and run
echo "=== START - docker container build and run ==="
docker-compose build
docker-compose up -d
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
docker-compose down
echo "=== END - docker container stop ==="
echo

echo "pr collect tool end. please look under \"out\" directory."