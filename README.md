# git-backup

Backup files/folders to a git repo. Run on a cron schedule or repeated loop with delay. Archive files/folders and set specific destinations in remote repository.


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
    gitbackup-dev
```

### Test
```sh
echo "<GITHUB_KEY> > .env"
./test/functional/test.sh
```

### Build
```sh
docker build -t gitbackup-dev .
```

### Run
```sh
docker run -it --rm -v $PWD/volume:/backup/config \
    -e REPO_NAME=<REPO_NAME> \
    -e REPO_OWNER=<REPO_OWNER> \
    -e GIT_TOKEN=<GIT_TOKEN> \
    -e PATHS=<PATHS> \
    -e COMPRESS=<tar|zip|gztar|bztar|xztar|true|false> \
    gitbackup-dev
```

### Open shell
```sh
docker run -it --rm -e="CLI=true" -v $PWD/volume:/backup/config gitbackup-dev /bin/bash
```