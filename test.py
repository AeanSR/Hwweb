#!/usr/bin/python
# coding=utf-8
import os
import tornado.ioloop
import tornado.web
import motor
import datetime


# the quiz self has four status:
# UNPUBLISH PUBLISH END RIVIEW
# the solution done by user has two status:
# SAVE SUBMIT
QuizStatus = {"UNPUBLISH":0, "PUBLISH":1, "SAVE":2, "SUBMIT":3, "END":4, "RIVIEW":5}
QuesStatus = {"UNDONE":0, "DONE":1}

# UNDONE: the user save till the deadline has passed or the user hasn't done anything about the quiz
# SAVE: the user save before the deadline
# SEMI_SCORED: submit but the subjective questions haven't been reviewed
# FULL_SCORED: submit and the subjective questions have been reviewed
QuizFlag = {"UNDONE":0,"SAVE":1,"SEMI_SCORED":2 ,"FULL_SCORED":3}

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
	def get(self):
		doc={"time":datetime.datetime.now()}
		print doc
		yield db.abc.insert(doc)
		docc = yield db.abc.find({},{"time":1, "_id":0}).to_list(length=100)
		print docc[0]["time"]
		self.write( docc[0]["time"].strptime("%Y-%m-%d %H:%M:%S %f"))
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




#hasn't been implemented
class QuizSaveHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	#Only submit, save function hasn't been implemented
	def post(self, quiz_id):
		quiz_contents = yield db.quizs.find_one({"quiz_id": int(quiz_id)}, {"content":1, "_id":0})
		ques_count = self.get_argument("ques_count")
		solutions = yield db.solutions.find_one({"userId":int(self.current_user)})
		doc = {}
		doc["userId"] =  self.current_user
		doc["quiz_id"] = quiz_id
		count = 0
		solutions= []
		status = 0
		for a_content in quiz_contents["content"]:
			ques_status = QuesStatus["UNDONE"]
			answer = []
			count +=1
			#if a_content["type"] = 3
			# to do
			# if submit , i will test whether the student had done all the questions
			if self.get_argument("quiz_"+quiz_id+"_"+str(count), None) :
				ques_status = QuesStatus["DONE"]
				answer.append(self.get_argument("quiz_"+quiz_id+"_"+str(count)))
				print "a_content=" , a_content
			solutions.append({"type":a_content["type"], "solution":answer, "score":0, "status":ques_status})
		doc["solutions"] = solutions
		doc["all_score"] = 0
		# to do: status vary from the action which the studuent choose, "save" or "submit"
		doc["status"] = QuizStatus["SAVE"]
		print doc
		self.finish()


class QuizSubmitHandler(BaseHandler):
	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def post(self, quiz_id):
		quiz_contents = yield db.quizs.find_one({"quiz_id": int(quiz_id)}, {"content":1, "_id":0})
		doc = {}
		doc["userId"] =  self.current_user
		doc["quiz_id"] = quiz_id
		count = 0
		solutions= []
		all_score = 0
		status = 0
		for a_content in quiz_contents["content"]:
			ques_status = QuesStatus["UNDONE"]
			solution = []
			score = 0
			count +=1
			#if a_content["type"] = 3
			# to do
			# if submit , i will test whether the student had done all the questions
			if self.get_argument("quiz_"+quiz_id+"_"+str(count), None) :
				ques_status = QuesStatus["DONE"]
				solution.append(self.get_argument("quiz_"+quiz_id+"_"+str(count)))
				print "a_content=" , a_content
				if set(a_content["answer"])  == set(solution) :
					score = a_content["score"]
					all_score += score
			solutions.append({"type":a_content["type"], "solution":solution, "score":score, "status":ques_status})
		doc["solutions"] = solutions
		doc["all_score"] = all_score
		# to do: status vary from the action which the studuent choose, "save" or "submit"
		doc["status"] = QuizStatus["SUBMIT"]
		print "doc=", doc
		self.finish()

class QuizHandler(BaseHandler):

	@tornado.web.authenticated
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def get(self, quiz_id):
		a_quiz = yield db.quizs.find_one({"quiz_id": int(quiz_id)})
		if not a_quiz  or a_quiz["status"] == QuizStatus["UNPUBLISH"]:
			self.redirect("/main")
		else:
			# quizs for indexing
			quiz_cursor = db.quizs.find({},{"status":1, "quiz_id":1, "releaseTime":1, "deadline":1})
	    		quizs = yield quiz_cursor.to_list(length=20)
			user_quiz = yield db.solutions.find_one({"quiz_id":int (quiz_id), "userId":self.current_user})
			flag = 0 #it mark the quiz_flag out of the QuizFlag map
			if not user_quiz or user_quiz["status"] == QuizStatus["SAVE"] and a_quiz["status"] >= QuizStatus["END"]:
				flag = QuizFlag["UNDONE"]
			elif user_quiz["status"] == QuizStatus["SAVE"]:
				flag = QuizFlag["SAVE"]
			elif user_quiz["status"] == QuizStatus["SUBMIT"] and a_quiz["status"] == QuizStatus["RIVIEW"]:
				flag = QuizFlag["SEMI_SCORED"]
			else:
				flag = QuizFlag["FULL_SCORED"]
			self.render("./quiz.template", a_quiz = a_quiz, info = self.online_data[self.get_current_user()],  quizs=quizs, QuizStatus=QuizStatus,user_quiz=user_quiz, flag=flag,QuizFlag=QuizFlag)
		return

	
		


class LoginHandler(BaseHandler):
	def get(self):
		# test 
		self.test_user()
		self.redirect("/main")
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
				#, name=a_user["name"], grade=a_user["grade"],userId=a_user["userId"])
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
    (r"/quiz/([0-9]+)", QuizHandler),
    (r"/quiz/([0-9]+)/submit", QuizSubmitHandler),
    (r"/quiz/([0-9]+)/save", QuizSaveHandler),
    (r"/test", TestHandler)
    ],**settings )

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
