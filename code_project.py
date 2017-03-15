#!/usr/bin/python
# coding=utf-8
import tornado.web
from base import BaseHandler


class CodeMainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
	 	self.render("./template/code_project.html" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs)
	 	return

class CodeOriginPictureHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
	 	self.render("./template/main.html" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs)
	 	return

class CodeSubmitCodeHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def post(self):
	 	self.render("./template/main.html" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs)
	 	return

class CodeSubmitPictureHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def post(self):
	 	self.render("./template/main.html" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs)
	 	return
