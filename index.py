#!/usr/bin/python
# coding=utf-8
import os
import re
import tornado.ioloop
import tornado.web
import motor
import json
import sys
import copy

import zipfile
import hashlib
import random
import pymongo
import logging
import logging.config

from datetime import datetime
from datetime import timedelta
import time

from sockjs.tornado import SockJSRouter, SockJSConnection
from HwWebUtil import HwWebUtil
from HwWebUtil import QuizStatus
from HwWebUtil import QuesStatus
from HwWebUtil import QuizFlag
from HwWebUtil import QuizType
from HwWebUtil import ProjectStatus
from HwWebUtil import TopoStatus
from HwWebUtil import UploadType

# to do, filter the text input
# to do, 多选题
# to do, admin打包下载报告
# to do, admin上传题目
# to do, 用上a_ques 数据的id字段，将所有使用cnt/count的换成id

db = motor.MotorClient('localhost', 27017).hwweb
sdb = pymongo.MongoClient('localhost', 27017).hwweb
testdb = motor.MotorClient('localhost', 27017).test_hwweb
domain = ".ucas-2014.tk"
expires_days = 7
md5Salt='a~n!d@r#e$w%l^e&e'
deployed=True

logpath = os.path.join(os.path.dirname(__file__),'log')
if not os.path.exists(logpath):
	os.makedirs(logpath)
logging.config.fileConfig('conf/logging.conf')
logger = logging.getLogger("index")


def strSolution(solu):
	strSolu = ""
	for s in solu["solutions"]:
		strSolu += str(s['solution'])
	return strSolu

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
	# 	quiz_cursor = db.quizs.find()
	# 	quizs = yield quiz_cursor.to_list(None)
 #    		for a_quiz in quizs:
 #    			if a_quiz["status"] == QuizStatus["PUBLISH"] and not datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
 #    				tmp = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])
 #    				if not tmp:
 #    					a_quiz['status'] = QuizStatus["REVIEW"]
 #    					yield db.quizs.update({"quiz_id":a_quiz['quiz_id']}, {"$set":{"status":QuizStatus['REVIEW']}})

 #    	# 将每道客观题的分数和客观提总分保存到数据库
 #    	# 针对solution的选择题分数和客观题总分
 #    	@tornado.gen.coroutine
 #    	def reviewSelectionQues(self, user_quiz, a_quiz, essayQueses):
	# 	all_score = 0
	# 	cnt = 0
	# 	for a_content in a_quiz["content"]:
	# 		score = 0
	# 		if a_content["type"] != QuizType["ESSAYQUES"] and set(a_content["answer"])  == set(user_quiz["solutions"][cnt]["solution"]) :
	# 			score = a_content["score"]
	# 			all_score += a_content["score"]
	# 		user_quiz["solutions"][cnt]["score"] = score
	# 		cnt += 1
	# 	user_quiz["all_score"] = all_score
	# 	# 如果全部为选择题，不仅进行自动打分操作，而且设置solu为REVIEW，flag为QuizFlag["FULL_SCORED"]
	# 	if not essayQueses:
	# 		user_quiz['status'] = QuizStatus["REVIEW"]
	# 	yield db.solutions.save(user_quiz)

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

class MainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		# self.checkQuizAndUpdateStatus()

    		nt_cursor = db.notices.find().sort("time", pymongo.DESCENDING)
    		notices = yield nt_cursor.to_list(None)
    		quiz_cursor = db.quizs.find().sort("quiz_id", pymongo.ASCENDING)
    		quizs = yield quiz_cursor.to_list(None)
	 	self.render("./template/main.template" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs)
	 	return

class QuizSaveHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine

	def post(self, quiz_id):

		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
		user_quiz = yield db.solutions.find_one({"quiz_id":int (quiz_id), "userId":self.current_user})
		op_now = datetime.now()

		# submit or save operation is false
		if not HwWebUtil.canSaveOrSubmit(a_quiz, user_quiz, op_now):
			self.redirect("/main")
			return


		quiz_contents = yield db.quizs.find_one({"quiz_id": int(quiz_id)}, {"content":1, "_id":0})
		doc = {}
		if user_quiz:
			doc["_id"] =  user_quiz['_id']
			doc['userId'] = user_quiz["userId"]
		doc["userId"] =  self.current_user
		doc["quiz_id"] = int(quiz_id)
		solutions= []
		status = 0
		for a_content in quiz_contents["content"]:
			ques_status = QuesStatus["UNDONE"]
			ques_id = a_content['id']
			answer = []
			tmp = self.get_argument("quiz_"+quiz_id+"_"+str(ques_id), None)
			# 检测选择题输入，要求必须在选项之内
			if  tmp:
				if a_content['type'] == QuizType['SINCHOICE']:
					if not tmp in map(lambda x:x['value'],a_content['choices']):
						logger.info("student: %s failed to save an answer for homework-%d: %s " %(doc['userId'], int(quiz_id), str(tmp)))
						self.write('<script>alert("答案不符合规定, 请重新提交");window.history.back()</script>')
						self.finish()
						return
				ques_status = QuesStatus["DONE"]
				answer.append(tmp)
			solutions.append({"type":a_content["type"], "solution":answer, "score":0, "status":ques_status, "id":ques_id})
		doc["lastTime"] = op_now.strftime("%Y-%m-%d %H:%M:%S")
		doc["solutions"] = solutions
		doc["all_score"] = 0
		doc["status"] = QuizStatus["SAVE"]
		logger.info("student: %s is saving an answer for homework-%d: %s " %(doc['userId'], int(quiz_id), strSolution(doc)))
		yield db.solutions.save(doc)
		self.redirect("/quiz/"+quiz_id)

class QuizSubmitHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self, quiz_id):

		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
		user_quiz = yield db.solutions.find_one({"quiz_id":int (quiz_id), "userId":self.current_user})
		op_now = datetime.now()

		# submit or save operation is false
		if not HwWebUtil.canSaveOrSubmit(a_quiz, user_quiz, op_now):
			self.redirect("/main")
			return
		quiz_contents = yield db.quizs.find_one({"quiz_id": int(quiz_id)}, {"content":1, "_id":0})
		doc = {}
		if user_quiz:
			doc["_id"] =  user_quiz['_id']
			doc['userId'] = user_quiz["userId"]
		doc["userId"] =  self.current_user
		doc["quiz_id"] = int(quiz_id)
		solutions= []
		status = 0
		for a_content in quiz_contents["content"]:
			ques_status = QuesStatus["UNDONE"]
			ques_id = a_content['id']
			solution = []
			score = 0
			tmp = self.get_argument("quiz_"+quiz_id+"_"+str(ques_id), None)
			# 检测选择题输入，要求必须在选项之内
			if  tmp:
				if a_content['type'] == QuizType['SINCHOICE']:
					if not tmp in map(lambda x:x['value'],a_content['choices']):
						logger.info("student: %s failed to submit an answer for homework-%d: %s " %(doc['userId'], int(quiz_id), str(tmp)))
						self.write('<script>alert("答案不符合规定, 请重新提交");window.history.back()</script>')
						self.finish()
						return
			# to do
			# if submit , i will test whether the student had done all the questions
				ques_status = QuesStatus["DONE"]
				solution.append(tmp)
			solutions.append({"type":a_content["type"], "solution":solution, "score":score, "status":ques_status, "id":ques_id})
		doc["lastTime"] = op_now.strftime("%Y-%m-%d %H:%M:%S")
		doc["solutions"] = solutions
		doc["all_score"] = 0
		doc["status"] = QuizStatus["SUBMIT"]
		logger.info("student: %s is submitting an answer for homework-%d: %s " %(doc['userId'], int(quiz_id), strSolution(doc)))
		yield db.solutions.save(doc)
		self.redirect("/quiz/"+quiz_id)
		return

class QuizHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self, quiz_id):
		# self.checkQuizAndUpdateStatus()

		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
		if not a_quiz  or a_quiz["status"] == QuizStatus["UNPUBLISH"] or datetime.now() < datetime.strptime(a_quiz["releaseTime"], "%Y-%m-%d %H:%M:%S"):
			self.redirect("/main")
			return
		else:
			if 'content' in a_quiz:
				essayQueses = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])
			else:
				a_quiz['content'] = {}
				essayQueses = {}

			# quizs for indexing
			quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1}).sort("quiz_id", pymongo.ASCENDING)
	    		quizs = yield quiz_cursor.to_list(None)
			user_quiz = yield db.solutions.find_one({"quiz_id":int (quiz_id), "userId":self.current_user})
			flag = 0 #it mark the quiz_flag out of the QuizFlag map
			if not user_quiz and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
				flag = QuizFlag["UNDONE"]
			# 为了兼容新添的用户没有作业记录，同时作业也截止了。
			elif not user_quiz:
				flag = QuizFlag["BLANK"]
			elif user_quiz["status"] == QuizStatus["SAVE"]:
				flag = QuizFlag["SAVE"]
			elif user_quiz["status"] == QuizStatus["SUBMIT"] and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
				flag = QuizFlag["SUB_NOTSCORED"]
			# note: solution在SUBMIT后，若quiz已经截止，则可以查看到客观题分数
			elif user_quiz["status"] == QuizStatus["SUBMIT"]:
				# self.reviewSelectionQues(user_quiz=user_quiz, a_quiz=a_quiz, essayQueses=essayQueses)
				if not essayQueses:
					flag = QuizFlag["FULL_SCORED"]
				else:
					flag = QuizFlag["SEMI_SCORED"]
			elif user_quiz["status"] == QuizStatus["BLANK"]:
				flag = QuizFlag["BLANK"]
			# user_quiz["status"] == QuizStatus["REVIEW"]
			else:
				flag = QuizFlag["FULL_SCORED"]

			logger.info("student: %s is viewing the homework-%d(status: %s)" %(self.get_current_user(), int(quiz_id), flag))
			self.render("./template/quiz.html", a_quiz = a_quiz, info = self.online_data[self.get_current_user()],  quizs=quizs, user_quiz=user_quiz, flag=flag)
			return

class ProjectMainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		pro_cursor = db.projects.find().sort("pro_id", pymongo.ASCENDING)
    		projects = yield pro_cursor.to_list(None)
    		scheduleTable= copy.deepcopy(HwWebUtil.getSchedule())
    		for exp_date in scheduleTable["date"]:
    			for i in range(0, len(exp_date)) :
    				exp_date[i] = exp_date[i].strftime("%Y-%m-%d %H:%M:%S")

    		scheduleTable = json.dumps(scheduleTable)
	 	self.render("./template/project-index.html", projects = projects, info = self.online_data[self.get_current_user()], scheduleTable=scheduleTable)
	 	return

class ProjectHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self, pro_id):
    		try:
    			pro_id = int(pro_id)
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return
    		info = self.online_data[self.get_current_user()]
    		pro_cursor = db.projects.find().sort("pro_id", pymongo.ASCENDING)
    		projects = yield pro_cursor.to_list(None)
    		a_pro = yield db.projects.find_one({"pro_id":pro_id, "status":ProjectStatus["PUBLISH"]})
    		if not a_pro:
    			self.redirect("/project")
    			return
    		userId = self.get_current_user()
    		presentation_up_record = yield db.user_uploads.find_one({"pro_id": pro_id, "group": info["group"], "type":UploadType["PRESENTATION"],  "year":info["yearOfEntry"]})
    		report_up_record = yield db.user_uploads.find_one({"pro_id": pro_id, "group": info["group"], "type":UploadType["EXPREPORT"], "year":info["yearOfEntry"]})
    		flag = 0
    		if not datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S')  :
    			flag = ProjectStatus["END"]
    		else:
    			flag = ProjectStatus["PUBLISH"]
	 	self.render("./template/project.html", projects = projects,a_pro=a_pro, info = info, flag=flag,  p_up_record=presentation_up_record, r_up_record=report_up_record)
	 	return

class ProjectUploadHandler(BaseHandler):

	support_type=["application/pdf"]

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self, pro_id, type_id):
		try:
    			pro_id = int(pro_id)
    			type_id = int(type_id)
    			if not type_id in UploadType.values():
    				raise ValueError("type %d is not valid" % type_id)
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return
    		info = self.online_data[self.get_current_user()]
    		a_pro = yield db.projects.find_one({"pro_id":pro_id,"status":ProjectStatus["PUBLISH"]})

    		logger.info("user: %s of gruop %s try to upload file for exp %d in type %d" %(self.get_current_user(), info["group"], pro_id, type_id))

    		# 不存在此project或project已经截止
    		if not a_pro or not datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S')  :
    			self.redirect("/project")
    			return


    		up_record = yield  db.user_uploads.find_one({"pro_id": pro_id, "group": info["group"], "type":type_id, "year":info["yearOfEntry"]})

		upload_path=os.path.join(os.path.dirname(__file__),'report_files',str(pro_id))
		# 创建目录
		if not os.path.exists(upload_path):
			os.makedirs(upload_path)

		filename = None
		arg_name = None
		if type_id == UploadType["PRESENTATION"]:
			arg_name = "presentation"
			filename = str(info["yearOfEntry"]) +"-" + str(pro_id) + "-" + info["group"] + "-presentation.pdf"
		else:
			arg_name = "report"
			filename =  str(info["yearOfEntry"])  +"-" + str(pro_id) + "-"+ info["group"] + "-report.pdf"

		if self.request.files.get(arg_name, None):

			uploadFile = self.request.files[arg_name][0]
			file_size = len(uploadFile['body'])

			# 检测MIME类型
			if not uploadFile["content_type"] in self.support_type or not re.match(r'^.*\.pdf$',uploadFile['filename'].lower() ):
				self.write('<script>alert("仅支持pdf格式,doc/ppt需要转化为pdf格式才能上传");window.location="/project/'+ str(pro_id)+'"</script>')
				self.finish()
				return
			# 检测文件大小
			if  file_size > 10 * 1024 * 1024:
				self.write('<script>alert("请上传10M以下");window.location="/project/'+ str(pro_id)+'"</script>')
				self.finish()
				return
			else :
				logger.info("user: %s of gruop %s succeed to upload file for exp %d in type %d" %(self.get_current_user(), info["group"], pro_id, type_id))
				filepath=os.path.join(upload_path,filename)
				if up_record and os.path.exists(filepath):
					os.remove(filepath)
				elif not up_record:
					up_record = {}
					up_record["year"] = info["yearOfEntry"]
					up_record["group"]=info["group"]
					up_record["pro_id"]=pro_id
					up_record["type"]=type_id
					up_record["file_suffix"]="pdf"
				up_record["uploadTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
				up_record["size"] = file_size
				with open(filepath,'wb') as up:      #有些文件需要已二进制的形式存储，实际中可以更改
					up.write(uploadFile['body'])
				yield db.user_uploads.save(up_record)
		else:
			self.write('<script>alert("请选择文件");window.history.back()</script>')
			self.finish()
			return
		self.redirect('/project/'+ str(pro_id))
		return



# 学生可以通过指定pro_id下载其对应的报告
class ProjectDownloadHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self, pro_id, type_id):
    		try:
    			pro_id = int(pro_id)
    			type_id = int(type_id)
    			if not type_id in UploadType.values():
    				raise ValueError("type %d is not valid" % type_id)
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return
    		info = self.online_data[self.get_current_user()]
    		up_record = yield  db.user_uploads.find_one({"pro_id": pro_id, "group": info["group"], "type":type_id, "year":info["yearOfEntry"]})
    		if not up_record:
    			self.render("./template/404.template")
    			return
    		else:
    			upload_path=os.path.join(os.path.dirname(__file__),'report_files',str(pro_id))
    			if type_id == UploadType["PRESENTATION"]:
				filename = str(info["yearOfEntry"]) +"-" + str(pro_id) + "-" + info["group"] + "-presentation." + up_record["file_suffix"]
			else:
				filename =  str(info["yearOfEntry"]) +"-" + str(pro_id) + "-" + info["group"] + "-report." + up_record["file_suffix"]
    			filepath=os.path.join(upload_path,filename)
    			if not os.path.exists(filepath):
    				self.write('<script>alert("不存在此文件，请重新上传");window.history.back()</script>')
    				self.finish()
    				return
    			with open(filepath, "rb") as f:
    				self.set_header('Content-Disposition', 'attachment;filename='+filename)
    				self.set_header('Content-Type','application/pdf')
      				self.write(f.read())
      			self.finish()
      			return



class AdminHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		if not self.get_current_admin():
			self.redirect("/login")
			return

		# self.checkQuizAndUpdateStatus()
    		nt_cursor = db.notices.find().sort("time", pymongo.DESCENDING)
    		notices = yield nt_cursor.to_list(None)
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1, "content":1}).sort("quiz_id", pymongo.ASCENDING)
    		quizs_index = yield quiz_cursor.to_list(None)
	 	self.render("./template/admin/admin-index.html", info = self.online_data[self.get_current_admin()],notices = notices, quizs_index=quizs_index)
	 	return

class TransciptHandler(BaseHandler):

	@tornado.gen.coroutine
	def get(self, quiz_id):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		transcipt_dir=os.path.join(os.path.dirname(__file__), 'transcipt')
		if not os.path.exists(transcipt_dir):
			os.makedirs(transcipt_dir)
		filename = "transcipt-" + str(quiz_id) + ".csv"
		transcipt_path = os.path.join(transcipt_dir, filename)
		if os.path.exists(transcipt_path):
			os.remove(transcipt_path)
		users_cursor = db.users.find().sort("userId", pymongo.ASCENDING)
		users = yield users_cursor.to_list(None)
		with open(transcipt_path,'w') as up:
			up.write(",".join(["学号", "姓名", "班级", "分数"]) + "\n")
			for user in users:
				if re.match(r"^ucas\d+$", user["userId"]):
					continue
				user_solution = yield db.solutions.find_one({"quiz_id":int(quiz_id), "userId":user["userId"]}, {"_id":0,"all_score":1})
				record = ",".join([user["userId"], user["name"] , str(user["classNo"]), str(user_solution["all_score"] ) ])
				up.write(record.encode('utf8') + "\n")
		with open(transcipt_path, "r") as f:
			self.set_header('Content-Disposition', 'attachment;filename='+filename)
			self.set_header('Content-Type','application/csv')
			self.write(f.read().decode('utf-8'))
      			self.finish()
      		return

class ReportZipDownload(BaseHandler):

	@tornado.gen.coroutine
	def get(self, quiz_id):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		report_dir = os.path.join(os.path.dirname(__file__), 'report_files/' + quiz_id)
		if not os.path.exists(report_dir):
			self.write('<script>alert("学生未上传报告，无法下载");window.history.back()</script>')
			self.finish()
			return
		zipfilename = 'report_' + quiz_id + '.zip'
		zipfilepath = os.path.join(os.path.dirname(__file__), 'report_files/' + zipfilename)
		if os.path.exists(zipfilepath):
			os.remove(zipfilepath)
		f = zipfile.ZipFile(zipfilepath, 'w', zipfile.ZIP_DEFLATED)
		tmpDir = u'实验' + quiz_id + u"-报告包/"
		for dirpath, dirnames, filenames in os.walk(report_dir):
		    for filename in filenames:
		        f.write(os.path.join(report_dir, filename), tmpDir + filename)
		f.close()
		with open(zipfilepath, "rb") as f:
			self.set_header('Content-Disposition', 'attachment;filename='+zipfilename)
			self.set_header('Content-Type','application/zip')
			self.write(f.read())
      			self.finish()
      		return


class StudentListHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		# self.checkQuizAndUpdateStatus()
		page = int(self.get_argument("page", 1))
		quiz_id = int(self.get_argument("quiz_id", 0))
		quiz_cursor = None
		quizs = None
		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1,"content":1}).sort("quiz_id", pymongo.ASCENDING)
		quizs_index = yield quiz_cursor.to_list(None)

		url="/studentlist?"
		# 列出学生所有成绩情况
		if quiz_id == 0:
			quizs = quizs_index
			quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1,"content":1}).sort("quiz_id", pymongo.ASCENDING)
		else:
			url = "/studentlist?quiz_id="+str(quiz_id)
			quiz_cursor = db.quizs.find({"quiz_id":quiz_id},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1,"content":1})
			quizs = yield quiz_cursor.to_list(None)
		# 以30条目为一页
		users_cursor = db.users.find({}, {"name":1, "userId":1}).sort('userId', pymongo.ASCENDING).skip((page-1) * 30)
		cnt = yield users_cursor.count()
    		page_num = (cnt-1)/30 + 1
		users = yield users_cursor.to_list(length=30)
	    	users_list=[]
	    	if not quizs:
	    		self.redirect("./admin")
		for user in users:
			quiz_info=[]
			for a_quiz in quizs:
				if a_quiz['status'] == QuizStatus["UNPUBLISH"]:
					flag = QuizFlag["UNDONE"]
					quiz_info.append({"quiz_id":a_quiz["quiz_id"], "all_score":0, "flag":flag})
					continue
				essayQueses = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])

				user_quiz = yield db.solutions.find_one({"quiz_id":a_quiz['quiz_id'], "userId":user["userId"]})
				flag = 0 #it mark the quiz_flag out of the QuizFlag map
				if not user_quiz and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
					flag = QuizFlag["UNDONE"]
					quiz_info.append({"quiz_id":a_quiz["quiz_id"], "all_score":0, "flag":flag})
					continue
				# 为了兼容新添的用户没有作业记录，同时作业也截止了。
				elif not user_quiz:
					flag = QuizFlag["BLANK"]
					quiz_info.append({"quiz_id":a_quiz["quiz_id"], "all_score":0, "flag":flag})
					continue
				elif user_quiz["status"] == QuizStatus["SAVE"]:
					flag = QuizFlag["SAVE"]
				elif user_quiz["status"] == QuizStatus["SUBMIT"] and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
					flag = QuizFlag["SUB_NOTSCORED"]
				elif user_quiz["status"] == QuizStatus["SUBMIT"]:
					# self.reviewSelectionQues(user_quiz=user_quiz, a_quiz=a_quiz, essayQueses=essayQueses)
					if not essayQueses:
						flag = QuizFlag["FULL_SCORED"]
					else:
						flag = QuizFlag["SEMI_SCORED"]

				elif user_quiz['status'] == QuizStatus['BLANK']:
					flag = QuizFlag["BLANK"]
				# user_quiz["status"] == QuizStatus["REVIEW"]
				else:
					flag = QuizFlag["FULL_SCORED"]
				quiz_info.append({"quiz_id":a_quiz["quiz_id"], "all_score":user_quiz["all_score"], "flag":flag})
			users_list.append({"userId":user["userId"],"name":user["name"], "quiz_info":quiz_info})
		self.render("./template/admin/studentlist.html", info = self.online_data[self.get_current_admin()], users_list=users_list, quizs_index=quizs_index, quizs=quizs, current_page=page,page_num=page_num,url=url)
		return


class ReviewHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self, quiz_id):
    		if not self.get_current_admin():
			self.redirect("/login")
			return
		# self.checkQuizAndUpdateStatus()
    		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1}).sort("quiz_id", pymongo.ASCENDING)
    		quizs_index = yield quiz_cursor.to_list(None)
    		if not a_quiz or a_quiz["status"] == QuizStatus["UNPUBLISH"]:
    			nt_cursor = db.notices.find().sort("time", pymongo.DESCENDING)
    			notices = yield nt_cursor.to_list(None)
    			self.render("./template/admin/admin-index.html", info = self.online_data[self.get_current_admin()], notices = notices, quizs_index=quizs_index)
    			return
    		# can't be reviewd because it's before the deadline, so just list the questions.
    		elif datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
    			self.redirect("/studentlist?quiz_id=" + quiz_id)
    			#self.render("./template/quiz_view.template", info = self.online_data[self.get_current_admin()], a_quiz=a_quiz,quizs_index=quizs_index)
    			return
    		# it has been reviewd
    		elif a_quiz["status"] == QuizStatus["REVIEW"]:
    			self.redirect("/studentlist?quiz_id=" + quiz_id)
    			return

    		# 选择查看已经批阅的用户，还是未批阅的用户。默认是未批阅的用户
    		reviewed = int(self.get_argument("reviewed", 0))
    		page = int(self.get_argument("page", 1))
		# 筛选出问答题
    		essayQueses = filter(lambda x:x["type"]==QuizType["ESSAYQUES"], a_quiz["content"])



    		if reviewed == 0:
    			# 如果没有问答题，则显示没有问答题，不用评分
    			if not essayQueses:
    				self.write('<script>alert("没有问答题，不用评分");window.location="/studentlist?quiz_id='+str(a_quiz["quiz_id"])+'"</script>')
    				self.finish()
    				return
    			url = "/review/%d?"%a_quiz["quiz_id"]
    			users_solutions=[]
    			# 从数据库中选出没有review的solution，分页为30个一页
    			solutions_cursor = db.solutions.find({"quiz_id":a_quiz["quiz_id"], "status":QuizStatus["SUBMIT"]}).sort("userId", pymongo.ASCENDING).skip((page-1) * 30)
    			cnt = yield solutions_cursor.count()
    			page_num = (cnt-1)/30 + 1
    			solutions = yield solutions_cursor.to_list(length=30)
    			# 也是只筛选出问答题的solution
    			for a_user_solu in solutions:
    				solu_tmp= filter(lambda x: x["type"] == QuizType["ESSAYQUES"],a_user_solu["solutions"])

    				# self.reviewSelectionQues(user_quiz=a_user_solu, a_quiz=a_quiz, essayQueses=essayQueses)
    				user = yield db.users.find_one({"userId":a_user_solu["userId"]}, {"name":1, "_id":0,"userId":1})
    				users_solutions.append({"userId":user["userId"], "solutions":solu_tmp,"all_score":a_user_solu["all_score"], "name":user["name"]})
    			# 将content只保存问答题
    			a_quiz["content"] = essayQueses
	    		self.render("./template/quiz_review.template", info = self.online_data[self.get_current_admin()], a_quiz=a_quiz,quizs_index=quizs_index, users_solutions=users_solutions, current_page=page, page_num=page_num, url=url)
	    		return
	    	else:
	    		# to do
	    		# url = "/review/%d?reviewed=1"%a_quiz["quiz_id"]
	    		# users_solutions=[]
    			# 从数据库中选出没有review的solution，分页为30个一页
    			#solutions_cursor = db.solutions.find({"quiz_id":a_quiz["quiz_id"], "status":QuizStatus["REVIEW"]}, {"solutions" : 1 , "all_score":1, "userId":1} ).sort("userId", pymongo.ASCENDING).skip((page-1) * 30)
    			#cnt = yield solutions_cursor.count()
    			#page_num = (cnt-1)/30 + 1
    			#solutions = yield solutions_cursor.to_list(length=30)
    			# 也是只筛选出问答题的solution
    			#for a_user_solu in solutions:
    			#	solu_tmp= filter(lambda x: x["type"] == QuizType["ESSAYQUES"],a_user_solu["solutions"])
    			#	user = yield db.users.find_one({"userId":a_user_solu["userId"]}, {"name":1, "_id":0,"userId":1})
    			#	users_solutions.append({"userId":user["userId"], "solutions":solu_tmp,"all_score":a_user_solu["all_score"], "name":user["name"]})
	    		#	self.render("./template/quiz_review.template", a_quiz=a_quiz,quizs_index=quizs_index, users_solutions=users_solutions, current_page=page, page_num=page_num, url="/review/%d?"%a_quiz["quiz_id"])
	    		return

	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def post(self, quiz_id):
    		if not self.get_current_admin():
			self.redirect("/login")
			return
    		# 找出quiz_id/问答题的id/问答题分数的区域，这些都是为了检验提交分数是否对应
    		a_quiz = None
    		try:
    			a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return
    		if not a_quiz:
    			self.render("./template/404.template")
    			return
    		essayQueses = filter(lambda x:x["type"]==QuizType["ESSAYQUES"], a_quiz["content"])
    		if not essayQueses:
    			self.render("./template/404.template")
    			return
    		# eg: {4:10, 5:15} 即quiz_id的Quiz只有2个问答题，其中id=4的满分为10分，id=5的满分为15分
    		quesMap = {}
    		pattern = "^("+quiz_id+")_(\d+)_("
    		for ques in essayQueses:
    			quesMap[ques['id']] = ques["score"]
    			pattern += (str(ques['id']) + "|")
    		pattern += ")$"
    		#print quesMap
    		print pattern
    		#记录review，格式如下：{userId:[review_ques_id, ..],..}，最后来判断某学生的问答题是否都准确评价，如果是的话才进行数据库写操作
    		review_history ={}

    		args = self.request.arguments
    		for arg in args.items():
    			matchArg = re.match(pattern, arg[0])
    			score = 0
    			try:
    				score = int(arg[1][0])
    			except ValueError, e:
    				print "The argument does not contain numbers\n", e
    				continue
    			if not matchArg or score > quesMap[int(matchArg.group(3))]   or score < 0 :
    				continue
    			else:
    				quesId = int(matchArg.group(3))
    				userId = matchArg.group(2)
    				if not userId in review_history:
    					review_history[userId] = {}
    				review_history[userId][quesId] = score
    		for item in review_history.items():
    			quids = item[1].keys()
    			# 题号和本quiz的问答题号完全吻合
    			if len(quids) == len(quesMap.keys()) and set(quids) == set(quesMap.keys()):
    				sum = 0
    				for id in quids:
    					sum += item[1][id]
    					# 更新每一个问答题的分数
    					yield db.solutions.update({"userId":item[0],"quiz_id":a_quiz["quiz_id"],"status":QuizStatus["SUBMIT"]}, {"$set":{"solutions."+str(id-1)+".score":item[1][id] }})
    				# 更新solution的状态和总分
    				yield db.solutions.update({"userId":item[0],"quiz_id":a_quiz["quiz_id"],"status":QuizStatus["SUBMIT"]},{"$set":{"status":QuizStatus["REVIEW"] }, "$inc":{"all_score": sum} } )

    		# to do 如果将所有solution都REVIEW了，置quiz的status为REVIEW状态
    		# solutions_cursor = db.solutions.find({"quiz_id":a_quiz["quiz_id"], "status":QuizStatus["SUBMIT"]})
    		# cnt = yield solutions_cursor.count()
    		# if cnt == 0:
    		#	db.quizs.update({"quiz_id":a_quiz["quiz_id"]}, {"$set":{"status":QuizStatus["REVIEW"]}})
    		self.redirect("/review/"+quiz_id)
    		return


