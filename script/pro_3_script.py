#!/usr/bin/env python
import pymongo
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.hwweb


print "group, score"
for groupInfo in db.routeTopo.find({"mode":0},{"_id":0, "finalScore":1, "group":1}).sort("group", pymongo.ASCENDING):
    if "finalScore" in groupInfo:
        print "%s, %d" %(groupInfo["group"], groupInfo["finalScore"])
