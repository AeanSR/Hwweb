#!/usr/bin/env bash
dumpPath=$(cd `dirname $0`; pwd)/backupDump-`date "+%Y-%m-%d_%H-%M-%S"`
MONGO_HOME=/usr/local/mongodb-linux-x86_64-2.6.4
#MONGO_HOME=/usr
cmd="$MONGO_HOME/bin/mongodump -h localhost --port 27017 -d hwweb -o $dumpPath"
echo $cmd && ${cmd}
