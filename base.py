#!/usr/bin/python
# coding=utf-8
import os
import re
import tornado.web
import json
import sys
import copy

import motor
import pymongo
import logging
import logging.config

from datetime import datetime, timedelta
import time

from HwWebUtil import HwWebUtil, QuizStatus, QuesStatus, QuizFlag, ProjectStatus, TopoStatus, UploadType, QuizType

db = motor.MotorClient('localhost', 27017).hwweb
sdb = pymongo.MongoClient('localhost', 27017).hwweb
testdb = motor.MotorClient('localhost', 27017).test_hwweb
domain = ".csintro.ucas.ac.cn"
expires_days = 7
md5Salt='a~n!d@r#e$w%l^e&e'
deployed=True

upload_dir = "users_upload"

logpath = os.path.join(os.path.dirname(__file__),'log')
if not os.path.exists(logpath):
	os.makedirs(logpath)
logging.config.fileConfig('conf/logging.conf')
logger = logging.getLogger("index")

# compatible code
pre_match = re.compile("ucas-2017.tk")
new_main_page = "http://csintro.ucas.ac.cn"

class BaseHandler(tornado.web.RequestHandler):
    online_data = {}
    # admin 登录
    def get_current_admin(self):
        adminId = self.get_secure_cookie("adminId")
        if adminId and self.online_data and adminId in self.online_data.keys():
            return adminId
        else:
            return None

    # admin 注销
    def clear_current_admin(self):
        adminId = self.get_secure_cookie("adminId")
        if not adminId:
            return
        elif self.online_data and adminId in self.online_data.keys():
            del self.online_data[adminId]
        self.clear_cookie("adminId", domain=domain)

    # 普通学生登录
    def get_current_user(self):
        userId = self.get_secure_cookie("userId")
        if userId and self.online_data and userId in self.online_data.keys():
            return userId
        else:
            return None

    # 普通学生注销
    def clear_current_user(self):
        userId = self.get_secure_cookie("userId")
        if not userId:
            return
        elif self.online_data and userId in self.online_data.keys():
            del self.online_data[userId]
        self.clear_cookie("userId", domain=domain)

    def write_error(self, status_code, **kwargs):
        self.write("You caused a %d error." % status_code)
        if "exc_info" in kwargs.keys():
            print kwargs["exc_info"]
        self.flush()

    # # 如果存在全是客观题，状态为publish，且已过deadline的quiz，置其状态为review
    # # 所有有Quiz状态信息的都要首先调用这个函数
    # # 针对Quiz状态
    # @tornado.gen.coroutine
    # def checkQuizAndUpdateStatus(self):
    #     quiz_cursor = db.quizs.find()
    #     quizs = yield quiz_cursor.to_list(None)
 #            for a_quiz in quizs:
 #                if a_quiz["status"] == QuizStatus["PUBLISH"] and not datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
 #                    tmp = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])
 #                    if not tmp:
 #                        a_quiz['status'] = QuizStatus["REVIEW"]
 #                        yield db.quizs.update({"quiz_id":a_quiz['quiz_id']}, {"$set":{"status":QuizStatus['REVIEW']}})

 #        # 将每道客观题的分数和客观提总分保存到数据库
 #        # 针对solution的选择题分数和客观题总分
 #        @tornado.gen.coroutine
 #        def reviewSelectionQues(self, user_quiz, a_quiz, essayQueses):
    #     all_score = 0
    #     cnt = 0
    #     for a_content in a_quiz["content"]:
    #         score = 0
    #         if a_content["type"] != QuizType["ESSAYQUES"] and set(a_content["answer"])  == set(user_quiz["solutions"][cnt]["solution"]) :
    #             score = a_content["score"]
    #             all_score += a_content["score"]
    #         user_quiz["solutions"][cnt]["score"] = score
    #         cnt += 1
    #     user_quiz["all_score"] = all_score
    #     # 如果全部为选择题，不仅进行自动打分操作，而且设置solu为REVIEW，flag为QuizFlag["FULL_SCORED"]
    #     if not essayQueses:
    #         user_quiz['status'] = QuizStatus["REVIEW"]
    #     yield db.solutions.save(user_quiz)

    def isTestUser(self, userId):
        regexEx = r'^ucas'
        if re.match(regexEx, userId.lower()):
            return True
        else:
            return False

    def canDoExperiment(self, exp_id):
        if not self.isTestUser(self.get_current_user()):
            if not HwWebUtil.isValid(self.online_data[self.get_current_user()]["classNo"], exp_id):
                logger.warn("Exp%d user: %s try to do experiment 3 when the exp%d is not available for himself" %(exp_id, self.get_current_user(), exp_id)  )
                info = copy.deepcopy(self.online_data[self.get_current_user()])
                if "loginTime" in info:
                    del info['loginTime']
                self.write(json.dumps({"status":"NA", "info":info})) # not availabe
                self.finish()
                return False
        return True


    #for test, release version needs to delete it
    def test_user(self):
        self.set_secure_cookie("userId", "ucas1-1", domain=domain, expires_days=expires_days)
        self.online_data["ucas1"] = {'name': "Sai",'userId':"ucas1-1", "classNo":"0", "group":"0-1", "yearOfEntry":2014}

    #for test, release version needs to delete it
    def test_admin(self):
        self.set_secure_cookie("adminId", "lichundian", domain=domain, expires_days=expires_days)
        self.online_data["lichundian"] = {'name': "李春典",'adminId':"lichundian"}


class StaticFileHandler(BaseHandler):
    FileCache = {}
    DefaultContentType = "text/plain"
    ContentTypeMap = {
            "html": "text/html",
            "css":  "text/css",
            "js":   "text/javascript",
            "pdf":  "application/pdf",
            "gif":  "image/gif",
            "png":  "image/png",
            "bmp":  "image/bmp",
            "jpg":  "image/jpeg",
            "svg":  "text/xml"}

    def get(self, relative_path):
        path = os.path.join(os.path.dirname(__file__), "static", relative_path)
        if os.path.isfile(path):
            if path in StaticFileHandler.FileCache:
                read_data = StaticFileHandler.FileCache[path]
            else:
                with open(path, 'r') as f:
                    read_data = f.read()
                StaticFileHandler.FileCache[path] = read_data
            suffix = path[path.rfind(".")+1:]
            if suffix in StaticFileHandler.ContentTypeMap:
                contentType = StaticFileHandler.ContentTypeMap[suffix]
            else:
                contentType = StaticFileHandler.DefaultContentType
            self.set_header("Content-Type", contentType)
            self.write(read_data)
            self.finish()
        else:
            self.render("./template/404.html")
        return
