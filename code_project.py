#!/usr/bin/python
# coding=utf-8
import tornado.web
from base import *
from HwWebUtil import HwWebUtil, ProjectStatus
from datetime import datetime, timedelta
import time
import re

CodeProjectId = 7
# 编程实验上传文件类型
EXPREPORT_TYPE = "report"
CODE_TYPE = "code"
BMP_TYPE = "bmp"

CodeUploadType = {EXPREPORT_TYPE:0, CODE_TYPE:1, BMP_TYPE: 2}
UploadSupportType=["application/pdf", "text/plain", "image/bmp", "application/octet-stream"]
CodeUploadTypeMap = {EXPREPORT_TYPE:("pdf","application/pdf"),
    BMP_TYPE:("bmp","image/bmp"),
    CODE_TYPE:("go","text/plain")}

class CodeProjectMainHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        info = self.online_data[self.get_current_user()]
        a_pro = yield db.projects.find_one({"pro_id":CodeProjectId, "status":ProjectStatus["PUBLISH"]})
        if not a_pro:
            self.write('<script>alert("实验未开始");window.history.back()</script>')
            self.finish()
            return
        report_up_record = yield db.user_code_uploads.find_one({"userId": info["userId"], "type":CodeUploadType[EXPREPORT_TYPE], "year":info["yearOfEntry"]})
        code_up_record = yield db.user_code_uploads.find_one({"userId": info["userId"], "type":CodeUploadType[CODE_TYPE], "year":info["yearOfEntry"]})
        bmp_up_record = yield db.user_code_uploads.find_one({"userId": info["userId"], "type":CodeUploadType[BMP_TYPE], "year":info["yearOfEntry"]})
        flag = 0
        if not datetime.now() < datetime.strptime(a_pro['deadline'], '%Y-%m-%d %H:%M:%S')  :
            flag = ProjectStatus["END"]
        else:
            flag = ProjectStatus["PUBLISH"]
        self.render("./template/code-project.html", a_pro=a_pro, info = info, flag=flag,  report_up_record=report_up_record, code_up_record=code_up_record, bmp_up_record=bmp_up_record)
        return

class CodeProjectFetchPicHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self):
        self.write('<script>alert("暂未开通，开通后通知大家");window.location="/code_project"</script>')
        self.finish()
        return

