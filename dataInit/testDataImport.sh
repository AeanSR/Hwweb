#!/usr/bin/env bash

#===用于测试的数据库(test_hwweb),可能会清空========================================

#导入test_game_users到test_hwweb数据库(游戏测试)
mongoimport -h localhost --port 27017 -d test_hwweb -c users --jsonArray --file test_game_users.mongo

#导入test_homework_users到hwweb数据库(作业测试),作业测试角色和普通角色一致
mongoimport -h localhost --port 27017 -d hwweb -c users --jsonArray --file test_homework_user.mongo
