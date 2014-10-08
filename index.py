#!/usr/bin/python
# coding=utf-8
import os
import re
import tornado.ioloop
import tornado.web
import motor
import json

import hashlib

import pymongo

from datetime import datetime
from datetime import timedelta

from HwWebUtil import HwWebUtil
from HwWebUtil import QuizStatus
from HwWebUtil import QuesStatus
from HwWebUtil import QuizFlag
from HwWebUtil import QuizType
from HwWebUtil import ProjectStatus
from HwWebUtil import ProjectFlag

# to do, filter the text input
# to do, 多选题
# to do, admin打包下载报告
# to do, admin上传题目

#db = motor.MotorClient('localhost', 27017).test
db = motor.MotorClient('localhost', 27017).hwweb
domain = ".ucas-2014.tk"
expires_days = 7
md5Salt='a~n!d@r#e$w%l^e&e'

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
		self.clear_cookie("adminId")

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

	# 如果存在全是客观题，状态为publish，且已过deadline的quiz，置其状态为review
	# 所有有Quiz状态信息的都要首先调用这个函数
	# 针对Quiz状态
	@tornado.gen.coroutine
	def checkQuizAndUpdateStatus(self):
		quiz_cursor = db.quizs.find()
		quizs = yield quiz_cursor.to_list(None)
    		for a_quiz in quizs:
    			if a_quiz["status"] == QuizStatus["PUBLISH"] and not datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
    				tmp = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])
    				if not tmp:
    					a_quiz['status'] = QuizStatus["REVIEW"]
    					yield db.quizs.update({"quiz_id":a_quiz['quiz_id']}, {"$set":{"status":QuizStatus['REVIEW']}})

    	# 将每道客观题的分数和客观提总分保存到数据库
    	# 针对solution的选择题分数和客观题总分
    	@tornado.gen.coroutine
    	def reviewSelectionQues(self, user_quiz, a_quiz, essayQueses):
    		if user_quiz["all_score"] == -1 :
					all_score = 0
					cnt = 0
					for a_content in a_quiz["content"]:
						score = 0
						if a_content["type"] != QuizType["ESSAYQUES"] and set(a_content["answer"])  == set(user_quiz["solutions"][cnt]["solution"]) :
							score = a_content["score"]
							all_score += a_content["score"]
						user_quiz["solutions"][cnt]["score"] = score
						cnt += 1
					user_quiz["all_score"] = all_score
					# 如果全部为选择题，不仅进行自动打分操作，而且设置solu为REVIEW，flag为QuizFlag["FULL_SCORED"]
					if not essayQueses:
						user_quiz['status'] = QuizStatus["REVIEW"]
					yield db.solutions.save(user_quiz)

	#for test, release version needs to delete it
	def test_user(self):
		self.set_secure_cookie("userId", "201428013229018", domain=domain, expires_days=expires_days)
		#self.set_secure_cookie("userId", "201428013229018")
		self.online_data["201428013229018"] = {'name': "李春典", 'grade':"大一",'userId':"201428013229018"}

	#for test, release version needs to delete it
	def test_admin(self):
		self.set_secure_cookie("adminId", "lichundian", expires_days=expires_days)
		self.online_data["lichundian"] = {'name': "李春典",'adminId':"lichundian"}

class MainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		self.checkQuizAndUpdateStatus()

    		nt_cursor = db.notices.find().sort("id", pymongo.DESCENDING)
    		notices = yield nt_cursor.to_list(None)
    		quiz_cursor = db.quizs.find().sort("quiz_id", pymongo.ASCENDING)
    		quizs = yield quiz_cursor.to_list(None)
	 	self.render("./template/main.template" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs)

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
		count = 0
		solutions= []
		status = 0
		for a_content in quiz_contents["content"]:
			ques_status = QuesStatus["UNDONE"]
			answer = []
			count +=1
			tmp = self.get_argument("quiz_"+quiz_id+"_"+str(count), None)
			# 检测选择题输入，要求必须在选项之内
			if  tmp:
				if a_content['type'] == QuizType['SINCHOICE']:
					if not tmp in map(lambda x:x['value'],a_content['choices']):
						self.write('<script>alert("答案不符合规定, 请重新提交");window.history.back()</script>')
						self.finish()
						return
				ques_status = QuesStatus["DONE"]
				answer.append(tmp)
			solutions.append({"type":a_content["type"], "solution":answer, "score":0, "status":ques_status, "id":a_content["id"]})
		doc["lastTime"] = op_now.strftime("%Y-%m-%d %H:%M:%S")
		doc["solutions"] = solutions
		doc["all_score"] = -1
		doc["status"] = QuizStatus["SAVE"]
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
		count = 0
		solutions= []
		status = 0
		for a_content in quiz_contents["content"]:
			ques_status = QuesStatus["UNDONE"]
			solution = []
			score = 0
			count +=1
			tmp = self.get_argument("quiz_"+quiz_id+"_"+str(count), None)
			# 检测选择题输入，要求必须在选项之内
			if  tmp:
				if a_content['type'] == QuizType['SINCHOICE']:
					if not tmp in map(lambda x:x['value'],a_content['choices']):
						self.write('<script>alert("答案不符合规定, 请重新提交");window.history.back()</script>')
						self.finish()
						return
			# to do
			# if submit , i will test whether the student had done all the questions
				ques_status = QuesStatus["DONE"]
				solution.append(tmp)
			solutions.append({"type":a_content["type"], "solution":solution, "score":score, "status":ques_status, "id":a_content["id"]})
		doc["lastTime"] = op_now.strftime("%Y-%m-%d %H:%M:%S")
		doc["solutions"] = solutions
		doc["all_score"] = -1
		doc["status"] = QuizStatus["SUBMIT"]
		yield db.solutions.save(doc)
		self.redirect("/quiz/"+quiz_id)
		return

class QuizHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self, quiz_id):
		self.checkQuizAndUpdateStatus()

		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
		if not a_quiz  or a_quiz["status"] == QuizStatus["UNPUBLISH"]:
			self.redirect("/main")
			return
		else:
			essayQueses = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])

			# quizs for indexing
			quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1}).sort("quiz_id", pymongo.ASCENDING)
	    		quizs = yield quiz_cursor.to_list(length=20) #???
			user_quiz = yield db.solutions.find_one({"quiz_id":int (quiz_id), "userId":self.current_user})
			flag = 0 #it mark the quiz_flag out of the QuizFlag map
			if not user_quiz and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
				flag = QuizFlag["UNDONE"]
			elif (not user_quiz or user_quiz["status"] == QuizStatus["SAVE"]) and not datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):#a_quiz["status"] >= QuizStatus["END"]:
				flag = QuizFlag["END"]
			elif user_quiz["status"] == QuizStatus["SAVE"]:
				flag = QuizFlag["SAVE"]
			elif user_quiz["status"] == QuizStatus["SUBMIT"] and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
				flag = QuizFlag["SUB_NOTSCORED"]
			# note: solution在SUBMIT后，若quiz已经截止，则可以查看到客观题分数
			elif user_quiz["status"] == QuizStatus["SUBMIT"]:
				#initial value of all_score is -1, all_score == -1 means it hasn't ever been calculated
				self.reviewSelectionQues(user_quiz=user_quiz, a_quiz=a_quiz, essayQueses=essayQueses)
				if not essayQueses:
					flag = QuizFlag["FULL_SCORED"]
				else:
					flag = QuizFlag["SEMI_SCORED"]
			# user_quiz["status"] == QuizStatus["REVIEW"]
			else:
				flag = QuizFlag["FULL_SCORED"]

			self.render("./template/quiz.template", a_quiz = a_quiz, info = self.online_data[self.get_current_user()],  quizs=quizs, user_quiz=user_quiz, flag=flag)
		return

class ProjectMainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		pro_cursor = db.projects.find().sort("pro_id", pymongo.ASCENDING)
    		projects = yield pro_cursor.to_list(None)
	 	self.render("./template/project.template", projects = projects, info = self.online_data[self.get_current_user()], main=1, flag=0)

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
    		pro_cursor = db.projects.find().sort("pro_id", pymongo.ASCENDING)
    		projects = yield pro_cursor.to_list(None)
    		a_pro = yield db.projects.find_one({"pro_id":pro_id, "status":ProjectStatus["PUBLISH"]})
    		if not a_pro:
    			self.redirect("/project")
    			return
    		userId = self.get_current_user()
    		up_record = yield db.user_uploads.find_one({"pro_id": pro_id, "userId": userId})
    		flag = 0
    		if not up_record and not  datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S')  :
    			flag = ProjectFlag["END"]
    		elif not up_record:
    			flag = ProjectFlag["UNDONE"]
    		elif datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S') :
    			flag = ProjectFlag["SUBMIT"]
    		else :
    			flag = ProjectFlag["DEAD"]
	 	self.render("./template/project.template", projects = projects,a_pro=a_pro, info = self.online_data[self.get_current_user()], flag=flag, main=0, up_record=up_record)
	 	return

class ProjectUploadHandler(BaseHandler):

	support_type=["application/pdf"]

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self, pro_id):
		try:
    			pro_id = int(pro_id)
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return

    		a_pro = yield db.projects.find_one({"pro_id":pro_id,"status":ProjectStatus["PUBLISH"]})

    		# 不存在此project或project已经截止
    		if not a_pro or not datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S')  :
    			self.redirect("/project")
    			return

    		userId = self.get_current_user()
    		up_record = yield db.user_uploads.find_one({"pro_id":pro_id, "userId": userId})

		upload_path=os.path.join(os.path.dirname(__file__),'report_files',str(pro_id))
		# 创建目录
		if not os.path.exists(upload_path):
			os.makedirs(upload_path)


		if self.request.files.get('uploadfile', None):
			uploadFile = self.request.files['uploadfile'][0]
			file_size = len(uploadFile['body'])

			# 检测MIME类型
			if not uploadFile["content_type"] in self.support_type or not re.match(r'^.*\.pdf$',uploadFile['filename'] ):
				self.write('<script>alert("仅支持pdf格式,doc/ppt需要转化为pdf格式才能上传");window.location="/project/'+ str(pro_id)+'"</script>')
				self.finish()
				return
			# 检测文件大小
			if  file_size > 10 * 1024 * 1024:
				self.write('<script>alert("请上传10M以下");window.location="/project/'+ str(pro_id)+'"</script>')
				self.finish()
				return
			else :
				filename = userId + ".pdf"
				filepath=os.path.join(upload_path,filename)
				if up_record and os.path.exists(filepath):
					os.remove(filepath)
				else:
					up_record = {}
					up_record["userId"]=userId
					up_record["pro_id"]=pro_id
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
    	def get(self, pro_id):
    		try:
    			pro_id = int(pro_id)
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return
    		userId = self.get_current_user()
    		up_record = yield db.user_uploads.find_one({"pro_id":pro_id, "userId": userId})
    		if not up_record:
    			self.render("./template/404.template")
    			return
    		else:
    			upload_path=os.path.join(os.path.dirname(__file__),'report_files',str(pro_id))
    			filename = userId + "." + up_record["file_suffix"]
    			filepath=os.path.join(upload_path,filename)
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

		self.checkQuizAndUpdateStatus()
    		nt_cursor = db.notices.find().sort("id", pymongo.DESCENDING)
    		notices = yield nt_cursor.to_list(None)
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1, "content":1}).sort("quiz_id", pymongo.ASCENDING)
    		quizs_index = yield quiz_cursor.to_list(None)


	 	#self.render("./main" ,info = self.online_data[self.get_current_user()], notices = notices)
	 	self.render("./template/admin.template", info = self.online_data[self.get_current_admin()],notices = notices, quizs_index=quizs_index)

