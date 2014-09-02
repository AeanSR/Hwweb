#!/usr/bin/python
# coding=utf-8
import os
import tornado.ioloop
import tornado.web
import motor
import json
import pymongo

from datetime import datetime
from apscheduler.schedulers.tornado import TornadoScheduler

from HwWebUtil import HwWebUtil
from HwWebUtil import QuizStatus
from HwWebUtil import QuesStatus
from HwWebUtil import QuizFlag
from HwWebUtil import QuizType



db = motor.MotorClient('localhost', 27017).test


class BaseHandler(tornado.web.RequestHandler):
	online_data = {}
	def get_current_user(self):
		userId = self.get_secure_cookie("userId")
		if self.online_data and self.online_data[userId]:
			return userId
		else:
			return None
	def clear_current_user(self):
		userId = self.get_secure_cookie("userId")
		if userId and self.online_data and self.online_data[userId]:
			del self.online_data[userId]
		self.clear_cookie(userId)

	#for test, release version needs to delete it
	def test_user(self):
		self.set_secure_cookie("userId", "201428013229018")
		self.online_data["201428013229018"] = {'name': "李春典", 'grade':"大一",'userId':"201428013229018"}


# test case
class TestHandler(tornado.web.RequestHandler):

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def quartz(self, doc, time) :
		print "Start run at %s."  % time
		cursor =  db.solutions.find({"quiz_id":doc["quiz_id"], "status":QuizStatus["SUBMIT"]} )
		user_quizs = yield cursor.to_list(length=1000)
		for user_quiz in user_quizs:
			print "origin :user_quiz = " ,user_quiz
			print "user_quiz['solutions'][0] =  ", user_quiz['solutions'][0]
			all_score = 0 
			cnt = 0
			for a_content in doc["content"]:
				score = 0
				if set(a_content["answer"])  == set(user_quiz["solutions"][cnt]["solution"]) :
					score = a_content["score"]
					all_score += a_content["score"]
				user_quiz["solutions"][cnt]["score"] = score
				cnt += 1
			user_quiz["status"] = QuizStatus["SUBMIT"]
			user_quiz["all_score"] = all_score
			print "now :user_quiz = " ,user_quiz
			yield db.solutions.save(user_quiz)		
	

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		doc={"time":datetime.now()}
		print doc
		yield db.abc.insert(doc)
		docc = yield db.abc.find({},{"time":1, "_id":0}).to_list(length=100)
		print docc[0]["time"]
		self.write( docc[0]["time"].strptime("%Y-%m-%d %H:%M:%S"))
		self.finish()

	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		doc = self.get_argument("doc", None)
		if not doc:
			self.finish()
		doc = json.loads(doc)
		print "datetime.strptime(doc['deadline'], '%Y-%m-%d %H:%M:%S') = ", datetime.strptime(doc["deadline"], "%Y-%m-%d %H:%M:%S")
		
		scheduler.add_job(self.quartz, 'date', run_date=datetime.strptime(doc["deadline"], "%Y-%m-%d %H:%M:%S"), args=[doc, datetime.now()])
		
		
		self.finish()



class MainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		nt_cursor = db.notices.find()
    		# to_list (length ?)
    		notices = yield nt_cursor.to_list(None)
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1})
    		quizs = yield quiz_cursor.to_list(None)
	 	#self.render("./main" ,info = self.online_data[self.get_current_user()], notices = notices)
	 	self.render("./main.template" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs)




class QuizSaveHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	#Only submit, save function hasn't been implemented
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

			if self.get_argument("quiz_"+quiz_id+"_"+str(count), None) :
				ques_status = QuesStatus["DONE"]
				answer.append(self.get_argument("quiz_"+quiz_id+"_"+str(count)))
			solutions.append({"type":a_content["type"], "solution":answer, "score":0, "status":ques_status})
		doc["lastTime"] = op_now.strftime("%Y-%m-%d %H:%M:%S")
		doc["solutions"] = solutions
		doc["all_score"] = 0
		doc["status"] = QuizStatus["SAVE"]
		print "doc=", doc
		yield db.solutions.save(doc)
		self.redirect("/quiz/"+quiz_id)



