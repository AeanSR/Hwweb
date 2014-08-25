#!/usr/bin/python
# coding=utf-8

from datetime import datetime
import os
import tornado.ioloop
import tornado.web

# the quiz self has four status:
# UNPUBLISH PUBLISH END RIVIEW
# the solution done by user has two status:
# SAVE SUBMIT
QuizStatus = {"UNPUBLISH":0, "PUBLISH":1, "SAVE":2, "SUBMIT":3, "END":4, "RIVIEW":5}
QuesStatus = {"UNDONE":0, "DONE":1}

# END: the user only save when passing the deadline
# UNDONE: the user hasn't done anything about the quiz before deadline
# SAVE: the user save before the deadline
# SEMI_SCORED: submit but the subjective questions haven't been reviewed
# FULL_SCORED: submit and the subjective questions have been reviewed
QuizFlag = {"END": -1,"UNDONE":0,"SAVE":1,"SEMI_SCORED":2 ,"FULL_SCORED":3}

class HwWebUtil:
	@staticmethod
	def canSaveOrSubmit(a_quiz, user_quiz, op_now):
		if not a_quiz or a_quiz["status"] != QuizStatus["PUBLISH"] or op_now > datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S") or user_quiz and user_quiz["status"] != QuizStatus["SAVE"]:
			return False
		else:
			return True

	@staticmethod
	def quartz(db, scheduler, a_quiz):
    		print('Tick! The time is: %s' % datetime.now())

	@staticmethod
	@tornado.web.asynchronous
	@tornado.gen.coroutine
	def review():
    		pass
