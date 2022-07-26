#!/bin/bash

set -e

cd "$(dirname "$0")"
cd "../.."

[ -f ./.env ] && source ./.env

: "${TAG:=dev}"
: "${USER:=maxakuru}"
: "${IMAGE:=git-backup}"
: "${GIT_NAME:=maxakuru}"
: "${GIT_EMAIL:=maxakuru@users.noreply.github.com}"
: "${REPO:=git-backup}"
: "${OWNER:=maxakuru}"
: "${BRANCH:=tests-ci}"
: "${GIT_PUSH:=0}"
: "${PATHS:='test/functional/paths/a.d:foo/a.d,./test/functional/paths/b:./foo/b,/backup/test/functional/paths/c.txt:/bar/c.txt'}"


now="$(date)"
echo "A_ACTUAL=\"$now\"" > "$PATHS/a.d/a"
echo "B_ACTUAL=\"$now\"" > "$PATHS/b"
echo "C_ACTUAL=\"$now\"" > "$PATHS/c.txt"

docker run --rm -v $PWD/volume/config:/backup/config \
    -v $PWD/volume/repos:/backup/repos \
    -v $PWD/volume/secrets:/backup/secrets \
    -v $PWD/test:/backup/test \
    -v $PWD/git_backup:/backup/git_backup \
    -e REPO_NAME=$REPO \
    -e REPO_OWNER=$OWNER \
    -e REPO_BRANCH=$BRANCH \
    -e GIT_TOKEN=$MY_GIT_TOKEN \
    -e PATHS=$PATHS \
    -e LOOP=false \
    -e COMPRESS=zip \
    -e SAVE_CONFIG=0 \
    -e SAVE_SECRETS=0 \
    -e GIT_PUSH=$GIT_PUSH \
    -e GIT_EMAIL=$GIT_EMAIL \
    -e GIT_NAME=$GIT_NAME \
    $USER/$IMAGE:$TAG

mkdir -p ./tmp

unzip volume/repos/$OWNER/$REPO/foo/a.zip -d tmp/a
unzip volume/repos/$OWNER/$REPO/foo/b.zip -d tmp/b
unzip volume/repos/$OWNER/$REPO/bar/c.zip -d tmp/c

source ./tmp/a/a.d/a
[ "$A_ACTUAL" == "$now" ] || (echo "Test failed, A_ACTUAL has incorrect value: $A_ACTUAL (expected $now)" && rm -rf ./tmp && exit 1)

source ./tmp/b/b
[ "$B_ACTUAL" == "$now" ] || (echo "Test failed, B_ACTUAL has incorrect value: $B_ACTUAL (expected $now)" && rm -rf ./tmp && exit 1)

source ./tmp/c/c.txt
[ "$C_ACTUAL" == "$now" ] || (echo "Test failed, C_ACTUAL has incorrect value: $C_ACTUAL (expected $now)" && rm -rf ./tmp && exit 1)

rm -rf ./tmp

