#!/usr/bin/env bash

#===用于测试的数据库(test_hwweb),可能会清空========================================

#导入users到test_hwweb数据库
mongoimport -h localhost --port 27017 -d test_hwweb -c users --jsonArray --file test_users.mongo
