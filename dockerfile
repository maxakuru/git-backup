# syntax=docker/dockerfile:1
FROM python:3.9-alpine
WORKDIR /backup

RUN apk add --no-cache bash git rsync

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY git_backup /backup/git_backup
COPY run.sh /backup/run.sh

ENTRYPOINT ["/backup/run.sh"]