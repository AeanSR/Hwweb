#!/usr/bin/python
# coding=utf-8
import os
import tornado.web
import motor
import pymongo
import logging
import logging.config

db = motor.MotorClient('localhost', 27017).hwweb
sdb = pymongo.MongoClient('localhost', 27017).hwweb
testdb = motor.MotorClient('localhost', 27017).test_hwweb
domain = ".ucas-2017.tk"
expires_days = 7
md5Salt='a~n!d@r#e$w%l^e&e'
deployed=True

upload_dir = "users_upload"

logpath = os.path.join(os.path.dirname(__file__),'log')
if not os.path.exists(logpath):
	os.makedirs(logpath)
logging.config.fileConfig('conf/logging.conf')
logger = logging.getLogger("index")

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

class StaticFileHandler(BaseHandler):
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
            with open(path, 'r') as f:
                read_data = f.read()
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