# 清除游戏记录
class ClearProjectRecord(BaseHandler):


	def get(self):
		self.post()
		return

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		userId = self.get_current_user()
		if not self.isTestUser(userId):
			logger.warn("user: %s tried to attack to clear experiment records" %userId)
			self.redirect("/main")
			return
		logger.info("user: %s clear experiment records" %userId)
		group = self.online_data[userId]["group"]
		# 清除路由器实验的记录
		yield db.routeTopo.remove({"group":group, "year":self.online_data[userId]["yearOfEntry"]})

		# 老鼠实验
		yield db.games.remove({"userId":userId})
		yield db.games.remove({"group":group})
		# 系统实验
		group = self.online_data[userId]["group"]
		try:
			yield db.exp4g.remove({"group":group+'-submit'})
			yield db.exp4g.remove({"group":group+'-test'})
			yield db.exp4u.remove({"group":group+'-test'})
			yield db.exp4u.remove({"group":group+'-submit'})
			if group+'-test' in Exp4Connection.clients:
				Exp4Connection.clients.pop(group+'-test')
				for uid in Exp4Connection.members[group+'-test']:
					Exp4Connection.members[group+'-test'][uid]['online'] = False
					tornado.ioloop.IOLoop.instance().remove_timeout(Exp4Connection.timers[group+'test'] )
					Exp4Connection.timers[group+'test'] = None
			if group+'-submit' in Exp4Connection.clients:
				Exp4Connection.clients.pop(group+'-submit')
				for uid in Exp4Connection.members[group+'-submit']:
					Exp4Connection.members[group+'-submit'][uid]['online'] = False
					tornado.ioloop.IOLoop.instance().remove_timeout(Exp4Connection.timers[group+'submit'] )
					Exp4Connection.timers[group+'submit'] = None
		except:
			None
		self.write('<script>alert("已成功清除所有实验信息");window.location="/main"</script>')
		self.finish()
		return

# 设置游戏记录，以便演示
class  SetProjectRecord(BaseHandler):

	def get(self):
		self.post()
		return

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		userId = self.get_current_user()
		if not self.isTestUser(userId):
			logger.warn("user: %s tried to attack to set experiment records" %userId)
			self.redirect("/main")
			return
		logger.info("user: %s set experiment records" %userId)
		users_cursor = db.users.find({"group":self.online_data[userId]["group"], "yearOfEntry":self.online_data[userId]["yearOfEntry"]}, {"userId":1}).sort("userId", pymongo.ASCENDING)
		usersInGroup = yield users_cursor.to_list(None)
		assert(len(usersInGroup) == 5)


		# 设置路由器实验的记录 （先进行清除）
		yield db.routeTopo.remove({"group":self.online_data[userId]["group"], "year":self.online_data[userId]["yearOfEntry"]})
		routePath =os.path.join(os.path.dirname(__file__),'presentData','routes.json')
		with open(routePath, "r") as f:
      			routeJSON = f.readline()
      			linkJSON = f.readline()
		topo_record = { "status" : 1, "scale" : 30, "group" : self.online_data[userId]["group"], "distributeNodes" : { usersInGroup[0]["userId"] : [ 1, 6, 9, 13, 16, 17 ],\
		 		usersInGroup[1]["userId"] : [ 10, 11, 15, 18, 19, 22 ], usersInGroup[2]["userId"] : [ 3, 12, 21, 25, 28, 29 ], usersInGroup[3]["userId"] : [ 0, 20, 23, 24, 26, 27 ],\
		  		usersInGroup[4]["userId"]: [ 2, 4, 5, 7, 8, 14 ] }, "year" : self.online_data[userId]["yearOfEntry"], "gameTimes" : 1, "mode" : 1 }
		topo_record["route"] = json.loads(routeJSON)
		topo_record["link"] = json.loads(linkJSON)
		ano_topo_record = copy.deepcopy(topo_record)
		ano_topo_record["mode"] = 0
		yield db.routeTopo.save(topo_record)
		yield db.routeTopo.save(ano_topo_record)

		# 老鼠实验

		# 系统实验
		sys_record = yield db.exp4g.find_one({"group":self.online_data[userId]["group"]+"-test"})
		if sys_record:
			sys_record["numPlayers"] = 1
			yield db.exp4g.save(sys_record)
		else:
			sys_record = {"group":self.online_data[userId]["group"]+"-test",
				"days":0,
				"numPlayers":1
				}
			yield db.exp4g.save(sys_record)
		sys_record = yield db.exp4g.find_one({"group":self.online_data[userId]["group"]+"-submit"})
		if sys_record:
			sys_record["numPlayers"] = 1
			yield db.exp4g.save(sys_record)
		else:
			sys_record = {"group":self.online_data[userId]["group"]+"-submit",
				"days":0,
				"numPlayers":1
				}
			yield db.exp4g.save(sys_record)
		self.write('<script>alert("已成功设置所有实验信息");window.location="/main"</script>')
		self.finish()
		return


class APIGetHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):

		if deployed:
			self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		else:
			self.set_header('Access-Control-Allow-Origin','http://project.ucas-2014.tk:8080')
		self.set_header('Access-Control-Allow-Credentials','true')
		try:
			gameId = int(self.get_argument("gameId", 1))
		except:
			return
		userId = self.get_current_user()
		group = self.online_data[userId]["group"]

		if gameId not in [1,2,3,4,5]:
			return
		if not self.isTestUser(userId):
			if gameId in [1,2,3,4]:
				if not HwWebUtil.isValid(self.online_data[userId]["classNo"], 2):
					return
			elif gameId in [5]:
				if not HwWebUtil.isValid(self.online_data[userId]["classNo"], 4):
					return
		# 分组游戏情况
		if gameId in [1,2,3,4,5]:
			record = yield db.games.find_one({"gameId":gameId, "group": group})
			if not record:
				record = {"group":group,
					"gameId":gameId,
					"curLoop":0,
					"scores":{},
					"bestScore":"None",
					"histories":{}}
				yield db.games.save(record)
		else:
			None
		logger.info("Exp2: Group %s user %s gets info of game %d."% (group, userId, gameId))
		self.write(json.dumps({"userId":userId,
			"curLoop":record["curLoop"],
			"name":self.online_data[userId]["name"],
			"group":self.online_data[userId]["group"],
			"bestScore":record["bestScore"]}))
		self.finish()
		return

class APIPutHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		if deployed:
			self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		else:
			self.set_header('Access-Control-Allow-Origin','http://project.ucas-2014.tk:8080')
		self.set_header('Access-Control-Allow-Credentials','true')
		try:
			gameId = int(self.get_argument("gameId", 1))
			gameLoop = int(self.get_argument("gameLoop", 1))
			gameScore = int(self.get_argument("gameScore", 1))
			gameHist = json.loads(self.get_argument("gameHist", 1))
		except:
			return
		#print gameId,gameLoop,gameScore,gameHist
		userId = self.get_current_user()
		group = self.online_data[userId]["group"]
		if gameId not in [1,2,3,4]:
			return
		# 分组游戏情况

		if gameId in [1,2,3,4]:
			record = yield db.games.find_one({"gameId":gameId,
				"group": group})
			if not record:
				record = {"group":group,
					"gameId":gameId,
					"curLoop":0,
					"scores":{},
					"bestScore":"None",
					"histories":{}}
		else:
			None
		if gameId in [1,2,3]:
			if gameLoop!=record["curLoop"] or gameLoop>2:
				return
		if gameId in [4]:
	 		if gameLoop!=record["curLoop"] or gameLoop>4:
				return
		# 游戏分数优于16的，我们要判断其是否作弊
		if gameScore>0:
			if gameScore != len(gameHist['results']) and gameScore<16:
				logger.warn("Exp2: Group %s user %s submits info of game %d with a wrong result."% (group, userId, gameId, gameScore))
				return
		if record["bestScore"] == "None":
			if gameScore>0:
				record["bestScore"] = gameScore
		else:
			if gameScore>0 and gameScore < record["bestScore"] and gameId in [1,2,3]:
				record["bestScore"] = gameScore
			if gameScore>0 and gameId in [4]:
				record["bestScore"]  = (record["bestScore"]*gameLoop + gameScore) / (gameLoop + 1)

		record["scores"][str(gameLoop)] = gameScore
		record["histories"][str(gameLoop)] = gameHist
		record["curLoop"] = gameLoop + 1

		yield db.games.save(record)
		logger.info("Exp2: Group %s user %s submits info of game %d with score of %d."% (group, userId, gameId, gameScore))
		self.write('true')
		self.finish()
		return


class RouteAPIGetInfoHandler(BaseHandler):

	def get(self):
		self.post()

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		self.set_header('Access-Control-Allow-Credentials','true')
		if not self.canDoExperiment(3):
			return
		mode = int(self.get_argument("mode", 1))
		group = self.online_data[self.get_current_user()]["group"]
		logger.info("Exp3: %s of group %s try to getinfo in mode %d" %(self.get_current_user(), group, mode) )
		group_users_cursor = db.users.find({"group":group}, {"name": 1, "_id" :0, "userId" : 1})
		group_users = yield group_users_cursor.to_list(None)
		info = copy.deepcopy(self.online_data[self.get_current_user()])
		if "loginTime" in info:
			del info['loginTime']
		gameTimes = 1
		step = 0 #客户端此时应该在第几步后
		topo_cursor = db.routeTopo.find({"group":group, "year":self.online_data[self.get_current_user()]["yearOfEntry"], "mode":mode}).sort("gameTimes", pymongo.DESCENDING)
		topos = yield topo_cursor.to_list(None)
		if not topos or len(topos) == 0:
			pass
		elif topos[0]["status"] == TopoStatus["NEW"] or topos[0]["status"] == TopoStatus["ING"]:
			step = 1
			gameTimes = topos[0]["gameTimes"]
		else:
			#TopoStatus["DONE"]
			step = 3
		record = {"info":info,
			"group_users" : group_users, "gameTimes":gameTimes, "step":step}
		if gameTimes > 10:
			record["status"] = "ERROR"
		else:
			record["status"] = "NORMAL" #正常
		if step == 3:
			record["finalScore"] = topos[0]["finalScore"]
			record["averageRateScore"] = topos[0]["averageRateScore"]
			record["averageLengthScore"] = topos[0]["averageLengthScore"]
		logger.info("Exp3: %s of group %s 's experiment step is %d in mode %d" %(self.get_current_user(), group, step, mode) )
		self.write(json.dumps(record))
		self.finish()
		return

