#!/usr/bin/python
# coding=utf-8

from datetime import datetime
import os
import tornado.ioloop
import tornado.web

# the quiz self has four status:
# UNPUBLISH PUBLISH REVIEW
# the solution done by user has two status:
# SAVE SUBMIT REVIEW
# note: solution在SUBMIT后，若quiz已经截止，则可以查看到客观题分数，此时用flag=QuizFlag["SEMI_SCORED"]来表示
# note: solution的REVIEW条件：admin对其非客观题打分
QuizStatus = {"UNPUBLISH":0, "PUBLISH":1, "SAVE":2, "SUBMIT":3, "REVIEW":4}
QuesStatus = {"UNDONE":0, "DONE":1}
ProjectStatus = {"UNPUBLISH":0, "PUBLISH":1}
ProjectFlag = {"END":-1, "UNDONE":0, "SUBMIT":1, "DEAD":2}

# END: the user only save when passing the deadline
# UNDONE: the user hasn't done anything about the quiz before deadline
# SAVE: the user save before the deadline
# SEMI_SCORED: submit but the subjective questions haven't been reviewed
# FULL_SCORED: submit and the subjective questions have been reviewed
QuizFlag = {"END": -1,"UNDONE":0,"SAVE":1,"SUB_NOTSCORED":2,"SEMI_SCORED":3 ,"FULL_SCORED":4}

QuizType = {"SINCHOICE":1, "MULTICHOICE":2, "ESSAYQUES":3}

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
