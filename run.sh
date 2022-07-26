#!/bin/bash

COMMAND="python3 -m git_backup.main"

if [ -n "$CLI" ] && [ $CLI = true ]; then
    COMMAND="$@"
fi

echo "starting with command: $COMMAND"

exec $COMMAND