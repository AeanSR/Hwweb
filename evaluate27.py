import subprocess
import random
import os
import pymongo
import motor
from datetime import datetime
import copy
from HwWebUtil import HwWebUtil
db = motor.MotorClient('localhost', 27017).hwweb
sdb = pymongo.MongoClient('localhost', 27017).hwweb
testdb = motor.MotorClient('localhost', 27017).test_hwweb
Exp5scheduleTable= copy.deepcopy(HwWebUtil.getExp5Schedule())
for exp_date in Exp5scheduleTable["date"]:
    for i in range(0, len(exp_date)) :
    	exp_date[i] = exp_date[i].strftime("%Y-%m-%d %H:%M:%S")
execisepath = os.path.join(os.path.dirname(__file__),'report_files/exp5/4/')
picturepath = os.path.join(os.path.dirname(__file__),'exp5picture/')

src='abcdefghigklmnopqrstuvwxyz \'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def get_words(): #get test words randomly
    length=random.randint(10000,40000)
    RightWords=''
    for i in range(0,length):
        RightWords +=random.choice(src)#from the file  I should do something here
    text=open(picturepath+'word1.txt','w') #write the words into file
    text.write(RightWords)
    text.close()
    return(RightWords)


if __name__=='__main__':
     
    while datetime.strptime(exp_date[len(exp_date)-1],"%Y-%m-%d %H:%M:%S")<datetime.now():
        pass;
    else:
        i=0
        up_record =sdb.user_uploads.find({"pro_id": 4,"kind":"exp5"})
        for item in up_record:
            filename="2015-4-"+item["userId"]+"-program.py"
            hideInfo=get_words()
            StuWords=''
            try:
                prcs1=subprocess.Popen(['python3', execisepath+filename,execisepath+'test.bmp','hide',picturepath+'word1.txt',picturepath+item["userId"]+'.bmp'],
                                       shell=False)
                returnCode=prcs1.wait()
                prcs2=subprocess.Popen(['python3', execisepath+filename,picturepath+item["userId"]+'.bmp','show'],
                                       shell=False,
                                       universal_newlines=True,
                                       stdout=subprocess.PIPE)
                returncode=prcs2.wait()
                StuWords=prcs2.communicate()[0]
                prcs3=subprocess.Popen(['python3', execisepath+'example.py',picturepath+item["userId"]+'.bmp','show'],
                                       shell=False,
                                       universal_newlines=True,
                                       stdout=subprocess.PIPE)
                returncode=prcs3.wait()
                mywords=prcs3.communicate()[0]
                #subprocess.call(['python3', execisepath+filename,execisepath+'test.bmp','hide',picturepath+'word1.txt',picturepath+item["userId"]+'.bmp'],shell=False)  #run student's programme to creat a newbmp with hiding imformation
                #StuWords=subprocess.check_output(['python3', execisepath+filename,picturepath+item["userId"]+'.bmp','show'],shell=False,universal_newlines=True) #stu answer
                #mywords=subprocess.check_output(['python3',execisepath+'example.py',picturepath+item["userId"]+'.bmp','show'],shell=False,universal_newlines=True) #my answer
            except Exception,e:
                sdb.user_uploads.update({"userId":item["userId"],"kind":"exp5","pro_id": 4},{'$set':{"score":"0"}})
                print e
    #I should use my progamme to test their bmp
            else:
                if  (hideInfo!=StuWords[:-1]):
                    sdb.user_uploads.update({"userId":item["userId"],"kind":"exp5","pro_id": 4},{'$set':{"score":"0"}})
                    print '2'
                elif StuWords!=mywords:
                    sdb.user_uploads.update({"userId":item["userId"],"kind":"exp5","pro_id": 4},{'$set':{"score":"60"}})
                else:
                    
                    print '1'
                    sdb.user_uploads.update({"userId":item["userId"],"kind":"exp5","pro_id": 4},{'$set':{"score":"100"}})

                    
        

