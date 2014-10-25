#!/usr/bin/python
# coding=utf-8

from datetime import datetime
import os
import tornado.ioloop
import tornado.web

# the quiz self has four status:
# UNPUBLISH PUBLISH REVIEW(所有题目都已经批改，否则不进入RIVIEW)

# the solution done by user has two status:
# SAVE SUBMIT REVIEW
# note: solution在SUBMIT后，若quiz已经截止，则可以查看到客观题分数，此时用flag=QuizFlag["SEMI_SCORED"]来表示
# note: solution的REVIEW条件：admin对其非客观题打分
# 截至日过后，solution要么进入BLANK最终状态，要么直接进入REVIEW状态，要么进入SUBMIT再进入REVIEW
QuizStatus = {"UNPUBLISH":0, "PUBLISH":1, "SAVE":2, "SUBMIT":3, "REVIEW":4, "BLANK":5}
QuesStatus = {"UNDONE":0, "DONE":1}
ProjectStatus = {"UNPUBLISH":0, "PUBLISH":1}
ProjectFlag = {"END":-1, "UNDONE":0, "SUBMIT":1, "DEAD":2}


# UNDONE: the user hasn't done anything about the quiz before deadline
# SAVE: save before the deadline
# SUB_NOTSCORED: submit before the deadline 
# SEMI_SCORED: save or submit but the subjective questions haven't been reviewed
# FULL_SCORED: save or submit and the subjective questions have been reviewed
# BLANK: the user hasn't done anything about the quiz after deadline, the system add a blank record for his solution
# 截至前的状态有：UNDONE/SAVE/SUB_NOTSCORED, 截止后的状态有:BLANK/SEMI_SCORED/FULL_SCORED
QuizFlag = {"BLANK": -1,"UNDONE":0,"SAVE":1,"SUB_NOTSCORED":2,"SEMI_SCORED":3 ,"FULL_SCORED":4}

QuizType = {"SINCHOICE":1, "MULTICHOICE":2, "ESSAYQUES":3}

TopoStatus = {"NEW" : 0, "ING":1, "DONE":2}

class HwWebUtil:
	@staticmethod
	def canSaveOrSubmit(a_quiz, user_quiz, op_now):
		if not a_quiz or a_quiz["status"] != QuizStatus["PUBLISH"] or op_now > datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S") or user_quiz and user_quiz["status"] != QuizStatus["SAVE"]:
			return False
		else:
			return True