# admin opearation
class QuizCreateHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self, quiz_id):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		## except quiz_id, releaseTime, status, all other parameters are needed
		doc = self.get_argument("quiz_json")
		cursor = yield db.quizs.find({},{"_id":0, "quiz_id":1}).sort("quiz_id", pymongo.ASCENDING)
		quiz_id_list = cusor.to_list("length=20") ##???
		doc["quiz_id"] = max(quiz_id_list) + 1
		doc["releaseTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
		doc["status"] = QuizStatus["PUBLISH"]
		deadline = datetime.strptime(doc["deadline"], "%Y-%m-%d %H:%M:%S")
		scheduler.add_job(review, 'date', run_date=deadline,args=[doc])

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def review(doc):
		print doc
		cursor = yield db.solutions.find({"quiz_id":doc["quiz_id"], "status":QuizStatus["SUBMIT"]})
		user_quizs = cursor.to_list("length=1000")
		for user_quiz in user_quizs:
			all_score = 0
			cnt = 0
			for a_content in doc["content"]:
				score = 0
				if set(a_content["answer"])  == set(user_quiz["solutions"][cnt]["solution"]) :
					score = a_content["score"]
					all_score += a_content["score"]
				cnt += 1
				user_quiz["solutions"][cnt]["score"] = score
			user_quiz["all_score"] = all_score
			yield db.solutions.save(user_quiz)
		self.finish()
		return

class StudentListHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		if not self.get_current_admin():
			self.redirect("/login")
			return
		self.checkQuizAndUpdateStatus()
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
				essayQueses = filter(lambda x:x['type']==QuizType['ESSAYQUES'],a_quiz['content'])

				user_quiz = yield db.solutions.find_one({"quiz_id":a_quiz['quiz_id'], "userId":user["userId"]})
				flag = 0 #it mark the quiz_flag out of the QuizFlag map
				if not user_quiz:
					flag = QuizFlag["UNDONE"]
					quiz_info.append({"quiz_id":a_quiz["quiz_id"], "all_score":-1, "flag":flag})
					continue
				elif user_quiz["status"] == QuizStatus["SAVE"] and not datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):#a_quiz["status"] >= QuizStatus["END"]:
					flag = QuizFlag["END"]
				elif user_quiz["status"] == QuizStatus["SAVE"]:
					flag = QuizFlag["SAVE"]
				elif user_quiz["status"] == QuizStatus["SUBMIT"] and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
					flag = QuizFlag["SUB_NOTSCORED"]
				elif user_quiz["status"] == QuizStatus["SUBMIT"]:
					# all_score == -1 means it hasn't ever been calculated

					self.reviewSelectionQues(user_quiz=user_quiz, a_quiz=a_quiz, essayQueses=essayQueses)

					if not essayQueses:
						flag = QuizFlag["FULL_SCORED"]
					else:
						flag = QuizFlag["SEMI_SCORED"]
				# user_quiz["status"] == QuizStatus["REVIEW"] 即可
				else:
					flag = QuizFlag["FULL_SCORED"]
				quiz_info.append({"quiz_id":a_quiz["quiz_id"], "all_score":user_quiz["all_score"], "flag":flag})
			users_list.append({"userId":user["userId"],"name":user["name"], "quiz_info":quiz_info})
		self.render("./template/studentlist.template", info = self.online_data[self.get_current_admin()], users_list=users_list, quizs_index=quizs_index, quizs=quizs, current_page=page,page_num=page_num,url=url)