class CodeProjectUploadHandler(BaseHandler):

    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def post(self, type_id):
        # typeid: 0-2
        try:
            type_id = int(type_id)
            if not type_id in CodeUploadType.values():
                    raise ValueError("type %d is not valid" % type_id)
        except ValueError, e:
            print "The argument does not contain correct numbers\n", e
            self.render("./template/404.html")
            return
        info = self.online_data[self.get_current_user()]
        a_pro = yield db.projects.find_one({"pro_id":CodeProjectId,"status":ProjectStatus["PUBLISH"]})

        logger.info("user: %s try to upload file for exp %d in type %d" %(self.get_current_user(), CodeProjectId, type_id))

        up_record = yield db.user_code_uploads.find_one({"type":type_id, "year":info["yearOfEntry"]})

        normal_upload_path=os.path.join(os.path.dirname(__file__),upload_dir, 'report_files',str(CodeProjectId))
        code_upload_path=os.path.join(os.path.dirname(__file__),upload_dir, 'code_files')
        bmp_upload_path=os.path.join(os.path.dirname(__file__),upload_dir, 'bmp_files')
        upload_paths = {"report":normal_upload_path, "code":code_upload_path, "bmp":bmp_upload_path}

        # 创建目录
        for p in upload_paths.values():
            if not os.path.exists(p):
                os.makedirs(p)

        filename = None
        arg_name = None
        if type_id == CodeUploadType[EXPREPORT_TYPE]:
            arg_name = EXPREPORT_TYPE
            filename = str(info["yearOfEntry"]) +"-" + str(CodeProjectId) + "-" + info['userId'] + "-report.pdf"
        elif type_id == CodeUploadType[CODE_TYPE]:
            arg_name = CODE_TYPE
            filename = "hide_" + info['userId'] + ".go"
        elif type_id == CodeUploadType[BMP_TYPE]:
            arg_name = BMP_TYPE
            filename = "m_ucas_" + info['userId'] + ".bmp"
        else:
            self.write('<script>alert("上传错误");window.location="/code_project"</script>')
            self.finish()
            return

        if self.request.files.get(arg_name, None):
            uploadFile = self.request.files[arg_name][0]
            file_size = len(uploadFile['body'])

            # 检测MIME类型
            if not uploadFile["content_type"] in UploadSupportType or not re.match(r'^.*\.' + CodeUploadTypeMap[arg_name][0] + '$',uploadFile['filename'].lower()):
                self.write('<script>alert("仅支持' + CodeUploadTypeMap[arg_name][0] + '格式");window.location="/code_project"</script>')
                self.finish()
                return

            # 检测文件大小
            if  file_size > 10 * 1024 * 1024:
                self.write('<script>alert("请上传10M以下");window.location="/code_project/"</script>')
                self.finish()
                return
            else :
                filepath=os.path.join(upload_paths[arg_name], filename)
                logger.info("user: %s of gruop %s succeed to upload file for exp %d in type %d, file: %s" %(self.get_current_user(), info["userId"], CodeProjectId, type_id, filepath))
                if up_record and os.path.exists(filepath):
                        os.remove(filepath)
                elif not up_record:
                    up_record = {}
                    up_record["year"] = info["yearOfEntry"]
                    up_record["userId"] = info["userId"]
                    up_record["type"] = type_id
                    up_record["name"] = filename
                    up_record["file_suffix"] = filename[filename.rfind(".")+1:]
                up_record["uploadTime"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                up_record["size"] = file_size
                with open(filepath,'wb') as up:
                        up.write(uploadFile['body'])
                yield db.user_code_uploads.save(up_record)
        else:
            self.write('<script>alert("请选择文件");window.history.back()</script>')
            self.finish()
            return
        self.redirect('/code_project')
        return

class CodeProjectDownloadHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, type_id):
        try:
            type_id = int(type_id)
            if not type_id in CodeUploadType.values():
                raise ValueError("type %d is not valid" % type_id)
        except ValueError, e:
            print "The argument does not contain correct numbers\n", e
            self.render("./template/404.html")
            return
        info = self.online_data[self.get_current_user()]
        up_record = yield db.user_code_uploads.find_one({"userId": info["userId"], "type":type_id, "year":info["yearOfEntry"]})
        if not up_record:
            self.render("./template/404.html")
            return
        else:
            if type_id == CodeUploadType[EXPREPORT_TYPE]:
                upload_path = os.path.join(os.path.dirname(__file__), upload_dir, 'report_files', str(CodeProjectId))
                filename = str(info["yearOfEntry"]) +"-" + str(CodeProjectId) + "-" + info['userId'] + "-report.pdf"
                arg_name = EXPREPORT_TYPE
            elif type_id == CodeUploadType[CODE_TYPE]:
                upload_path = os.path.join(os.path.dirname(__file__), upload_dir, 'code_files')
                filename = "hide_" + info['userId'] + ".go"
                arg_name = CODE_TYPE
            else:
                upload_path = os.path.join(os.path.dirname(__file__), upload_dir, 'bmp_files')
                filename = "m_ucas_" + info['userId'] + ".bmp"
                arg_name = BMP_TYPE

            filepath=os.path.join(upload_path,filename)
            if not os.path.exists(filepath):
                self.write('<script>alert("不存在此文件，请重新上传");window.history.back()</script>')
                self.finish()
                return
            with open(filepath, "rb") as f:
                self.set_header('Content-Disposition', 'attachment;filename='+filename)
                self.set_header('Content-Type',CodeUploadTypeMap[arg_name][1])
                self.write(f.read())
            self.finish()
            return
