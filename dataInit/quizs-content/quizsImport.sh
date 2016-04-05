#!/usr/bin/env bash

#导入quizs到hwweb数据库
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-1-2014.mongo
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-2-2014.mongo
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-3-2014.mongo
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-4-2014.mongo

