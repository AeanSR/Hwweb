#!/usr/bin/env bash

#===同学使用的数据库(hwweb)=============================================

#导入admin到hwweb数据库
echo "admin"
mongoimport -h localhost --port 27017 -d hwweb -c admin --jsonArray --file admin.mongo

#导入users到hwweb数据库
echo "users"
mongoimport -h localhost --port 27017 -d hwweb -c users --jsonArray --file users.mongo

#导入notices到hwweb数据库
echo "notices"
mongoimport -h localhost --port 27017 -d hwweb -c notices --jsonArray --file notices.mongo

#导入quizs到hwweb数据库
echo "quizs"
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quizs.mongo

#导入projects到hwweb数据库
echo "projects"
mongoimport -h localhost --port 27017 -d hwweb -c projects --jsonArray --file projects.mongo