class ReviewHandler(BaseHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self, quiz_id):
    		if not self.get_current_admin():
			self.redirect("/login")
			return
		self.checkQuizAndUpdateStatus()
    		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1}).sort("quiz_id", pymongo.ASCENDING)
    		quizs_index = yield quiz_cursor.to_list(None)
    		if not a_quiz or a_quiz["status"] == QuizStatus["UNPUBLISH"]:
    			nt_cursor = db.notices.find().sort("id", pymongo.DESCENDING)
    			notices = yield nt_cursor.to_list(None)
    			self.render("./template/admin.template", info = self.online_data[self.get_current_admin()], notices = notices, quizs_index=quizs_index)
    			return
    		# can't be reviewd because it's before the deadline, so just list the questions.
    		elif datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
    			self.render("./template/quiz_view.template", info = self.online_data[self.get_current_admin()], a_quiz=a_quiz,quizs_index=quizs_index)
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

    				self.reviewSelectionQues(user_quiz=a_user_solu, a_quiz=a_quiz, essayQueses=essayQueses)
    				user = yield db.users.find_one({"userId":a_user_solu["userId"]}, {"name":1, "_id":0,"userId":1})
    				users_solutions.append({"userId":user["userId"], "solutions":solu_tmp,"all_score":a_user_solu["all_score"], "name":user["name"]})
    			# 将content只保存问答题
    			a_quiz["content"] = essayQueses
	    		self.render("./template/quiz_review.template", info = self.online_data[self.get_current_admin()], a_quiz=a_quiz,quizs_index=quizs_index, users_solutions=users_solutions, current_page=page, page_num=page_num, url=url)
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


class UnfoundHandler(BaseHandler):
    	def get(self):
	 	self.render("./template/404.template")
	 	return
	def post(self):
	 	self.render("./template/404.template")
	 	return


class ProjectMainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		pro_cursor = db.projects.find().sort("pro_id", pymongo.ASCENDING)
    		projects = yield pro_cursor.to_list(None)
	 	self.render("./template/project.template", projects = projects, info = self.online_data[self.get_current_user()], main=1, flag=0)

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
    		pro_cursor = db.projects.find().sort("pro_id", pymongo.ASCENDING)
    		projects = yield pro_cursor.to_list(None)
    		a_pro = yield db.projects.find_one({"pro_id":pro_id, "status":ProjectStatus["PUBLISH"]})
    		if not a_pro:
    			self.redirect("/project")
    			return
    		userId = self.get_current_user()
    		up_record = yield db.user_uploads.find_one({"pro_id": pro_id, "userId": userId})
    		flag = 0
    		if not up_record and not  datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S')  :
    			flag = ProjectFlag["END"]
    		elif not up_record:
    			flag = ProjectFlag["UNDONE"]
    		elif datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S') :
    			flag = ProjectFlag["SUBMIT"]
    		else :
    			flag = ProjectFlag["DEAD"]
	 	self.render("./template/project.template", projects = projects,a_pro=a_pro, info = self.online_data[self.get_current_user()], flag=flag, main=0, up_record=up_record)
	 	return

class ProjectUploadHandler(BaseHandler):

	support_type=["application/pdf"]

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self, pro_id):
		try:
    			pro_id = int(pro_id)
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return

    		a_pro = yield db.projects.find_one({"pro_id":pro_id,"status":ProjectStatus["PUBLISH"]})

    		# 不存在此project或project已经截止
    		if not a_pro or not datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S')  :
    			self.redirect("/project")
    			return

    		userId = self.get_current_user()
    		up_record = yield db.user_uploads.find_one({"pro_id":pro_id, "userId": userId})

		upload_path=os.path.join(os.path.dirname(__file__),'report_files',str(pro_id))
		# 创建目录
		if not os.path.exists(upload_path):
			os.makedirs(upload_path)


		if self.request.files.get('uploadfile', None):
			uploadFile = self.request.files['uploadfile'][0]
			file_size = len(uploadFile['body'])

			# 检测MIME类型
			if not uploadFile["content_type"] in self.support_type or not re.match(r'^.*\.pdf$',uploadFile['filename'] ):
				self.write('<script>alert("仅支持pdf格式,doc/ppt需要转化为pdf格式才能上传");window.location="/project/'+ str(pro_id)+'"</script>')
				self.finish()
				return
			# 检测文件大小
			if  file_size > 10 * 1024 * 1024:
				self.write('<script>alert("请上传10M以下");window.location="/project/'+ str(pro_id)+'"</script>')
				self.finish()
				return
			else :
				filename = userId + ".pdf"
				filepath=os.path.join(upload_path,filename)
				if up_record and os.path.exists(filepath):
					os.remove(filepath)
				else:
					up_record = {}
					up_record["userId"]=userId
					up_record["pro_id"]=pro_id
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
    	def get(self, pro_id):
    		try:
    			pro_id = int(pro_id)
    		except ValueError, e:
    			print "The argument does not contain numbers\n", e
    			self.render("./template/404.template")
    			return
    		userId = self.get_current_user()
    		up_record = yield db.user_uploads.find_one({"pro_id":pro_id, "userId": userId})
    		if not up_record:
    			self.render("./template/404.template")
    			return
    		else:
    			upload_path=os.path.join(os.path.dirname(__file__),'report_files',str(pro_id))
    			filename = userId + "." + up_record["file_suffix"]
    			filepath=os.path.join(upload_path,filename)
    			with open(filepath, "rb") as f:
    				self.set_header('Content-Disposition', 'attachment;filename='+filename)
    				self.set_header('Content-Type','application/pdf')
      				self.write(f.read())
      			self.finish()
      			return

class APIGetHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://project.ucas-2014.tk')
		self.set_header('Access-Control-Allow-Credentials','true')
		try:
			gameId = int(self.get_argument("gameId", 1))
		except:
			return
		userId = self.get_current_user()
		if gameId not in [1,2,3]:
			return
		record = yield db.games.find_one({"gameId":gameId, "userId": userId})
		if not record:
			record = {"userId":userId,
				"gameId":gameId,
				"curLoop":0,
				"scores":{},
				"bestScore":"None",
				"histories":{}}
			yield db.games.save(record)
		self.write(json.dumps({"userId":userId,
			"curLoop":record["curLoop"],
			"name":self.online_data[userId]["name"],
			"bestScore":record["bestScore"]}))
		self.finish()
		return

class APIPutHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		self.set_header('Access-Control-Allow-Origin','http://project.ucas-2014.tk')
		self.set_header('Access-Control-Allow-Credentials','true')
		try:
			gameId = int(self.get_argument("gameId", 1))
			gameLoop = int(self.get_argument("gameLoop", 1))
			gameScore = int(self.get_argument("gameScore", 1))
			gameHist = json.loads(self.get_argument("gameHist", 1))
		except:
			return
		print gameId,gameLoop,gameScore,gameHist
		userId = self.get_current_user()
		record = yield db.games.find_one({"gameId":gameId,
			"userId": userId})
		if gameId not in [1,2,3]:
			return
		#if gameId is 1:
		if True:
			if not record:
				record = {"userId":userId,
					"gameId":gameId,
					"curLoop":0,
					"scores":{},
					"bestScore":"None",
					"histories":{}}
			if gameLoop!=record["curLoop"] or gameLoop>2:
				return
			if record["bestScore"] == "None":
				if gameScore>0:
					record["bestScore"] = gameScore
			else:
				if gameScore>0 and gameScore < record["bestScore"]:
					record["bestScore"] = gameScore
			if gameScore>0:
				gameScore != len(gameHist['results'])
				return
			record["scores"][str(gameLoop)] = gameScore
			record["histories"][str(gameLoop)] = gameHist
			record["curLoop"] = gameLoop + 1

		else:
			return
		yield db.games.save(record)
		self.write('true')
		self.finish()
		return

