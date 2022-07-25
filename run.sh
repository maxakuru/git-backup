#!/bin/bash

COMMAND="python3 -m git_backup.main"

if [ -n "$CLI" ] && [ $CLI = true ]; then
    COMMAND="$@"
fi

exec $COMMAND