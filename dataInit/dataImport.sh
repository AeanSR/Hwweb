#!/usr/bin/env bash

echo "admin"
mongoimport -h localhost --port 27017 -d hwweb -c admin --jsonArray --file admin.mongo

echo "users_test"
mongoimport -h localhost --port 27017 -d hwweb -c users --jsonArray --file users_test.mongo

echo "notices"
mongoimport -h localhost --port 27017 -d hwweb -c notices --jsonArray --file notices.mongo

echo "quizs"
mongoimport -h localhost --port 27017 -d hwweb -c quizs --jsonArray --file quizs.mongo

echo "projects"
mongoimport -h localhost --port 27017 -d hwweb -c projects --jsonArray --file projects.mongo
