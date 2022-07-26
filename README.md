# git-backup

[![Docker Image Version (latest by date)](https://img.shields.io/docker/v/maxakuru/git-backup?label=Docker%20image)](https://hub.docker.com/r/maxakuru/git-backup) [![Publish](https://github.com/maxakuru/git-backup/actions/workflows/publish.yml/badge.svg)](https://github.com/maxakuru/git-backup/actions/workflows/publish.yml) [![Test](https://github.com/maxakuru/git-backup/actions/workflows/test.yml/badge.svg)](https://github.com/maxakuru/git-backup/actions/workflows/test.yml)

```
🚨 Git is not designed to serve as a backup tool.
```

..but this does it anyway. Backup files/folders to a git repo. Run on a cron schedule or repeated loop with delay. Archive files/folders and set specific destinations in remote repository. Use Git LFS or chunking for oversized files.

## Install

### With Docker
```sh
docker pull maxakuru/git-backup
```
```sh
docker run -it --rm \
    -v $PWD/config:/backup/config \
    -v $PWD/repos:/backup/repos \
    -v $PWD/secrets:/backup/secrets \
    -e REPO_NAME=<REPO_NAME> \
    -e REPO_OWNER=<GIT_OWNER> \
    -e GIT_TOKEN=<GIT_PATOKEN> \
    -e PATHS=local/path/one:remote/path/one,local/path/two:remote/path/two \
    -e LOOP=<false|true> \
    -e LOOP_INTERVAL=<minutes (float)> \
    -e LOOP_SCHEDULE=<crontab expression (string)> \
    -e COMPRESS=<zip|tar|gztar|bztar|xztar|true|false> \
    -e SAVE_CONFIG=<bool> \
    -e SAVE_SECRETS=<bool> \
    -e GIT_ADD=<bool> \
    -e GIT_COMMIT=<bool> \
    -e GIT_PUSH=<bool> \
    -e GIT_MESSAGE=<string> \
    -e GIT_EMAIL=<string> \
    -e GIT_NAME=<string> \
    -e LOG_LEVEL=<0|1|2|3|4|5> \
    maxakuru/git-backup
```

## With Docker Compose
```yaml
# docker-compose.yaml
backup:
    container_name: backup
    image: maxakuru/git-backup:latest
    restart: always
    environment:
        - REPO_NAME=<REPO_NAME>
        - REPO_OWNER=<REPO_OWNER>
        - GIT_TOKEN=<GIT_TOKEN>
        # - ... see above
```


## Dev

### Run with local changes
```sh
docker run -it --rm -v $PWD/volume:/backup/config \
    -v $PWD/git_backup:/backup/git_backup \
    -e REPO_NAME=<REPO_NAME> \
    -e REPO_OWNER=<REPO_OWNER> \
    -e GIT_TOKEN=<GIT_TOKEN> \
    -e PATHS=<PATHS> \
    maxakuru/git-backup:dev
```

### Test
```sh
echo "MY_GITHUB_TOKEN=<GITHUB_PAT> >> .env"
./test/functional/test.sh
```

### Build
```sh
docker build -t maxakuru/git-backup:dev .
```

### Run
```sh
docker run -it --rm -v $PWD/volume:/backup/config \
    -e REPO_NAME=<REPO_NAME> \
    -e REPO_OWNER=<REPO_OWNER> \
    -e GIT_TOKEN=<GIT_TOKEN> \
    -e PATHS=<PATHS> \
    maxakuru/git-backup:dev
```

### Open shell
```sh
docker run -it --rm -e="CLI=true" -v $PWD/volume:/backup/config maxakuru/git-backup:dev /bin/bash
```