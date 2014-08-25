#!/usr/bin/python
# coding=utf-8
import os
import tornado.ioloop
import tornado.web
import motor
import json

from datetime import datetime
from apscheduler.schedulers.tornado import TornadoScheduler

from HwWebUtil import HwWebUtil
from HwWebUtil import QuizStatus
from HwWebUtil import QuesStatus
from HwWebUtil import QuizFlag



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

	@staticmethod
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def quartz(doc) :
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
		print "doc['deadline'].strptime('%Y-%m-%d %H:%M:%S') = ", doc['deadline'].strptime("%Y-%m-%d %H:%M:%S")
		
		scheduler.add_job(quartz, 'date', run_date=doc['deadline'].strptime("%Y-%m-%d %H:%M:%S"), args=[doc])
		
		
		self.finish()



class MainHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
    	def get(self):
    		nt_cursor = db.notices.find()
    		# to_list (length ?)
    		notices = yield nt_cursor.to_list(length=20)
    		quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1})
    		quizs = yield quiz_cursor.to_list(length=20)
	 	#self.render("./main" ,info = self.online_data[self.get_current_user()], notices = notices)
	 	self.render("./main.template" ,info = self.online_data[self.get_current_user()], notices = notices, quizs=quizs, QuizStatus=QuizStatus)




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
			elif user_quiz["status"] == QuizStatus["SAVE"] and a_quiz["status"] >= QuizStatus["END"]:
				flag = QuizFlag["END"]
			elif user_quiz["status"] == QuizStatus["SAVE"]:
				flag = QuizFlag["SAVE"]
			elif user_quiz["status"] == QuizStatus["SUBMIT"] and a_quiz["status"] != QuizStatus["RIVIEW"]:
				flag = QuizFlag["SEMI_SCORED"]
			else:
				flag = QuizFlag["FULL_SCORED"]
			print "flag = " ,flag

			self.render("./quiz.template", a_quiz = a_quiz, info = self.online_data[self.get_current_user()],  quizs=quizs, QuizStatus=QuizStatus,user_quiz=user_quiz, flag=flag,QuizFlag=QuizFlag)
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
    (r"/test", TestHandler)
    ],**settings )
scheduler = TornadoScheduler()
scheduler.add_jobstore('mongodb', collection='quiz_semi_review')

if __name__ == "__main__":
	application.listen(8888)
	scheduler.start()
	
	tornado.ioloop.IOLoop.instance().start()
	
	print('Press Ctrl+{0} to exit'.format('Break' if os.name == 'nt' else 'C'))

	
