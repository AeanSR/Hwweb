#!/usr/bin/python
# coding=utf-8

from datetime import datetime
from datetime import timedelta
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
ProjectStatus = {"UNPUBLISH":0, "PUBLISH":1, "END":2}

# 实验上传的文件类型
UploadType = {"PRESENTATION":0, "EXPREPORT":1}

# UNDONE: the user hasn't done anything about the quiz before deadline
# SAVE: save before the deadline
# SUB_NOTSCORED: submit before the deadline 
# SEMI_SCORED: save or submit but the subjective questions haven't been reviewed
# FULL_SCORED: save or submit and the subjective questions have been reviewed
# BLANK: the user hasn't done anything about the quiz after deadline, the system add a blank record for his solution
# 截至前的状态有：UNDONE/SAVE/SUB_NOTSCORED, 截止后的状态有:BLANK/SEMI_SCORED/FULL_SCORED
QuizFlag = {"BLANK": -1,"UNDONE":0,"SAVE":1,"SUB_NOTSCORED":2,"SEMI_SCORED":3 ,"FULL_SCORED":4}

QuizType = {"SINCHOICE":1, "MULTICHOICE":2, "ESSAYQUES":3}

TopoStatus = {"CHOOSING" : -1, "NEW" : 0, "ING":1, "DONE":2}

class HwWebUtil:
	scheduleTable = {}
	@staticmethod
	def canSaveOrSubmit(a_quiz, user_quiz, op_now):
		if not a_quiz or a_quiz["status"] != QuizStatus["PUBLISH"] or op_now > datetime.strptime(a_quiz["deadline"], "%Y-%m-%d %H:%M:%S") or user_quiz and user_quiz["status"] != QuizStatus["SAVE"]:
			return False
		else:
			return True

	@staticmethod
	def getSchedule():
		scheduleTable = HwWebUtil.scheduleTable
		if not scheduleTable:
			schedleFile =os.path.join(os.path.dirname(__file__),'conf','schedule.csv')
			with open(schedleFile, "r") as f:
				heads = f.readline().split(",")
				scheduleTable["date"] = []
				for dateStr in heads[1:]:
					startDate = datetime.strptime(dateStr.split("-")[0].strip(), "%Y/%m/%d/%H/%M/%S") 
					endDate = datetime.strptime(dateStr.split("-")[1].strip(), "%Y/%m/%d/%H/%M/%S") 
					if str(endDate)[5:7] == '06':
						presentationDeadline = endDate.replace(hour=23) + timedelta(days=20)
						reportDeadline = presentationDeadline
					else: 
						presentationDeadline = endDate.replace(hour=23) + timedelta(days=13)
						reportDeadline = presentationDeadline

					scheduleTable["date"].append([startDate, endDate, presentationDeadline, reportDeadline])
				scheduleTable["table"] = {}
				line = f.readline().strip()
	      			while line:
	      				nos = line.split(",")
	      				scheduleTable["table"][int(nos[0])] = nos[1:]
	      				line = f.readline().strip()
	      	return scheduleTable

	@staticmethod
	def isValid(classNo, projectNo):
		classNo = int(classNo)
		scheduleTable = HwWebUtil.getSchedule()
		
	      	# 测试帐号都是0班级
	      	if classNo == 0:
	      		return True
	      	now = datetime.now()
	      	project_time = 0
	      	for i in range(0, len(scheduleTable["date"])):
	      		if now > scheduleTable["date"][i][0] and now < scheduleTable["date"][i][1]:
	      			project_time = i + 1
	      			break
	      	if project_time == 0 or int(scheduleTable["table"][classNo][project_time-1]) != projectNo:
	      		return False
	      	else:
	      		return True



	# 检测是否为连通图
	@staticmethod
	def isConnectedGraph(scale, links):
		AdjList = [ [] for i in range(scale)]
		for link in links:
			x = int(link.split("-")[0])
			y = int(link.split("-")[1])
			AdjList[x].append(y)
			AdjList[y].append(x)
		count = HwWebUtil.BFS(AdjList, 0)
		if count == scale:
			return True
		else:
			return False

	# BFS，返回BFS树的节点数
	@staticmethod
	def BFS(AdjList, i):
		scale = len(AdjList)
		markArray = [ False for i in range(scale)]
		count = 1
		queue = []
		markArray[i] = True
		queue.append(i)
		while len(queue) != 0:
			u = queue[0]
			del queue[0]
			for v in AdjList[u]:
				if not markArray[v]:
					markArray[v] = True
					count += 1
					queue.append(v)
		return count
