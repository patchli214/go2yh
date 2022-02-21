#!/usr/bin/env python
# -*- coding:utf-8 -*-
from teacher.views import login
import time
import random
__author__ = 'patch'
from mongoengine.queryset.visitor import Q
import os,datetime
import itertools,json
from go2.settings import BASE_DIR,USER_IMAGE_DIR
from operator import attrgetter
from django.http import HttpResponse,HttpResponseRedirect
from datetime import timedelta
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from statistic.models import *
from branch.models import Branch,City
from regUser.models import Student,StudentFile,GradeClass,Contract,ContractType
from teacher.models import Login_teacher
from teacher.models import Teacher
from gradeClass.models import Lesson
from student.models import User,History, Suspension, Question
from teacher.models import Target
from django.views.decorators.csrf import ensure_csrf_cookie
from tools.utils import checkCookie,getDateNow,getWeekBegin,getTeachers
from tools import utils,http,constant
from tools.http import pageVisit,teacherlogin_zhenpuweiqi_com,getUser
from tools.sign import Sign
from django.views.decorators.csrf import  csrf_exempt
from regUser.views import saveRemind

@ensure_csrf_cookie
# Create your views here.

def titleLogin(request):
    iconUrl = '/go_static/img/logo.png'
    return render(request, 'titleLogin.html', {'iconUrl':iconUrl})

def title(request):
    studentId = request.GET.get("studentId")
    uname = request.GET.get("uname")

    if not studentId:
        query = Q(name=uname)
        users = User.objects.filter(query)  # @UndefinedVariable
        if users and len(users) > 0 :
            user = users[0]
            studentId = str(user.student.id)
    user = None
    try:
        student = Student.objects.get(id=studentId)  # @UndefinedVariable
    except:
        ret = {"err":u"没有这个学生"}
        return http.JSONResponse(ret)  # @UndefinedVariable
    try:
        users = User.objects.filter(student=studentId).order_by("-id")  # @UndefinedVariable
        user = None
        if users and len(users) > 1:
            user = users[0]
            for u in users:
                if u.id != user.id:
                    u.delete()
        elif users and len(users) == 1:
            user = users[0]
        else:
            user = User(student=student.id)
            user.name = student.name
    except Exception,e:
        user = User(student=student.id)
        user.name = student.name
    iconUrl = '/go_static/img/logo.png'
    userPic = "/go_static/img/bunny.png"
    studentFiles = None
    query = Q(student=studentId)&Q(fileType=1)
    studentFiles = StudentFile.objects.filter(query).order_by('order')  # @UndefinedVariable
    if studentFiles and len(studentFiles)>0:
        pic = studentFiles[0]
        userPic = USER_IMAGE_DIR+pic.filepath+pic.filename

    matchs = user.history_total_match_count
    quests = user.history_total_question_count
    title = ''
    if quests < 800 and matchs < 400:
        title = u'童子'
    if quests >= 800 and quests < 6000  and matchs < 400:
        title = u'骑士'
    if quests >= 6000 and quests < 10000  and matchs < 400:
        title = u'智者'
    if quests >= 10000 and quests < 20000  and matchs < 1000:
        title = u'大师'
    if quests >= 20000 and matchs < 1000:
        title = u'魔法师'
    if quests < 10000  and matchs >= 400:
        title = u'圣斗士'
    if quests >= 10000 and matchs >= 1000:
        title = u'王者'

    token = http.getAccessToken()
    ticket = http.getJsapiTicket(token)
    url = 'http://www.go2crm.cn/go2/student/habit?studentId='+studentId
    fromMessage = request.GET.get("from")
    if fromMessage:
        url = url + '&from=' + fromMessage
    sign = Sign(ticket, url)
    res,string1 = sign.sign()


    return render(request, 'title.html', {"imagePath":USER_IMAGE_DIR,
                                "student":student,
                                "ticket":ticket,'res':res,"string1":string1,
                                "appId":constant.APPID,"url":url,"iconUrl":iconUrl,
                                "userPic":userPic,"title":title,
                                'studentFiles':studentFiles,"user":user})