class RouteAPISubmitRouteHandler(BaseHandler):

	# 提交路由表
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		self.set_header('Access-Control-Allow-Credentials','true')
		if not self.canDoExperiment(3):
			return
		mode = int(self.get_argument("mode", 1))
		group = self.online_data[self.get_current_user()]["group"]
		gameTimes = int(self.get_argument("times", None))
		if not gameTimes:
			self.finishi()
			return
		routeJson = self.get_argument("route", None)
		logger.info("Exp3: %s of group %s try to save route in mode %d: %s" %(self.get_current_user(), group, mode, routeJson) )
		topo = yield db.routeTopo.find_one({"group":group, "gameTimes":gameTimes, "year":self.online_data[self.get_current_user()]["yearOfEntry"], "mode":mode})
		route = None
		returnStatus = "ING"
		if not routeJson or not topo or routeJson == "null":
			returnStatus = "ERROR"
			self.write(json.dumps({"status": returnStatus}))
			self.finish()
			return
		if topo["status"] == TopoStatus["DONE"]:
			returnStatus = "REJECT"
			self.write(json.dumps({"status": returnStatus}))
			return
		try:
			route = json.loads(routeJson);
		except ValueError, e:
			returnStatus = "ERROR"
			self.write(json.dumps({"status": returnStatus}))
			self.finish()
			return

		for node in route:
			topo["route"][node] = route[node]
		# topo["result"]= dict(topo["result"].items() + result.items())
		topo["status"] = TopoStatus["ING"]
		logger.info("Exp3: %s of group %s try to save route in mode %d: %s" %(self.get_current_user(), group, mode, routeJson) )
		yield db.routeTopo.save(topo)
		self.write(json.dumps({"status": returnStatus, "gameTimes":gameTimes, "route":route}))
		self.finish()
		return


# 提交选定的topo图
class RouteAPISubmitTopoHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		self.set_header('Access-Control-Allow-Credentials','true')
		if not self.canDoExperiment(3):
			return

		mode = int(self.get_argument("mode", 1))
		topoStr = self.get_argument("topo", None)
		group = self.online_data[self.get_current_user()]["group"]
		logger.info("Exp3: %s of group %s try to decide network topology in mode %d" %(self.get_current_user(), group, mode) )
		if not topoStr:
			self.write(json.dumps({"status":"ERROR"}))
		else:
			topo = None
			try:
				topo = json.loads(topoStr)
			except ValueError, e:
				self.write(json.dumps({"status": "ERROR"}))
				self.finish()
				return

			# 检测数据库是否已经有topo，如果有，则返回错误信息
			# to do 还要验证gameTimes是否正确？
			if "group" in topo and "gameTimes" in topo:
				topoInDB = yield db.routeTopo.find_one({"group":topo["group"], "gameTimes":int(topo["gameTimes"]), "year":self.online_data[self.get_current_user()]["yearOfEntry"], "mode":mode},{"_id": 0})
				if topoInDB:
					logger.info("Exp3: %s of group %s failed to decide network topology in mode %d: %s" %(self.get_current_user(), group, mode, topoStr) )
					self.write(json.dumps({"status": "someoneSubmited"}))
					self.finish()
					return
			else:
				self.write(json.dumps({"status":"ERROR"}))

			if "scale" in topo and "link" in topo and HwWebUtil.isConnectedGraph(topo["scale"], topo["link"]):
				logger.info("Exp3: %s of group %s succeed to decide network topology in mode %d: %s" %(self.get_current_user(), group, mode, topoStr) )
				yield db.routeTopo.save(topo)
				self.write(json.dumps({"status":"NORMAL"}))
			else:
				self.write(json.dumps({"status":"ERROR"}))
		self.finish()
		return

# 获取topo，选取topo和查看已确定的topo都从这儿开始
class RouteAPIGetTopoHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		self.set_header('Access-Control-Allow-Credentials','true')
		if not self.canDoExperiment(3):
			return

		mode = int(self.get_argument("mode", 1))
		gameTimes = int(self.get_argument("times", None))

		if not gameTimes:
			self.finish()
			return
		scale = int(self.get_argument("scale", 30))
		group = self.online_data[self.get_current_user()]["group"]
		group_users_cursor = db.users.find({"group":group}, {"name": 1, "_id" :0, "userId":1})
		group_users = yield group_users_cursor.to_list(None)
		topo = yield db.routeTopo.find_one({"group":group, "gameTimes":gameTimes, "year":self.online_data[self.get_current_user()]["yearOfEntry"], "mode":mode},{"_id": 0})
		if not topo:
			logger.info("Exp3: %s of group %s try to get a new network topology in mode %d" %(self.get_current_user(), group, mode) )
			topo ={}
			topo["scale"] = scale
			topo["gameTimes"] = gameTimes
			topo["group"] = group
			topo["year"] = self.online_data[self.get_current_user()]["yearOfEntry"]
			#topo["status"] = TopoStatus["NEW"]
			topo["status"] = TopoStatus["CHOOSING"]
			topo["route"] = {}
			topo["mode"] = mode

			# 将结点随机分配给该组成员
			x = (scale - 1) / len(group_users) + 1
			user_hash = {}
			for i in range(0, scale) :
				y = int(random.random()*len(group_users))
				while True:
					a_userId = group_users[y]['userId']
					if a_userId not in user_hash:
						user_hash[a_userId] = []
						user_hash[a_userId].append(i)
						break
					elif len(user_hash[a_userId]) == x:
						y+=1
						y%=len(group_users)
						continue
					else:
						user_hash[a_userId].append(i)
						break
			link = self.initialLink(scale)
			topo["distributeNodes"] = user_hash
			topo["link"] = link
		else:
			logger.info("Exp3: %s of group %s try to get a exsited network topology in mode %d" %(self.get_current_user(), group, mode) )
		self.write(json.dumps(topo))
		self.finish()
		return

	def initialLink(self, scale):
		link = []
		# 3个同心的正多边形
		edgeNum = scale / 3
		outerEdgeNum = scale - edgeNum * 2
		randomThreshold = 0.4
		while True:
			link = []
			for i in range(0, edgeNum) :
				# 最里面/中间的正多边形的各自顶点相连
				if random.random() < randomThreshold:
					link.append("%d-%d" %(i, (i + 1) %edgeNum ))
				middleFirst = edgeNum
				if random.random() < randomThreshold:
					link.append("%d-%d" %(i + middleFirst, (i + 1) %edgeNum + middleFirst))
				# 中间和里面多边形顶点间相连
				middleIndex = i + middleFirst
				if random.random() < randomThreshold:
					link.append("%d-%d" %(middleIndex, middleIndex % edgeNum ))
				if random.random() < randomThreshold:
					link.append("%d-%d" %(middleIndex, (middleIndex + 1) % edgeNum ))
				if random.random() < randomThreshold:
					link.append("%d-%d" %(middleIndex, (middleIndex + 9) % edgeNum ))
			for i in range(0, outerEdgeNum) :
				# 最外边的正多边形的顶点相连
				middleFirst = edgeNum
				outerFirst = 2 * edgeNum
				if random.random() < randomThreshold:
					link.append("%d-%d" %(i + outerFirst, (i + 1)%outerEdgeNum + outerFirst))
				# 外面和中间的多边形顶点间相连
				outerIndex = i + outerFirst
				if random.random() < randomThreshold:
					link.append("%d-%d" %(outerIndex, outerIndex % edgeNum + middleFirst))
				if random.random() < randomThreshold:
					link.append("%d-%d" %(outerIndex, (outerIndex + 1) % edgeNum + middleFirst))
				if random.random() < randomThreshold:
					link.append("%d-%d" %(outerIndex, (outerIndex + 9) % edgeNum + middleFirst))
			# 里边正多边形有一个偏对角相连
			x = random.random()*((edgeNum+1)/2)
			y = x + (edgeNum-1)/2
			link.append("%d-%d" %(x, y))

			if HwWebUtil.isConnectedGraph(scale, link):
				break
		return link


class RouteAPIClearRouteInTestModeHandler(BaseHandler):

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		self.set_header('Access-Control-Allow-Credentials','true')
		if not self.canDoExperiment(3):
			return
		mode = int(self.get_argument("mode", 1))
		userId = self.get_current_user()
		group = self.online_data[userId]["group"]
		# 清除路由器实验的记录
		if mode == 1:
			logger.info("Exp3: %s of group %s succeed to clear their experiment records in mode %d" %(self.get_current_user(), group, mode) )
			yield db.routeTopo.remove({"group":group, "year":self.online_data[userId]["yearOfEntry"], "mode":mode})
			self.write(json.dumps({"status": "NORMAL"}))
			self.finish()
			return
		else:
			logger.warn("Exp3: %s of group %s failed to clear their experiment records in mode %d" %(self.get_current_user(), group, mode) )
			self.write(json.dumps({"status": "ERROR"}))
			self.finish()
			return



# 保存测试结果，实验结束
class RouteAPISubmitRouteEvaluationHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://ucas-2014.tk:8889')
		self.set_header('Access-Control-Allow-Credentials','true')
		if not self.canDoExperiment(3):
			return

		mode = int(self.get_argument("mode", 1))
		gameTimes = int(self.get_argument("times", None))
		score = self.get_argument("score", None)
		group = self.online_data[self.get_current_user()]["group"]

		logger.info("Exp3: %s of group %s try to submit evaluation in mode %d" %(self.get_current_user(), group, mode) )
		if not score:
			logger.warn("Exp3: %s of group %s failed to submit evaluation in mode %d because of socre is invalid" %(self.get_current_user(), group, mode) )
			self.write(json.dumps({"status": "ERROR"}))
			self.finish()
			return
		else:
			try:
				score = json.loads(score)
			except ValueError, e:
				logger.warn("Exp3: %s of group %s failed to submit evaluation in mode %d because of socre is invalid" %(self.get_current_user(), group, mode) )
				self.write(json.dumps({"status": "ERROR"}))
				self.finish()
				return
		# 验证是否有同学提交
		topo = yield db.routeTopo.find_one({"group":self.online_data[self.get_current_user()]["group"], "gameTimes":gameTimes, "year":self.online_data[self.get_current_user()]["yearOfEntry"], "mode":mode})
		if not topo or topo["status"] == TopoStatus["DONE"]:
			logger.info("Exp3: %s of group %s failed to submit evaluation in mode %d because of submited evaluation" %(self.get_current_user(), group, mode) )
			self.write(json.dumps({"status":"DONE", "averageRateScore":topo["averageRateScore"], "averageLengthScore":topo["averageLengthScore"], "finalScore":topo["finalScore"]}))
			self.finish()
			return

		# 最终评分
		# averageLengthScore practiceLengthScore  averageRateScore practiceRateScore 全是平均的实测数据，并没有换算到分数
		topo["practiceLengthScore"] = score["practiceLengthScore"]
		topo["averageLengthScore"] = score["averageLengthScore"]
		topo["finalScore"] = score["finalScore"]
		topo["averageRateScore"] = score["averageRateScore"]
		topo["practiceRateScore"] = score["practiceRateScore"]
		topo["status"] = TopoStatus["DONE"]
		logger.info("Exp3: %s of group %s succeed to submit evaluation in mode %d, finalscore:%d" %(self.get_current_user(), group, mode, topo["finalScore"]) )
		yield db.routeTopo.save(topo)
		self.write(json.dumps({"status": "NORMAL", "averageRateScore":topo["averageRateScore"], "averageLengthScore":topo["averageLengthScore"], "finalScore":topo["finalScore"]}))
		self.finish()
		return


