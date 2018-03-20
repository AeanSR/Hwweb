#!/usr/bin/env bash

#===用于测试的数据库(test_hwweb),可能会清空========================================

#导入users_test.mongo到hwweb数据库(作业测试和实验测试，都是为了老师演示),作业测试角色和普通角色一致
# 测试数据的组都是"0"开头，和普通角色的组的命名不一样
mongoimport -h localhost --port 27017 -d hwweb -c users --jsonArray --file users_test.mongo
mongoimport -h localhost --port 27017 -d hwweb -c users --jsonArray --file users.mongo
