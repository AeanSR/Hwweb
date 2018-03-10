#!/usr/bin/env bash
if [ $# -lt 1 ]; then
    echo "usage: ./restore.sh sourcePath"
    exit
fi
dumpPath=$1
MONGO_HOME=/usr/local/mongodb-linux-x86_64-2.6.4
cmd="$MONGO_HOME/bin/mongorestore -h localhost --port 27017 -d hwweb $dumpPath/hwweb"
echo $cmd && ${cmd}
