#!/usr/bin/python
# coding=utf-8
import tornado.web


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
