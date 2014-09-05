#!/usr/bin/env bash

#导入admin到test数据库
#mongoimport -h localhost --port 27017 -d test -c admin --jsonArray --file admin.mongo

#导入users到test数据库
#mongoimport -h localhost --port 27017 -d test -c users --jsonArray --file users.mongo
#mongoimport -h localhost --port 27017 -d test -c users --jsonArray --file quiz_3_users.mongo

#导入notices到test数据库
#mongoimport -h localhost --port 27017 -d test -c notices --jsonArray --file notices.mongo

#导入quizs到test数据库
#mongoimport -h localhost --port 27017 -d test -c quizs --jsonArray --file quizs.mongo

#导入solutions到test数据库
#mongoimport -h localhost --port 27017 -d test -c solutions --jsonArray --file solutions.mongo
#mongoimport -h localhost --port 27017 -d test -c solutions --jsonArray --file quiz_3_solutions.mongo
#mongoimport -h localhost --port 27017 -d test -c solutions --jsonArray --file quiz_4_solutions.mongo

#导入projects到test数据库
#mongoimport -h localhost --port 27017 -d test -c projects --jsonArray --file projects.mongo

#导入user_uploads到test数据库
#mongoimport -h localhost --port 27017 -d test -c user_uploads--jsonArray --file user_uploads.mongo
