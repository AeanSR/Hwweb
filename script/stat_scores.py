#!/usr/bin/env python
import pymongo
from pymongo import MongoClient
import xlsxwriter

client = MongoClient('mongodb://localhost:27017/')
db = client.hwweb
scoreTable = {}
workbook = xlsxwriter.Workbook('scores.xlsx')
worksheet1 = workbook.add_worksheet("exp2&exp3")
worksheet2 = workbook.add_worksheet("exp4")
def getAndCreateList(group):
    if group not in scoreTable:
        scoreTable[group] = {}
    return scoreTable[group]
print "group, score"

# Exp2
for row in db.games.find({"group":{"$regex":"^[^0]"},"gameId":{"$lt":5}},{'bestScore':1,'group':1,'gameId':1}).sort("group", pymongo.ASCENDING):
    score = row['bestScore']
    try:
        score = int(score)
    except:
        score = -1
    rowRecord = getAndCreateList(row["group"])
    if row['gameId'] is 1:
        if score is -1:
            score = 16
        score = (20 - score)/ (20.0 - 8.0) * 100 
        rowRecord['exp2-1'] = score
    elif row['gameId'] is 2:
        if score is -1:
            score = 8
        score = (13 - score)/ (13.0 - 4.0) * 100 
        rowRecord['exp2-2'] = score
    elif row['gameId'] is 3:
        if score is -1:
            score = 16
        score = (20 - score)/ (20.0 - 5.0) * 100 
        rowRecord['exp2-3'] = score
    elif row['gameId'] is 4:
        if score is -1:
            score = 16
        if score<4:
            score = 4
        score = (20 - score)/ (20.0 - 4.0) * 100 
        rowRecord['exp2-4'] = score

for group in scoreTable:
    rowRecord = scoreTable[group]
    rowRecord['exp2'] = rowRecord['exp2-1']*0.25 + rowRecord['exp2-2']*0.25 + rowRecord['exp2-3']*0.25 + rowRecord['exp2-4']*0.25
    rowRecord['exp2'] = int(rowRecord['exp2'])
# Exp3
for row in db.routeTopo.find({"mode":0},{"_id":0, "finalScore":1, "group":1}).sort("group", pymongo.ASCENDING):
    if "finalScore" in row:
        rowRecord = getAndCreateList(row["group"])
        rowRecord['exp3'] = row["finalScore"]

# Exp4
for row in db.exp4u.find({"group":{"$regex":"^[^0].+submit"}}):
    group = row['group']
    group = group[0:group.find('-submit')]
    rowRecord = getAndCreateList(group)
    if 'exp4-scores' not in rowRecord:
        rowRecord['exp4-scores'] = {}
    rowRecord['exp4-scores'][row['userId']] = int((row['score'] - 80)/20.0 + 94)
    if rowRecord['exp4-scores'][row['userId']]>100:
        rowRecord['exp4-scores'][row['userId']] = 100
    # rowRecord['exp4'] = sum(rowRecord['exp4-scores'])/len(rowRecord['exp4-scores'])

cols = ['exp2','exp3']
r = 0
sortedkeys = sorted(scoreTable.keys(), key=lambda x:int(x.split('-')[0])*10+int(x.split('-')[1]))
for group in sortedkeys:
    c = 0
    worksheet1.write(r,c, group)
    c = 1
    for col in cols:
        worksheet1.write(r,c, scoreTable[group][col])
        c = c + 1
    r = r +1

r = 0
for group in sortedkeys:
    for uid in scoreTable[group]['exp4-scores']:
        c = 0
        worksheet2.write(r,c, group)
        c = 1
        worksheet2.write(r,c, uid)
        c = 2
        worksheet2.write(r,c, db.users.find({"userId":uid})[0]['name'])
        c = 3
        worksheet2.write(r,c, scoreTable[group]['exp4-scores'][uid])
        r = r +1
workbook.close()