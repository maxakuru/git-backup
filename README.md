# git-backup

Backup files/folders to a git repo. Run on a cron schedule or repeated loop with delay. Archive files/folders and set specific destinations in remote repository.

## Install

### With Docker
```sh
docker pull maxakuru/git-backup

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

## Deploy
```sh
docker build -t maxakuru/git-backup .
docker push maxakuru/git-backup[:tag]
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
    -e COMPRESS=<tar|zip|true|false> \
    maxakuru/git-backup:dev
```

### Test
```sh
echo "<GITHUB_KEY> > .env"
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
    -e COMPRESS=<tar|zip|gztar|bztar|xztar|true|false> \
    maxakuru/git-backup:dev
```

### Open shell
```sh
docker run -it --rm -e="CLI=true" -v $PWD/volume:/backup/config maxakuru/git-backup:dev /bin/bash
```