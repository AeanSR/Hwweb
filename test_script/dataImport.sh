#!/usr/bin/env bash


#导入users到test数据库
#mongoimport -h localhost --port 27017 -d test -c users --jsonArray --file users.mongo

#导入notices到test数据库
#mongoimport -h localhost --port 27017 -d test -c notices --jsonArray --file notices.mongo

#导入quizs到test数据库
#mongoimport -h localhost --port 27017 -d test -c quizs --jsonArray --file quizs.mongo

#导入results到test数据库
mongoimport -h localhost --port 27017 -d test -c results --jsonArray --file results.mongo



