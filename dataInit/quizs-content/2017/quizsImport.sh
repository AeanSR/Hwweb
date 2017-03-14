#!/usr/bin/env bash

#导入quizs到hwweb数据库
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-1.mongo
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-2.mongo
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-3.mongo
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quiz-4.mongo