def studentDo(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    query = Q(name__contains='hf')
    students = User.objects.filter(query)  # @UndefinedVariable
    begin = datetime.datetime.strptime("20171231","%Y%m%d")
    end = datetime.datetime.strptime("20190101","%Y%m%d")
    print begin
    temp = []
    print len(students)
    for s in students:
        query = Q(user=s.id)&Q(type=5)&Q(date__gt=begin)&Q(date__lt=end)
        hs = History.objects.filter(query)  # @UndefinedVariable
        print hs._query

        sd = 0
        for h in hs:
            try:
                sd = sd + int(h.memo)
            except:
                err = 0
        print sd
        if sd > 0:
            s.memo = sd
            temp.append(s)
    for s in temp:
        print s.name
        print s.memo
    return render(request, 'studentDo.html', {
        "students":temp
                                })

def habit(request):
    studentId = request.GET.get("studentId")
    goid = request.GET.get("goid")
    #mobile = request.GET.get("mobile")
    user = None
    history = None
    studentFiles = None
    try:
        student = Student.objects.get(id=studentId)  # @UndefinedVariable
    except:
        ret = {"err":u"没有这个学生"}
        return http.JSONResponse(ret)  # @UndefinedVariable
    try:
        users = User.objects.filter(student=studentId).order_by("-id")  # @UndefinedVariable
        user = None
        if users and len(users) > 1:
            user = users[0]
            for u in users:
                if u.id != user.id:
                    u.delete()
        elif users and len(users) == 1:
            user = users[0]
        else:
            user = User(student=student.id)
            user.name = student.name
    except Exception,e:
        user = User(student=student.id)
        user.name = student.name

    if user:
        try:
            query = Q(user=user.id)&(Q(type=4)|Q(type=5))
            history = History.objects.filter(query).order_by("-date")  # @UndefinedVariable


            temp = []
            ldate = None
            has4 = None
            has5 = None
            for h in history:
                if h.date != ldate:
                    if has4 and has5:
                        hall = has4
                        hall.memo = hall.memo + ', ' + has5.memo
                        temp.append(hall)

                    if has4 and not has5:
                        temp.append(has4)

                    if has5 and not has4:
                        temp.append(has5)

                    ldate = h.date
                    hall = None
                    has4 = None
                    has5 = None

                if h.type == 4 and h.memo:
                    if h.memo.find('|') > -1:
                        h.memo = h.memo[0:h.memo.find('|')]
                    h.memo = u'在线下棋'+h.memo+u'盘'
                    has4 = h
                if h.type == 5 and h.memo:
                    h.memo = u'做了'+h.memo+u'题'
                    has5 = h
            history = temp
            lastday = utils.getDateNow().strftime("%Y-%m-%d")
            print lastday
            temp = []
            for h in history:
                hdate = (h.date + timedelta(days=1)).strftime("%Y-%m-%d")
                if hdate == lastday:
                    temp.append(h)
                    lastday = h.date.strftime("%Y-%m-%d")
                else:
                    break
            history = temp
        except Exception,e:
            print e
            history = None
    else:
        user = User()

    days = 0
    try:
        days = len(history)
    except:
        days = 0


    iconUrl = '/go_static/img/logo.png'
    if studentFiles and len(studentFiles)>0:
        pic = studentFiles[0]
        iconUrl = USER_IMAGE_DIR+pic.filepath+pic.filename
    token = http.getAccessToken()
    ticket = http.getJsapiTicket(token)


    url = 'http://www.go2crm.cn/go2/student/habit?studentId='+studentId
    fromMessage = request.GET.get("from")
    if fromMessage:
        url = url + '&from=' + fromMessage

    sign = Sign(ticket, url)
    res,string1 = sign.sign()

    userPic = "/go_static/img/bunny.png"
    return render(request, 'habit.html', {"imagePath":USER_IMAGE_DIR,
                                "history":history,"student":student,
                                "ticket":ticket,'res':res,"string1":string1,
                                "appId":constant.APPID,"url":url,"iconUrl":iconUrl,
                                "days":days,"userPic":userPic,
                                'studentFiles':studentFiles,"user":user})





def achievement(request):
    port = request.META['SERVER_PORT']
    thisurl = request.get_full_path()
    if port == '443':
        thisurl = 'https://' + request.get_host() + thisurl
    else:
        thisurl = 'http://' + request.get_host() + thisurl

    print thisurl
    studentId = request.GET.get("studentId")
    goid = request.GET.get("goid")
    beginStr = request.GET.get("begin")
    endStr = request.GET.get("end")
    begin = None
    end = None
    match = 0
    question = 0
    if beginStr:
        try:
            begin = datetime.datetime.strptime(beginStr,"%Y-%m-%d")
        except:
            beginStr = None
    if endStr:
        try:
            end = datetime.datetime.strptime(endStr,"%Y-%m-%d")
        except:
            endStr = None
    user = None
    history = None
    studentFiles = None
    target = None
    try:
        student = Student.objects.get(id=studentId)  # @UndefinedVariable
    except:
        ret = {"err":u"没有这个学生"}
        print ret
        return http.JSONResponse(ret)  # @UndefinedVariable
    try:

        users = User.objects.filter(student=studentId).order_by("-id")  # @UndefinedVariable
        user = None
        if users and len(users) > 1:
            user = users[0]
            for u in users:
                if u.id != user.id:
                    u.delete()
        elif users and len(users) == 1:
            user = users[0]
        else:
            user = User(student=student.id)
            user.name = student.name

        if user.targets and len(user.targets) > 0:
            for t in user.targets:
                if not target:
                    target = t
                elif target.beginDate < t.beginDate:
                    target = t
    except Exception,e:
        print e
        user = User(student=student.id)
        user.name = student.name

    #成就-星际考、证书等
    badges = None
    if user:
        query = (Q(type=2)|Q(type=3)|Q(type=8))&Q(user=user.id)
        badges = History.objects.filter(query).order_by("type","date")  # @UndefinedVariable

        try:
            qdate = None
            qdate2 = None
            qdate3 = None
            if begin:
                qdate = Q(date__gte=begin)
                qdate2 = Q(lessonTime__gte=begin)
                qdate3 = Q(fileCreateTime__gte=begin)
                if end:
                    qdate = qdate&Q(date__lte=end)
                    qdate2 = qdate2&Q(lessonTime__lte=end)
                    qdate3 = qdate3&Q(fileCreateTime__lte=end)

            elif end:
                qdate = Q(date_lte=end)
                qdate2 = Q(lessonTime__lte=end)
                qdate3 = Q(fileCreateTime__lte=end)

            query = Q(user=user.id)
            if qdate:
                query = query&qdate
            history = History.objects.filter(query).order_by("-date")  # @UndefinedVariable
            query = Q(student=studentId)&(Q(type=1)|Q(type=3))&Q(checked=True)#&Q(value__ne=0)
            if qdate2:
                query = query&qdate2
            lessons = Lesson.objects.filter(query).order_by("-lessonTime")  # @ @UndefinedVariable
            ls = None
            if len(lessons)>0:
                student.lessons = len(lessons)
                query = Q(gradeClass=lessons[0].gradeClass)&Q(type=0)&Q(checked=True)
                if qdate2:
                    query = query&qdate2
                ls = Lesson.objects.filter(query).order_by("-lessonTime")  # @UndefinedVariable
                i = 0
                for l in ls:
                    has = False
                    for ll in lessons:
                        if ll.lessonTime == l.lessonTime and ll.checked:
                            has = True
                            i = i + 1
                            break
                    if not has:
                        break

                user.lessonContinue = i

            temp = []
            ldate = None
            has4 = None
            has5 = None
            #lastIs4or5 = False
            ldate2 = None
            for h in history:
                if h.date != ldate:
                    if has4 and has5:
                        hall = has4
                        hall.memo = hall.memo + ', ' + has5.memo
                        temp.append(hall)

                    if has4 and not has5:
                        temp.append(has4)

                    if has5 and not has4:
                        temp.append(has5)

                    ldate = h.date
                    hall = None
                    has4 = None
                    has5 = None
                if h.type == 1:
                    t = u'努力下棋，升了'
                    if h.memo[0:1] == '-':
                        h.memo = h.memo[1:len(h.memo)]
                        h.memo = t+h.memo+'K'
                        temp.append(h)
                if h.type == 2 or h.type == 3 or h.type == 6  or h.type == 8:
                    temp.append(h)
                if h.type == 4 and h.memo:
                    try:
                        ss = h.memo.split('|')
                        if len(ss) > 0:

                            match = match + int(ss[0])
                    except:
                        err = 1
                    h.memo = u'在线下棋'+h.memo+u'胜'
                    has4 = h
                if h.type == 5 and h.memo:
                    try:
                        question = question + int(h.memo)
                    except:
                        err = 1
                    h.memo = u'做了'+h.memo+u'题'
                    has5 = h
                if h.type == 11 and h.memo:
                    has11 = True
                    sp = h.memo.split(',')
                    h.memo = u'本周做题数'+sp[0]+u',下棋'+sp[1]+u'盘'
                    question = question + int(sp[0])
                    match = match + int(sp[1])
                    temp.append(h)

            if begin or end:
                    if has4 and has5:
                        hall = has4
                        hall.memo = hall.memo + ', ' + has5.memo
                        temp.append(hall)

                    if has4 and not has5:
                        temp.append(has4)

                    if has5 and not has4:
                        temp.append(has5)
            history = temp
            add = False
            for l in lessons:
                h = History()
                h.type = 0
                h.user = user
                h.date = l.lessonTime
                h.memo1 = ' '
                if l.memo and len(l.memo)>0:
                    h.memo = l.memo

                    if h.memo.find(u'[上课]') == 0:
                        h.memo1 = h.memo[4:len(h.memo)]
                        if h.memo.find(u'[表现]') > -1:
                            h.memo1 = h.memo[4:h.memo.find(u'[表现]')]
                            h.memo2 = h.memo[h.memo.find(u'[表现]')+4:len(h.memo)]

                history.append(h)
                add = True
            if add:
                history = sorted(history, key=attrgetter('date'),reverse=True)
            query = Q(student=user.student.id)
            if qdate3:
                query = query&qdate3
            query = query&Q(filename__ne='refundApp.jpg')
            studentFiles = StudentFile.objects.filter(query).order_by("order","fileCreateTime")  # @UndefinedVariable
        except Exception,e:
            print e
            history = None
    else:
        user = User()


    voucher = 0
    try:
        voucher = int(user.lessonContinue/12)
    except:
        voucher = 0

    iconUrl = '/go_static/img/logo.png'
    if studentFiles and len(studentFiles)>0:
        pic = studentFiles[0]
        iconUrl = USER_IMAGE_DIR+pic.filepath+pic.filename
    res = http.getJieli360WXToken()
    #print res
    token = res['access_token']
    #token = http.getAccessToken()
    ticket = http.getJsapiTicket(token)
    #print ticket
    #url = 'https://rang.jieli360.com/go2/student/achievement?studentId='+studentId
    url = thisurl
    fromMessage = request.GET.get("from")
    #if fromMessage:
    #    url = url + '&from=' + fromMessage
    print url
    sign = Sign(ticket, url)
    res,string1 = sign.sign()
    if begin or end:
        user.history_total_match_count = match
        user.history_total_question_count = question
    else:
        beginStr = None
        endStr = None
    nowPercent = 0
    unPercent = 100
    if user.level and target:
        startDate = target.beginDate
        now = utils.getDateNow(8)
        days = (now - startDate).days
        if days < 183:
            nowPercent = float(days)*1.5/float(365)*100
        else:
            nowPercent = float(days)/float(365)*100
        nowPercent = int(round(nowPercent))
        if nowPercent < 10:
            nowPercent = 10
        unPercent = 100 - nowPercent - 10
        start = constant.GO_LEVEL[target.beginLevel]
        quarter = constant.GO_LEVEL[target.quarterTarget]
        halfyear = constant.GO_LEVEL[target.halfyearTarget]
        end = constant.GO_LEVEL[target.yearTarget]
        nowlevel = constant.GO_LEVEL[user.level]


    return render(request, 'student.html', {"imagePath":USER_IMAGE_DIR,
                                "history":history,"student":student,"badges":badges,
                                "voucher":voucher,"begin":beginStr,"end":endStr,
                                "ticket":ticket,'res':res,"string1":string1,
                                "appId":constant.APPID,"url":url,"iconUrl":iconUrl,
                                "nowPercent":nowPercent,"unPercent":unPercent,
                                'studentFiles':studentFiles,"user":user,"target":target})


def tweet(request):
    iconUrl = '/go_static/img/logo.png'
    res = http.getJieli360WXToken()
    token = res['access_token']
    #token = http.getAccessToken()
    ticket = http.getJsapiTicket(token)
    url = request.build_absolute_uri()
    url = 'http://rang.jieli360.com/go2/student/tweet'
    fromMessage = request.GET.get("from")
    bid = request.GET.get("bid")
    branch = None
    print bid
    try:
        branch = Branch.objects.get(branchCode=bid)  # @UndefinedVariable
    except:
        branch = None
    tel = ''
    if branch:
        tel = branch.branchTel
    #print fromMessage
    if not fromMessage and branch:
        url = url + '?bid='+bid
    if fromMessage and branch:
        url = url + '?bid='+bid+'&from=' + fromMessage
    if fromMessage and not branch:
        url = url + '?from=' + fromMessage

    isapp = request.GET.get("isappinstalled")
    if isapp:
        url = url + '&isappinstalled=' + isapp
    #print url
    url = request.build_absolute_uri()
    sign = Sign(ticket, url)
    res,string1 = sign.sign()
    #page = Page()
    student = Student()
    student.branch = None
    print tel
    return render(request, 'tweet.html', {"imagePath":USER_IMAGE_DIR,"tel":tel,"bid":bid,
                                "ticket":ticket,'res':res,"string1":string1,
                                "appId":constant.APPID,"url":url,"iconUrl":iconUrl
                                })
@csrf_exempt
def api_tweet(request):
    print 'in-----'
    tel = request.POST.get("tel")
    if not tel:
        tel = ''
    if len(tel) < 8:
        res = {"error": 1,"msg":"手机号码过短"}
        print 'err'
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    name = request.POST.get("name")
    if not name:
        name = ''
    print name
    bid = request.POST.get("bid")
    print bid
    branch = None
    try:
        branch = Branch.objects.get(branchCode=bid)  # @UndefinedVariable
    except:
        branch = Branch.objects.get(id=constant.NET_BRANCH)  # @UndefinedVariable

    query = (Q(prt1mobile=tel)|Q(prt1mobile=tel))&Q(regBranch=branch.id)
    bs = Student.objects.filter(query)  # @UndefinedVariable
    student = None

    datenow = utils.getDateNow(8)
    if bs and len(bs) > 0:
        student = bs[0]
    else:

        student = Student()
        student.regBranch = branch
        student.branch = branch
        student.regBranchName = branch.branchName
        student.branchName = branch.branchName
        student.prt1mobile = tel
        student.name = name
        student.sourceType = 'C'
        student.callInTime = datenow
        student.regTime = datenow
        student.save()

    remTeacher = None
    try:
                query = Q(branch=student.branch)&Q(role=5)&Q(status__gt=-1)
                remTeacher = Teacher.objects.filter(query)[0]  # @UndefinedVariable
    except:
                remTeacher = None
    if not remTeacher:
                query = Q(branch=student.branch)&Q(role=7)&Q(status__gt=-1)
                remTeacher = Teacher.objects.filter(query)[0]  # @UndefinedVariable
    print '111'
    teacher_list = []
    print '222'
    teacher_list.append(remTeacher)

    print '333'
    try:
        saveRemind(None,student,teacher_list,datenow,u'2019开学礼包转介',None)
    except Exception,e:
        print e

    print 'yyy'
    res = {"error": 0}
    print 'END'
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


def students(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    searchName = request.GET.get("searchName")
    searchTel = request.GET.get("searchTel")
    res = None
    query = Q(branch=login_teacher.branch)&Q(siblingId=None)
    if login_teacher.role < 5:
        query = (query)&(Q(teacher=login_teacher.id)|Q(regTeacher=login_teacher.id))
    query = (query)&Q(status=1)
    res = Student.objects.filter(query)  # @UndefinedVariable
    datenow = utils.getDateNow()
    temp = []
    #print res._query
    #print len(res)
    for s in res:
        try:
            days = (datenow-s.birthday).days
            y = days/365
            m = days%365/30
            s.yearMonth = str(y)+'.'+str(m)
            if m == 0:
                s.yearMonth = str(y)
        except Exception,e:
            err = 1

        try:

            if s.contractDeadline < datenow:
                s.canStop = True
        except:
            s.canStop = False

        try:
            gradeClass = GradeClass.objects.get(id=s.gradeClass)  # @UndefinedVariable
            if gradeClass:
                day = u'周'
                if gradeClass.school_day == 1:
                    day = day + u'一'
                if gradeClass.school_day == 2:
                    day = day + u'二'
                if gradeClass.school_day == 3:
                    day = day + u'三'
                if gradeClass.school_day == 4:
                    day = day + u'四'
                if gradeClass.school_day == 5:
                    day = day + u'五'
                if gradeClass.school_day == 6:
                    day = day + u'六'
                if gradeClass.school_day == 7:
                    day = day + u'日'
            s.className = s.teacherName+day + gradeClass.school_time

        except:
            gradeClass = None
        isNormal = False
        try:
            for sc in s.contract:

                if sc.contractType.type == 0:
                    isNormal = True
                    break
        except:
            doFixContract(s.contract,s.branch.city)
            isNormal = True
            err = 1
        if isNormal:
            if (s.siblingName and len(s.siblingName) > 0) or (s.siblingName2 and len(s.siblingName2) > 0) or s.siblingName3 and len(s.siblingName3) > 0:
                #print  'sibling!'
                query = Q(siblingId=str(s.id))
                siblings = Student.objects.filter(query)  # @UndefinedVariable
                #print len(siblings)
                for ss in siblings:
                    #print ss.name
                    if ss not in temp:
                        #print 'add'
                        temp.append(ss)
            if s not in temp:
                temp.append(s)
        else:
            print s.id
            s.status = 0
            s.save()
    res = temp

    response = render(request, 'students.html', {"login_teacher":login_teacher,
                                             "students":res,"datenow":datenow,
                                             "searchName":searchName,
                                             "searchTel":searchTel,
                                             })
    response.set_cookie("mainurl",'/go2/student/students')
    contractFrom = request.path + '?' + request.META['QUERY_STRING']
    response.set_cookie("contractFrom",contractFrom)
    return response



    return


#没有合同类型缠裹10周的合同，添加合同类型
def doFixContract(contracts,city):
    ct = None
    query = Q(city=city)&Q(duration__gte=10)&Q(deleted__ne=1)

    cts = ContractType.objects.filter(query).order_by("duration")  # @UndefinedVariable
    if cts and len(cts) > 0:
        for c in cts:
            ct = c
            break
    if ct:
        for c in contracts:
            try:
                if c.weeks > 10 and not c.contractType:
                    c.contractType = ct
                    c.save()
            except:
                err = 1


def getStudentLessons(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    sid = request.GET.get("sid")
    try:
        s = Student.objects.get(id=sid)  # @UndefinedVariable
        allLessons,sd,lessonLeft = utils.getLessonLeft(s)
        s.singDate = sd
        s.allLessons = allLessons
        s.lessonLeft = lessonLeft
        s.lessons = allLessons - lessonLeft
        res = {"error": 0, "all": allLessons,"left":lessonLeft,"lessons":s.lessons}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    except:
        return

def studentMemo(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    sid = request.GET.get("sid")
    student = None
    user = None
    now = utils.getDateNow(8)
    weekbegin = utils.getWeekBegin(now,1)
    day = weekbegin - timedelta(days=1)


    try:
        student = Student.objects.get(id=sid)  # @UndefinedVariable
        user = User.objects.filter(student=student.id)[0]  # @UndefinedVariable
    except:
        student = None
    histories = None
    query = Q(user=user.id)&(Q(type=2)|Q(type=3)|Q(type=6))
    histories = History.objects.filter(query).order_by("-date")  # @UndefinedVariable
    target = None
    if user.targets and len(user.targets) > 0:
        for t in user.targets:
            if not target:
                target = t
            elif target.beginDate < t.beginDate:
                target = t
    needTarget = False
    if not target:
        needTarget = True
    elif target.endDate and target.endDate <= utils.getDateNow(8):
        needTarget = True
    query = Q(date=day)&Q(user=user.id)&Q(type=11)
    h = None
    try:
        h = History.objects.get(query)  # @UndefinedVariable
        hs = h.memo.split(',')
        h.q = hs[0]
        h.m = hs[1]
    except:
        err = 1
    return render(request, 'studentMemo.html', {
                                "GO_LEVEL":constant.GO_LEVEL,"day":day,"lastWeek":h,
                                "histories":histories,"user":user,"target":target,"needtarget":needTarget
                                })
@csrf_exempt
def api_studentMemo(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    userId = request.POST.get("userId")
    typeStr = request.POST.get("type")
    dateStr = request.POST.get("date")
    memo = request.POST.get("memo")
    type = -1
    if typeStr:
        if len(typeStr) > 1:
            typeStr0 = typeStr[0:1]
            type = int(typeStr0)
            typeStr1 = typeStr[1:2]
            if typeStr1 == 'a':
                memo = u'一星考'
            if typeStr1 == 'b':
                memo = u'二星考'
            if typeStr1 == 'c':
                memo = u'三星考'
            #memo = u'通过' + memo
        else:
            type = int(typeStr)
    if type == -1:
        res = {"error": 1,"msg":"wrong type"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    date = datetime.datetime.strptime(dateStr,"%Y-%m-%d")
    user = None

    try:
        user = User.objects.get(id=userId)  # @UndefinedVariable
    except:
        user = None
    if user:
        query = Q(user=user.id)&Q(type=type)&Q(memo=memo)
        existHs = History.objects.filter(query)  # @UndefinedVariable
        if existHs and len(existHs)>0:
            res = {"error": 1,"msg":u'已录入过'}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        h = History(user=user)
        h.type=type
        h.date=date
        h.memo=memo
        h.save()
        res = {"error": 0}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def api_editTarget(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    tid = request.POST.get("tid")
    uid = request.POST.get("userId")
    user = None
    try:
        user = User.objects.get(id=uid)  # @UndefinedVariable
    except:
        res = {"error": 1,"msg":"user err"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    targets = user.targets
    if not targets:
        targets = []
    target = None
    res = {"error":0,"msg":"OK"}
    temp = []
    if not tid:
        target = Target()

    else:
        for t in targets:
            if str(t.id) == tid:
                target = t
                targets.remove(t)
                break
        print target.id
    if not target:
        target = Target()

    beginDate = None
    endDate = None
    quarterTarget = None
    halfyearTarget = None
    yearTarget = None
    beginLevel = None
    endLevel = None
    try:
        beginDate = datetime.datetime.strptime(request.POST.get("beginDate"),"%Y-%m-%d")
        #endDate = beginDate + timedelta.days(361)
        beginLevel = request.POST.get("beginLevel")
        #endLevel = request.POST.get("endLevel")
        quarterTarget = request.POST.get("quarterTarget")
        halfyearTarget = request.POST.get("halfyearTarget")
        yearTarget = request.POST.get("yearTarget")
    except:
        res = {"error": 1,"msg":"wrong input"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        target.userId = uid
        target.beginDate = beginDate
        target.endDate = endDate
        target.beginLevel = beginLevel
        target.endLevel = endLevel
        target.quarterTarget = quarterTarget
        target.halfyearTarget = halfyearTarget
        target.yearTarget = yearTarget
        target.save()
        targets.append(target)
        user.targets = targets
        user.save()
    except Exception,e:
        res = {"error": 1,"msg":str(e)}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
@csrf_exempt
def api_saveRecord(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    uid = request.POST.get("userId")
    memo = request.POST.get("memo")
    level = request.POST.get("level")
    if not memo or len(memo) == 0:
        res = {"error": 1,"msg":"memo err"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    hdateStr = request.POST.get("hdate")
    hdate = None
    if not hdateStr:
        now = utils.getDateNow(8)
        weekbegin = utils.getWeekBegin(now,1)
        hdate = weekbegin - timedelta(days=1)
    if not hdate:
      try:
        hdate = datetime.datetime.strptime(hdateStr,"%Y-%m-%d")
      except:
        res = {"error": 1,"msg":"date err"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    type = request.POST.get("type")
    type = 11
    user = None
    try:
        user = User.objects.get(id=uid)  # @UndefinedVariable
    except:
        res = {"error": 1,"msg":"user err"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    try:
        q = Q(type=type)&Q(date=hdate)&Q(user=user.id)
        hs = History.objects.filter(q)  # @UndefinedVariable
        history = None
        if hs and len(hs) > 0:
            for h in hs:
                if not history:
                    history = h
                else:
                    h.delete()
        if not history:
            history = History()
            history.date = hdate
            history.type = type
            history.user = user
        history.memo = memo
        history.level = level
        history.save()
        user.level = history.level
        user.save()
        res = {"error": 0}
    except Exception,e:
        res = {"error": 1,"msg":str(e)}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
@csrf_exempt
def api_memoDelete(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    hid = request.POST.get("hid")

    if not hid:
        res = {"error": 1,"msg":"no id"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    try:
        h = History.objects.filter(id=hid)  # @UndefinedVariable
        h.delete()
        res = {"error": 0}
    except:
        res = {"error": 1,"msg":"wrong id"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

#学籍结束，出班，合同结束，学生状态改为结束，老师不变
@csrf_exempt
def api_end(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    sid = request.POST.get("sid")
    ed = request.POST.get("endDate")

    if not sid:
        res = {"error": 1,"msg":"no id"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    datenow = utils.getDateNow()
    enddate = datenow
    try:
        enddate = datetime.datetime.strptime(ed,"%Y-%m-%d")

    except:
        enddate = datenow
    print enddate
    try:
        student = Student.objects.get(id=sid)  # @UndefinedVariable
        if student:
            query = Q(student_oid=sid)&Q(status=constant.ContractStatus.sign)
            validContracts = Contract.objects.filter(query)  # @UndefinedVariable
            for c in validContracts:
                c.status = constant.ContractStatus.finish
                c.endDate = enddate
                c.save()
            query = Q(students=student.id)
            gcs = GradeClass.objects.filter(query)  # @UndefinedVariable

            for gc in gcs:
                stus = gc.students
                temp = []
                for s in stus:
                    if s.id != student.id:
                        temp.append(s)
                gc.students = temp
                gc.save()
            student.status = constant.StudentStatus.finish
            student.save()
        res = {"error": 0}
    except Exception,e:
        res = {"error": 1,"msg":str(e)}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
@csrf_exempt
def api_suspend(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    sid = request.POST.get("sid")

    beginDateStr = request.POST.get("beginDate")
    endDateStr = request.POST.get("endDate")

    beginDate = None
    endDate = None
    if not sid:
        res = {"error": 1,"msg":"no id"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    try:
        student = Student.objects.get(id=sid)  # @UndefinedVariable

    except Exception,e:
        res = {"error": 2,"msg":'No User'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        beginDate = datetime.datetime.strptime(beginDateStr,"%Y-%m-%d")
        endDate = datetime.datetime.strptime(endDateStr,"%Y-%m-%d")
    except:
        res={'error':3,'msg':'wrong date'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    if student:
        sus = Suspension(student=sid)
        try:
            sus.branch = str(student.branch.id)
        except:
            err = 1
        sus.beginDate = beginDate
        sus.endDate = endDate
        sus.save()
        res = {"error": 0,'msg':u'保存休学成功'}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
@csrf_exempt
def api_delSuspension(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    sus = None
    if not id:
        res = {"error": 1,"msg":"no id"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    try:
        sus = Suspension.objects.get(id=id)  # @UndefinedVariable

    except Exception,e:
        res = {"error": 2,"msg":'No Sus'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        if sus:
            sus.delete()
            res = {"error": 0,'msg':u'删除成功'}
        else:
            res={'error':3,'msg':'remove err'}
    except:
        res={'error':3,'msg':'remove err'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def question(request):
    e = None
    branch = None
    bid = request.GET.get("bid")
    if not bid:
         bid = request.POST.get("bid")
    teachers = []
    name = request.POST.get("name")

    teacherId = request.POST.get("teacher")
    length = request.POST.get("length")

    res = None
    if True:

        branch = Branch.objects.get(branchCode=bid)  # @UndefinedVariable
        student = None
        if name:
            quest = None
            teacher = Teacher.objects.get(id=teacherId)  # @UndefinedVariable
            query = Q(studentName=name)&Q(branch=branch.id)&Q(teacher=teacher.id)
            try:
                quest = Question.objects.get(query)  # @UndefinedVariable
            except:
                quest = Question()

            query = Q(branch=branch.id)&Q(name=name)
            students = Student.objects.filter(query)  # @UndefinedVariable
            if students and len(students) > 0:
                student = students[0]
                quest.student = student

            quest.branch = branch

            quest.teacher = teacher
            quest.studentName = name

            quest.length = request.POST.get("length")
            quest.a1 = request.POST.get("a1")
            quest.a2 = request.POST.get("a2")
            quest.a3 = request.POST.get("a3")
            a4 =  request.POST.getlist('a4[]')

            a4str = ''
            for el in a4:
                a4str = a4str + ' ' + el
            quest.a4 = a4str
            quest.a5 = request.POST.get("a5")
            quest.a6 = request.POST.get("a6")
            quest.a7 = request.POST.get("a7")
            quest.b1 = request.POST.get("b1")
            quest.b2 = request.POST.get("b2")
            quest.b3 = request.POST.get("b3")
            quest.b4 = request.POST.get("b4")
            quest.appDate = utils.getDateNow(8)
            quest.save()
            res = "OK"

        else:
            query = Q(status__ne=-1)&Q(role__ne=5)&Q(branch=branch.id)
            teachers = Teacher.objects.filter(query)  # @UndefinedVariable

    #except Exception,e:
     #   err = e
    return render(request, 'question2.html', {
        "teachers":teachers,"branch":branch,"res":res,"err":e
                                })

def quests(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    quests = None
    query = Q(branch=login_teacher.branch)
    quests = Question.objects.filter(query).order_by("teacher")  # @UndefinedVariable
    branch = Branch.objects.get(id=login_teacher.branch)  # @UndefinedVariable
    qrcode = 'http://go2crm.cn/go2/student/question?bid='+branch.branchCode
    return render(request, 'quests.html', {"qrcode":qrcode,
        "quests":quests,"branchName":login_teacher.branchName
                                })