class LoginHandler(BaseHandler):
	def get(self):
		# test
		#self.test_user()
		#self.test_admin()
		#self.redirect("/main")
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
				self.clear_cookie("adminId")
		self.render("./template/login.template", error="")
		return

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		userId = self.get_argument("userId")
		password = self.get_argument("password")
		a_user = yield db.users.find_one({"userId":userId, "password":hashlib.md5(password + md5Salt).hexdigest()})
		a_admin = yield db.admin.find_one({"userId":userId, "password":hashlib.md5(password + md5Salt).hexdigest()})
		if a_user:
			self.set_secure_cookie("userId", a_user['userId'],domain=domain, expires_days=expires_days)
			#self.set_secure_cookie("userId", a_user['userId'])
			self.online_data[userId] = {'name': a_user['name'], 'grade':a_user['grade'],'userId':a_user['userId'], "loginTime":datetime.now()}
			self.redirect("/main")
			return
		elif a_admin:
			self.set_secure_cookie("adminId", a_admin['userId'], expires_days=expires_days)
			self.online_data[userId] = {'name': a_admin['name'],'adminId':a_admin['userId'], "loginTime":datetime.now()}
			self.redirect("/admin")
			return
		else:
			self.render("./template/login.template", error="用户名或密码错误")
		return

class PasswordHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		regEx = r'^([0-9a-zA-Z]){6,15}$'
		userId = self.get_current_user()
		origin_pass = self.get_argument("origin_pass")
		new_pass = self.get_argument("new_pass")
		new_pass_again = self.get_argument("new_pass_again")
		if userId:
			a_user = yield db.users.find_one({"userId":userId, "password":hashlib.md5(origin_pass + md5Salt).hexdigest()})
			if a_user and new_pass==new_pass_again and re.match(regEx, new_pass):
				a_user["password"] = hashlib.md5(new_pass + md5Salt).hexdigest()
				yield db.users.save(a_user)
			else:
                                self.write('<script>alert("原密码有误或新密码不符合输入规则，修改失败");;window.history.back()</script>')
				self.finish()
				return
		self.redirect("/main")
		return

class UnfoundHandler(BaseHandler):
	@tornado.web.authenticated
    	def get(self):
	 	self.render("./template/404.template")
	 	return

	@tornado.web.authenticated
	def post(self):
	 	self.render("./template/404.template")
	 	return


class ExitHandler(BaseHandler):
	def get(self):
		self.clear_current_user()
		self.clear_current_admin()
		self.redirect("./login")
		return

settings = {
	#"debug": True,
	"default_handler_class": UnfoundHandler,
	"static_path": os.path.join(os.path.dirname(__file__), "static"),
	"cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
 	"login_url": "/login",
}

application = tornado.web.Application([
    (r"/", tornado.web.RedirectHandler, {"url":"/main", "permanent":False}),
    (r"/login", LoginHandler),
    (r"/main", MainHandler),
    (r"/exit", ExitHandler),
    (r"/password", PasswordHandler),
    (r"/quiz/([0-9]+)/submit", QuizSubmitHandler),
    (r"/quiz/([0-9]+)/save", QuizSaveHandler),
    (r"/quiz/([0-9]+)", QuizHandler),
    (r"/studentlist", StudentListHandler),
    (r"/admin", AdminHandler),
    (r"/review/([0-9]+)", ReviewHandler),
    (r"/project", ProjectMainHandler),
    (r"/project/([0-9]+)/upload", ProjectUploadHandler),
    (r"/project/([0-9]+)/download", ProjectDownloadHandler),
    (r"/project/([0-9]+)", ProjectHandler),
    (r"/api/getinfo",APIGetHandler),
    (r"/api/putinfo",APIPutHandler)
    ],**settings )


# 每隔30秒进行在线用户过滤， 过期时间设置为10分钟。由于打作业时间较长，暂不提供这个功能
def filterOnlineData():
	od = BaseHandler.online_data
	now = datetime.now()
	for key in od.keys():
		if  (now - od[key]["loginTime"]) > timedelta(minutes=20):
			del od[key]
	tornado.ioloop.IOLoop.instance().add_timeout(
            		timedelta(seconds=30),
            		lambda: filterOnlineData
       	)



if __name__ == "__main__":
	#application.listen(80)
	application.listen(8888)
	print "The http server has been started!"
	#tornado.ioloop.IOLoop.instance().add_timeout(
            	#	timedelta(seconds=5),
            	#	lambda: filterOnlineData
       	#)
	tornado.ioloop.IOLoop.instance().start()
