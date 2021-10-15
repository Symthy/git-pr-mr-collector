#!/bin/bash

export GITLAB_HOME=/srv/gitlab

docker run --detach \
  --hostname localhost  \
  --publish 443:443 --publish 80:80 --publish 22:22 \
  --name gitlab \
  --volume $GITLAB_HOME/config:/etc/gitlab \
  --volume $GITLAB_HOME/logs:/var/log/gitlab \
  --volume $GITLAB_HOME/data:/var/opt/gitlab \
  gitlab/gitlab-ce:latest