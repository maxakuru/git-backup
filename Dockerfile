# syntax=docker/dockerfile:1
FROM python:3.9-alpine
WORKDIR /backup

RUN apk add --no-cache bash git rsync git-lfs
RUN git config http.postBuffer 524288000

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY git_backup /backup/git_backup
COPY run.sh /backup/run.sh
RUN chmod +x /backup/run.sh

ENTRYPOINT ["./run.sh"]