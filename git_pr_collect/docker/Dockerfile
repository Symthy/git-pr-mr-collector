FROM python:3
USER root

RUN apt-get update && \
  apt-get -y install locales && \
  localedef -f UTF-8 -i ja_JP ja_JP.UTF-8
ENV LANG ja_JP.UTF-8
ENV LANGUAGE ja_JP:ja
ENV LC_ALL ja_JP.UTF-8
ENV TZ JST-9
ENV TERM xterm

RUN mkdir -p /work
COPY docker/require_lib.txt /work
WORKDIR /work

RUN pip install --upgrade pip && \
  pip install --upgrade setuptools && \
  pip install -r require_lib.txt