# 全局函数，创建以组为一级索引的用户表
@tornado.gen.coroutine
def createUserlist(userlist, mapper):
	cursor = db.users.find()
	for message in (yield cursor.to_list(None)):
		if message:
			uid = message['userId']
			group = message['group']
			if group+'-test' not in userlist:
				userlist[group+'-test'] = {}
			if group+'-submit' not in userlist:
				userlist[group+'-submit'] = {}
			userlist[group+'-test'][uid] = {}
			userlist[group+'-submit'][uid] = {}
			userlist[group+'-test'][uid]['online'] = False
			userlist[group+'-submit'][uid]['online'] = False
			userlist[group+'-test'][uid]['name'] = message['name']
			userlist[group+'-submit'][uid]['name'] = message['name']
	for group in userlist:
		i = 0
		for uid in userlist[group]:
			if group not in mapper:
				mapper[group] = {}
			mapper[group][uid] = str(i)
			# 由于uid比较大，不会冲突
			mapper[group][str(i)] = uid
			i += 1

class Exp4Connection(SockJSConnection):
	"""Exp4 connection implementation"""
	# 面向系统
	clients = {}
	# 面向用户
	members = {}
	# 记录userid，group -> id 映射 ,用户不可见
	maps = {}
	# 构建用户登陆表
	createUserlist(members,maps)
	# 存储timer
	timers = {}
	# 存储days
	days = {}
	numPlayers = {}
	numTraitor = 1
	# 一天的实际时间
	interval = 1200

	def send_error(self, message, error_type=None):
		"""
		Standard format for all errors
		"""
		return self.send(json.dumps({
			'data_type': 'error' if not error_type else '%s_error' % error_type,
			'data': {
				'message': message
			}
        }))

	def send_message(self, message, data_type):
		"""
		Standard format for all messages
		"""
		return self.send(json.dumps({
			'data_type': data_type,
			'data': message,
		}))

	def broadcast_message(self, src, dest, message, data_type):
		"""
		Standard format for all messages
		"""
		return self.broadcast(self.getDest(dest),json.dumps({
			'data_type': data_type,
			'data': message,
			'from': src
		}))

	def broadcast_userlist(self,event):
		"""
		Standard format for boardcasting messages to everyone
		"""
		return self.broadcast(self.getDest([]),json.dumps({
			'data_type': 'update',
			'data': self.members[self.group],
			'event':event
		}))


	def on_open(self, request):
		"""
		Request the client to authenticate and add them to client pool.
		"""
		self.authenticated = False
		self.channel = None
		self.send_message({}, 'request_login')

	def on_message(self, msg):
		"""
		Handle authentication and notify the client if anything is not ok,
		but don't give too many details
		"""
		
		try:
			message = json.loads(msg)
		except ValueError:
			self.send_error("Invalid JSON")
			return
		if message['data_type'] == 'login' and not self.authenticated:
			try:
				userId = message['data']['userId']
				group = BaseHandler.online_data[userId]["group"]
				submitMode = message['data']['submitMode']
				if submitMode is True:
					group = group + "-submit"
				else:
					group = group + "-test"
			except:
				self.send_error("Invalid user")
				return
			self.group = group
			self.userId = userId
			self.submitMode = submitMode
			self.end = False
			userRecord = sdb.exp4u.find_one({"group":group,"userId":userId})
			groupRecord = sdb.exp4g.find_one({"group":group})
			if not groupRecord:
				groupRecord = {"group":group,
					"days":0,
					"numPlayers":5			
					}
			if not userRecord:
				userRecord = {"group":group,
					"userId":userId,
					'traitor': None,
					'traitorTimes': 0,
					'messages':0,
					'stage':0,
					'cond':{
						"weahter":[ "==", "0" ],
						"troops":[ "<=", 4000 ],
						"supply":[ "<=", 4000 ] 
						},
					'ready':None,
					'resource':{'troops':5000,'supply':5000,'weahter':0},
					'score':80,
					'scores':{},
					'history':{}
				}
			if group not in self.clients:
				self.clients[group] = {}
			if userId not in self.clients[group]:
				self.clients[group][userId] = {}
				isTraitor = False
				if len(self.clients[group]) ==1:
					isTraitor = True
				userRecord['traitor'] = isTraitor
			self.clients[group][userId]['sock'] = self
			self.clients[group][userId]['attack'] = None
			self.clients[group][userId]['messages'] = 0
			self.authenticated = True
			self.members[group][userId]['online'] = True
			self.broadcast_userlist(True)

			self.send_message({'notify': 'success', 'isTraitor':userRecord['traitor'], 
				'id':self.maps[group][userId],'messages':userRecord['messages'],
				'stage':userRecord['stage'],'cond':userRecord['cond'],
				'resource':userRecord['resource'],'ready':userRecord['ready'],'test':self.isTestUser(userId)}, 'auth'
				)
			logger.info("Exp4:Client authenticated for %s" % userId)
			sdb.exp4u.save(userRecord)
			sdb.exp4g.save(groupRecord)
			self.isStart()

		elif message['data_type'] == 'nextstage' and self.authenticated:
			userRecord = sdb.exp4u.find_one({"group":self.group,"userId":self.userId})
			if userRecord['stage'] == 0:
				if self.isTestUser(self.userId):
					userRecord['cond'] = {
						"weahter":[ "==", "0" ],
						"troops":[ "<=", 4000 ],
						"supply":[ "<=", 4000 ] 
						}
					userRecord['stage'] += 1
					sdb.exp4u.save(userRecord)
					self.isStart()
				else:
					if message['data']['cond']=="":
						return
					userRecord['cond'] = message['data']['cond']
					userRecord['stage'] += 1
					sdb.exp4u.save(userRecord)
					self.isStart()

		elif message['data_type'] == 'message' and self.authenticated and self.timers[self.group] != None:
			# example: GM.sock.send(GM.getMsgJson(["2014n1000706041"], 'hello',"message"))
			self.broadcast_message(self.maps[self.group][self.userId], message['to'],message['data'],"message")

		elif message['data_type'] == 'report' and self.authenticated and self.timers[self.group] != None and self.end ==False:
			# Report the current ready status
			# example: GM.sock.send(GM.getMsgJson(1, {ready:true},"report"))
			userRecord = sdb.exp4u.find_one({"group":self.group,"userId":self.userId})
			userRecord['ready'] = message['data']['ready']
			userRecord['resource']['troops'] = message['data']['troops']
			userRecord['resource']['weahter'] = message['data']['weahter']
			userRecord['resource']['supply'] = message['data']['supply']
			sdb.exp4u.save(userRecord)

		elif message['data_type'] == 'attack' and self.authenticated  and self.timers[self.group] != None and self.end ==False:
			if self.clients[self.group][self.userId]['attack'] == None:
				self.clients[self.group][self.userId]['attack'] = message['data']['decide']
				self.clients[self.group][self.userId]['messages'] = message['data']['messages']
				self.broadcast_message(-1,[], message['data'],"attack")
				groupRecord = sdb.exp4g.find_one({"group":self.group})
				day = str(groupRecord["days"])
				iswin = self.isWin()
				if iswin == True:
					# Game Win
					self.broadcast_message("",[],{'event':'gameresult','win':True},'notify')
					for id in self.clients[self.group]:
						userRecord = sdb.exp4u.find_one({"group":self.group,"userId":id})
						if userRecord["traitor"] == False:
							userRecord["score"] = userRecord["score"] + 10
							userRecord["scores"][day] = 10
						else:
							userRecord["score"] = userRecord["score"] - 40
							userRecord["scores"][day] = -40
						if "history" not in userRecord:
							userRecord["history"] = {}
						if day not in userRecord["history"]:
							userRecord["history"][day] = {}
						userRecord["history"][day]['traitor'] = userRecord["traitor"]
						userRecord["history"][day]['ready'] = userRecord['ready']
						userRecord["history"][day]['attack'] = self.clients[self.group][id]['attack']
						sdb.exp4u.save(userRecord)


					self.resetTimer()
					self.newDay()

				elif iswin == False:
					# Game Lose
					self.broadcast_message("",[],{'event':'gameresult','win':False},'notify')
					for id in self.clients[self.group]:
						userRecord = sdb.exp4u.find_one({"group":self.group,"userId":id})
						if userRecord["traitor"] == False:
							userRecord["score"] = userRecord["score"] - 10
							userRecord["scores"][day] = -10
						else:
							userRecord["score"] = userRecord["score"] + 40
							userRecord["scores"][day] = 10
						if "history" not in userRecord:
							userRecord["history"] = {}
						if day not in userRecord["history"]:
							userRecord["history"][day] = {}
						userRecord["history"][day]['traitor'] = userRecord["traitor"]
						userRecord["history"][day]['ready'] = userRecord['ready']
						userRecord["history"][day]['attack'] = self.clients[self.group][id]['attack']
						sdb.exp4u.save(userRecord)

					self.resetTimer()
					self.newDay()

				else:
					# Game continue
					None

		elif message['data_type'] == 'register' and self.authenticated  and self.timers[self.group] != None and self.end ==False:
			#self.clients[self.group][self.userId]['name'] = message['data']['generalname']
			None
		else:
			self.send(msg)
			#self.send_error("Invalid data type %s" % message['data_type'])
			logger.info("Exp4:Invalid data type %s" % message['data_type'])

	def on_close(self):
		"""
		Remove client from pool. Unlike Socket.IO connections are not
		re-used on e.g. browser refresh.
		"""
		try:
			if self.group in self.members:
				self.members[self.group][self.userId]['online'] = False
			self.broadcast_userlist(False)
			if self.group in self.timers and self.timers[self.group] != None:
				tornado.ioloop.IOLoop.instance().remove_timeout(self.timers[self.group] )
				self.timers[self.group] = None
			if self.group in self.clients:
				self.clients[self.group][self.userId]['sock'] = None
			return super(Exp4Connection, self).on_close()
		except:
			return

	def getDest(self, to):
		dest = set()
		if len(to)>0:
			for id in to:
				try:
					dest.add(self.clients[self.group][self.maps[self.group][id]]['sock'])
				except:
					None
		else:
			for userid in self.clients[self.group]:
				sock = self.clients[self.group][userid]['sock']
				if sock:
					dest.add(self.clients[self.group][userid]['sock'])
		return dest

	def isStart(self):
		#print "numPlayers ", self.numPlayers[self.group]
		groupRecord = sdb.exp4g.find_one({"group":self.group})
		if len(self.clients[self.group]) == groupRecord["numPlayers"]:
			allStage2 = True
			for id in self.clients[self.group]:
				userRecord = sdb.exp4u.find_one({"group":self.group,"userId":id})
				if userRecord['stage'] !=1:
					allStage2 = False
			if allStage2 == True:
				if self.isEnd():
					return
				self.broadcast_message("",[],{'event':'start','interval':self.interval,'day':groupRecord["days"]},'notify')
				self.resetTimer()
				logger.info("Exp4: %s 's players are in position. Now game start." % self.group)


	def isWin(self):
		groupRecord = sdb.exp4g.find_one({"group":self.group})
		attack = set()
		not_attack =set()
		loyals =  groupRecord["numPlayers"] - self.numTraitor
		loyal = set()
		for id in self.clients[self.group]:
			#print 'a,', self.clients[self.group][id]['traitor'],  self.clients[self.group][id]['attack'] , id
			userRecord = sdb.exp4u.find_one({"group":self.group,"userId":id})
			if userRecord['traitor'] == False:
				loyal.add(id)
				if self.clients[self.group][id]['attack'] == True:
					attack.add(id)
				elif self.clients[self.group][id]['attack'] == False:
					not_attack.add(id)
		# 一致性：只关注忠诚的将军的决策结果, 忠诚将军达成一致决策。
		#print 'b,', len(attack), len(not_attack), loyals
		if len(attack) + len(not_attack) != loyals:
			# 终止性条件：所有忠臣将军做出决策，此情况为未决策完。
			return None
		elif len(attack) == loyals:
			decideAttack = True
		elif len(not_attack) == loyals:
			decideAttack = False
		else:
			return False

		R = 0
		for id in loyal:
			userRecord = sdb.exp4u.find_one({"group":self.group,"userId":id})
			if userRecord['ready']:
				R += 1
		# 有效性：当Ｒ大于N时做出决定攻击，R<N情况拒绝攻击, R=N 随便
		N = loyals - R
		if (R>N and decideAttack == True) or  (R<N and decideAttack == False) or R==N:
			return True
		else:
			return False

	
	def resetTimer(self):
		try:
			tornado.ioloop.IOLoop.instance().remove_timeout(self.timers[self.group])
		except:
			None
		self.timers[self.group] = tornado.ioloop.IOLoop.instance().add_timeout(
			timedelta(seconds=self.interval),
			self.sync
			)

	def chooseTraiter(self):
		groupRecord = sdb.exp4g.find_one({"group":self.group})
		TimesList = {} 
		for userId in self.clients[self.group]:
			userRecord = sdb.exp4u.find_one({"group":self.group,"userId":userId})
			TimesList[userId] = userRecord["traitorTimes"]
		minTimes =  min(TimesList.values())
		minTimesUserlist = []
		for userId in TimesList:
			if TimesList[userId] == minTimes:
				minTimesUserlist.append(userId)
		#print minTimesUserlist,TimesList
		traitor = random.randint(0,len(minTimesUserlist)-1)
		return minTimesUserlist[traitor]

	def newDay(self):
		groupRecord = sdb.exp4g.find_one({"group":self.group})
		#traitor= random.randint(0,groupRecord["numPlayers"]-1)
		traitor = self.chooseTraiter()
		groupRecord["days"] += 1
		sdb.exp4g.save(groupRecord)
		if self.isEnd():
			return
		for userId in self.clients[self.group]:
			userRecord = sdb.exp4u.find_one({"group":self.group,"userId":userId})
			if self.clients[self.group][userId] and self.clients[self.group][userId]['sock']!=None:
				self.clients[self.group][userId]['attack'] = None
				self.clients[self.group][userId]['messages'] = 0
				if userId!= traitor:
					userRecord['traitor'] = False
				else:
					userRecord['traitor'] = True
					userRecord['traitorTimes'] += 1
				self.clients[self.group][userId]['sock'].send_message({
					'event':'sync', 'day':groupRecord["days"],'isTraitor':userRecord['traitor']}, "notify")
				sdb.exp4u.save(userRecord)

	def sync(self):
		self.timers[self.group] = tornado.ioloop.IOLoop.instance().add_timeout(
			timedelta(seconds=self.interval),
			self.sync
			)
		for id in self.clients[self.group]:
			userRecord = sdb.exp4u.find_one({"group":self.group,"userId":id})
			userRecord["score"] = userRecord["score"] - 20
			sdb.exp4u.save(userRecord)
		self.newDay()
		#self.broadcast_message("",[],{'event':'sync', 'day':self.days[self.group]},'notify')
	def isEnd(self):
		groupRecord = sdb.exp4g.find_one({"group":self.group})
		if groupRecord["days"]>4 and self.submitMode == True:
			self.end = True
			self.broadcast_message("",[],{'event':'end','scores':None},'notify')
			return True
		else:
			self.end = False
			return False
	def isTestUser(self, userId):
		regexEx = r'^ucas'
		if re.match(regexEx, userId.lower()):
			return True
		else:
			return False