# ? score need to be calculated after submiting?
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
		#all_score = 0
		status = 0
		for a_content in quiz_contents["content"]:
			ques_status = QuesStatus["UNDONE"]
			solution = []
			score = 0
			count +=1
			# to do
			# if submit , i will test whether the student had done all the questions
			if self.get_argument("quiz_"+quiz_id+"_"+str(count), None) :
				ques_status = QuesStatus["DONE"]
				solution.append(self.get_argument("quiz_"+quiz_id+"_"+str(count)))
			solutions.append({"type":a_content["type"], "solution":solution, "score":score, "status":ques_status})
		doc["lastTime"] = op_now.strftime("%Y-%m-%d %H:%M:%S")
		doc["solutions"] = solutions
		doc["all_score"] = 0 #all_score
		doc["status"] = QuizStatus["SUBMIT"]
		print "doc=", doc
		yield db.solutions.save(doc)
		self.redirect("/quiz/"+quiz_id)
		return



class QuizHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self, quiz_id):
		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
		if not a_quiz  or a_quiz["status"] == QuizStatus["UNPUBLISH"]:
			self.redirect("/main")
			return
		else:
			# quizs for indexing
			quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1})
	    		quizs = yield quiz_cursor.to_list(length=20) #???
			user_quiz = yield db.solutions.find_one({"quiz_id":int (quiz_id), "userId":self.current_user})
			flag = 0 #it mark the quiz_flag out of the QuizFlag map
			if not user_quiz:
				flag = QuizFlag["UNDONE"]
			elif user_quiz["status"] == QuizStatus["SAVE"] and not datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):#a_quiz["status"] >= QuizStatus["END"]:
				flag = QuizFlag["END"]
			elif user_quiz["status"] == QuizStatus["SAVE"]:
				flag = QuizFlag["SAVE"]
			elif user_quiz["status"] == QuizStatus["SUBMIT"] and datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
				flag = QuizFlag["SUB_NOTSCORED"]
			# note: solution在SUBMIT后，若quiz已经截止，则可以查看到客观题分数
			elif user_quiz["status"] == QuizStatus["SUBMIT"]:
				#initial value of all_score is -1, all_score == -1 means it hasn't ever been calculated 
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
					yield db.solutions.save(user_quiz)
				flag = QuizFlag["SEMI_SCORED"]
			# user_quiz["status"] == QuizStatus["REVIEW"] 
			else:
				flag = QuizFlag["FULL_SCORED"]

			self.render("./quiz.template", a_quiz = a_quiz, info = self.online_data[self.get_current_user()],  quizs=quizs, user_quiz=user_quiz, flag=flag)
		return


# admin opearation
class QuizCreateHandler(BaseHandler):
	
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self, quiz_id):
		## except quiz_id, releaseTime, status, all other parameters are needed
		doc = self.get_argument("quiz_json")
		cursor = yield db.quizs.find({},{"_id":0, "quiz_id":1})
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

class StudentListHandler(BaseHandler):
	
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self):
		# page
		# quiz_id
		page = int(self.get_argument("page", 1))
		quiz_id = int(self.get_argument("quiz_id", 0))
		quiz_cursor = None

		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1,"content":1}).sort("quiz_id", pymongo.ASCENDING)
		quizs_index = yield quiz_cursor.to_list(None)
		# 列出学生所有成绩情况
		if quiz_id == 0:
			quizs = quizs_index
			quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1,"content":1}).sort("quiz_id", pymongo.ASCENDING)
		else:
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
						yield db.solutions.save(user_quiz)
					flag = QuizFlag["SEMI_SCORED"]
				# user_quiz["status"] == QuizStatus["REVIEW"] 即可
				else:
					flag = QuizFlag["FULL_SCORED"]
				quiz_info.append({"quiz_id":a_quiz["quiz_id"], "all_score":user_quiz["all_score"], "flag":flag})
			users_list.append({"userId":user["userId"],"name":user["name"], "quiz_info":quiz_info})
		self.render("./studentlist.template", users_list=users_list, quizs_index=quizs_index, quizs=quizs, current_page=page,page_num=page_num,url="/studentlist")


