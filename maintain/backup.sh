#!/usr/bin/env bash
dumpPath=$(cd `dirname $0`; pwd)/backupDump-`date "+%Y-%m-%d_%H-%M-%S"`
echo $dumpPath >> /home/andrew/ccc
MONGO_HOME=/usr/local/mongodb-linux-i686-2.6.5
cmd="$MONGO_HOME/bin/mongodump -h localhost --port 27017 -d hwweb -o $dumpPath"
echo $cmd && ${cmd}
