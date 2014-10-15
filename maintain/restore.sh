#!/usr/bin/env bash
if [ $# -lt 1 ]; then
    echo "usage: ./restore.sh sourcePath"
    exit
fi

dumpPath=$1
cmd="mongorestore -h localhost --port 27017 -d hwweb $dumpPath/hwweb"
echo $cmd && ${cmd}