class ReviewHandler(BaseHandler):
	
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self, quiz_id):
    		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)}, {"content":1,"status":1, "quiz_id":1, "releaseTime":1, "deadline":1,"title":1})
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1})
    		quizs_index = yield quiz_cursor.to_list(None)
    		if not a_quiz or a_quiz["status"] == QuizStatus["UNPUBLISH"]:
    			nt_cursor = db.notices.find()
    			notices = yield nt_cursor.to_list(None)
    			self.render("./admin.template", notices = notices, quizs=quizs)
    			return
    		# can't be reviewd because it's before the deadline, so just list the questions.
    		elif datetime.now() < datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S"):
    			self.render("./quiz_view.template", a_quiz=a_quiz,quizs=quizs)
    			return
    		# it has been reviewd 
    		elif a_quiz["status"] == QuizStatus["REVIEW"]:
    			self.redirect("/studentlist?quiz_id=" + quiz_id)
    			return

    		# 选择查看已经批阅的用户，还是未批阅的用户。默认是未批阅的用户
    		reviewed = int(self.get_argument("reviewed", 0))
    		page = int(self.get_argument("page", 1))
		# 筛选出问答题
    		a_quiz["content"] = filter(lambda x:x["type"]==QuizType["ESSAYQUES"], a_quiz["content"])
    		if reviewed == 0:
    			users_solutions=[]
    			# 分页为30个一页
    			solutions_cursor = db.solutions.find({"quiz_id":a_quiz["quiz_id"], "status":QuizStatus["SUBMIT"]}, {"solutions" : 1 , "all_score":1, "userId":1} ).sort("userId", pymongo.ASCENDING).skip((page-1) * 30)
    			cnt = yield solutions_cursor.count()
    			page_num = (cnt-1)/30 + 1
    			solutions = yield solutions_cursor.to_list(length=30)
    			# 也是只筛选出问答题的solution
    			for a_user_solu in solutions:
    				solu_tmp= filter(lambda x: x["type"] == QuizType["ESSAYQUES"],a_user_solu["solutions"])
    				user = yield db.users.find_one({"userId":a_user_solu["userId"]}, {"name":1, "_id":0,"userId":1})
    				users_solutions.append({"userId":user["userId"], "solutions":solu_tmp,"all_score":a_user_solu["all_score"], "name":user["name"]})
	    		self.render("./quiz_review.template", a_quiz=a_quiz,quizs_index=quizs_index, users_solutions=users_solutions, current_page=page, page_num=page_num, url="/review/%d"%a_quiz["quiz_id"])
	    	else:
	    		# to do
	    		return
	 	

class AdminHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		nt_cursor = db.notices.find()
    		notices = yield nt_cursor.to_list(None)
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1})
    		quizs_index = yield quiz_cursor.to_list(None)
	 	#self.render("./main" ,info = self.online_data[self.get_current_user()], notices = notices)
	 	self.render("./admin.template", notices = notices, quizs_index=quizs_index)

class LoginHandler(BaseHandler):
	def get(self):
		# test 
		self.test_user()
		self.redirect("/main")
		return
		# delete when releasing

		userId = self.get_secure_cookie("userId")
		if userId:
			if self.online_data and self.online_data[userId]:
				self.redirect("/main")
				return
			else:
				self.clear_cookie("userId")
		self.render("./login.template", error="")
		return
	
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self):
		userId = self.get_argument("userId")
		password = self.get_argument("password")
		a_user = yield db.users.find_one({"userId":userId, "password":password})
		if a_user:
			self.set_secure_cookie("userId", a_user['userId'])
			self.online_data[userId] = {'name': a_user['name'], 'grade':a_user['grade'],'userId':a_user['userId']}
			self.redirect("./main")
			return
		else:
			self.render("login.template", error="用户名密码错误")
		return


class ExitHandler(BaseHandler):
	def get(self):
		self.clear_current_user()
		self.redirect("./login")
		return

settings = {
	"static_path": os.path.join(os.path.dirname(__file__), "static"),
	"cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
 	"login_url": "/login",
}

application = tornado.web.Application([
    (r"/", tornado.web.RedirectHandler, {"url":"/main", "permanent":False}),
    (r"/login", LoginHandler),
    (r"/main", MainHandler),
    (r"/exit", ExitHandler),
    (r"/quiz/([0-9]+)/submit", QuizSubmitHandler),
    (r"/quiz/([0-9]+)/save", QuizSaveHandler),
    (r"/quiz/([0-9]+)", QuizHandler),
    (r"/test", TestHandler),
    (r"/studentlist", StudentListHandler),
    (r"/admin", AdminHandler),
    (r"/review/([0-9]+)", ReviewHandler)
    ],**settings )
scheduler = TornadoScheduler()
scheduler.add_jobstore('mongodb', collection='quiz_semi_review')

if __name__ == "__main__":
	application.listen(8888)
	scheduler.start()
	print "The apscheduler has been started."
	tornado.ioloop.IOLoop.instance().start()
	
	print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

	