class LoginHandler(BaseHandler):
	def get(self):
		# test
		#self.test_user()
		#self.redirect("/main")
		#self.test_admin()
		#self.redirect("/admin")
		#return
		# delete when releasing
		userId = self.get_secure_cookie("userId")
		if userId:
			if self.online_data and userId in self.online_data.keys():
				self.redirect("/main")
				return
			else:
				self.clear_cookie("userId", domain=domain)
		adminId = self.get_secure_cookie("adminId")
		if adminId:
			if self.online_data and adminId in self.online_data.keys():
				self.redirect("/admin")
				return
			else:
				self.clear_cookie("adminId", domain=domain)
		self.render("./template/login.html", error="")
		return

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		db_ptr = db
		# admin暂不支持test模式
		testMode = False
		userId = self.get_argument("userId")
		password = self.get_argument("password")
		regexStr = "^%s$" %userId
		# if self.isTestUser(userId):
		# 	db_ptr = testdb
		# 	testMode = True
		a_user = yield db_ptr.users.find_one({"userId":{"$regex":regexStr, "$options":"i"}, "password":hashlib.md5(password + md5Salt).hexdigest()})
		a_admin = yield db_ptr.admin.find_one({"userId":{"$regex":regexStr, "$options":"i"}, "password":hashlib.md5(password + md5Salt).hexdigest()})
		if a_user:
			self.clear_current_admin()
			self.set_secure_cookie("userId", a_user['userId'],domain=domain, expires_days=expires_days)
			self.online_data[a_user['userId']] = {'name': a_user['name'],'userId':a_user['userId'], "loginTime":datetime.now(), 'classNo':a_user['classNo'], 'group':a_user['group'],'yearOfEntry':a_user['yearOfEntry']}
			# testMode 下只能做支持实验测试，其他测试无法支持
			if testMode:
				logger.debug("test user: %s is logging in" %userId)
				self.redirect("http://project.ucas-2014.tk")
				#self.render("./template/test_entrance.template")
				return
			else:
				logger.info("student: %s is logging in" %userId)
				self.redirect("/main")
				return
		elif a_admin:
			self.clear_current_user()
			logger.info("administrator: %s is logging in" %userId)
			self.set_secure_cookie("adminId", a_admin['userId'],domain=domain, expires_days=expires_days)
			self.online_data[a_admin['userId']] = {'name': a_admin['name'],'adminId':a_admin['userId'], "loginTime":datetime.now()}
			self.redirect("/admin")
			return
		else:
			logger.warn("user: %s failed to log in" %userId)
			self.render("./template/login.html", error="用户名或密码错误")
		return

class PasswordHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		regEx = r'^([0-9a-zA-Z]){6,15}$'
		userId = self.get_current_user()
		adminId = self.get_current_admin()
		origin_pass = self.get_argument("origin_pass", None)
		new_pass = self.get_argument("new_pass", None)
		new_pass_again = self.get_argument("new_pass_again", None)
		a_user = yield db.users.find_one({"userId":userId, "password":hashlib.md5(origin_pass + md5Salt).hexdigest()})
		a_admin = yield db.admin.find_one({"userId":adminId, "password":hashlib.md5(origin_pass + md5Salt).hexdigest()})
		if userId and a_user and new_pass==new_pass_again and re.match(regEx, new_pass):
				logger.info("student: %s is modifying password to %s" %(userId, new_pass))
				a_user["password"] = hashlib.md5(new_pass + md5Salt).hexdigest()
				yield db.users.save(a_user)
				self.clear_current_user()
				self.clear_current_admin()
				self.write('<script>alert("修改成功，请重新登录系统");window.location="/login"</script>')
				self.finish()
				return
		elif adminId and a_admin and new_pass==new_pass_again and re.match(regEx, new_pass):
			logger.info("administrator: %s is modifying password to %s" %(adminId, new_pass))
			a_admin["password"] = hashlib.md5(new_pass + md5Salt).hexdigest()
			yield db.admin.save(a_admin)
			self.clear_current_user()
			self.clear_current_admin()
			self.write('<script>alert("修改成功，请重新登录系统");window.location="/login"</script>')
			self.finish()
			return
		else:
			logger.info("student: %s failed to modify password to %s" %(userId, new_pass))
			self.write('<script>alert("原密码有误或新密码不符合输入规则，修改失败");window.history.back()</script>')
			self.finish()
			return



class UnfoundHandler(BaseHandler):
	@tornado.web.authenticated
    	def get(self):
    		logger.warn("user: %s is try to visit %s"  %(self.get_current_user(), self.request.uri))
	 	self.render("./template/404.template")
	 	return

	@tornado.web.authenticated
	def post(self):
		logger.warn("user: %s is try to visit %s" %(self.get_current_user(), self.request.uri))
	 	self.render("./template/404.template")
	 	return

class NoticeManagerHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		if not self.get_current_admin():
			self.redirect("/login")
			return

    		nt_cursor = db.notices.find().sort("time", pymongo.DESCENDING)
    		notices = yield nt_cursor.to_list(None)
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1, "content":1}).sort("quiz_id", pymongo.ASCENDING)
    		quizs_index = yield quiz_cursor.to_list(None)
	 	self.render("./template/admin/notice-manager.html", info = self.online_data[self.get_current_admin()],notices = notices, quizs_index=quizs_index)
	 	return


class DeleteNotice(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self, notice_id):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		notice_id = int(notice_id)
		logger.info("administrator: %s is deleting a notice(id is %d)" %(self.get_current_admin(), notice_id))
		yield db.notices.remove({"id":notice_id})
		self.redirect("/admin/notice/list")
		return

class PublishNotice(BaseHandler):

	@tornado.web.asynchronous
	def get(self):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		self.render("./template/admin/publish-notice.html")
		return

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		description = self.get_argument("description", None)
		creator = self.get_argument("creator", None)
		content = self.get_argument("content", None)
		color = self.get_argument("color", None)
		if description and creator and content and color:
			nt_cursor = db.notices.find({},{"id":1}).sort("time", pymongo.DESCENDING)
    			notices = yield nt_cursor.to_list(None)
    			no_id = 1
    			if notices:
    				no_id = notices[0]["id"]+1
			logger.info("administrator: %s is publishing a notice, description is %s" %(self.get_current_admin(), description))
			db.notices.save({"id":no_id, "description":description, "creator":creator, "content":content, "importance":color, "time":datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
			self.write('<script>alert("发布成功");window.location="/admin/notice/list"</script>')
			self.finish()
			return
		else:
			self.write('<script>alert("所有字段都不能为空，发布失败");window.history.back()</script>')
			self.finish()
			return


class ResetPassword(BaseHandler):

	@tornado.web.asynchronous
	def get(self):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		self.write("<a href='/admin'>主页</a><br/><form action='/admin/resetPassword' method='post'><label>学号</label><input type='text' name='userId'/></br><label>密码</label> <input type='text' name='password'/> <input type='submit' value='重置密码'/> </form>")
		self.finish()
		return

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		userId = self.get_argument("userId", None)
		new_pass = self.get_argument("password", None)
		if userId and new_pass:
			userId = userId.strip()
			new_pass = new_pass.strip()
			a_user = yield db.users.find_one({"userId":userId.lower()})
			if a_user:
				logger.info("administrator: %s is reseting %s's password to %s" %(self.get_current_admin(), userId.lower(), new_pass))
				a_user["password"] = hashlib.md5(new_pass + md5Salt).hexdigest()
				yield db.users.save(a_user)
				self.write('<script>alert("修改成功");window.location="/admin"</script>')
				self.finish()
				return
			else:
				self.write('<script>alert("此学生不存在，重置失败");window.history.back()</script>')
				self.finish()
				return

		self.write('<script>alert("参数错误，重置失败");window.history.back()</script>')
		self.finish()
		return


class ExitHandler(BaseHandler):

	def get(self):
		userId = self.get_current_user()
		logger.info("user: %s is exiting" %userId)
		self.clear_current_user()
		self.clear_current_admin()
		self.redirect("./login")
		return


# 每隔30秒进行在线用户过滤， 过期时间设置为10分钟。由于学生在大实验上需要较长时间，暂不提供这个功能
def filterOnlineData():
	od = BaseHandler.online_data
	now = datetime.now()
	for key in od.keys():
		if  (now - od[key]["loginTime"]) > timedelta(minutes=20):
			del od[key]
	tornado.ioloop.IOLoop.instance().add_timeout(
            		timedelta(seconds=30),
            		lambda: filterOnlineData()
       	)

# 自动批改作业, quiz_id为int
@tornado.gen.coroutine
def reviewQuiz(quiz_id):
	a_quiz = yield db.quizs.find_one({"quiz_id":quiz_id})
	logger.info("system: reviewing homework-%d " %quiz_id)
	op_now = datetime.now()
	if a_quiz['status'] == QuizStatus['UNPUBLISH']:
		logger.error("system: review homework-%d has encountered a problem: the homework is unpublished" % quiz_id)
		return
	elif a_quiz['status'] == QuizStatus['REVIEW']:
		logger.error("system: review homework-%d has encountered a problem: the homework has been reviewed" % quiz_id)
		return
	else:
		if 'content' in a_quiz:
			essayQueses = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])
		else:
			return
		users_cursor = db.users.find()
		users = yield users_cursor.to_list(None)
		for user in users:
			user_solution = yield db.solutions.find_one({"quiz_id":quiz_id, "userId":user["userId"]})
			# 完全没有记录的学生，生成一条0分的空记录
			# 暂存的学生和提交的同学，一视同仁，不进行区分
			# review the total score of all the objective questions
			if not user_solution:
				user_solution = {}
				user_solution["userId"] =  user['userId']
				user_solution["quiz_id"] = quiz_id
				user_solution["lastTime"] = op_now.strftime("%Y-%m-%d %H:%M:%S")
				user_solution["solutions"] = []
				user_solution["all_score"] = 0
				user_solution["status"] = QuizStatus["BLANK"]
				yield db.solutions.save(user_solution)
			else:
				all_score = user_solution["all_score"]

				# 兼容以前的数据逻辑
				if user_solution['status'] == QuizStatus["SAVE"]:
					user_solution['status'] = QuizStatus['SUBMIT']
				if all_score < 0:
					all_score = 0

				cnt = 0
				for a_content in a_quiz["content"]:
					score = 0
					if a_content["type"] != QuizType["ESSAYQUES"] and set(a_content["answer"])  == set(user_solution["solutions"][cnt]["solution"]) :
						score = a_content["score"]
						all_score += score
					user_solution["solutions"][cnt]["score"] = score
					cnt += 1
				user_solution["all_score"] = all_score
				# change the status of user_solutions to "REVIEW"
				# 如果全部为选择题，不仅进行自动打分操作，而且设置solu为REVIEW
				if not essayQueses:
					user_solution['status'] = QuizStatus["REVIEW"]
				yield db.solutions.save(user_solution)
		# change the status of the quiz to "REVIEW"
		if not essayQueses:
			a_quiz['status'] = QuizStatus["REVIEW"]
			yield db.quizs.save(a_quiz)
		logger.info("system: review homework-%d perfectly(deadline: %s)" % (quiz_id, a_quiz['deadline']) )

# 遍历quizs，将定时任务加入到系统，每次系统初始化都要做此工作
@tornado.gen.coroutine
def involeQuartzTasks():
	print "system: scan the quizs and add the timing-reviewing tasks"
	logger.info("system: scan the quizs and add the timing-reviewing tasks")
	quizs_cursor = db.quizs.find({"status":QuizStatus["PUBLISH"]},{"content":0, "description":0,"title":0})
	quizs = yield quizs_cursor.to_list(None)
	for a_quiz in quizs:
		# 满足以下条件，才进行客观提评分。否则说明客观提已评分，只是主管题未评分
		# 如果由于各种原因系统在截至日时没有给予客观提评分，那么只能将此次Quiz的截至日调后进行批改
		if datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
			print "system: add the quartz task: homework-%d will get reviewd at %s" %(a_quiz['quiz_id'], a_quiz['deadline'])
			logger.info("system: add the quartz task: homework-%d will get reviewd at %s" %(a_quiz['quiz_id'], a_quiz['deadline']))
			tornado.ioloop.IOLoop.instance().add_timeout(
		            		datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S") - datetime.now(),
		            		reviewQuiz,
		            		a_quiz['quiz_id']
		       	)

settings = {
	#"debug": True,
	"default_handler_class": UnfoundHandler,
	"static_path": os.path.join(os.path.dirname(__file__), "static"),
	"cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
 	"login_url": "/login",
}
SockRouter = SockJSRouter(Exp4Connection, '/api/exp4')
application = tornado.web.Application([
    (r"/", tornado.web.RedirectHandler, {"url":"/main", "permanent":False}),
    (r"/login", LoginHandler),
    (r"/main", MainHandler),
    (r"/exit", ExitHandler),
    (r"/password", PasswordHandler),
    # (r"/quiz/([0-9]+)/submit", QuizSubmitHandler),
    (r"/quiz/([0-9]+)/save", QuizSaveHandler),
    (r"/quiz/([0-9]+)", QuizHandler),
    (r"/studentlist", StudentListHandler),
    (r"/studentlist/transcipt/([0-9]+)", TransciptHandler),
    (r"/admin", AdminHandler),
    (r"/admin/resetPassword", ResetPassword),
    (r"/admin/notice/publish", PublishNotice),
    (r"/admin/notice/delete/([0-9]+)", DeleteNotice),
    (r"/admin/notice/list", NoticeManagerHandler),
    (r"/review/([0-9]+)", ReviewHandler),
    (r"/project", ProjectMainHandler),
    (r"/project/([0-9]+)/upload/([0-9]+)", ProjectUploadHandler),
    (r"/project/([0-9]+)/download/([0-9]+)", ProjectDownloadHandler),
    (r"/project/([0-9]+)", ProjectHandler),
    (r"/project/zipdownload/([0-9]+)", ReportZipDownload),
    (r"/api/clearProjectRecord",ClearProjectRecord),
    (r"/api/setProjectRecord",SetProjectRecord),
    (r"/api/getinfo",APIGetHandler),
    (r"/api/putinfo",APIPutHandler),
    (r"/api/route/getinfo",RouteAPIGetInfoHandler),
    (r"/api/route/getTopo",RouteAPIGetTopoHandler),
    (r"/api/route/submitTopo",RouteAPISubmitTopoHandler),
    (r"/api/route/submitRoute",RouteAPISubmitRouteHandler),
    (r"/api/route/submitRouteEvaluation",RouteAPISubmitRouteEvaluationHandler),
    (r"/api/route/clearRouteRecordInTestMode",RouteAPIClearRouteInTestModeHandler)
    ] + SockRouter.urls, **settings )

# 每次加入新的作业或者修改作业的截止日期都必须要重启一次系统，因为需要把自动该作业的任务加入到定时任务中去
if __name__ == "__main__":
	if len(sys.argv) == 2:
		if sys.argv[1] == 'test':
			deployed = False
	if deployed:
		application.listen(80)
	else:
		application.listen(8888)
	print "The http server has been started!"
	logger.info("The http server has been started!")
	#tornado.ioloop.IOLoop.instance().add_timeout(
            	#	timedelta(seconds=5),
            	#	lambda: filterOnlineData()
       	#)
	involeQuartzTasks()
	tornado.ioloop.IOLoop.instance().start()
