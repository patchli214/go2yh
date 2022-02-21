#!/usr/bin/env python
# -*- coding:utf-8 -*-
import json,datetime,time,itertools,sys,bson
from mongoengine.queryset.visitor import Q
from go2.settings import BASE_DIR,USER_IMAGE_DIR
from regUser.models import StudentFile
from regUser.forms import PicForm
from operator import attrgetter
from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from regUser.models import *
from teacher.models import *
from gradeClass.views import getDayClasses,Lesson
from tools import http, utils, constant, util2
from tools.utils import checkCookie,getStat,getDateNow,getTeachers,getMessage,dateOfYearMonth,saveTrack
from tools.http import pageVisit
from datetime import timedelta
from __builtin__ import range
from django.template.defaulttags import now
from tools.sign import Sign
from posix import dup
from django.views.decorators.csrf import  csrf_exempt
# Create your views here.

def reg(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    sourceTypes = SourceType.objects.all()
    query = Q(branch=login_teacher.branch)&Q(deleted__ne=1)
    sourceCategory = SourceCategory.objects.filter(query)
    sources = Source.objects.filter(branch=login_teacher.branch).filter(deleted__ne=1)
    teachers = getTeachers(login_teacher.branch)

    branchs = utils.getCityBranch(login_teacher.cityId)
    nb = None
    try:
        nb = Branch.objects.get(id=login_teacher.cityHeadquarter)
    except Exception,e:
        print e
        nb = None

    classTypes = ClassType.objects.all().order_by("sn")
    timeNow = getDateNow(8)
    year = [1,2,3,4,5,6,7,8,9,10,11,12,13]
    month = [1,2,3,4,5,6,7,8,9,10,11]

    student_oid = request.GET.get("student_oid")
    student = None
    studentYear = None
    studentMonth = None
    try:
        student = Student.objects.get(id=student_oid)
        if student.birthday:
            days = (timeNow-student.birthday).days
            y = days/365
            m = days%365/30
            studentYear = y
            studentMonth = m
    except:
        student = None

    return render(request, 'studentReg.html',{"year":year,"month":month,
                                              "nb":nb,
                                              "studentYear":studentYear,
                                              "studentMonth":studentMonth,
                                              "student":student,
                                              "timeNow":timeNow,
                                              "classTypes":classTypes,
                                              "branchs":branchs,
                                              "teachers":teachers,
                                              "sourceTypes":sourceTypes,
                                              "login_teacher":login_teacher,
                                              "sourceCategory":sourceCategory,
                                              "sources":sources})
# 网络部录入简版（用于周末手机录入）
def netReg(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    sources = Source.objects.filter(branch=login_teacher.branch).filter(deleted__ne=1)
    branchs = utils.getCityBranch(login_teacher.cityId)
    classTypes = ClassType.objects.all().order_by("sn")
    return render(request, 'netReg.html',{"branchs":branchs,"sources":sources,
                                              "login_teacher":login_teacher})

#2018 周年庆 广告注册页
def fan(request):
    sourceType = request.GET.get("st")
    sourceCategory = request.GET.get("sc")
    source =  request.GET.get("s")
    branchCode = request.GET.get('branchCode')
    year = [3,4,5,6,7,8,9,10,11,12,13]
    month = [1,2,3,4,5,6,7,8,9,10,11]
    cid = request.GET.get('cid')
    cityId = constant.BEIJING
    try:
        cityId = City.objects.get(id=cid).id
    except:
        cityId = constant.BEIJING
    branches = utils.getCityBranch(cityId)
    return render(request, 'fan.html',{"year":year,"month":month,
                                       "sourceType":sourceType,
                                       "sourceCategory":sourceCategory,
                                       "branches":branches,
                                       "source":source})


#某个用户的转介页面汇总
def referPages(request):

    rid = request.GET.get("rid")
    student = None
    filepath = ''
    nburl = None
    nbqrurl = None
    rrurl = None
    rrqrurl = None
    try:
        student = Student.objects.get(id=rid)
        nburl = '/go2/regUser/rr?st=C&rid='+rid+'&title=n'
        rrurl = '/go2/regUser/rr?st=C&rid='+rid
        nbqrurl = '/go_static/users/' + str(student.branch.id) + '/' + str(student.id) + '/' + 'nbqrcode.jpg'
        rrqrurl = '/go_static/users/' + str(student.branch.id) + '/' + str(student.id) + '/' + 'rrqrcode.jpg'
        userImagePath = BASE_DIR + rrqrurl
        import os.path
        isFile = os.path.isfile(userImagePath)

        if not isFile:

            nbqrurl = utils.makeQrcode(str(student.branch.id), str(student.id), 'nbqrcode.jpg',nburl)
            rrqrurl = utils.makeQrcode(str(student.branch.id), str(student.id), 'rrqrcode.jpg',rrurl)

    except:
        err = 1

    return render(request, 'referPages.html',{"nburl":nburl,"nbqrurl":nbqrurl,"rrurl":rrurl,"rrqrurl":rrqrurl,
                                              "rid":rid,"student":student})


#referal register page
def rr(request):
    title=request.GET.get('title')

    sourceType = request.GET.get("st")
    sourceCategory = request.GET.get("sc")
    source =  request.GET.get("s")
    rid = request.GET.get("rid")
    file_oid = request.GET.get("file_oid")
    filepath = None
    student = None
    try:
        student = Student.objects.get(id=rid)
    except:
        student = None

    if file_oid:
        sf = StudentFile.objects.get(id=file_oid)
        if sf.filepath and sf.filename:
            filepath = USER_IMAGE_DIR+sf.filepath+sf.filename
    branch = None
    try:
        branch = Branch.objects.get(id=student.branch.id)
    except:
        branch = None
    year = [3,4,5,6,7,8,9,10,11,12,13]
    month = [1,2,3,4,5,6,7,8,9,10,11]
    page = "register"
    teacher = None
    if student and student.teacher:
        try:
            teacher = str(student.teacher.id)
        except:
            teacher = None
    if not teacher:
        try:
            teacher = str(student.regTeacher.id)
        except:
            teacher = None
    branchid = None
    if student and student.branch:
        branchid = str(student.branch.id)
    else:
        branchid = request.GET.get("branchid")
    studentid = None
    if not branch:
        try:
            branch = Branch.objects.get(id=branchid)
        except:
            branch = None
    if student:
        studentid = str(student.id)
    ip = http.getVisitIp(request)
    pageVisit(branchid,studentid,teacher,page,ip)

    return render(request, 'rr.html',{"year":year,"month":month,
                                       "rid":rid,
                                       "filepath":filepath,
                                       "student":student,
                                       "branch":branch,
                                       "sourceType":sourceType,
                                       "sourceCategory":sourceCategory,
                                       "branchid":branchid,
                                       "title":title,
                                       "source":source})


def checkIfDup(student,st,s,regBranch,branch,branch2,branch3,branch4):
    #regBranch一方为网络部,一方branch校区，是另一方regBranch校区
    if str(st.regBranch.id) == constant.NET_BRANCH or str(regBranch.id) == constant.NET_BRANCH or str(st.regBranch.id) == constant.NET_BRANCH2 or str(regBranch.id) == constant.NET_BRANCH2:

        if str(st.regBranch.id) == branch or str(regBranch.id) == str(st.branch.id):
            student.dup = -1
        elif str(st.regBranch.id) == branch2:
            student.dup = -1
        elif str(st.regBranch.id) == branch3:
            student.dup = -1
        elif str(st.regBranch.id) == branch4:
            student.dup = -1
    if student.dup == -1:
        student.resolved = -1
        s.resolved = -1
        s.dup = -1
        s.save()
    return student


# register api from referral page
@csrf_exempt
def rer(request):
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    err = 0
    res = ''
    student = Student()
    sourceType = request.POST.get("sourceType")
    sourceCategory = request.POST.get("sourceCategory")
    source = request.POST.get("source")
    referrer = request.POST.get("referrer")
    referTeacherId = request.POST.get("teacher")
    regBranchId = request.POST.get("regBranch")
    branchId = request.POST.get("branch")
    regTeacherId = request.POST.get("regTeacher")
    name = request.POST.get("name")
    prt1mobile = request.POST.get("prt1mobile")
    title = request.POST.get("title")
    test = prt1mobile
    if not prt1mobile:
        test = 'NO prt1mobile!'
    if not name:
        name = 'NO NAME'

    gender = request.POST.get("gender")
    ageYear = request.POST.get("ageYear")
    ageMonth = request.POST.get("ageMonth")
    birthday = None
    if ageYear:
        days = int(ageYear)*365
        if ageMonth:
            days = days+int(ageMonth)*30
        now = getDateNow()
        birthday = now - timedelta(days=days)


    if not branchId:
        branchId = regBranchId
    if not regBranchId:
        regBranchId = branchId
    if not prt1mobile:
        res = u"没有填写手机号"
        err = 1
        return render(request, 'rer.html', {"err":err,"res":res})
    try:
        regBranch = Branch.objects.get(id=regBranchId)
    except:
        regBranch = None
    try:
        branch = Branch.objects.get(id=branchId)
    except:
        branch = None
    students = Student.objects.filter(prt1mobile=prt1mobile)
    status = 0
    dupStatus = 0
    resolved = 0 #无冲突
    if students: #记录已存在
        if len(students) >= 1: #有重复记录

            st = None
            for s in students:
                st = s

            if str(st.branch.id) == regBranchId:#重复记录是本校区的
                res = "手机号:"+prt1mobile+"已经注册过"
                err = 1
                return render(request, 'rer.html', {"err":err,"res":res})
            else:

                student = checkIfDup(student,st,s,regBranch,branchId,None,None,None)


    student.status = status
    #student.dup = dupStatus
    #student.resolved = resolved
    student.regTime = getDateNow()
    student.callInTime = student.regTime

    student.sourceType = sourceType
    try:
        student.sourceCategory = SourceCategory.objects.get(id=sourceCategory)
    except Exception,e:
        student.sourceCategory = None



    if regBranch:
        student.regBranch = regBranch
        student.regBranchName = regBranch.branchName
    if branch:
        student.branch = branch
        student.branchName = branch.branchName
    regTeacher = None
    openIds = []
    try:
        if regTeacherId:
            regTeacher = Teacher.objects.get(id=regTeacherId)
        informTeachers = Teacher.objects.filter(branch=student.regBranch.id).filter(role__gte=5)
        for t in informTeachers:
            if t.openId:
                openIds.append(t.openId)
    except Exception,e:
        a=2
    if regTeacher:
        student.regTeacher = regTeacher
        student.regTeacherName = regTeacher.name

# info
    student.name = name
    student.prt1mobile = prt1mobile
    student.gender = gender
    student.birthday = birthday
    student.referrer = referrer
    referrerName = request.POST.get("refname")
    if not referrerName:
      try:
        refer = Student.objects.get(id=referrer)
        if refer:
            referrerName = "["+refer.branchName+']'+refer.name
            if refer.name2:
                referrerName = referrerName + "("+refer.name2+')'
      except:
        referrerName = None


    student.referrerName = referrerName
    referTeacher = None
    referTeacherName = None
    try:
        referTeacher = Teacher.objects.get(id=referTeacherId)
        if referTeacher:
            student.regTeacher = referTeacher
            referTeacherName = referTeacher.name
            student.regTeacherName = referTeacherName
    except Exception,e:
        print e
        referrerName = None


    if source:
        try:
            ss = Source.objects.get(id=source)
            student.source = ss
        except:
            student.source = None
    if title == 'newbee':
        student.memo = '暑期启蒙班1680'
    print student.regBranch
    student.save()
    teachers = Teacher.objects.filter(branch=student.branch).filter(role=5)
    if len(teachers) == 0:
        teachers = Teacher.objects.filter(branch=student.branch).filter(role=7)
    now = getDateNow()
    std = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 12:00','%Y-%m-%d %H:%M')

    if now > std:
        now = now + timedelta(days=1)

    saveRemind(None,student,teachers,now,u'新转介',None)
    referrerName = ''
    try:
        referrerName = Student.objects.get(id=student.referrer).name
    except:
        referrerName = None

    return render(request, 'rer.html', {"err":err,"res":res,
                                        "referrerName":referrerName,
                                        "student": student,
                                        "openIds":openIds})

def regFromWxProg(request):
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    err = 0
    res = ''
    student = Student()

    name = request.POST.get("name")
    prt1mobile = request.POST.get("prt1mobile")
    branchCode = request.POST.get("code")
    sourceType = request.POST.get("sourceType")
    sourceCategory = request.POST.get("sourceCategory")
    source = request.POST.get("source")
    branch = None
    try:
        branch = Branch.objects.get(branchCode=branchCode)
    except:
        branch = None
    test = prt1mobile
    if not prt1mobile:
        test = 'NO prt1mobile!'
    if not name:
        name = 'NO NAME'
    #utils.save_log('/data/log/go.log', test)
    if not branchCode:
        branchCode = 'NO BRANCH'
    if branch:
        utils.save_log('/data/log/go.log', branch.branchCode+','+prt1mobile)

    if not prt1mobile:
        res = u"没有填写手机号"
        err = 1
        result = {"err":err,"res":res}
        return http.JSONResponse(json.dumps(result, ensure_ascii=False))
    query = Q(prt1mobile=prt1mobile)
    if branch:
        query = query&Q(branch=branch.id)
    students = Student.objects.filter(query)
    status = 0
    dupStatus = 0
    resolved = 0 #无冲突
    if students: #记录已存在
      if len(students) >= 1: #有重复记录
            res = "手机号:"+prt1mobile+"已经注册过"
            err = 1
            result = {"err":err,"res":res}
            return http.JSONResponse(json.dumps(result, ensure_ascii=False))

    if branch:
        student.branch = branch
        student.branchName = branch.branchName
    if sourceType:
        student.sourceType = sourceType
    if sourceCategory:
        try:
            sc = SourceCategory.objects.get(id=sourceCategory)
        except:
            sc = None
        if sc:
            student.sourceCategory = sc
    if source:
        try:
            so = Source.objects.get(id=source)
        except:
            so = None
        if so:
            student.source = so
    student.regTime = getDateNow(8)
    student.callInTime = student.regTime

# info
    student.name = name
    student.prt1mobile = prt1mobile

    student.status = 0
    student.save()
    result = {'err':'0'}
    url = 'http://jieli360.cn/api/message'
    query = Q(branch=branch)&Q(role__gt=3)&Q(status__ne=-1)
    teachers = Teacher.objects.filter(query)
    if so and sc:
        first = sc.categoryName+so.sourceName + u'预约'
        keyword1 = u'真朴围棋'
        keyword2 = name
        keyword3 = prt1mobile
        keyword5 = branch.branchName + u'校区'
        for t in teachers:

            if t.openId and len(t.openId) > 10:# and t.openId == 'oRcnlt2T_M0N8ohsHTcoAPiQCtO0':
                _data = { 'openId': t.openId,'first': first ,'keyword1':keyword1,'keyword2':keyword2,'keyword3':keyword3,'keyword4':'keyword4','keyword5':keyword5,'url':'http://www.go2crm.cn' }
                res = http.http_post(url, _data)
                utils.save_log('/data/log/go.log', res)
    return http.JSONResponse(json.dumps(result, ensure_ascii=False))


# standard register api
def api_reg(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.POST.get("student_oid")
    student = Student()
    code = request.POST.get("code")
    sourceType = request.POST.get("sourceType")
    probability = request.POST.get("probability")
    sourceCategory = request.POST.get("sourceCategory")
    source = request.POST.get("source")
    referrerName = request.POST.get("referrerName")
    referrer = request.POST.get("referrer")
    referTeacher = request.POST.get("referTeacher")
    referTeacherName = request.POST.get("referTeacherName")
    regBranchId = request.POST.get("regBranch")
    branch = request.POST.get("branch")
    regTeacherId = request.POST.get("regTeacher")
    teacherId = request.POST.get("teacher")
    co_teacher = request.POST.get("co_teacher")
    callInTime_str = request.POST.get("callInTime")
    name = request.POST.get("name")
    name2 = request.POST.get("name2")
    siblingName = request.POST.get("siblingName")
    siblingName2 = request.POST.get("siblingName2")
    siblingName3 = request.POST.get("siblingName3")
    prt1mobile = request.POST.get("prt1mobile")
    prt1 = request.POST.get("prt1")
    prt2mobile = request.POST.get("prt2mobile")
    prt2 = request.POST.get("prt2")
    wantClass = request.POST.get("wantClass")
    gender = request.POST.get("gender")
    ageYear = request.POST.get("ageYear")
    ageMonth = request.POST.get("ageMonth")
    memo = request.POST.get("memo")
    demoTime = request.POST.get("demoTime")
    branch2 = request.POST.get("branch2")
    branch3 = request.POST.get("branch3")
    branch4 = request.POST.get("branch4")
    birthdayStr = request.POST.get("birthday")
    netStatusStr = request.POST.get("netStatus")
    kindergarten = request.POST.get("kindergarten")
    school = request.POST.get("school")
    Bsub = request.POST.get("Bsub")


    branchOri = None
    if student_oid:
        try:
            student = Student.objects.get(id=student_oid)
            branchOri = student.branch
        except:
            res = {"error": 2, "msg": "未找到要修改的孩子"}

    track_txt = None
    openIds = []
    weixin = 0 #1-转校区,2-网络部分配
    toSendMessage = False
    if branch and student and student.branch and branch != str(student.branch.id):

        query = Q(id=student.gradeClass)
        student.gradeClass = None
        hisGcs = GradeClass.objects.filter(query)
        try:
            hisGc = hisGcs[0]
            sss = hisGc.students
            temp = []
            for ss in sss:
                if str(ss.id) != str(student.id):
                    temp.append(ss)
            hisGc.students = temp
            hisGc.save()
        except Exception,e:
            err = 1
        if login_teacher.branchType == '1':
            weixin = 0
        else:
            toSendMessage = True
            weixin = 1
            addTrack = True
            trackId = None
            trackTime = None
            toBranchName = Branch.objects.get(id=branch).branchName
            track_txt = u'转校区：【'+student.branchName+u"】转到【"+toBranchName+u'】'+student.name+'-'+student.prt1mobile

    birthday = None
    if not birthdayStr and ageYear:
        days = int(float(ageYear))*365+int(float(ageMonth))*30
        now = getDateNow()
        birthday = now - timedelta(days=days)
    if birthdayStr:
        try:
            birthday = datetime.datetime.strptime(birthdayStr,"%Y-%m-%d")
        except:
            birthday = None

    netStatus = 0
    if netStatusStr:
        try:
            netStatus = int(netStatusStr)
        except:
            netStatus = 0
    if not prt1mobile:
        res = {"error": 1, "msg": "请填写电话"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    status = 0
    regBranch = None
    try:
        regBranch = Branch.objects.get(id=regBranchId)
    except:
        regBranch = None

    if (student.resolved != 1 and student.resolved != 0) or (student and student.branch and str(student.branch.id) != branch):
      students = Student.objects.filter(prt1mobile=prt1mobile)

      dupTel = prt1mobile
      if students.count() < 1:
        students = Student.objects.filter(prt2mobile=prt1mobile)
        if students.count() < 1 and prt2mobile and len(prt2mobile) > 7:
            dupTel = prt2mobile
            students = Student.objects.filter(prt1mobile=prt2mobile)
            if students.count() < 1:
                students = Student.objects.filter(prt2mobile=prt2mobile)

        # add trace record

      resolved = 0 #无冲突
      dupStatus = 0
      if students: #记录已存在
        if student_oid: #是从修改页面来的保存请求
            temp = []
            for s in students:
                if str(s.id) != student_oid:
                    temp.append(s)
            students = temp

        if len(students) >= 1: #有重复记录
            st = None
            for s in students:
                st = s
                if regBranch and st.regBranch:
                  if str(st.regBranch.id) == str(regBranch.id):#重复记录是本校区的
                      res = {"error": 1, "msg": u"手机号:"+dupTel+u"已经注册过"}
                      return http.JSONResponse(json.dumps(res, ensure_ascii=False))
                  else:
                      student = checkIfDup(student,st,s,regBranch,branch,branch2,branch3,branch4)
        else:
            student.dup = 0
#source
    if not probability:
        probability = 'A'
    student.probability = probability
    if probability == 'C':
        student.cdate = getDateNow()
    if not student_oid:
        student.status = status

    student.memo = memo
    try:
        student.callInTime = datetime.datetime.strptime(callInTime_str,"%Y-%m-%d %H:%M")
    except:
        student.callInTime = None
    if not student_oid:
        student.regTime = getDateNow()
        if not student.callInTime:
            student.callInTime = student.regTime

    if demoTime:
        student.wantDemoTime = datetime.datetime.strptime(demoTime,"%Y-%m-%d %H:%M")
    if sourceType and len(sourceType)>0:
        student.sourceType = sourceType
    try:
        student.sourceCategory = SourceCategory.objects.get(id=sourceCategory)
    except Exception,e:
        errermsg = 1

    if regBranch:
        student.regBranch = regBranch
        student.regBranchName = regBranch.branchName
    student.inTeacher = Teacher.objects.get(id=login_teacher.id)
    regTeacher = None
    teacher = None
    try:
        regTeacher = Teacher.objects.get(id=regTeacherId)
    except:
        regTeacher = None
    if regTeacher:
        student.regTeacher = regTeacher
        student.regTeacherName = regTeacher.name
    else:
        student.regTeacher = None
        student.regTeacherName = None
    try:
        teacher = Teacher.objects.get(id=teacherId)
    except:
        a=3
    if teacher:
        student.teacher = teacher
        student.teacherName = teacher.name
    co = []
    if co_teacher:
        if len(co_teacher)>0:
            ts = co_teacher.split(",")
            for tid in ts:
                try:
                    tes = Teacher.objects.filter(name=tid).filter(branch=login_teacher.branch)
                    if len(tes)>0:
                        te = tes[0]
                        co.append(te)
                except:
                    te = None
    student.co_teacher = co

# info
    student.name = name
    student.prt1 = prt1
    student.prt1mobile = prt1mobile
    student.prt2 = prt2
    student.prt2mobile = prt2mobile
    student.name2 = name2


    sib1 = student.siblingName
    sib2 = student.siblingName2
    sib3 = student.siblingName3

    student.siblingName = siblingName
    student.siblingName2 = siblingName2
    student.siblingName3 = siblingName3


    if not siblingName and not siblingName2 and not siblingName3:
        query = Q(siblingId=str(student.id))
        try:
            ss = Student.objects.filter(query)
            if ss and len(ss) > 0:
                for s in ss:
                    query = Q(student=str(s.id))&Q(checked=True)
                    siblessons = Lesson.objects.filter(query)  # @UndefinedVariable
                    if siblessons and len(siblessons) > 0:
                        student.siblingName = sib1
                    else:
                        s.delete()
        except Exception,e:
            print e
            err = 1

        student.gender = gender
    student.birthday = birthday
    if referrer and len(referrer)>0:
        student.referrer = referrer
    if referrerName and len(referrerName)>0:
        student.referrerName = referrerName
    if referTeacherName and len(referTeacherName)>0:
        student.referTeacherName = referTeacherName
    if referTeacher and len(referTeacher)>0:
        student.referTeacher = referTeacher
    student.wantClass = wantClass
    student.kindergarten = kindergarten
    student.school = school
    student.Bsub = Bsub
    ss = None
    if source:
        try:
            ss = Source.objects.get(id=source)
            student.source = ss

        except:
            err = 1#student.source = None


    try:
        branch = Branch.objects.get(id=branch)
        if branch:
            student.branch = branch
            student.branchName = branch.branchName
    except:
        branch = None
    try:
      if branch2:
        student.branch2 = branch2
        student.branch2name = Branch.objects.get(id=branch2).branchName
      elif student_oid:
          student.branch2 = None
          student.branch2name = None
      if branch3:
        student.branch3 = branch3
        student.branch3name = Branch.objects.get(id=branch3).branchName
      elif student_oid:
          student.branch3 = None
          student.branch3name = None
      if branch4:
        student.branch4 = branch4
        student.branch4name = Branch.objects.get(id=branch4).branchName
      elif student_oid:
          student.branch4 = None
          student.branch4name = None
    except Exception,e:
        print e
    contracts = student.contract
    contractStatus = 0
    if contracts:
        for c in contracts:
            try:
                cstatus = c.status
            except:
                c.status = 0
            if c.status == 0:
                contractStatus = 1
                break
    student.status = contractStatus
    student.netStatus = netStatus
    if code and len(code)>0:
        student.code = code

    student.save()

    saveSibling(student)

    res = {"error": 0, "msg": "注册成功"}

    if branch and student.regBranch:
        if student.regBranch.type == 1:
            if login_teacher.branchType == '1':
                if branch.sn != regBranch.sn:
                    trackId = None
                    trackTime = None
                    if not student_oid:
                        track_txt = regBranch.branchName+u'新推送'
                        addTrack = True
                        weixin = 2
                    elif not branchOri and branch or branchOri.id != branch.id:
                        track_txt = regBranch.branchName+u'新分配'
                        addTrack = True
                        weixin = 2
    if weixin > 0:
        #send 微信 to 校区运营
        res = saveTrack(addTrack,student,trackId,trackTime,login_teacher.id,track_txt)
        trackInformTeachers = Teacher.objects.filter(branch=branch).filter(role__gt=3)
        if trackInformTeachers and len(trackInformTeachers)>0:
            for t in trackInformTeachers:
                if t.openId:
                    openIds.append(t.openId)
        #create remind for 分配校区
        if True:
            remindTime = getDateNow()
            remTeacher = None
            try:
                query = Q(branch=student.branch)&Q(role=5)&Q(status__gt=-1)
                remTeacher = Teacher.objects.filter(query)[0]
            except:
                remTeacher = None
            if not remTeacher:
                query = Q(branch=student.branch)&Q(role=7)&Q(status__gt=-1)
                remTeacher = Teacher.objects.filter(query)[0]
            teacher_list = []
            teacher_list.append(remTeacher)

            saveRemind(None,student,teacher_list,remindTime,track_txt,0)

    if toSendMessage:
        query = Q(branch=student.branch)&Q(role__gt=3)&Q(role__lt=8)&Q(status__ne=-1)
        toTeachers = Teacher.objects.filter(query)
        url = '/go2/regUser/studentInfo/'+str(student.id)+'/'
        for t in toTeachers:
            utils.sendMessage(login_teacher.branchName,login_teacher.id, login_teacher.teacherName, str(t.id), track_txt, None, url)
    demos = []
    gradeClass = None
    try:
        birthday = student.birthday
        if birthday:
            days = (getDateNow()-birthday).days
            y = days/365
            m = days%365/30
            student.yearMonth = str(y)+'岁'+str(m)+'个月'

        if student.gradeClass:
            gradeClass = GradeClass.objects.get(id=student.gradeClass)

        if student.demo:
            for demo_oid in student.demo:
                d = GradeClass.objects.get(id=demo_oid)
                if d:
                    demos.append(d)

    except Exception,e:
        errermsg = 1


    return render(request, 'afterreg.html', {"student": student,
                                             "track_txt":track_txt,
                                             "openIds":openIds})

def saveSibling(student):
    if student.siblingName and len(student.siblingName)>0:
        sibling = None
        query = Q(siblingId=str(student.id))&Q(siblingName__ne=None)&Q(siblingName__ne='')
        try:
            sibling = Student.objects.get(query)
        except:
            sibling = Student(siblingId=str(student.id))
        sibling.name = student.siblingName
        sibling.siblingName = student.name
        if student.name2:
            sibling.siblingName = sibling.siblingName+'('+student.name2+')'
        if student.teacher:
            sibling.teacher = student.teacher
        sibling.branch = student.branch
        sibling.status = student.status
        sibling.deleted = False
        sibling.save()
    else:
        query = Q(siblingId=str(student.id))&Q(siblingName__ne=None)&Q(siblingName__ne='')
        try:
            sibling = Student.objects.get(query)
            sibling.deleted = True
            sibling.save()
        except:
            sibling = None
    if student.siblingName2 and len(student.siblingName2)>0:
        sibling = None
        query = Q(siblingId=str(student.id))&Q(siblingName2__ne=None)&Q(siblingName2__ne='')
        try:
            sibling = Student.objects.get(query)
        except:
            sibling = Student(siblingId=str(student.id))
        sibling.name = student.siblingName2
        sibling.siblingName2 = student.name
        if student.name2:
            sibling.siblingName2 = sibling.siblingName2+'('+student.name2+')'
        if student.teacher:
            sibling.teacher = student.teacher
        sibling.branch = student.branch
        sibling.status = student.status
        sibling.save()
    else:
        query = Q(siblingId=str(student.id))&Q(siblingName2__ne=None)&Q(siblingName2__ne='')
        try:
            sibling = Student.objects.get(query)
            sibling.deleted = True
            sibling.save()
        except:
            sibling = None
    if student.siblingName3 and len(student.siblingName3)>0:
        sibling = None
        query = Q(siblingId=str(student.id))&Q(siblingName3__ne=None)&Q(siblingName3__ne='')
        try:
            sibling = Student.objects.get(query)
        except:
            sibling = Student(siblingId=str(student.id))
        sibling.name = student.siblingName3
        sibling.siblingName3 = student.name
        if student.name2:
            sibling.siblingName3 = sibling.siblingName3+'('+student.name2+')'
        if student.teacher:
            sibling.teacher = student.teacher
        sibling.branch = student.branch
        sibling.status = student.status
        sibling.save()
    else:
        query = Q(siblingId=str(student.id))&Q(siblingName3__ne=None)&Q(siblingName3__ne='')
        try:
            sibling = Student.objects.get(query)
            sibling.deleted = True
            sibling.save()
        except:
            sibling = None
    return

def saveRemind(teacherRemind,student,teachers,remindTime,txt,done):
    if not student:
        return
    reminds = TeacherRemind.objects.filter(student=student.id)
    for r in reminds:
        r.delete()
    teacherRemind = TeacherRemind(student=student)
    if not remindTime:
        remindTime = getDateNow()

    teacherRemind.remindTime = remindTime
    teacherRemind.remindTeachers = teachers
    teacherRemind.remind_txt = txt
    teacherRemind.isDone = done
    if student.branch:
        teacherRemind.branch = str(student.branch.id)
    else:
        teacherRemind.branch = str(student.regBranch.id)
    if student.regBranch:
        teacherRemind.regBranch = str(student.regBranch.id)
    teacherRemind.save()
    student.remind_txt = txt
    student.remindTime = remindTime
    student.remindTeacher = teachers[0]
    student.remindTeacherName = teachers[0].name
    student.isDone = done
    student.save()
    return

#某一号码全部的冲突客户
def getDupByTel(student,resolved=None):
    query = None
    if resolved == 0:
        query = Q(resolved=resolved)#&Q(id__ne=student.id)
    else:
        query = Q(resolved__ne=0)#&Q(id__ne=student.id)
    queryTel = Q(prt1mobile=student.prt1mobile)|Q(prt2mobile=student.prt1mobile)
    if student.prt2mobile and len(student.prt2mobile) > 5:
        queryTel = queryTel|Q(prt1mobile=student.prt2mobile)|Q(prt2mobile=student.prt2mobile)
    query = query&(queryTel)
    d1 = Student.objects.filter(query)

    return d1

#冲突解决第一步：单边解决
def resolve0_api(request):

    mainurl = request.COOKIES.get('mainurl','')
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    sid = request.POST.get("sid")
    track_txt = request.POST.get("track_txt")
    student = Student()
    if request.method == 'POST':

        try:
            student = Student.objects.get(id=sid)
            student.resolved = -2
            student.resolver = Teacher.objects.get(id=login_teacher.id)
            student.save()
            saveTrack(1,student,None,utils.getDateNow(),login_teacher.id,track_txt,1)
            d1 = getDupByTel(student)

            for s in d1:
                if s.id != student.id:
                    s.resolved = -3
                else:
                    s.resolved = -2
                s.save()

        except Exception,e:
            print e
            student = None
        mainurl = request.COOKIES.get('mainurl','')
        res = {"error": 0, "msg": u'已提交解决，等待对方同意',"url":mainurl}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))


def resolve0(request):
    mainurl = request.COOKIES.get('mainurl','')
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    student = Student()
    dups = None
    prt1mobile = request.GET.get("prt1mobile")
    dups = Student.objects.filter(prt1mobile=prt1mobile)
    return render(request, 'resolve0.html', {"dups": dups})

#解决冲突等待对方同意的数量查询，用于页面badge No，显示
def resolveToDo_api(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    num = 0
    temp = []
    try:
        query = Q(regBranch=login_teacher.branch)&(Q(resolved=-2)|Q(resolved=-3))
        dups = Student.objects.filter(query)

        for s in dups:
            qu = Q(prt1mobile=s.prt1mobile)|Q(prt2mobile=s.prt1mobile)
            if s.prt2mobile and len(s.prt2mobile) > 5:
                qu = qu|Q(prt1mobile=s.prt2mobile)|Q(prt2mobile=s.prt2mobile)
        #重复号码的全部客户
            all = Student.objects.filter(qu)
            if len(all) > 1:
                temp.append(s)

        num = len(temp)

    except Exception,e:
        print e
    res = {"error": 0, "num": num}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

#冲突解决第二步：对方同意后解决
def resolve_api(request):
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student = Student()
    nameall = None

    if request.method == 'POST':
        resolved = request.POST.get("resolved")
        prt1mobile = request.POST.get("prt1mobile")
        validStudent = request.POST.get("validStudent")

        try:
            student = Student.objects.get(id=validStudent)
        except:
            err = 1
        dups = getDupByTel(student)
        if resolved == '-1':
          try:
            student.resolved = -1
            student.resolver = None
            student.save()
            d1 = dups
            for s in d1:
                s.resolved = -1
                s.save()
          except Exception,e:
            print e
          res = {"error": 0, "msg": "不同意对方请求，请继续协商"}
          return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        informBranch = None #接受微信消息方
        informBranches = [] #双方
        text = None

        track_txt = None
        prt1mobile = None
        branchName = None
        url = ''
        track_txt2 = ''
        remindTime = getDateNow(8)
        for s in dups:
            sid = None
            try:
                sid = s.regBranch.id
            except:
                try:
                    sid = s.branch.id
                except:
                    sid = None

            if sid not in informBranches:
                informBranches.append(sid)
            if str(sid) != str(login_teacher.branch):
                #student = s
                informBranch = sid
                code = None
                if not s.code:
                    code = ''
                else:
                    code = s.code + '|'
                name = None
                if not s.name:
                     name = ''
                else:
                    name = s.name + '-'
                name2 = None
                if not s.name2:
                     name2 = ''
                else:
                    name2 = s.name2 + '-'
                nameall = name + name2
                prt1mobile = s.prt1mobile
                if s.regBranchName:
                    branchName = s.regBranchName
                elif s.regBranchName:
                    branchName = s.fromBranchName
                else:
                    branchName=''
                track_txt = nameall + s.prt1mobile + u'解决冲突'
                track_txt2 = u'[保留' + student.regBranchName + u']'
                track_txt  = track_txt + track_txt2
                url = '/go2/regUser/studentInfo/'+str(s.id)+'/'
            if str(s.id) == validStudent:
                if s.dup == -1:
                    s.dup = 0
                s.resolved = 0

            else:
                s.dup = -1
                s.resolved = 0
                saveTrack(1,s,None,utils.getDateNow(8),login_teacher.id,track_txt,1)
            s.save()
        if student:
          student.name = nameall
          student.prt1mobile = prt1mobile
          #student.regBranchName = branchName


          saveTrack(1,student,None,utils.getDateNow(8),login_teacher.id,track_txt,1)
          i = 0
          query = None
          for b in informBranches:
            if i == 0:
                query = Q(branch=b)
            else:
                query = query|Q(branch=b)
            i = i + 1
          query = (query)&Q(role__gt=3)&Q(role__lt=8)&Q(status__ne=-1)
          allTeachers = Teacher.objects.filter(query)
          query = Q(branch=informBranch)&Q(role__gt=3)&Q(role__lt=8)&Q(status__ne=-1)
          toTeachers = Teacher.objects.filter(query)

          for t in allTeachers:
            utils.sendMessage(login_teacher.branchName,login_teacher.id, login_teacher.teacherName, str(t.id), track_txt, None, url)

        res = {"error": 0, "msg": "重复号码已解决"}

        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        #render(request, 'afterResovle.html', {"openIds": openIds,"login_teacher":login_teacher,"track_txt":track_txt,"student":student})
        #return HttpResponseRedirect('/go2/regUser/studentList')


def dboard(request):
    login_teacher = checkCookie(request)
    login = request.GET.get('login')
    if constant.DEBUG:
        print 'dboard'
        login
    if not login_teacher:
        if constant.DEBUG:
            print 'login_teacher is None'
        return HttpResponseRedirect('/go2/login')
    else:
        return render(request, 'dboard.html',{"login_teacher":login_teacher,'login':login,"NET_BRANCH":constant.NET_BRANCH})

# today remind
def dboard1(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    millis0 = int(round(time.time() * 1000))
    beginMillis = millis0
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    teachers = []

    queryTime = Q(remindTime__gte=todayBegin)&Q(remindTime__lte=todayEnd)
    query = (Q(regBranch=login_teacher.branch)|Q(branch=login_teacher.branch))&queryTime
    qt = None
    if login_teacher.branchType != constant.BranchType.school:
        teachers = getTeachers(login_teacher.branch)
        i = 0

        for t in teachers:
            if i == 0:
                qt = Q(remindTeacher=t.id)
            else:
                qt = qt|Q(remindTeacher=t.id)
            i = i + 1

    if qt:

        query = query&(qt)
    remindstudents = Student.objects.filter(query).order_by("-regTime")

    temp = []
    stemp = []

    if login_teacher.branchType != '1':
        year = int(now.strftime("%Y"))
        date = now.strftime("%m-%d")
        print '------------------------YEAR DATE--------------------'
        print year
        print date
        query = Q(branch=login_teacher.branch)&Q(status=1)
        q2 = None
        leap = 0
        if year%100 == 0:
                if year%4 == 0:
                    print '400 leap-------------'
                    leap = 1
        elif year%4 == 0:
                print '4 leap-------------'

                leap = 1
        print 'IF LEAP?--------'
        print leap
        for i in range(15):
            y = year - i
            thatleap = 0
            if y%100 == 0:
                if y%4 == 0:
                    print '400 leap-------------'
                    thatleap = 1
            elif y%4 == 0:
                print '4 leap-------------'
                thatleap = 1
            print 'THAT LEAP----'
            print y
            print thatleap
            if leap == 0 or (leap == 1 and thatleap == 1):

                try:
                  begin = datetime.datetime.strptime(str(y)+'-'+date+' 00:00:00',"%Y-%m-%d %H:%M:%S")
                  end = begin + timedelta(days=1)
                  if i == 0:
                    q2 = (Q(birthday__gte=begin)&Q(birthday__lt=end))
                  else:
                    q2 = q2|(Q(birthday__gte=begin)&Q(birthday__lt=end))
                except Exception,e:
                    print e
                    print y
                    print date
        query = query&(q2)
        students = Student.objects.filter(query).order_by("birthday")
        #print students._query
        for s in students:
            s.memo = ''

            s.remind_txt = u'生日'
            try:
                        days = (now-s.birthday).days
                        y = days/365
                        m = days%365/30
                        s.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            s.yearMonth = str(y)
            except:
                        err = 1
            temp.append(s)
    for s in remindstudents:

            try:
                        days = (now-s.birthday).days
                        y = days/365
                        m = days%365/30
                        s.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            s.yearMonth = str(y)
            except:
                        err = 1
            temp.append(s)
    reminds = temp

    millis0 = int(round(time.time() * 1000))
    endMillis = millis0
    if constant.DEBUG:
        print '[board1]'+str(endMillis-beginMillis)+' ms'
    response = render(request, 'dboard1.html', {"now":now,"reminds":reminds,"login_teacher":login_teacher})
    response.set_cookie("mainurl",'/go2/regUser/dboard1')
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response


# today remind
def dboard1a(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    millis0 = int(round(time.time() * 1000))
    beginMillis = millis0
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    teachers = []
    if login_teacher.branchType == '1':
        teachers = getTeachers(login_teacher.branch)
    queryTime = Q(remindTime__gte=todayBegin)&Q(remindTime__lte=todayEnd)
    reminds = TeacherRemind.objects.filter(queryTime).order_by("branch")
    temp = []
    stemp = []

    for r in reminds:
        y = False
        ts = []
        try:
            if r.student and r not in temp and r.student not in stemp:
                if r.branch == login_teacher.branch:
                    if login_teacher.role > 3 or str(r.student.regBranch.id) == login_teacher.branch:
                        y = True
                else:
                    for t in teachers:
                        for rt in r.remindTeachers:
                            if t.name == rt.name:
                                y = True
                                break
                        if y:
                            break

                if y:
                    r.regTime = r.student.regTime
                    try:
                        days = (getDateNow()-r.student.birthday).days
                        y = days/365
                        m = days%365/30
                        r.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            r.yearMonth = str(y)
                    except:
                        err = 1

                    if r.student.memo:
                        r.student.memo = u'【备注】'+r.student.memo
                    else:
                        r.student.memo = u'【备注】'
                    #===========================================================
                    # tq = Q(student=r.student.id)&Q(track_txt__ne=u'总部新推送')&Q(track_txt__ne=u'总部新分配')&Q(deleted__ne=1)
                    # tracks = StudentTrack.objects.filter(tq).order_by("trackTime")
                    # if tracks and len(tracks)>0:
                    #     for track in tracks:
                    #         r.student.memo = "["+track.trackTime.strftime('%Y%m%d')+"]"+track.track_txt+r.student.memo
                    #===========================================================

                    for t in r.remindTeachers:
                        if str(t.branch.id) == login_teacher.cityHeadquarter:
                            t.name = u'网络部'
                        ts.append(t)
                    r.remindTeachers = ts
                    temp.append(r)
                    stemp.append(r.student)
        except Exception,e:
            print e
            a = 1

    reminds = temp
    try:
        if login_teacher.branchType != '1':
            reminds = sorted(temp, key=attrgetter('regTime'),reverse=True)
    except:
        reminds = temp

    if login_teacher.branchType != '1':
        year = int(now.strftime("%Y"))
        date = now.strftime("%m-%d")
        query = Q(branch=login_teacher.branch)&Q(status=1)
        q2 = None
        for i in range(15):
            y = year - i
            begin = datetime.datetime.strptime(str(y)+'-'+date+' 00:00:00',"%Y-%m-%d %H:%M:%S")
            end = begin + timedelta(days=1)
            if i == 0:
                q2 = (Q(birthday__gte=begin)&Q(birthday__lt=end))
            else:
                q2 = q2|(Q(birthday__gte=begin)&Q(birthday__lt=end))
        query = query&(q2)
        students = Student.objects.filter(query).order_by("birthday")
        temp = []
        for s in students:
            s.memo = ''
            remind = TeacherRemind(student=s)
            remind.remind_txt = u'生日'
            try:
                        days = (now-remind.student.birthday).days
                        y = days/365
                        m = days%365/30
                        remind.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            remind.yearMonth = str(y)
            except:
                        err = 1
            temp.append(remind)
        for r in reminds:
            temp.append(r)
        reminds = temp
    millis0 = int(round(time.time() * 1000))
    endMillis = millis0
    if constant.DEBUG:
        print '[board1]'+str(endMillis-beginMillis)+' ms'
    response = render(request, 'dboard1.html', {"now":now,"reminds":reminds,"login_teacher":login_teacher})
    response.set_cookie("mainurl",'/go2/regUser/dboard1')
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response


#remind not done
def dboard2(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    monthBegin = datetime.datetime.strptime(now.strftime("%Y-%m")+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    weekBegin = todayBegin - timedelta(days=todayBegin.weekday())
    lastWeekBegin = weekBegin - timedelta(days=7)
    lastWeekEnd = weekBegin - timedelta(days=1)
    query = Q(branch=login_teacher.branch)
    query = query&Q(remindTime__lt=todayBegin)&Q(isDone__ne=1)

    teachers = getTeachers(login_teacher.branch)

    if login_teacher.branchType == '1':
        query = Q(regBranch=login_teacher.branch)&Q(remindTime__lt=todayBegin)&Q(isDone__ne=1)
        qq = None
        i = 0
        for t in teachers:
            if i == 0:
                qq = Q(remindTeachers__contains=t.id)
            else:
                qq = qq|Q(remindTeachers__contains=t.id)
            i = i + 1
        query = query&(qq)



    reminds = TeacherRemind.objects.filter(query).order_by("-remindTime")

    temp = []
    stemp = []

    if login_teacher.branchType == '1':
      for r in reminds:
        y = False #是否自己校区老师的提醒
        try:
            if r.student and r not in temp and r.student not in stemp:
                if r.branch == login_teacher.branch:
                    if login_teacher.role > 3 or str(r.student.regBranch.id) == login_teacher.branch:
                        y = True
                else:
                    for t in teachers:
                        for rt in r.remindTeachers:
                            if t.id == rt.id:
                                y = True
                                break
                        if y:
                            break

                if y:
                    try:
                        r.student.prt1mobile = r.student.prt1mobile.replace(';',' ')
                    except Exception,e:
                        err = 1
                    r.regTime = r.student.regTime
                    try:
                        days = (getDateNow()-r.student.birthday).days
                        y = days/365
                        m = days%365/30
                        r.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            r.yearMonth = str(y)
                    except:
                        err = 1


                    if r.student.memo:
                        r.student.memo = u'【备注】'+r.student.memo
                    else:
                        r.student.memo = u'【备注】'
                    #===========================================================
                    # tq = Q(student=r.student.id)&Q(track_txt__ne=u'总部新推送')&Q(track_txt__ne=u'总部新分配')&Q(deleted__ne=1)
                    # tracks = StudentTrack.objects.filter(tq).order_by("trackTime")
                    # if tracks and len(tracks)>0:
                    #     for track in tracks:
                    #         r.student.memo = "["+track.trackTime.strftime('%Y%m%d')+"]"+track.track_txt+r.student.memo
                    #===========================================================
                    ts = []
                    for t in r.remindTeachers:
                        if str(t.branch.id) == login_teacher.cityHeadquarter:
                            t.name = u'网络部'
                        ts.append(t)
                    r.remindTeachers = ts
                    temp.append(r)
                    stemp.append(r.student)
        except Exception,e:
            print e
            a = 1

    else:
        j = 0
        i = 0
        k = 0
        for r in reminds:
            try:
                if r.student:
                    try:
                        days = (getDateNow()-r.student.birthday).days
                        y = days/365
                        m = days%365/30
                        r.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            r.yearMonth = str(y)
                    except:
                        err = 1
                    k = k + 1
                    if login_teacher.role > 3:
                        temp.append(r)
                        j+=1
                    elif login_teacher.role == 3 and str(r.student.regBranch.id) == login_teacher.branch:
                        temp.append(r)
                        j+=1
                    else:
                        i+=1
                    #===========================================================
                    # if login_teacher.role == 3 and (str(r.student.regTeacher.id) == login_teacher.id or not r.student.regTeacher or r.student.regTeacher.status == -1):
                    #     temp.append(r)
                    #     j = j + 1
                    # elif login_teacher.role == 3 and r.student.co_teacher and str(r.student.co_teacher) > 0:
                    #     for cot in r.student.co_teacher:
                    #         if str(cot.id) == login_teacher.id:
                    #             temp.append(r)
                    #             j = j + 1
                    # elif login_teacher.role > 3:
                    #    temp.append(r)
                    #    j = j + 1
                    #===========================================================
                    # else:
                    #     i = i + 1
                    #===========================================================
            except:
                r.delete()


    reminds = temp
    response = render(request, 'dboard2.html', {"now":now,"reminds":reminds,"login_teacher":login_teacher})
    response.set_cookie("mainurl",'/go2/regUser/dboard2')
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)

    return response

#remind next month
def dboard13(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    searchBegin = todayBegin + timedelta(days=1)
    searchEnd = todayBegin + timedelta(days=8)
    #todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    #monthBegin = datetime.datetime.strptime(now.strftime("%Y-%m")+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    #weekBegin = todayBegin - timedelta(days=todayBegin.weekday())
    #lastWeekBegin = weekBegin - timedelta(days=7)
    #lastWeekEnd = weekBegin - timedelta(days=1)
    query = Q(branch=login_teacher.branch)
    query = query&Q(remindTime__gte=searchBegin)&Q(remindTime__lt=searchEnd)&Q(isDone__ne=1)
    teachers = getTeachers(login_teacher.branch)

    if login_teacher.branchType == '1':
        query = Q(regBranch=login_teacher.branch)&Q(remindTime__gte=searchBegin)&Q(remindTime__lt=searchEnd)&Q(isDone__ne=1)
        qq = None
        i = 0
        for t in teachers:
            if i == 0:
                qq = Q(remindTeachers__contains=t.id)
            else:
                qq = qq|Q(remindTeachers__contains=t.id)
            i = i + 1
        query = query&(qq)


    reminds = TeacherRemind.objects.filter(query).order_by("remindTime")
    temp = []
    stemp = []



    if login_teacher.branchType != '1':
      for r in reminds:
        y = False #是否自己校区老师的提醒
        try:
            if r.student and r not in temp and r.student not in stemp:
                if r.branch == login_teacher.branch:
                    y = True
                else:
                    for t in teachers:
                        for rt in r.remindTeachers:
                            if t.id == rt.id:
                                y = True
                                break
                        if y:
                            break

                if y:
                    try:
                        r.student.prt1mobile = r.student.prt1mobile.replace(';',' ')
                    except Exception,e:
                        err = 1
                    r.regTime = r.student.regTime
                    try:
                        days = (getDateNow()-r.student.birthday).days
                        y = days/365
                        m = days%365/30
                        r.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            r.yearMonth = str(y)
                    except:
                        err = 1


                    if r.student.memo:
                        r.student.memo = u'【备注】'+r.student.memo
                    else:
                        r.student.memo = u'【备注】'
                    tq = Q(student=r.student.id)&Q(track_txt__ne=u'总部新推送')&Q(track_txt__ne=u'总部新分配')&Q(deleted__ne=1)
                    tracks = StudentTrack.objects.filter(tq).order_by("trackTime")
                    if tracks and len(tracks)>0:
                        for track in tracks:
                            r.student.memo = "["+track.trackTime.strftime('%Y%m%d')+"]"+track.track_txt+r.student.memo
                    ts = []
                    for t in r.remindTeachers:
                        if str(t.branch.id) == login_teacher.cityHeadquarter:
                            t.name = u'网络部'
                        ts.append(t)
                    r.remindTeachers = ts
                    temp.append(r)
                    stemp.append(r.student)
        except Exception,e:
            a = 1

      reminds = temp
    response = render(request, 'dboard13.html', {"now":now,"reminds":reminds,"login_teacher":login_teacher})
    response.set_cookie("mainurl",'/go2/regUser/dboard13')
    return response

#网络部－校区今日应联系
def dboard9(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    monthBegin = datetime.datetime.strptime(now.strftime("%Y-%m")+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    weekBegin = todayBegin - timedelta(days=todayBegin.weekday())
    lastWeekBegin = weekBegin - timedelta(days=7)
    lastWeekEnd = weekBegin - timedelta(days=1)
    reminds = TeacherRemind.objects.filter(branch__ne=login_teacher.branch).filter(remindTime__gte=todayBegin).filter(remindTime__lte=todayEnd).order_by("branch")
    temp = []
    students = []
    for r in reminds:
        try:
            if r.student and r not in temp and r.student not in students and str(r.student.regBranch.id) == login_teacher.branch:
                yes = False
                for rt in r.remindTeachers:
                    if str(rt.branch.id) != login_teacher.cityHeadquarter:
                        yes = True
                        break

                if yes:

                    try:
                        days = (getDateNow()-r.student.birthday).days
                        y = days/365
                        m = days%365/30
                        r.yearMonth = str(y)+'.'+str(m)
                        if m == 0:
                            r.yearMonth = str(y)
                        if r.student.gender:
                            r.yearMonth = r.student.gender + ' ' + r.yearMonth
                    except:
                        err = 1

                    ts = []
                    for rt in r.remindTeachers:
                        if str(rt.branch.id) == login_teacher.cityHeadquarter:
                            rt.name = u'网络部'
                        ts.append(rt)
                    students.append(r.student)
                    r.regTime = r.student.regTime
                    r.remindTeachers = ts
                    temp.append(r)
        except:
            a = 1
    reminds = temp

    response = render(request, 'dboard9.html', {"now":now,"reminds":reminds,"login_teacher":login_teacher})
    response.set_cookie("mainurl",'/go2/regUser/dboard9')
    return response

#网络部客户校区未完成提醒
def dboard10(request):
    millis0 = int(round(time.time() * 1000))
    beginMillis = millis0

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    query = Q(branch=constant.NET_BRANCH)&(Q(role=5)|Q(role=7))
    netTeachers = Teacher.objects.filter(query)
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    monthBegin = datetime.datetime.strptime(now.strftime("%Y-%m")+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    weekBegin = todayBegin - timedelta(days=todayBegin.weekday())
    lastWeekBegin = weekBegin - timedelta(days=7)
    lastWeekEnd = weekBegin - timedelta(days=1)
    query = Q(regBranch=login_teacher.branch)&Q(remindTime__lt=todayBegin)&Q(isDone__ne=1)
    qq = None
    i = 0

    for t in netTeachers:
        if i == 0:
            qq = Q(remindTeachers__ne=t.id)
        else:
            qq = qq&Q(remindTeachers__ne=t.id)
        i = i + 1
    #query = query&(qq)
    reminds = TeacherRemind.objects.filter(query).order_by("branch")

    temp = []
    students = []

    millis1 = int(round(time.time() * 1000))


    response = render(request, 'dboard10.html', {"now":now,"reminds":reminds,"login_teacher":login_teacher})
    response.set_cookie("mainurl",'/go2/regUser/dboard10')
    return response


#forgot
def dboard3(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    reminds = TeacherRemind.objects.filter(branch=login_teacher.branch).order_by("student")
    query = Q(branch=login_teacher.branch)&Q(status=0)&Q(probability__ne='C')&(Q(demo=[])|Q(demo=None))&Q(status=0)&Q(siblingId=None)
    students = Student.objects.filter(query).order_by("-regTime")
    #tracks = StudentTrack.objects.filter(student_branch=login_teacher.branch).order_by("student")
    res = []
    for student in students:
        hasR = False
        hasT = False
        for r in reminds:
            rid = None
            try:
                rid = r.student.id
            except:
                a = 1
            if student.id == rid:
                hasR = True
                break
        if not hasR:
            tracks = StudentTrack.objects.filter(student=student)
            if tracks and len(tracks)>0:
                hasT = True
        if hasR or hasT:
            a = 1
        else:
            try:
                if login_teacher.role > 3 or str(student.regBranch.id) == login_teacher.branch:
                    res.append(student)
            except:
                err = 1
    return render(request, 'dboard3.html', {"students":res,"login_teacher":login_teacher})

def dboard4(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    query = Q(branch=login_teacher.branch)&Q(status=1)&Q(lessons__lte=4)&Q(lessons__gte=1)
    students = Student.objects.filter(query).order_by("-lessons")
    temp = []
    multi = 0
    for s in students:
        for c in s.contract:
            multi = 0


            if c.status == 0 and c.multi != constant.MultiContract.newDeal:
                multi = 1
        if multi == 0:
            if constant.DEBUG:
                print str(multi) + '--' + s.name
            temp.append(s)
    students = temp
    response = render(request, 'dboard4.html', {"students":students,"login_teacher":login_teacher})
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)

    return response

def dboard5(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    students = Student.objects.filter(branch=login_teacher.branch).filter(status=1).filter(lessons__gt=4).order_by("lessons")
    temp = []
    for student in students:
        try:
            query = Q(student_oid=str(student.id))&Q(status=0)
            contracts = Contract.objects.filter(query).order_by("-singDate")
            cs = []
            for c in contracts:
                if c.contractType.type == constant.ContractType.free:
                    cs.append(c)
                elif c.multi == constant.MultiContract.oldRedeal:
                    cs.append(c)
                    break
                elif c.multi == constant.MultiContract.newRedeal:
                    cs.append(c)
                elif c.multi == constant.MultiContract.newDeal:
                    cs.append(c)
                    break

            allweeks = 0

            for c in cs:
                if c.weeks and c.weeks > 0:
                    allweeks = allweeks + c.weeks
                elif c.contractType.duration and c.contractType.duration > 0:
                    allweeks = allweeks + c.contractType.duration
            if allweeks > 0 and student.lessonLeft <15 and student.lessonLeft <= allweeks/2 :
                student.allLesson = allweeks
                endDate = None
                try:
                    id = str(student.id)

                    beginDate,endDate,days,learnDays = util2.getLessonCheckDeadline(id)
                    endDate,learnDays = util2.getEndDateAddVocation(beginDate, endDate, login_teacher.cityId,learnDays)
                    endDate,learnDays = util2.getEndDateAddSuspension(beginDate, endDate, id,learnDays)
                    if endDate:
                        student.endDate = endDate

                except Exception,e:
                    print e
                if constant.DEBUG:
                        print '[contract weeks]' + str(allweeks) + '[left]' + str(student.lessonLeft)
                temp.append(student)

        except:
            err = 1
    students = temp
    response = render(request, 'dboard5.html', {"students":students,"login_teacher":login_teacher})
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response
def dboard6(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    classTypes = ClassType.objects.all().order_by("sn")
    rooms = []
    branch = Branch.objects.get(id=login_teacher.branch)
    if not branch.branchRooms:branch.branchRooms = 1
    for i in range(1,branch.branchRooms+1):
        rooms.append(i)
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    monthBegin = datetime.datetime.strptime(now.strftime("%Y-%m")+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    weekBegin = todayBegin - timedelta(days=todayBegin.weekday())
    lastWeekBegin = weekBegin - timedelta(days=7)
    lastWeekEnd = weekBegin - timedelta(days=1)
    #课表
    dayClasses = getDayClasses(login_teacher.branch,todayBegin.weekday(),todayBegin, now,rooms,1,1)

    hours = ["08:","09:","10:","11:","12:","13:","14:","15:","16:","17:","18:","19:","20:"]
    return render(request, 'dboard6.html', {"now":now,"hours":hours,"dayClasses":dayClasses,"classTypes":classTypes,"login_teacher":login_teacher})

#branch forgot
def dboard11(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch = request.GET.get("branch")
    res = None
    branches = utils.getCityBranch(login_teacher.cityId)
    #Branch.objects.filter(sn__gt=0).filter(sn__lt=200).order_by("sn")

    if login_teacher.branchType == '1' and branch:

        netTeachers = Teacher.objects.filter(branch=branch)
        query = Q(track_txt__ne='')&Q(deleted__ne=1)
        q2 = Q(teacher=netTeachers[0])
        index = 0
        for t in netTeachers:
            if index > 0:
                q2 = q2|Q(teacher=t)
            index = index + 1
        query = query&(q2)
        reminds = StudentTrack.objects.filter(query)
        ind = 0
        for track in reminds:
            if track.branch:
                break
            ind = ind + 1
            for t in netTeachers:
                if t == track.teacher:
                    track.branch = str(t.branch.id)
                    track.save()

        reminds = StudentTrack.objects.filter(branch=branch)
        query = Q(branch=branch)&Q(status=0)&Q(regBranch=login_teacher.branch)&Q(probability__ne='C')&(Q(demo=[])|Q(demo=None))
        students = Student.objects.filter(query).order_by("branch,-regTime")
    #tracks = StudentTrack.objects.filter(student_branch=login_teacher.branch).order_by("student")
        res = []
        for student in students:
            hasR = False
            if student:
                if student.demo or student.status == 1 :
                    hasR = True
                else:
                  try:
                    for r in reminds:
                        rs = None
                        try:
                            rs = r.student
                        except:
                            rs = None
                        if student == rs:
                            hasR = True
                            break
                  except:
                    err = 1
            if not hasR:
                res.append(student)

    return render(request, 'dboard11.html', {"students":res,
                                             "branch":branch,
                                             "branches":branches,
                                             "login_teacher":login_teacher})
#birthday reminder
def dboard12(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    now = getDateNow()
    year = int(now.strftime("%Y"))
    date = now.strftime("%m-%d")
    query = Q(branch=login_teacher.branch)&Q(status=1)
    q2 = None
    for i in range(15):
        y = year - i
        begin = datetime.datetime.strptime(str(y)+'-'+date+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        end = begin + timedelta(days=31)
        if i == 0:
            q2 = (Q(birthday__gte=begin)&Q(birthday__lte=end))
        else:
            q2 = q2|(Q(birthday__gte=begin)&Q(birthday__lte=end))
    query = query&(q2)
    students = Student.objects.filter(query).order_by("birthday")
    temp = []
    for s in students:
        s.birth = s.birthday.strftime("%m-%d")
        if s.gradeClass and len(s.gradeClass)>0:
            try:
                c = GradeClass.objects.get(id=s.gradeClass)
            except:
                c = None
            if c:
                s.className = c.name
                if c.school_day == 7:
                    c.school_day = u'日'
                if c.school_day == 6:
                    c.school_day = u'六'
                if c.school_day == 5:
                    c.school_day = u'五'
                if c.school_day == 4:
                    c.school_day = u'四'
                if c.school_day == 3:
                    c.school_day = u'三'
                if c.school_day == 2:
                    c.school_day = u'二'
                if c.school_day == 1:
                    c.school_day = u'一'
                s.classTime = u'周'+c.school_day+' '+c.school_time
        else:
            err = 1
        temp.append(s)
        try:
            temp = sorted(temp, key=attrgetter('birth'),reverse=False)
        except:
            temp = temp
    students = temp
    response = render(request, 'dboard12.html', {"students":students,"login_teacher":login_teacher})
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response

def checkDup(all,login_teacher):
    has = False
    hasNet = False
    for other in all:
                if other.branch and str(other.branch.id) == str(login_teacher.branch):
                    #意向校区是自己校区
                    has = True
                    has0 = True
                if other.regBranch and str(other.regBranch.id) == str(login_teacher.branch):
                    #拜访登记校区是自己校区
                    has = True
                    has0 = True

                if other.regBranch and other.regBranch.type == 1:
                    if str(login_teacher.branch) == str(other.regBranch.id):
                      b1 = other.branch
                      b2 = other.branch2
                      b3 = other.branch3
                      b4 = other.branch4

                      b1IsMe = False
                      b2IsMe = False
                      b3IsMe = False
                      b4IsMe = False

                      for o in all:
                          try:
                            if o.regBranch == b1:
                              b1IsMe = True
                              break
                          except:
                              b1IsMe = False
                          try:
                            if str(o.regBranch.id) == str(b2):
                                b2IsMe = True
                                break
                          except:
                            b2IsMe = False
                          try:
                            if str(o.regBranch.id) == str(b3):
                              b3IsMe = True
                              break
                          except:
                              b3IsMe = False
                          try:
                            if str(o.regBranch.id) == str(b4):
                              b4IsMe = True
                              break
                          except:
                              b4IsMe = False

                      if b1IsMe or b2IsMe or b3IsMe or b4IsMe:
                        hasNet = True
                        hasNet0 = True
                    else:
                      b1IsMe = False
                      b2IsMe = False
                      b3IsMe = False
                      b4IsMe = False
                      try:
                        if str(other.branch.id) == str(login_teacher.branch):
                            b1IsMe = True
                      except:
                        b1IsMe = False
                      try:
                        if str(other.branch2) == str(login_teacher.branch):
                            b2IsMe = True
                      except:
                        b2IsMe = False
                      try:
                        if str(other.branch3) == str(login_teacher.branch):
                            b3IsMe = True
                      except:
                        b3IsMe = False
                      try:
                        if str(other.branch4) == str(login_teacher.branch):
                            b4IsMe = True
                      except:
                        b4IsMe = False
                      if b1IsMe or b2IsMe or b3IsMe or b4IsMe:
                        hasNet = True
                        hasNet0 = True

    return has,hasNet


def student_list(request):
    dateNow = utils.getDateNow(8)
    millis0 = int(round(time.time() * 1000))
    beginMillis = millis0
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    students = []
    teachers = getTeachers(login_teacher.branch)

    pageRow = 20
    try:
        pageRow = login_teacher.page
        if not pageRow:
            pageRow = 20
        if pageRow<20:
            pageRow = 20
    except:
        pageRow = 20
    page = request.GET.get('page')
    if not page:
        page = 1

    searchRemind = request.GET.get("searchRemind")
    searchRegTeacher = request.GET.get("searchRegTeacher")
    searchTeacher = request.GET.get("searchTeacher")
    searchSourceType = request.GET.get("searchSourceType")
    searchSource = request.GET.get("searchSource")
    searchName = request.GET.get("searchName")
    searchStatus = request.GET.get("searchStatus")
    searchDemo = request.GET.get("searchDemo")
    searchDeposit = request.GET.get("searchDeposit")
    searchLocal = request.GET.get("searchLocal")
    searchRegBranch = request.GET.get("searchRegBranch")
    searchBranch = request.GET.get("searchBranch")
    searchPhone = request.GET.get("searchPhone")
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    beginYear = request.GET.get("beginYear")
    endYear = request.GET.get("endYear")
    beginMonth = request.GET.get("beginMonth")
    endMonth = request.GET.get("endMonth")
    searchSchool = request.GET.get("searchSchool")
    searchCode = request.GET.get("searchCode")
    searchDate = None
    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None


    mainurl = '/go2/regUser/studentList?page='+str(page)
    if searchRemind:
        mainurl = mainurl + '&searchRemind='+searchRemind
    if searchRegTeacher:
        mainurl = mainurl + '&searchRegTeacher='+searchRegTeacher
    if searchTeacher:
        mainurl = mainurl + '&searchTeacher'+searchTeacher
    if searchSourceType:
        mainurl = mainurl + '&searchSourceType='+searchSourceType
    if searchSource:
        mainurl = mainurl + '&searchSource='+searchSource
    if searchName:
        mainurl = mainurl + '&searchName='+searchName
    if searchStatus:
        mainurl = mainurl + '&searchStatus='+searchStatus
    if searchDemo:
        mainurl = mainurl + '&searchDemo='+searchDemo
    if searchDeposit:
        mainurl = mainurl + '&searchDeposit='+searchDeposit
    if searchLocal:
        mainurl = mainurl + '&searchLocal='+searchLocal
    if searchRegBranch:
        mainurl = mainurl + '&searchRegBranch='+searchRegBranch
    if searchBranch:
        mainurl = mainurl + '&searchBranch='+ searchBranch
    if searchPhone:
        mainurl = mainurl + '&searchPhone='+ searchPhone
    if beginDate:
        mainurl = mainurl + '&beginDate='+ beginDate
    if endDate:
        mainurl = mainurl + '&endDate='+ endDate
    if beginYear:
        mainurl = mainurl + '&beginYear='+ beginYear
    if endYear:
        mainurl = mainurl + '&endYear=' + endYear
    if beginMonth:
        mainurl = mainurl + '&beginMonth='+ beginMonth
    if endMonth:
        mainurl = mainurl + '&endMonth='+ endMonth
    if searchSchool:
        mainurl = mainurl + '&searchSchool='+ searchSchool
    if searchCode:
        mainurl = mainurl + '&searchCode='+ searchCode

    #===========================================================================
    # 冲突记录
    #===========================================================================
    queryDup = Q(dup=-1)&Q(regBranch=login_teacher.branch)&(Q(resolved=-1)|Q(resolved=-2)|Q(resolved=-3))
    dup =  Student.objects.filter(queryDup).order_by("prt1mobile")

    millis1 = int(round(time.time() * 1000))
    if constant.DEBUG:
        print dup._query
        print 'after dup 0:'+str(millis1-millis0)
    millis0 = millis1
    dups = [] #冲突列表
    has0 = False
    hasNet0 = False
    has1 = False
    orderby = "-callInTime"
    i = 0
    for s in dup:
        if constant.DEBUG:
            millis1 = int(round(time.time() * 1000))
            print 'after dup every:'+str(millis1-millis0)
            millis0 = millis1
        qu = Q(prt1mobile=s.prt1mobile)|Q(prt2mobile=s.prt1mobile)
        if s.prt2mobile and len(s.prt2mobile) > 5:
            qu = qu|Q(prt1mobile=s.prt2mobile)|Q(prt2mobile=s.prt2mobile)
        #重复号码的全部客户
        other1 = Student.objects.filter(qu)
        if len(other1)>1:
            has = False
            hasNet = False
            has, hasNet = checkDup(other1,login_teacher)
            if has:
                has0 = True

            if has and hasNet: #自己校区拜访或意向是自己校区并且有网络部冲突
                #print other.prt1mobile
                has1 = True
                i = i + 1
                for other in other1:
                    other.probability = str(i)
                    dups.append(other)


    #===========================================================================
    # 冲突数据end
    #===========================================================================

    millis1 = int(round(time.time() * 1000))
    if constant.DEBUG:
        print 'after dup:'+str(millis1-millis0)
    millis0 = millis1
    query = None

    if login_teacher.role>3:
        query = (Q(regBranch=login_teacher.branch)|Q(branch=login_teacher.branch)|Q(branch2=login_teacher.branch)|Q(branch3=login_teacher.branch)|Q(branch4=login_teacher.branch))
    else:
        query = (Q(regTeacher=login_teacher.id)|Q(teacher=login_teacher.id))

    #===========================================================================
    # D、E
    #===========================================================================
    if not searchDemo:
        if bDate and not searchDemo and not searchStatus == '1' and not searchStatus == 'C':
            query = query&Q(callInTime__gte=bDate)
        if eDate and not searchDemo and not searchStatus == '1' and not searchStatus == 'C':
            query = query&Q(callInTime__lt=eDate)
        if bDate and searchStatus == 'C':
            query = query&Q(cdate__gte=bDate)
        if eDate and searchStatus == 'C':
            query = query&Q(cdate__lt=eDate)
        if searchRemind:
            if bDate:
                query = Q(remindTime__gte=bDate)
                if eDate:
                    query = query&Q(remindTime__lt=eDate)
            elif eDate:
                query = Q(remindTime__lt=eDate)


    if searchName:  #B
        query = query&(Q(name__icontains=searchName)|Q(name2__icontains=searchName))
        if int(login_teacher.branchType) == constant.BranchType.function:
            print 'search name'
            query = Q(name__icontains=searchName)|Q(name2__icontains=searchName)

    if searchPhone:  #A
        query = query&(Q(prt1mobile__contains=searchPhone)|Q(prt2mobile__contains=searchPhone))
        if int(login_teacher.branchType) == constant.BranchType.function:
            print 'search phone'
            query = Q(prt1mobile__contains=searchPhone)|Q(prt2mobile__contains=searchPhone)

    if searchCode:  #C

        query = query&(Q(code__icontains=searchCode)|Q(memo__icontains=searchCode))



    if searchBranch:  #K
        if searchBranch == '1':#非本校
            query = query&Q(branch__ne=login_teacher.branch)
        elif searchBranch == '-1':#未分配校区
            query = query&Q(branch=None)
        elif searchRemind:
            query = query&(Q(branch=searchBranch))


        else:
            query = query&(Q(branch=searchBranch)|Q(branch2=searchBranch)|Q(branch3=searchBranch)|Q(branch4=searchBranch))
    elif login_teacher.branch == constant.NET_BRANCH:
        query = query&(Q(regBranch=constant.NET_BRANCH))
    elif login_teacher.branch == constant.NET_BRANCH2:
        query = query&(Q(regBranch=constant.NET_BRANCH2))
    else:
        query = query&(Q(branch=login_teacher.branch))

    if searchRegTeacher:  #L
        query = query&Q(regTeacher=searchRegTeacher)


    if searchDeposit:  #N
        query = query&Q(deposit__gt=0)

    if searchRegBranch:  #J
        if searchRegBranch == '1':#网络部
            query = query&Q(regBranch=constant.NET_BRANCH)
        elif searchRegBranch == '0':#本校区
            query = query&Q(regBranch=login_teacher.branch)
        elif searchRegBranch == '2':#其他校区
            query = query&(Q(regBranch__ne=constant.NET_BRANCH)&Q(regBranch__ne=login_teacher.branch))
    if searchSourceType:  #Q
        query = query&Q(sourceType=searchSourceType)
    if searchSource:  #R
        if searchSource == "N":
            query = query&Q(source=None)
        else:
            query = query&Q(source=searchSource)
    if searchSchool:  #I
        query = query&(Q(school=searchSchool)|Q(kindergarten=searchSchool))
    if searchStatus:  #O
        if searchStatus == '1' or searchStatus == '2'  or searchStatus == '3':
            query = query&Q(status=searchStatus)
        if  searchStatus == '0' :
            query = query&Q(contract__size=0)
        if searchStatus == 'A' or searchStatus == 'B' or  searchStatus == 'C':
            query = query&(Q(probability=searchStatus)&Q(status=0))
        if searchStatus == '0-C':
            query = query&Q(contract__size=0)&Q(probability__ne='C')
        if searchStatus == '-1':
            query = query&Q(dup=-1)

    if beginYear:  #G
        beginAgeDate = dateOfYearMonth(beginYear,beginMonth)
        query = query&Q(birthday__lte=beginAgeDate)

    if endYear:   #H
        endAgeDate = dateOfYearMonth(endYear,endMonth)
        query = query&Q(birthday__gt=endAgeDate)

    #this query is the main query,exclude demo search,remind search and contract search
    genquery = query



    if searchDemo:
        if searchDemo == '1':
            query = query&Q(isDemo=1)

        searchDate = False
    if eDate or bDate:
        searchDate = True


    temp = []
    searchDemodate = False
    #other search: remind,demo and contract search

    if searchDemo:
        if bDate:
            searchDemodate = True
            query = Q(start_date__gte=bDate)
            if eDate:
                query = query&Q(start_date__lt=eDate)

        elif endDate:
            searchDemodate = True
            query = Q(start_date__lt=eDate)

        if searchDemodate:
            if searchDemo == '0': #未安排
                searchDemodate = None
                students = Student.objects.filter(genquery).order_by(orderby)

            else:
                if searchDemo == '1': #已上
                  query = query&Q(demoIsFinish=1)
                  thisq = genquery
                if searchDemo == '4': #取消
                  query = query&Q(demoIsFinish=-1)
                  thisq = genquery
                if searchDemo == '2':#未上
                    query = query&Q(demoIsFinish__ne=1)&Q(demoIsFinish__ne=-1)
                    date1 = datetime.datetime.strptime(dateNow.strftime("%Y-%m-%d")+' 00:00:00','%Y-%m-%d %H:%M:%S')

                    query =  query&Q(demoIsFinish__ne=1)&Q(demoIsFinish__ne=-1)&(Q(start_date__gt=dateNow)|Q(start_date=date1)&Q(school_time__gt=dateNow.strftime("%H:%M")))
                    thisq = genquery&Q(isDemo__ne=1)
                if searchDemo == '3':#所有未取消
                  query = query&Q(demoIsFinish__ne=-1)
                  thisq = genquery
                if searchDemo == '5': #未到场
                    date1 = datetime.datetime.strptime(dateNow.strftime("%Y-%m-%d")+' 00:00:00','%Y-%m-%d %H:%M:%S')

                    query =  query&Q(demoIsFinish__ne=1)&Q(demoIsFinish__ne=-1)&(Q(start_date__lt=date1)|Q(start_date=date1)&Q(school_time__lt=dateNow.strftime("%H:%M")))
                    thisq = genquery&Q(isDemo__ne=1)
                if searchBranch and searchBranch != '-1':
                    query = query&Q(branch=searchBranch)&Q(gradeClass_type=2)
                if login_teacher.branchType != '1':
                    query = query&Q(branch=login_teacher.branch)
                query = query&Q(gradeClass_type=2)
                demos = GradeClass.objects.filter(query).order_by("-start_date")
                print('-----------------SEARCH DEMO-----------------')
                print(demos._query)

                #utils.save_log('debug', str(demos._query))
                temp = []

                for demo in demos:

                    ok = True
                    if demo.students and len(demo.students)>0:
                        s = demo.students[0]
                        try:
                            na = s.name
                        except:
                            ok = False
                            continue
                        if searchRegTeacher:
                            try:
                              if not s.regTeacher:
                                ok = False
                                continue

                              elif str(s.regTeacher.id) != searchRegBranch:
                                ok = False
                                continue
                            except:
                                ok = False
                                continue
                        if searchTeacher:
                            try:
                                a = demo.teacher.id
                            except:
                                ok = False
                                continue
                            if str(demo.teacher.id) == searchTeacher:
                                ok = True
                            else:
                                ok = False
                                continue
                        # if login_teacher.branchType == '1':
                        #     if s.regBranch and str(s.regBranch.id) != login_teacher.cityHeadquarter:
                        #         ok = False
                        #         continue
                        if searchCode:
                            sco = s.code
                            sme = s.memo

                            if sco and s.code.find(searchCode)>-1 or (sme and s.memo.find(searchCode))>-1:
                                a = 1
                            else:
                                ok = False
                                continue
                        if searchStatus:
                            if searchStatus in ['0','1','2','3'] and s.status == int(searchStatus):
                                ok = True
                            elif searchStatus == '0-C' and s.status == 0 and s.probability != 'C':
                                ok = True
                            elif searchStatus in ['A','B','C'] and s.probability == searchStatus:
                                ok = True
                            else:
                                ok = False
                        if searchSource:
                            #print searchSource
                            #print s.source
                            try:
                              if str(s.source.id) == searchSource:
                                ok = ok
                              else:
                                ok = False
                            except:
                                ok = False

                        if searchRegBranch:
                            if searchRegBranch == "1" and str(s.regBranch.id) == constant.NET_BRANCH:
                                ok = ok

                            elif searchRegBranch == "0" and str(s.regBranch.id) == login_teacher.branch:
                                ok = ok

                            elif searchRegBranch == "2" and (str(s.regBranch.id) != constant.NET_BRANCH) and (str(s.regBranch.id) != login_teacher.branch):
                                ok = ok
                            else:
                                ok = False
                        elif login_teacher.branchType == '1':
                            if str(s.regBranch.id) == login_teacher.branch:
                                ok = ok
                            else:
                                ok = False
                        if searchSourceType and s.sourceType:
                            if searchSourceType == s.sourceType:
                                ok = ok
                            else:
                                ok = False

                        if ok:
                            try:
                                s.regTime = demo.start_date
                                s.demoTeacher = demo.teacher.name
                                s.demoMemo = demo.info

                                temp.append(s)
                            except:
                                a = 1
                students = temp
        else: #demo search but not search date,use main query
            students = Student.objects.filter(query).order_by(orderby)
    elif searchStatus == '1' and searchDate:
        if bDate:
            query = Q(singDate__gte=bDate)
            if eDate:
                query = query&Q(singDate__lt=eDate)
        elif eDate:
            query = Q(singDate__lt=eDate)
        query = query&Q(status=0)
        if login_teacher.branchType != '1':
            query = query&Q(branch=login_teacher.branch)
        contracts = Contract.objects.filter(query).order_by("-singDate")

        studentLarge = Student.objects.filter(genquery)
        students = []
        for c in contracts:
            s = None
            try:
                s = Student.objects.get(id=c.student_oid)
            except:
                s = None

            if s and s not in students and s in studentLarge:
                s.regTime = c.singDate
                students.append(s)

    else: #main query

        students = Student.objects.filter(query).order_by(orderby)
        #print students._query
        millis1 = int(round(time.time() * 1000))
        if constant.DEBUG:
            print students._query
            print 'after main search:'+str(millis1-millis0)
        millis0 = millis1

    temp = []

    if not searchDemodate:

      if searchDemo:
        if searchDemo == '3' : #全部未取消
            for s in students:
                if s.demo and len(s.demo)>0:
                    try:
                      demo = GradeClass.objects.get(id=s.demo[0])
                      if demo.demoIsFinish != -1:
                        if demo.start_date:
                            s.regTime = demo.start_date
                        if not s.regTime:
                            s.regTime = getDateNow()-timedelta(days=2000)
                        temp.append(s)
                    except:
                        err = 1
        if searchDemo == '2' : #未上
            for s in students:
                if s.isDemo != 1 and s.demo and len(s.demo)>0:
                    demo = GradeClass.objects.get(id=s.demo[0])
                    if demo.start_date:
                        s.regTime = demo.start_date
                    if not s.regTime:
                        s.regTime = getDateNow()-timedelta(days=2000)
                    temp.append(s)
        if searchDemo == '4' : #取消
            for s in students:
                if s.isDemo != 1 and s.demo and len(s.demo)>0:
                    demo = GradeClass.objects.get(id=s.demo[0])
                    if demo.start_date:
                        s.regTime = demo.start_date
                    if not s.regTime:
                        s.regTime = getDateNow()-timedelta(days=2000)
                    s.isDemo = -1
                    if demo.demoIsFinish == -1:
                        temp.append(s)
        if searchDemo == '1' : #已上
            for s in students:
                if s.demo and len(s.demo)>0:
                    demo = None
                    demoed = False
                    for did in s.demo:
                      try:
                        demo = GradeClass.objects.get(id=did)
                        if demo.demoIsFinish == 1:
                            demoed = True
                      except:
                          err = 1
                    if demoed and s.isDemo != 1:
                        s.isDemo = 1
                        s.save()
                    try:
                      if demo.start_date:
                        s.regTime = demo.start_date
                    except:
                        err = 1
                    if demo and demo.teacher:
                        s.demoTeacher = demo.teacher.name
                    if demo and demo.info:
                        s.demoMemo = demo.info
                    if not s.regTime:
                        s.regTime = getDateNow()-timedelta(days=2000)
                    temp.append(s)
        if searchDemo == '0':
            for s in students:
                if not s.demo or s.demo and len(s.demo)==0:
                    temp.append(s)
        if searchDemo != '0':
            students = sorted(temp, key=attrgetter('regTime'),reverse=True)
        else:
            students = temp
            # 页码设置
    temp = []

    #未报名非C类提醒已完成
    if searchStatus == '0-Cf':
        query = Q(contract__size=0)&Q(probability__ne='C')&Q(isDone=1)#未报名非C类
        if searchBranch:
            query = query&Q(branch=searchBranch)
        if str(login_teacher.branchType) == str(constant.BranchType.marketing):

            query = query&Q(regBranch=login_teacher.branch)
        else:
            query = query&Q(branch=login_teacher.branch)
        s0c = Student.objects.filter(query).order_by("-callInTime")

        students = s0c

    paginator = Paginator(students, pageRow)

    sss = students
    try:
        students = paginator.page(page)

    except Exception,e:
        students = sss
    temp = []
    millis1 = int(round(time.time() * 1000))
    if constant.DEBUG:
            print 'after page 1:'+str(millis1-millis0)
    millis0 = millis1

    dateNow = getDateNow()
    for s in students:
      try:
        if True:
            days = (dateNow-s.birthday).days
            y = days/365
            m = days%365/30
            s.yearMonth = str(y)+'.'+str(m)
            if m == 0:
                s.yearMonth = str(y)
      except:
          err = 1
      try:

        # if not searchRemind:
        if True:
            if s and s.memo:
                s.memo = u'【备注】'+s.memo
            else:
                s.memo = u'【备注】'
        if not s.track:
            s.track = ''
        try:
            if not s.name:
                s.name = s.name2
            if s.name == u'无':
                s.name = None

        except Exception,e:
            err = 1
        # add contract date
        if searchStatus == '1' and not searchDate:
            contracts = s.contract
            try:
                contracts = sorted(s.contract, key=attrgetter('singDate'),reverse=True)
            except:
                contracts = s.contract
            for c in contracts:
                try:
                  if c.status == 0:
                    s.regTime = c.singDate
                    break
                except:
                    err = 1
        if not s.siblingId:
            temp.append(s)
      except Exception,e:
        print s
        print e
    students = temp
    millis1 = int(round(time.time() * 1000))
    if constant.DEBUG:
            print 'after deal 1:'+str(millis1-millis0)
    millis0 = millis1
    if searchStatus == '1' and not searchDate:
        try:
            students = sorted(students, key=attrgetter('regTime'),reverse=True)
        except:
            err = 1
    else:
        students = students

    sourceTypes = SourceType.objects.all()
    querySource = (Q(branch=login_teacher.branch)|Q(branch="5ab8473597a75d3c74041a2f"))&Q(deleted__ne=1)
    sources = Source.objects.filter(querySource).order_by("categoryCode")
    temp = []
    for s in sources:
        try:
            sc = SourceCategory.objects.get(id=s.categoryCode)
            s.categoryCode = sc.categoryCode
        except:
            err = 1
        temp.append(s)
    sources = temp
    classTypes = ClassType.objects.all().order_by("sn")
    branchs = utils.getCityBranch(login_teacher.cityId)
    page = int(page)

    memoWidth = 250
    if login_teacher.branchType == '1':
        memoWidth = 400
    dupLen = len(dups)
    millis1 = int(round(time.time() * 1000))
    if constant.DEBUG:
            print 'end search:'+str(millis1-millis0)
    millis0 = millis1
    excel = request.GET.get("excel")
    endMillis = int(round(time.time() * 1000))
    if constant.DEBUG:
        print '[searchUser]'+str(endMillis-beginMillis)+' ms'
    NB = ''
    try:
        NB = Branch.objects.get(id=constant.NET_BRANCH).branchName
    except Exception,E:
        NB = '网络'
    response = render(request, 'studentList.html',
                  {"dupLen":dupLen,"has1":has1,"hasNet0":hasNet0,"has0":has0,
                    "dups":dups,"searchStatus":searchStatus,
                   "branchs":branchs,"NB":NB,
                   "memoWidth":memoWidth,
                   "searchTeacher":searchTeacher,
                   "searchRegTeacher":searchRegTeacher,
                   "teachers":teachers,"endDate":endDate,
                   "beginDate":beginDate,"searchPhone":searchPhone,
                   "searchName":searchName,"classTypes":classTypes,
                   "login_teacher":login_teacher,"students": students,
                   "searchDeposit":searchDeposit,"searchLocal":searchLocal,
                   "searchDemo":searchDemo,"searchBranch":searchBranch,
                   "searchRegBranch":searchRegBranch,
                   "searchSourceType":searchSourceType,"searchSource":searchSource,
                   "searchSchool":searchSchool,
                   "sourceTypes":sourceTypes,"sources":sources,
                   "beginYear":beginYear,"beginMonth":beginMonth,
                   "endYear":endYear,"endMonth":endMonth,
                   "searchRemind":searchRemind,
                   "searchCode":searchCode,
                   "pageNow":page,"sss":sss,"excel":excel,#"sum":len(sss),
                   'pages': paginator.page_range})
    response.set_cookie("mainurl",mainurl)
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response

def student_info(request, student_oid):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    mainurl = request.COOKIES.get('mainurl','')
    datenow = getDateNow()
    demos = []
    studentFiles = []
    gradeClass = None
    student = None
    sourceName = ''
    readonly = False
    ex = [constant.Role.admin,constant.Role.financial]
    teachers = getTeachers(login_teacher.branch,ex)
    remindTeachers = []
    for t in teachers:
        if t.username != 'patch3':
            remindTeachers.append(t)

    dup = False
    dupStudent = None
    try:
        student = Student.objects.get(id=student_oid)
#===============================================================================
#         m1 = student.prt1mobile
#         m2 = student.prt2mobile
#         if m1 and len(m1)>6:
#             query = Q(prt1mobile=m1)|Q(prt2mobile=m1)
#             if m2 and len(m2)>6:
#                 query = query|Q(prt1mobile=m2)|Q(prt2mobile=m2)
#             query = (query)&Q(id__ne=student.id)
#             ss = Student.objects.filter(query)
#
#         if student.dup == 0:
#             if ss and len(ss)>0:
#                 dupStudent = ss[0]
#                 print dupStudent.id
#
#         if student and student.dup == -1:
#
#             readonly = False
#
#             dup = True
#         elif student:
#
#                 if ss and len(ss)>0:
#                     dup = True
#===============================================================================

        all = getDupByTel(student,0)

        has,hasNet = checkDup(all, login_teacher)

        if has and hasNet:
            dup = True
            for ss in all:
                if ss.id != student.id:
                    dupStudent = ss
                    break



        if login_teacher.role == constant.Role.financial:
            readonly = True
        if student.source:
            sourceName = student.source.sourceName
        birthday = student.birthday
        if birthday:
            days = (datenow-birthday).days
            y = days/365
            m = days%365/30
            student.yearMonth = str(y)+'岁'+str(m)+'个月'

        if student.gradeClass:
            gradeClass = GradeClass.objects.get(id=student.gradeClass)

        if student.demo:
            for demo_oid in student.demo:
                d = GradeClass.objects.get(id=demo_oid)
                if d:
                    demos.append(d)
        if student.branch and login_teacher.branchType == '1':
            tq = Q(branch=student.branch.id)&Q(role=5)&Q(status__ne=-1)
            ts = Teacher.objects.filter(tq)
            if ts and len(ts)>0:
                remindTeachers.append(ts[0])
        try:
            regb = student.regBranch
            if regb.type == 1 and login_teacher.branchType != 1:

                qq = Q(branch=regb.id)&Q(role=7)
                tts = Teacher.objects.filter(qq)
                tt = None
                if tts and len(tts)>0:
                    tt = tts[0]
                tt.name = regb.branchName

                remindTeachers.append(tt)
        except Exception,e:

            err = 1
        studentFiles = StudentFile.objects.filter(student=student_oid).order_by("order","fileCreateTime")
    except Exception,e:
        errormsg = 1

    teacherRemind = None
    ownBranchRemind = None
    tracks = None
    try:
        teacherReminds = TeacherRemind.objects.filter(student=student_oid)
        if teacherReminds.count>0:
            last = None
            for tr in teacherReminds:
                if not tr.remindTeachers:
                    tr.delete()
                    continue
                last = tr
                if tr.isDone != 1:
                    teacherRemind = tr
            if not teacherRemind:
                teacherRemind = last
            try:
              for t in teacherRemind.remindTeachers:
                for bt in teachers:
                    if t.id == bt.id:
                        ownBranchRemind = True
                        break
                if ownBranchRemind:
                    break
            except Exception,e:
                try:
                    teacherRemind.delete()
                except:
                    a = 1

        tracks = StudentTrack.objects.filter(student=student_oid).filter(deleted__ne=1).order_by("-trackTime")
    except:
        teacherRemind = None
    if student.referrerName and len(student.referrerName)>0:
        a = 1
    else:
        student.referrerName = ''
        try:
            student.referrerName = Student.objects.get(id=student.referrer).name
        except:
            errormsg = 1
    response = render(request, 'studentInfo.html', {"login_teacher":login_teacher,
                                                    "dupStudent":dupStudent,
                                                "datenow":datenow,
                                                "sourceName":sourceName,
                                                "tracks":tracks,
                                                "teacherRemind":teacherRemind,
                                                "ownBranchRemind":ownBranchRemind,
                                                "student": student,
                                                "demos":demos,
                                                "gradeClass":gradeClass,
                                                "studentFiles":studentFiles,
                                                "readonly":readonly,"dup":dup,
                                                "imagePath":USER_IMAGE_DIR,
                                                "teachers":teachers,
                                                "remindTeachers":remindTeachers,
                                                "mainurl":mainurl
                                                })
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response

def student_deposit(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.GET.get("student_oid")
    student = Student.objects.get(id=student_oid)
    teachers = getTeachers(login_teacher.branch)
    return render(request, 'studentDeposit.html', {"teachers":teachers, "student":student,
                                                   "login_teacher": login_teacher,
                                                   "paymethods":constant.PAY_METHOD})


def student_save_deposit(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.POST.get("student_oid")
    depositTeacher = request.POST.get("depositTeacher")
    depositDate = request.POST.get("depositDate")
    depositWay = request.POST.get("depositWay")
    depositStr = request.POST.get("deposit")
    depositCompanyStr = request.POST.get("depositCompany")
    depositReturnStr = request.POST.get("depositReturn")
    deposit = 0
    depositReturn = 0
    if depositReturnStr:
        try:
            depositReturn = int(depositReturnStr)
        except:
            errormsg = 1
    try:
        deposit = int(depositStr)
        depositCompany = int(depositCompanyStr)
        student = Student.objects.get(id=student_oid)
        student.deposit = deposit
        student.depositCompany = depositCompany
        student.depositDate = depositDate
        student.depositWay = depositWay
        student.depositStatus = depositReturn
        try:
            student.depositCollecter = Teacher.objects.get(id=depositTeacher)
        except:
            student.depositCollecter = None
        student.save()

    except Exception,e:
        print e
        return http.JSONResponse({"error": 1})
    return http.JSONResponse({"error": 0})

#查找孩子api
@csrf_exempt
def searchKid(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    searchKid = request.POST.get("searchKid")
    query = Q(name__icontains=searchKid)|Q(name2__icontains=searchKid)|Q(prt1mobile__icontains=searchKid)|Q(prt2mobile__icontains=searchKid)
    kids = None
    try:
        kids = Student.objects.filter(query).order_by("branch")
    except Exception,e:
        kids = None
    ret = ''
    try:
        if kids:
            students = []
            for kid in kids:
                name = '['+kid.branchName+']'+kid.name
                if kid.name2:
                    name = name + '('+kid.name2+')'
                id = str(kid.id)
                k = {"name":name,"id":id}
                students.append(k)
            ret = {"error": 0,"students":students}
        else:
            ret = {"error": 1,"msg":u"未找到"+searchKid}
    except Exception,e:
        print e

    return http.JSONResponse(ret)

#查找老师api
@csrf_exempt
def searchReferTeacher(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    searchName = request.POST.get("searchName")
    query = Q(name__icontains=searchName)|Q(username__icontains=searchName)
    teachers = None
    try:
        teachers = Teacher.objects.filter(query).order_by("branch")
    except Exception,e:
        teachers = None
    ret = ''
    try:
        if teachers:
            ts = []
            for t in teachers:
                name = '['+t.branch.branchName+']'+t.name

                id = str(t.id)
                k = {"name":name,"id":id}
                ts.append(k)
            ret = {"error": 0,"teachers":ts}
        else:
            ret = {"error": 1,"msg":u"未找到"+searchName}
    except Exception,e:
        print e

    return http.JSONResponse(ret)


#保存提醒和联络记录
@csrf_exempt
def save_user_remind(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.POST.get("student_oid")
    teacherRemindId = request.POST.get("teacherRemindId")
    remindTeacherIds = request.POST.get("remindTeacherIds")
    remindTime = request.POST.get("remindTime")
    isDone = request.POST.get("isDone")
    try:
        isDone = int(isDone)
    except:
        isDone = 0
    remind_txt = request.POST.get("remind_txt")
    backurl = request.POST.get("backurl")
    student = Student.objects.get(id=student_oid)
    err = 0
    if not remindTime and not remind_txt:
        return http.JSONResponse({"error": 0})

    if student_oid:
        try:
            student = Student.objects.get(id=student_oid)
            if student and student.prt1mobile:
                err = 0
            else:
                err = 1
        except:
            err = 1
    else:
        err = 1
    if err == 1:
        return http.JSONResponse({"error": 1,"msg":u"学生不存在"})

    err = 0
    teacher_list = []
    if remindTeacherIds:
        remindTeacherIdsList = remindTeacherIds.split(",")
        for teacher_id in remindTeacherIdsList:
            try:
                teacher = Teacher.objects.get(id=teacher_id)
            except:
                err = 1
                break
            teacher_list.append(teacher)
    else:
        err = 1
    if err == 1:
        return http.JSONResponse({"error": 1,"msg":u"提醒老师不存在"})

    datenow = getDateNow()
    err = 0
    if remindTime:
        try:
            t = datetime.datetime.strptime(remindTime,"%Y-%m-%d")
        except:
            return http.JSONResponse({"error": 1,"msg":u"跟进日期格式不对"})

        if datenow.strftime("%Y-%m-%d")>t.strftime("%Y-%m-%d"):
            if isDone != 1:
                return http.JSONResponse({"error": 1,"msg":u"请修改跟进日期或勾选‘已完成’"})
        else:
            err = 0
    else:
        return http.JSONResponse({"error": 1,"msg":u"请填写跟进日期"})

    if not remind_txt or remind_txt == '':
        return http.JSONResponse({"error": 1,"msg":u"请填写跟进事项"})


    saveRemind(None,student,teacher_list,t,remind_txt,isDone)

    trackTime = request.POST.get("trackTime")

    track_txt = request.POST.get("track_txt")
    if trackTime:
        trackTime = datetime.datetime.strptime(trackTime,"%Y-%m-%d %H:%M")
    if track_txt and len(track_txt)>0:

        btime = trackTime.replace(hour=0)
        btime = btime.replace(minute=0)
        btime = btime.replace(second=0)
        btime = btime.replace(microsecond=0)
        etime = btime + datetime.timedelta(days=1)

        query = Q(student=student)&Q(teacher=login_teacher.id)&Q(track_txt=track_txt)&Q(trackTime__gte=btime)&Q(trackTime__lt=etime)
        existTracks = StudentTrack.objects.filter(query)
        if existTracks and len(existTracks) > 0:
            #print 'has exist track!!!!!!!!!!!!!!!!!!!'
            i = 0
            for track in existTracks:
                if i > 0:
                    track.delete()
                i = i + 1
        else:
            res = saveTrack(1,student,None,trackTime,login_teacher.id,track_txt)

    if backurl:
        return http.JSONResponse({"error": 0,"backurl":backurl+'?student_oid='+student_oid})
    else:
        return http.JSONResponse({"error": 0})


def done(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.GET.get("student_oid")
    backurl = request.GET.get("backurl")
    oid = request.GET.get("oid")
    try:
        remind = TeacherRemind.objects.get(id=oid)
        if remind:
            if remind.isDone == 1:
                remind.isDone = 0
            else:
                remind.isDone = 1
            remind.save()

    except Exception,e:
        errormsg = 1
    url = '/go2/regUser/studentInfo/'+student_oid
    if backurl:
        url = backurl+'?student_oid='+student_oid

    return HttpResponseRedirect(url)


@csrf_exempt
def addSourceCategory(request):
    categoryCode = request.POST.get("sourceCategoryCode")
    categoryName = request.POST.get("sourceCategoryName")
    typeCode = request.POST.get("sourceType")
    branchId = request.POST.get("branch")
    branch = Branch.objects.get(id=branchId)
    if not categoryCode:
        res = {"error": 1, "msg": "信息不全"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    q = SourceCategory.objects.filter(branch=branch)
    q2 = q.filter(categoryCode=categoryCode)
    if q2.count() >= 1:
        res = {"error": 1, "msg": "已存在"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    sourceCategory = SourceCategory()
    sourceCategory.categoryCode = categoryCode
    sourceCategory.categoryName = categoryName
    sourceCategory.typeCode = typeCode
    sourceCategory.branch = branch
    sourceCategory.save()
    res = {"error": 0, "msg": "注册成功"}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def addSource(request):
    categoryCode = request.POST.get("sourceCategoryCode")
    typeCode = request.POST.get("sourceType")
    branchId = request.POST.get("branch")
    branch = Branch.objects.get(id=branchId)
    sourceName = request.POST.get("sourceName")
    contact = request.POST.get("contact")
    mobile = request.POST.get("mobile")
    weixin = request.POST.get("weixin")
    sourceCode = request.POST.get("sourceCode")
    deleted = request.POST.get("deleted")

    if not sourceName:
        res = {"error": 1, "msg": "信息不全"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    q = Source.objects.filter(branch=branch)
    q2 = q.filter(sourceName=sourceName)
    if q2.count() >= 1:
        res = {"error": 1, "msg": "已存在"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    source = Source()
    source.categoryCode = categoryCode
    source.sourceName = sourceName
    source.typeCode = typeCode
    source.branch = branch
    source.contact = contact
    source.mobile = mobile
    source.weixin = weixin
    source.sourceCode = sourceCode
    if deleted:
        source.deleted = int(deleted)
    source.save()
    res = {"error": 0, "msg": "注册成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def api_save_demo(request, demo_oid):
    isDemo = request.POST.get("isDemo")
    demo_info = request.POST.get("demo_info")
    if isDemo:
        isDemo = 1
    try:
        demo = GradeClass.objects.get(id=demo_oid)
        if demo:
            demo.info = demo_info
            demo.demoIsFinish = isDemo
            demo.save()
            if demo.students:
                for student in demo.students:
                    student.isDemo = isDemo
                    student.save()
    except:
        res = {"error": 1, "msg": "学生错误"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    res = {"error": 0, "msg": "保存成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def api_search_user(request):
    keyword = request.POST.get("keyword")
    students = Student.objects.filter(code=keyword)
    res = {"error": 0, "msg": "保存成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def getByOids(request):
    oids = request.POST.get("ids")
    ids = oids.split("-")
    names = []
    for id in ids:
        try:
            s = Student.objects.get(id=id)
            names.append(s.name)
        except:
            {"error": 1, "0msg": "no data found"}

    res = {"error": 0, "names": names}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def sms(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.GET.get("student_oid")
    template_oid = request.GET.get("template_oid")
    student = None
    template = None
    demo = GradeClass()
    txt = ''
    txt2 = ''
    try:
        student = Student.objects.get(id=student_oid)
        if student.prt1.find(u'爸') or student.prt1.find(u'妈'):
            student.prt1 = student.prt1
        else:
            student.prt1 = u'家长'
        if student.demo:
            for demo_oid in student.demo:
                try:
                    d = GradeClass.objects.get(id=demo_oid)
                    if d and d.demoIsFinish==None and d.start_date.strftime('%Y-%m-%d')>=getDateNow().strftime('%Y-%m-%d'):
                        demo = d
                        break
                except:
                    errormsg = 1
        dt = ''
        try:
            dt = demo.start_date.strftime('%m-%d')+' '+demo.school_time.strftime('%H-%i')
        except:
            dt = ''
        try:
            if template_oid:
                template = SMSTemplate.objects.get(id=template_oid)
            else:
                ts = SMSTemplate.objects.filter(branch=login_teacher.branch)
                if ts:
                    template = ts[0]
        except:
            errormsg = 1
        if template:
            txt = template.txt

            txt = txt.replace(u'{孩子名}',student.name)
            txt = txt.replace(u'{家长称呼}',student.prt1)
            txt = txt.replace(u'{老师名}',login_teacher.name2)
            try:
                txt = txt.replace(u'{上课时间}',demo.start_date.strftime('%m-%d')+' '+demo.school_time.strftime('%H-%i'))
            except:
                txt = txt.replace(u'{上课时间}','')
        else:
            txt = student.name + student.prt1 + u'您好！我是真朴儿童围棋教室新宫槐房万达校区的' + login_teacher.name2+u'老师。我们已经为' + student.name+u'小朋友安排了'+ dt + u'的体验课，请爸爸妈妈陪同孩子一块参与。地址：新宫槐房万达二层2061真朴儿童围棋,电话：010-67916580,收到请回复“收到”，谢谢！【真朴儿童围棋教室】'

        txt2 = txt
    except Exception, e:
        errormsg = 1
    return render(request, 'studentSms.html',{"student":student,
                                              "template":template,
                                              "txt":txt,
                                              "txt2":txt2,
                                              "login_teacher":login_teacher,
                                              "demo":demo})

def smsTemplateEdit(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    template_oid = request.GET.get("template_oid")
    template = None
    try:
        template = SMSTemplate.objects.get(id=template_oid)
    except Exception, e:
        template = None
    return render(request, 'smsTemplateEdit.html',{"template":template,
                                              "login_teacher":login_teacher})

def api_saveSMSTemplate(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    template_oid = request.POST.get("template_oid")
    branch_oid = request.POST.get("branch_oid")
    if not branch_oid:
        branch_oid = login_teacher.branch
    default =  request.POST.get("default")
    txt =  request.POST.get("txt")
    try:
        if default == '1':
            isDefault = 1
        else:
            isDefault = 0
        try:
            template = SMSTemplate.objects.get(id=template_oid)
        except:
            template = SMSTemplate()
        if template == None:
            template = SMSTemplate()
        template.txt = txt
        template.isDefault = isDefault
        template.branch = login_teacher.branch
        template.save()
        res = {"error": 0, "msg": "保存成功"}
    except Exception,e:
        res = {"error":1,"msg":"err"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def showSMSTemplates(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch_oid = request.GET.get("branch_oid")
    if not branch_oid:
        branch_oid = login_teacher.branch
    templates = []
    try:
        templates = SMSTemplate.objects.filter(branch=branch_oid)
    except Exception, e:
        templates = None
    return render(request, 'smsTemplates.html',{"templates":templates,
                                                "login_teacher":login_teacher})
def uploadPic(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    student_oid = request.GET.get("student_oid")

    teacher_oid = login_teacher.id
    try:
        teacher_oid = Student.objects.get(id=student_oid).teacher.id
    except:
        teacher_oid = login_teacher.id
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PicForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            uploadFile = request.FILES['picFile']
            si = uploadFile.size
            t,filedate,relaPath = utils.handle_uploaded_image(uploadFile,login_teacher.branch,student_oid)
            try:
                studentFile = StudentFile.objects.get(student=student_oid,filename=t)
                return HttpResponseRedirect('/go2/regUser/studentInfo/'+student_oid)
            except:
                studentFile = StudentFile()
                studentFile.student = Student.objects.get(id=student_oid)
                teacher = studentFile.student.teacher
                if not teacher:
                    teacher = studentFile.student.regTeacher
                teacherId = None
                if teacher:
                    teacherId = str(teacher.id)
                if teacherId:
                    studentFile.teacher = teacherId
                studentFile.filename = t
                studentFile.filepath = login_teacher.branch+'/'+student_oid+'/'
                studentFile.fileCreateTime = getDateNow()
                studentFile.branch = str(studentFile.student.branch.id)
                studentFile.save()

            return HttpResponseRedirect('/go2/regUser/studentInfo/'+student_oid)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PicForm()
    return render(request, 'uploadPic.html', {'student_oid':student_oid,
                                              'teacher_oid':teacher_oid,
                                              'form': form})

def removeDup(request):
    msg = "删除不成功"
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < 5:
        msg = "无权限"
    else:
        student_oid = request.GET.get("id")

        try:
            student = Student.objects.get(id=student_oid)
            if login_teacher.username == 'patch' or login_teacher.username == 'patch2' or login_teacher.username == 'patch3' or login_teacher.username == 'patch4':
                student.delete()
                msg = "删除成功"

            #===================================================================
            # elif student.gradeClass:
            #     msg = "有班级不能删"
            # elif student.demo:
            #     msg = "有试听不能删除"
            #===================================================================
            elif Lesson.objects.filter(student=student_oid).count()>0:  # @UndefinedVariable
                msg = "有课不能删除"
            elif student.dup == -1:
                student.delete()
                msg = "删除成功"
            elif  login_teacher.role == 7:
                student.delete()
                msg = "删除成功"
        except Exception,e:
            msg = e

    return HttpResponseRedirect('/go2/regUser/studentList?msg='+msg)

def removePic(request):
    import os
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.GET.get("student_oid")
    file_oid = request.GET.get("file_oid")
    try:
        studentFile = StudentFile.objects.get(id=file_oid)
        if studentFile:
            filepath = BASE_DIR+USER_IMAGE_DIR+login_teacher.branch+'/'+student_oid+'/'+studentFile.filename
            studentFile.delete()
            os.remove(filepath)
    except Exception,e:
        errormsg = 1

    return HttpResponseRedirect('/go2/regUser/studentInfo/'+student_oid)



def excelUser(request):
    branch_oid = request.POST.get("bid")
    filepath = request.POST.get("filepath")
    index = utils.getUserFromExcel(filepath, branch_oid)
    res = {"error": 0, "msg": str(index)+"条记录保存成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def removeTrack(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    oid = request.POST.get("oid")
    try:
        track = StudentTrack.objects.get(id=oid)
        if track:
            track.deleted = 1
            track.save()
            res = {"error": 0, "msg": "删除成功"}
        else:
            res = {"error": 1, "msg": "未找到"}
    except Exception,e:
        errormsg = 1
        res = {"error":1,"msg":e}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def userShare(request):
    ip = http.getVisitIp(request)
    id = request.GET.get("id")
    file_oid = request.GET.get("file_oid")
    s = Student.objects.get(id=id)
    page = 'userShare'
    studentFiles = StudentFile.objects.filter(student=s.id).order_by("order","fileCreateTime")
    teacher = None
    if s.teacher:
        try:
            teacher = str(s.teacher.id)
        except:
            teacher = None
    if not teacher:
        try:
            teacher = str(s.regTeacher.id)
        except:
            teacher = None
    branch = None
    if s.branch:
        branch = str(s.branch.id)
    student = None
    if s:
        student = str(s.id)
    pageVisit(branch,student,teacher,page,ip)

    iconUrl = '/go_static/img/logo.png'
    if studentFiles and len(studentFiles)>0:
        pic = studentFiles[0]
        iconUrl = USER_IMAGE_DIR+pic.filepath+pic.filename
    token = http.getAccessToken()
    ticket = http.getJsapiTicket(token)

    url = 'http://www.go2crm.cn/go2/regUser/userShare?id='+id+'&file_oid='+file_oid
    fromMessage = request.GET.get("from")
    if fromMessage:
        url = url + '&from=' + fromMessage

    sign = Sign(ticket, url)
    res,string1 = sign.sign()

    return render(request, 'share.html',{
                                "ticket":ticket,'res':res,"string1":string1,
                                "appId":constant.APPID,"url":url,"iconUrl":iconUrl,
                                'file_oid':file_oid,'s':s,'files':studentFiles})

def picMemo(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    memo = request.POST.get("memo")
    orderStr = request.POST.get("order")
    try:
        image = StudentFile.objects.get(id=id)
        order = 100
        if orderStr:
            try:
                order = int(orderStr)
            except:
                order = 100
        if image:
            pics = StudentFile.objects.filter(student=image.student)
            for pic in pics:
                if not pic.order:
                    pic.order = 100
                    pic.save()
            image.memo = memo
            image.order = order
            image.save()
            res = {"error": 0, "msg": "成功"}
        else:
            res = {"error": 1, "msg": "未找到"}
    except Exception,e:
        res = {"error":1,"msg":e}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
