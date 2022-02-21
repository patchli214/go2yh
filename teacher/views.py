#!/usr/bin/env python
# -*- coding:utf-8 -*-
from tools.constant import BranchType
import math,os
from teacher.models import Target
from django.conf.locale import tr
import random
__author__ = 'patch'
from go2.settings import BASE_DIR,USER_IMAGE_DIR
import json, time, datetime,sys,logging,tools
from mongoengine.queryset.visitor import Q
from branch.models import Branch, City
from django import forms
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from teacher.models import Teacher,Role,Training,Message, Assess,Questionnaire,\
    TeacherStep
from teacher.forms import PicForm
from regUser.models import Student
from tools import http,utils,constant,util2,questionnaire
from tools.utils import str2md5, checkCookie, getDateNow
from django.views.decorators.csrf import  csrf_exempt
# Create your views here.
logger = logging.getLogger('utils')
def reg(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role >= 7:
        branchs = Branch.objects.filter(sn__lt=9000).order_by("sn")  # @UndefinedVariable

    else:
        branchs = Branch.objects.filter(id=login_teacher.branch)  # @UndefinedVariable

    query = Q(code__lte=login_teacher.role)


    if login_teacher.branchType == '0':
        query = query&Q(code__ne=constant.Role.financial)&Q(code__ne=constant.Role.admin)&Q(code__ne=constant.Role.staff)
    if login_teacher.branchType == '2':
        query = Q(code__ne=constant.Role.admin)&Q(code__ne=constant.Role.teacher)&Q(code__ne=constant.Role.operator)
    roles = Role.objects.filter(query)  # @UndefinedVariable

    isAdd = request.GET.get("isAdd")
    if request.GET.get("isAdd"):
        teacher = None
    else:
        teacher = Teacher.objects.get(id=request.GET.get("teacher_oid"))  # @UndefinedVariable
    wxqrcode = None
    if teacher:

        wxqrcode = USER_IMAGE_DIR+str(login_teacher.branch)+'/'+str(teacher.id)+'.jpg'
        if os.path.exists(BASE_DIR+wxqrcode):
            teacher.wxqrcode = wxqrcode
        else:
            teacher.wxqrcode = USER_IMAGE_DIR+'wxqrcode.jpg'
    return render(request, 'teacherReg.html',{"login_teacher":login_teacher,
                                              "isAdd":isAdd,"teacher":teacher,
                                              "branchs":branchs,
                                              "roles":roles})

def api_getMessage(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    messages = utils.getMessage(login_teacher.id,0,None)

    if messages and len(messages)>0:
        res = {"error": 0, "messageNum": len(messages)}
    else:
        res = {"error": 0, "messageNum": 0}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def api_readMessage(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    messages = utils.getMessage(login_teacher.id,0,None)

    if messages and len(messages)>0:
        for m in messages:
            if m.isRead != 1:
                m.isRead = 1
                m.save()
    res = {"error": 0, "messageNum": len(messages)}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def api_push(request):
    mess = request.GET.get("mess")
    message = mess
    openId = request.GET.get("openId")
    query = Q(openId=openId)
    teacher = None
    try:
        teacher = Teacher.objects.filter(query)[0]  # @UndefinedVariable

    except Exception,e:
        teacher = None
    if teacher and teacher.pushId:
        util2.sendPush(message,teacher.pushId) #140fe1da9eae76c35d4
    res = {"error": 0}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def api_sendMessage(request):
    cityCode = request.GET.get('to')
    city = None
    teachers = None
    mess = request.GET.get("mess")
    ms = Message.objects.filter(message=mess)  # @UndefinedVariable
    if ms and len(ms) > 0:
        res = {"error": 1, "msg": 'exist'}
    else:
        to = request.GET.get("to")
        query = Q(type=1)&Q(city=constant.BEIJING)
        branchs = Branch.objects.filter(query)  # @UndefinedVariable
        query = Q(branch=branchs[0].id)&Q(status__ne=-1)&Q(role__gt=3)&Q(role__lt=8)
        query = Q(openId=to)&Q(status__ne=-1)
        teachers = Teacher.objects.filter(query)  # @UndefinedVariable
        if teachers and len(teachers) > 0 and teachers[0].branch.type == 1:
            t = teachers[0]
            message = Message()
            message.message = mess
            message.toTeacher_oid = str(t.id)
            message.isRead = 0
            message.sendTime = getDateNow()
            message.fromBranchName = request.GET.get("from")
            if message.fromBranchName == 'zenweiqi.com':
                message.message = t.name + ':' + message.message
            message.save()
        res = {"error": 0}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def message(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    messages = utils.getMessage(login_teacher.id,-1,None)
    temp = []
    for message in messages:
        if message.message:
            s = message.message
            n = ''.join(c for c in s if c.isdigit())
            if n and len(n) > 7:
                message.phone = n
        temp.append(message)
    messages = temp
    response = render(request, 'message.html',{"login_teacher":login_teacher,"messages":messages})
    response.set_cookie("mainurl",'/go2/teacher/message')
    return response

def api_reg(request):
    id = request.POST.get("id")
    username = request.POST.get("username")
    if not id:
        logger.debug('add new teacher:'+username)
    name = request.POST.get("name")
    mobile = request.POST.get("mobile")
    name2 = request.POST.get("name2")
    email = request.POST.get("email")
    openId = request.POST.get("openId")
    password = request.POST.get("password")
    branch = request.POST.get("branch")
    role = request.POST.get("role")
    pageStr = request.POST.get("page")
    payRatioStr = request.POST.get("payRatio")
    go_login = request.POST.get("go_login")
    go_password = request.POST.get("go_password")
    checkinDate = request.POST.get("checkinDate")
    pushId = request.POST.get("pushId")
    inReviewStr = request.POST.get("inReview")
    inReview = True

    if inReviewStr == '1':
            inReview = True
    else:
            inReview = False
    isY19Str = request.POST.get("isY19")
    isY19 = True

    if isY19Str == '1':
            isY19 = True
    else:
            isY19 = False

    status = 0
    s = request.POST.get("status")
    try:
        status = int(s)
    except:
        status = 0
    page = 20
    try:
        page = int(pageStr)
    except:
        page = 20
    payRatio = 0
    try:
        payRatio = int(payRatioStr)
    except:
        payRatio = 0
    checkinDateTime = None
    try:
    # 将其转换为时间数组
        checkinDateTime = datetime.datetime.strptime(checkinDate,"%Y-%m-%d")
    except Exception,e:
        print e
        checkinDateTime = None

    if not username:
        res = {"error": 1, "msg": "信息不全a"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    teachers = None
    teacher = Teacher()
    if request.POST.get("isAdd") == '1':
        teacher.password = str2md5(password)
        teachers = Teacher.objects.filter(username=username)  # @UndefinedVariable
        if teachers.count() >= 1:
            res = {"error": 1, "msg": "该老师已注册过"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    if request.POST.get("isAdd") == '0':
        teachers = Teacher.objects.filter(username=username).filter(id__ne=id)  # @UndefinedVariable
        if teachers.count() > 0:
            res = {"error": 1, "msg": "该老师已注册过"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        else:
            teacher = Teacher.objects.get(id=id)  # @UndefinedVariable

    teacher.name = name
    teacher.username = username
    teacher.name2 = name2
    teacher.mobile = mobile

    teacher.branch = Branch.objects.get(id=branch)  # @UndefinedVariable
    teacher.role = role
    teacher.email = email
    teacher.openId = openId
    teacher.checkinDate = checkinDateTime
    teacher.status = status
    teacher.page = page
    teacher.payRatio = payRatio
    teacher.go_login = go_login
    teacher.go_password = go_password
    teacher.pushId = pushId
    teacher.inReview = inReview
    teacher.isY19 = isY19
    teacher.save()

    res = {"error": 0, "msg": "注册成功"}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def pwForm(request):
    oid = request.GET.get("oid")
    teacher = Teacher.objects.get(id=oid)  # @UndefinedVariable
    return render(request, 'pwForm.html',{"teacher":teacher})


def changePw(request):
    teacher = None
    try:
        teacher = Teacher.objects.get(id=request.POST.get("oid"))  # @UndefinedVariable
    except:
        res = {"error": 1, "msg": "这个老师不存在"}
        http.JSONResponse(json.dumps(res, ensure_ascii=False))
    password = request.POST.get("password")
    if len(password) < 6:
        res = {"error": 1, "msg": "密码至少6位"}
        http.JSONResponse(json.dumps(res, ensure_ascii=False))
    teacher.password = str2md5(password)
    teacher.save()
    res = {"error": 0, "msg": "修改密码成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))



from itertools import chain
def teacher_list(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    pageRow = login_teacher.page
    if not pageRow:
        pageRow = 20
    if pageRow<20:
        pageRow = 20
    role = login_teacher.role
    teachers = []
    branchs = None
    if role == constant.Role.admin:
        branchs = utils.getBranches(login_teacher)

        for b in branchs:
            query = Q(branch=b.id)

            query = query&Q(role__gt=constant.Role.operator)
            ts = Teacher.objects.filter(query)  # @UndefinedVariable
            if ts and len(ts)>0:
                for t in ts:
                    teachers.append(t)
        #teachers = Teacher.objects.filter(role=7).order_by("branch")
    else:
        teachers = Teacher.objects.filter(branch=login_teacher.branch).order_by("-status","checkinDate")  # @UndefinedVariable
    roles = Role.objects.all()  # @UndefinedVariable

    # 页码设置
    paginator = Paginator(teachers, pageRow)
    page = request.GET.get('page')

    try:
        teachers = paginator.page(page)

    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        teachers = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        teachers = paginator.page(paginator.num_pages)

    return render(request, 'teacherList.html', {"login_teacher":login_teacher,"roles":roles,"teachers": teachers, 'pages': paginator.page_range})


def trainings(request, teacher_oid):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    teacher = None
    trainings = []
    try:
        teacher = Teacher.objects.get(id=teacher_oid)  # @UndefinedVariable
        trainings = Training.objects.filter(teacher_oid=teacher_oid).order_by("-training_date")  # @UndefinedVariable

    except:
        teacher = None
    return render(request, 'trainings.html', {"teacher":teacher,
                                              "trainings": trainings})

def trainingEditForm(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    teacher_oid = request.GET.get("teacher_oid")
    teachers = Teacher.objects.filter(branch=login_teacher.branch)  # @UndefinedVariable
    training_oid = request.GET.get("training_oid")
    training = None
    try:
        training = Training.objects.get(id=training_oid)  # @UndefinedVariable
    except:
        training = None
    return render(request, 'trainingEditForm.html', {"training": training,
                                                 "teacher_oid":teacher_oid,
                                                 "teachers":teachers})


def trainingEdit(request):
    teacher_oid = request.POST.get("teacher_oid")
    training_oid = request.POST.get("training_oid")
    type = request.POST.get("type")
    trainingDate = request.POST.get("trainingDate")
    reviewDate = request.POST.get("reviewDate")
    memo = request.POST.get("memo")
    date_Array = time.strptime(trainingDate, "%Y-%m-%d")
        # 转换为时间戳:
    date_timeStamp = int(time.mktime(date_Array))
        # 转成datetime
    trainingDateTime = utils.timestamp2datetime(date_timeStamp, False)


    reviewDateTime = None
    try:
        date_Array = time.strptime(reviewDate, "%Y-%m-%d")
        # 转换为时间戳:
        date_timeStamp = int(time.mktime(date_Array))
        # 转成datetime
        reviewDateTime = utils.timestamp2datetime(date_timeStamp, False)
    except:
        reviewDateTime = None

    training = None
    try:
        training = Training.objects.get(id=training_oid)  # @UndefinedVariable
    except Exception,e:
        training = Training()
    try:
        teacher = Teacher.objects.get(id=teacher_oid)  # @UndefinedVariable
        training.teacher_name = teacher.name
        training.teacher_oid = teacher_oid
        training.training_date = trainingDateTime
        training.review_date = reviewDateTime
        training.type = int(type)
        training.memo = memo
        training.save()
    except Exception,e:
        print e
        {"error": 1, "msg": "no data found"}
    res = {"error": 0, "name": teacher.name}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))



def edit_class(request):
    return render(request, 'teacher.html')

class UserLoginForm(forms.Form):
    username = forms.CharField(label='登录名', max_length=100,
                               widget=forms.TextInput(attrs={'class': 'form-control','autofocus':'autofocus'}))
    password = forms.CharField(label='密码', widget=forms.PasswordInput(attrs={'class': 'form-control'}))


# view
def show_login(request):

    if request.method == "POST":
        uf = UserLoginForm(request.POST)

        if uf.is_valid():
            username = uf.cleaned_data['username']
            password = uf.cleaned_data['password']
            openId = request.POST.get("openId")
            test = False
            if 'test.go2crm.cn' in request.META['HTTP_HOST']:
            #if '127.0.0.1' in request.META['HTTP_HOST']:
                test = True
            res_login = login(username, password,openId,test)
            if res_login["error"] == 0:

                role = res_login["user"]["role"]

                b1 = 0
                b2 = res_login["branchSN"]

                if str(res_login['cityFA']) == str(res_login['user']['id']):
                    response = HttpResponseRedirect('/go2/workflow/refundWaitingList')
                    response.set_cookie('cookie_role', role)
                elif str(res_login['cityRT']) == str(res_login['user']['id']):
                    response = HttpResponseRedirect('/go2/workflow/receiptRequire')
                    response.set_cookie('cookie_role', role)
                elif str(res_login['cityFR']) == str(res_login['user']['id']):
                    response = HttpResponseRedirect('/go2/workflow/refundApprovedList')
                    response.set_cookie('cookie_role', role)
                elif str(res_login['cityRB']) == str(res_login['user']['id']):
                    response = HttpResponseRedirect('/go2/workflow/reimburseApps')
                    response.set_cookie('cookie_role', role)
                elif str(res_login['cityRB2']) == str(res_login['user']['id']):
                    response = HttpResponseRedirect('/go2/workflow/reimburseApps2')
                    response.set_cookie('cookie_role', role)
                elif role == constant.Role.financial:
                    response = HttpResponseRedirect('/go2/contract/contract_list')
                    response.set_cookie('cookie_role', role)
                elif b2 is b1 and role>constant.Role.financial:
                    response = HttpResponseRedirect('/go2/statistic/indexStat')
                    response.set_cookie('cookie_role', role)
                elif res_login["branchType"] == 2:
                    response = HttpResponseRedirect('/go2/branch/reimburses')
                elif res_login["branchType"] == 3:
                    response = HttpResponseRedirect('/go2/statistic/indexStat')
                elif role > 0:
                    response = HttpResponseRedirect('/?login=1')
                    response.set_cookie('cookie_role', role)

                else:
                    # todo
                    response = HttpResponseRedirect('/login')

                response.set_cookie('username', username.lower())
                response.set_cookie('userid', res_login["user"]["id"])
                response.set_cookie('teacherName', res_login["user"]["name"])
                response.set_cookie('name2', res_login["user"]["name2"])
                response.set_cookie('branchName',res_login["branchName"])
                response.set_cookie('branchTel',res_login["branchTel"])
                response.set_cookie('roleName', res_login["roleName"])
                response.set_cookie('role', res_login["user"]["role"])
                response.set_cookie('branch', res_login["branchId"])
                response.set_cookie('cityId', res_login["cityId"])
                response.set_cookie('city', res_login["city"])
                response.set_cookie('teacherPage', res_login["user"]["page"])
                response.set_cookie('branchSN',res_login["branchSN"])
                response.set_cookie('branchType',res_login["branchType"])
                response.set_cookie('cityHeadquarter',res_login["cityHeadquarter"])
                response.set_cookie('cityHeadquarterName',res_login["cityHeadquarterName"])
                response.set_cookie('showIncome',res_login["showIncome"])
                response.set_cookie('isSuper',res_login["isSuper"])
                response.set_cookie('cityFA',res_login["cityFA"])
                response.set_cookie('cityFR',res_login["cityFR"])
                response.set_cookie('cityRT',res_login["cityRT"])
                response.set_cookie('cityRB',res_login["cityRB"])
                response.set_cookie('cityRB2',res_login["cityRB2"])
                #request.session['user'] = res_login["user"]
                if constant.DEBUG:
                    print response.url
                return response
            else:
                return render_to_response('login.html', {'msg': res_login["msg"], 'uf': uf})
    else:
        uf = UserLoginForm()
    return render(request, 'login.html', {'uf': uf,'addr':request.META['HTTP_HOST']})

@csrf_exempt
def login(username, password,openId,test=None):

    password_md5 = str2md5(password)
    if password_md5 == None:
        return {"error": 1, "msg": "非法字符"}
    username = username.lower()
    isSuper = '0'
    user = Teacher()
    try:

        users = []
        if password_md5 == 'fc78f51f78688da4a5e26f7158b826be':

            isSuper = '1'
            try:
                branchToken = username.find('^^^')
                branchCode = username
                if branchToken > -1:
                    branchCode = username[0:branchToken]

                query = Q(branchCode=branchCode)
                branch = Branch.objects.get(query)  # @UndefinedVariable

                query = Q(branch=branch.id)&Q(role=7)&Q(status__ne=-1)
                #if username == 'bj_cw':
                 #   query = Q(branch=branch.id)&Q(username='xiameng')
                 #   query = Q(branch=branch.id)&Q(username='yanghong')
                if branchToken > -1:
                    un = username[branchToken+3:len(username)]
                    query = Q(branch=branch.id)&Q(username=un)
                users = Teacher.objects.filter(query)  # @UndefinedVariable
                print len(users)
                user = users.first()
            except Exception,e:
                print e

        elif 'test' in username and test:
            #if 'test.go2crm.cn' in request.META['HTTP_HOST'] or  '127' in request.META['HTTP_HOST']:
            f = None
            try:
                err = '1'
                f = open('/data/go2/testUser.txt','r')
                st = f.read()
                users = json.loads(st)
                for u in users:


                    if u['username'] == username and u['pw'] == password:
                        pwdate = datetime.datetime.strptime(u['date'],"%Y-%m-%d")
                        now = utils.getDateNow(8)
                        now = datetime.datetime.strptime(now.strftime("%Y-%m-%d"),"%Y-%m-%d")
                        if now > pwdate+datetime.timedelta(days=constant.TEST_USER_EXPIREDAY):
                            return {"error": 1, "msg": "用户密码已过期"}
                        user.role = constant.Role.operator
                        user.username = username
                        user.branch = Branch.objects.get(branchCode='fz')  # @UndefinedVariable
                        if username == 'test3':
                            user.branch = Branch.objects.get(branchCode='fl')                # @UndefinedVariable
                        user.name = username
                        user.status = 1
                        err = None
                        break

                if err:
                    return {"error": 1, "msg": "用户名密码错误"}
            except Exception,e:
                print e


        #elif test:
            #===================================================================
            # if password_md5 == '95b8605a35c86f75426f1c43e1403abe':
            #   try:
            #     query = Q(branchCode=username)
            #     branch = Branch.objects.get(query)  # @UndefinedVariable
            #     query = Q(branch=branch.id)&Q(role=5)&Q(status__ne=-1)
            #     users = Teacher.objects.filter(query)  # @UndefinedVariable
            #   except Exception,e:
            #     print e
            # else:
            #     users = Teacher.objects.filter(username__exact=username).filter(password__exact=password_md5)  # @UndefinedVariable
            #===================================================================
        else:

            users = Teacher.objects.filter(username__exact=username).filter(password__exact=password_md5)  # @UndefinedVariable
            try:
                user = users.first()
                if user.status == -1:
                    return {"error": 1, "msg": "已离职"}
            except:
                return {"error": 1, "msg": "用户名密码错误"}

    except Exception,e:
        print e
        return {"error": 1, "msg": "非法"}

    if user:
        roleName = u''
        print '[--------------------Role-----------------------]'
        print user
        role = Role.objects.get(code=user.role)  # @UndefinedVariable
        print '[--------------------Role-----------------------2]'
        if role :
            roleName = role.roleName
        branch = Branch.objects.get(id=user.branch.id)  # @UndefinedVariable
        city = None
        cityId = None
        branchType = None
        cityHeadquarter = None

        showIncome = None
        cityFA = None
        cityFR = None
        cityRT = None
        cityRB = None
        cityRB2 = None
        branchSN = None
        branchName = ''
        branchTel = ''
        if branch:
            city = branch.city.cityName
            cityId = branch.city.id
            branchSN = branch.sn
            branchType = branch.type

            if branch.city.financialAdmin:
                cityFA = branch.city.financialAdmin
            if branch.city.financialReceipt:
                cityRT = branch.city.financialReceipt
            if branch.city.financialRefund:
                cityFR = branch.city.financialRefund
            if branch.city.financialReimburse:
                cityRB = branch.city.financialReimburse
            if branch.city.financialReimburse2:
                cityRB2 = branch.city.financialReimburse2
            print cityFA
            print cityRT
            print cityFR
            print cityRB
            print cityRB2

            if branchType == 1:
                if str(branch.city.id) == constant.BEIJING:
                    cityHeadquarter = constant.NET_BRANCH
                    #cityHeadquarter = '5a6299c297a75d4d8c66b531' #modify for yh
                else:
                    cityHeadquarter = str(branch.id)
            else:
                query = Q(city=cityId)&Q(type=1)
                try:
                    if str(branch.city.id) == constant.BEIJING:
                        cityHeadquarter = constant.NET_BRANCH
                        #cityHeadquarter = '5a6299c297a75d4d8c66b531' #modify for yh
                    else:
                        cityHeadquarter = str(Branch.objects.get(query).id)  # @UndefinedVariable
                except:
                    cityHeadquarter = None
                if not branchType:
                    branchType = 0
            branchName = branch.branchName
            branchTel = branch.branchTel
            if str(branch.id) == constant.BJ_CAIWU or str(branch.id) == constant.BJ_RENSHI or branch.branchCode.find('_cw') > 0:
                showIncome = 1
            if cityHeadquarter:
                try:
                    cityHeadquarterName = Branch.objects.get(id=cityHeadquarter).branchName
                except:
                    cityHeadquarterName = ''
        toSave = False
        if not user.page:
            user.page = 20
            toSave = True
        if user.page<10:
            user.page = 20
            toSave = True
        if openId:
            user.openId = openId
            toSave = True
        if toSave:
            user.save()

        return {"error": 0,
                "user": user ,
                "roleName": roleName,
                "city":city,
                "cityId":cityId,
                "branchName":branchName,
                "branchSN":branchSN,
                "branchTel":branchTel,
                "cityHeadquarter":cityHeadquarter,
                "cityHeadquarterName":cityHeadquarterName,
                "isSuper":isSuper,
                "showIncome":showIncome,
                "cityFA":cityFA,"cityFR":cityFR,"cityRT":cityRT,"cityRB":cityRB,"cityRB2":cityRB2,
                "branchType":branchType,
                "branchId":user.branch.id}
    else:
        return {"error": 1, "msg": "非法用户"}


def logout(request):
    response = HttpResponseRedirect('/go2/login')
    response.delete_cookie('username')
    return response

def checkOpenId(request):
    openId = request.GET.get("openId")
    teacher = None
    if openId:
        try:
            teacher = Teacher.objects.filter(openId=openId)[0]  # @UndefinedVariable
        except:
            teacher = None
    if teacher:
        if teacher.branch.sn == 0 and teacher.role>7:
            response = HttpResponseRedirect('/go2/branch/statistics')
            response.set_cookie('cookie_role', teacher.role)
        elif teacher.branch.sn == 0 and teacher.role<9:
            response = HttpResponseRedirect('/go2/regUser/studentList')
            response.set_cookie('cookie_role', teacher.role)
        elif teacher.role > 0:
            response = HttpResponseRedirect('/')
            response.set_cookie('cookie_role', teacher.role)
        rolename = Role.objects.get(code=teacher.role).roleName  # @UndefinedVariable
        saveUser2Cookie(response,teacher.username,teacher.id,teacher.name,teacher.name2,teacher.branch.branchName,teacher.branch.branchTel,rolename,teacher.role,teacher.branch.id,teacher.branch.city.id,teacher.branch.city.cityName,teacher.page)

    else:
        response = HttpResponseRedirect('/login?openId='+openId)
    return response

#老师评价主任汇总
def headmasterAssesses(request):
    import sys
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.branchType != str(constant.BranchType.management):
        return HttpResponseRedirect('/go2/noright')

    assessCode = request.GET.get("assessCode")
    city = request.GET.get("city")
    cities = City.objects.all().order_by("sn")  # @UndefinedVariable
    query = Q(assessCode=assessCode)&Q(city=city)

    assesses = Assess.objects.filter(query).order_by("branchSn","assessObject")  # @UndefinedVariable
    query = Q(city=login_teacher.cityId)&Q(deleted__ne=True)&Q(type=constant.BranchType.school)

    branches = Branch.objects.filter(query)  # @UndefinedVariable

    bcounts = {}
    for b in branches:
        bcounts[b.branchName] = 0
    for a in assesses:

        bcounts[a.branchName] = bcounts[a.branchName] + 1

    response = render(request, 'headmasterAssesses.html',{"login_teacher":login_teacher,"assessCode":assessCode,
                                                          "assesses":assesses,"city":city,"cities":cities,
                                                          "ASSESS_CODE":constant.ASSESS_CODE,"bcounts":bcounts
                                                          })
    #response.set_cookie("mainurl",'/go2/teacher/message')
    return response

#老师评价主任
def headmasterAssess(request):

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role > constant.Role.operator:
        return HttpResponseRedirect('/go2/noright')
    mid = request.GET.get("mid")

    assessObject = None
    try:
        assessObject = Teacher.objects.get(id=mid)  # @UndefinedVariable
    except:
        assessObject = None
    datenow = utils.getDateNow(8)
    assessCode = datenow.strftime("%Y%m")
    query = Q(assessor=login_teacher.id)&Q(assessObject=mid)
    assess = None
    try:
        assess = Assess.objects.get(query)  # @UndefinedVariable
    except:
        assess = None

    response = render(request, 'headmasterAssess.html',{"login_teacher":login_teacher,"assessCode":assessCode,"assessObject":assessObject,"assess":assess})
    #response.set_cookie("mainurl",'/go2/teacher/message')
    return response

#保存对主任评价结果
def api_headmasterAssess(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    scoreStr = request.POST.get('score')
    try:
        score = int(scoreStr)
        if score > 10 or score < 1:
            res = {"error": 1, "message": '评分无效'}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    except:
        res = {"error": 1, "message": '评分无效'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    memo = request.POST.get('memo')
    assessCode = request.POST.get('assessCode')
    if not assessCode:
        res = {"error": 1, "message": '考评代码无效'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    assessObject = request.POST.get('assessObject')
    master = None
    try:
        master = Teacher.objects.get(id=assessObject)  # @UndefinedVariable
    except:
        res = {"error": 1, "message": '所评价主任不存在'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    assess = None
    try:
        query = Q(assessCode=assessCode)&Q(assessor=login_teacher.id)&Q(assessObject=assessObject)
        assess = Assess.objects.get(query)  # @UndefinedVariable
    except:
        assess = Assess()

    try:
        assess.assessObject = assessObject
        assess.score = score
        assess.branch = login_teacher.branch
        assess.assessDate = utils.getDateNow(8)
        assess.assessor = login_teacher.id
        assess.memo = memo
        assess.assessCode = assessCode
        assess.city = login_teacher.cityId
        assess.assessObjectName = master.name
        assess.branchName = login_teacher.branchName
        assess.branchSn = login_teacher.branchSN
        assess.save()
    except Exception,e:
        res = {"error": 1, "message": e}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    query = Q(assessCode=assessCode)&Q(assessObject=assessObject)
    assesses = Assess.objects.filter(query)  # @UndefinedVariable
    av = 0.0
    i = 0
    for a in assesses:
        i = i + 1
        av = av + a.score
    av = av / i

    for a in assesses:
        a.averageScore = av
        a.save()
    res = {"error": 0, "message": 'OK'}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))




def questionnaireResult(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < constant.Role.master and login_teacher.branchType != str(constant.BranchType.management):
        return HttpResponseRedirect('/go2/noright')
    qthis = {}
    quest = None
    keys = []
    assessCode = request.GET.get("assessCode")

    branches = utils.getCityBranch(login_teacher.cityId)
    branchId = request.GET.get("branchId")
    got = {}
    gotAll = 0
    average = {}
    gotAvs = []


    if login_teacher.branchType == str(constant.BranchType.school) and login_teacher.role == constant.Role.master:
        if not assessCode:
            assessCode = '201808'
        branchId = login_teacher.branch

    if not branchId or branchId == 'null' or branchId == '':

        query = Q(assessCode=None)
        qs = Questionnaire.objects.filter(query).order_by("branchName","assessObject")  # @UndefinedVariable

        for an in qs:
            if an.assessObjectName:
                gotAll = gotAll + 1
                try:
                    got[an.branchName+'-'+an.assessObjectName] = got[an.branchName+'-'+an.assessObjectName] + 1
                    average[an.branchName+'-'+an.assessObjectName] = average[an.branchName+'-'+an.assessObjectName] + int(an.answers['7'])
                except:
                    got[an.branchName+'-'+an.assessObjectName] = 1
                    average[an.branchName+'-'+an.assessObjectName] = int(an.answers['7'])
        for key in got.keys():
            k = key.split('-')
            av = round(float(average[key])/float(got[key]),1)
            gotAv = {'branch':k[0],'teacher':k[1],'score':av,'got':got[key]}
            gotAvs.append(gotAv)

    if not assessCode or not branchId:

        qthis['title'] = u'老师满意度调查'

        return render(request, 'questionnaireResult.html',{"q":qthis,"branches":branches,"gotAvs":gotAvs,"gotAll":gotAll})
    query = Q(branchId=branchId)
    qs = Questionnaire.objects.filter(query).order_by("assessObject")  # @UndefinedVariable

    for an in qs:
        if an.assessObjectName:
            gotAll = gotAll + 1
            try:
                got[an.assessObjectName] = got[an.assessObjectName] + 1
                average[an.assessObjectName] = average[an.assessObjectName] + int(an.answers['7'])
            except:
                got[an.assessObjectName] = 1
                average[an.assessObjectName] = int(an.answers['7'])
    for key in got.keys():
        av = round(float(average[key])/float(got[key]),1)
        got[key] = str(av)+'/'+str(got[key])
    qthis,quest = tools.questionnaire.readFileToJson('assess_'+assessCode+'_teacher.json')

    for qq in quest:
        keys.append(str(qq['sn']))

    count = int(qthis['questCount'])
    response = render(request, 'questionnaireResult.html',{"login_teacher":login_teacher,"assessCode":assessCode,
                                                        "q":qthis,"quest":quest,"branches":branches,"branchId":branchId,
                                                        "teacherResults":qs,"keys":keys,"got":got,"gotAll":gotAll
                                                        })
    #response.set_cookie("mainurl",'/go2/teacher/message')
    return response


#问卷展示（不登录）
def questionnaire(request):
    tags = request.GET.get("tag")
    if not tags:
        tags = ''
    if tags.find('_') <0:
        try:
            tags = tools.questionnaire.getShortValue(tags).value
        except Exception,e:
            print e
            tags = ''
    tag = tags.split('_')

    assessCode = None
    branchCode = None
    assessObjectId = None
    assessorId = None
    if len(tag)>0:
      if tag[0] and len(tag[0]) > 0:
        assessCode = tag[0]
    if len(tag)>1:
      if tag[1] and len(tag[1]) > 0:
        branchCode = tag[1]
    if len(tag)>2:
      if tag[2] and len(tag[2]) > 0:
        assessObjectId = tag[2]
    if len(tag)>3:
      if tag[3] and len(tag[3]) > 0:
        assessorId = tag[3]

    assessObject = None
    assessor = None
    branch = None
    teachers = None
    branches = None
    try:
        branch = Branch.objects.get(branchCode=branchCode)  # @UndefinedVariable
        teachers = utils.getTeachers(branch.id, [5,6,8,9], False)
        temp = []
        for t in teachers:
            if t.name2.find(u'老师') > -1:
                t.name2 = t.name2[0:t.name2.find(u'老师')]
            temp.append(t)
        teachers = temp
    except:
        branch = None

    try:
        assessObject = Teacher.objects.get(id=assessObjectId)  # @UndefinedVariable
    except:
        assessObject = None
    try:
        assessor = Student.objects.get(id=assessorId)  # @UndefinedVariable
    except Exception,e:
        assessor = None

    if not assessCode:
        datenow = utils.getDateNow(8)
        assessCode = datenow.strftime("%Y%m")
    q = None
    qs = []
    q,qs = tools.questionnaire.readFileToJson('assess_'+assessCode+'_teacher.json')


    query = Q(assessCode=assessCode)
    if assessor:
        query = query&Q(assessor=assessor.id)
    if assessObject:
        query = query&Q(assessObject=assessObject.id)
    assess = None
    try:
        assess = Assess.objects.get(query)  # @UndefinedVariable
    except:
        assess = None
    if not branch:
        query = Q(city=constant.BEIJING)&Q(type=constant.BranchType.school)
        branches = Branch.objects.filter(query).order_by("sn")  # @UndefinedVariable
    response = render(request, 'questionnaire.html',{"assessCode":assessCode,"assessObjectId":str(assessObjectId),
                                                        "assess":assess,"assessorId":str(assessorId),"assessor":assessor,
                                                        "branch":branch,"teachers":teachers,"branches":branches,
                                                        "q":q,"qs":qs})
    #response.set_cookie("mainurl",'/go2/teacher/message')
    return response

#保存问卷
def api_questionnaire(request):
    assessCode = request.POST.get('assessCode')
    assessObjectId = request.POST.get('assessObjectId')
    assessorId = request.POST.get('assessorId')
    branchId = request.POST.get('branchId')

    questCount = request.POST.get("questCount")
    assessor = request.POST.get("assessor")
    assessorName = request.POST.get("assessorName")

    qc = 50
    q = None
    try:
        query = Q(branchId=branchId)&Q(assessObject=assessObjectId)&Q(assessor=assessorId)
        qss = Questionnaire.objects.filter(query)  # @UndefinedVariable
        if qss:
            q = qss[0]
        if not q:
            query = Q(branchId=branchId)&Q(assessObject=assessObjectId)&Q(assessorName=assessorName)
            qss = Questionnaire.objects.filter(query)  # @UndefinedVariable
            if qss:
                q = qss[0]
        if not q:
            q = Questionnaire()
    except Exception,e:
        #print e
        q = Questionnaire()
    try:
        assessor = Student.objects.get(id=assessorId)  # @UndefinedVariable
        if assessor:
            q.assessor = str(assessor.id)
    except:
        q.assessor = None
    branch = None
    try:
        branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    except:
        branch = None
    if branch:
        q.branchId = str(branch.id)
        q.branchName = branch.branchName
        q.city = str(branch.city.id)
        #q.branchSn = str(branch.sn)
    q.assessCode = assessCode
    aon = None
    ao = None
    try:
        ao = Teacher.objects.get(id=assessObjectId)  # @UndefinedVariable
        aon = ao.name
    except:
        aon = None
    if ao:
        q.assessObject = str(ao.id)
        q.assessObjectName = aon
    if questCount:
        try:
            qc = int(questCount)
        except:
            qc = 50
    an = {}
    for i in range(qc):
        i = i + 1
        #ai = request.POST.get(str(i))
        aa = request.POST.getlist(str(i))
        ai = ''
        if aa:
            for a in aa:
               ai = ai + a
        an[str(i)] = ai
    #ans = json.dump(an)

    q.answers = an
    q.assessDate = utils.getDateNow(8)
    q.assessorName = assessorName
    q.save()

    res = {"error": 0, "message": 'OK'}
    response = render(request, 'questionnaireDone.html',{"sid":q.assessor,"sname":q.assessorName})
    return response
    #return http.JSONResponse(json.dumps(res, ensure_ascii=False))


#quest2019
def q2019(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch = Branch.objects.get(id=login_teacher.branch)  # @UndefinedVariable
    tags = request.GET.get("tag")
    if not tags:
        tags = ''
    if tags.find('_') <0:
        try:
            tags = tools.questionnaire.getShortValue(tags).value
        except Exception,e:
            print e
            tags = ''
    tag = tags.split('_')

    assessCode = None
    branchCode = None
    assessObjectId = None
    assessorId = None
    if len(tag)>0:
      if tag[0] and len(tag[0]) > 0:
        assessCode = tag[0]
    if len(tag)>1:
      if tag[1] and len(tag[1]) > 0:
        branchCode = tag[1]
    if len(tag)>2:
      if tag[2] and len(tag[2]) > 0:
        assessObjectId = tag[2]
    if len(tag)>3:
      if tag[3] and len(tag[3]) > 0:
        assessorId = tag[3]
    if not assessorId:
        assessorId = login_teacher.id
    assessObject = None
    assessor = None
    #branch = None
    teachers = None
    branches = None
    try:
        #branch = Branch.objects.get(branchCode=branchCode)  # @UndefinedVariable
        teachers = utils.getTeachers(branch.id, [5,6,8,9], False)
        temp = []
        for t in teachers:
            if t.name2.find(u'老师') > -1:
                t.name2 = t.name2[0:t.name2.find(u'老师')]
            temp.append(t)
        teachers = temp
    except:
        #branch = None
        err = 1

    try:
        assessObject = Teacher.objects.get(id=assessObjectId)  # @UndefinedVariable
    except:
        assessObject = None
    try:
        assessor = Teacher.objects.get(id=assessorId)  # @UndefinedVariable
    except Exception,e:
        assessor = None

    if not assessCode:
        datenow = utils.getDateNow(8)
        assessCode = datenow.strftime("%Y%m")
    q = None
    qs = []
    q,qs = tools.questionnaire.readFileToJson('assess_'+assessCode+'_teacher.json')


    query = Q(assessCode=assessCode)
    if assessor:
        query = query&Q(assessor=assessor.id)
    if assessObject:
        query = query&Q(assessObject=assessObject.id)
    assess = None
    try:
        assess = Assess.objects.get(query)  # @UndefinedVariable
    except:
        assess = None
    if not branch:
        query = Q(city=constant.BEIJING)&Q(type=constant.BranchType.school)
        branches = Branch.objects.filter(query).order_by("sn")  # @UndefinedVariable
    response = render(request, 'q2019.html',{"login_teacher":login_teacher,"assessCode":assessCode,"assessObjectId":str(assessObjectId),
                                                        "assess":assess,"assessorId":str(assessorId),"assessor":assessor,
                                                        "branch":branch,"teachers":teachers,"branches":branches,
                                                        "q":q,"qs":qs,"branch":branch})
    #response.set_cookie("mainurl",'/go2/teacher/message')
    return response


#保存问卷2019
csrf_exempt
def api_q2019(request):
    assessCode = request.POST.get('assessCode')

    assessorId = request.POST.get('assessorId')
    branchId = request.POST.get('branchId')

    questCount = request.POST.get("questCount")


    qc = 50
    q = None
    try:
        query = Q(branchId=branchId)&Q(assessor=assessorId)
        qss = Questionnaire.objects.filter(query)  # @UndefinedVariable
        if qss:
            q = qss[0]

        if not q:
            q = Questionnaire()
    except Exception,e:
        #print e
        q = Questionnaire()
    try:
        assessor = Teacher.objects.get(id=assessorId)  # @UndefinedVariable
        if assessor:
            q.assessor = str(assessor.id)
    except:
        q.assessor = None
    branch = None
    try:
        branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    except:
        branch = None
    if branch:
        q.branchId = str(branch.id)
        q.branchName = branch.branchName
        q.city = str(branch.city.id)
        #q.branchSn = str(branch.sn)
    q.assessCode = assessCode

    if questCount:
        try:
            qc = int(questCount)
        except:
            qc = 50
    an = {}
    for i in range(qc):
        i = i + 1
        #ai = request.POST.get(str(i))
        aa = request.POST.getlist(str(i))
        ai = ''
        if aa:
            for a in aa:
               ai = ai + a
        an[str(i)] = ai
    #ans = json.dump(an)

    q.answers = an
    q.assessDate = utils.getDateNow(8)

    q.save()

    res = {"error": 0, "message": 'OK'}
    response = render(request, 'q2019Done.html',{"sid":q.assessor,"sname":q.assessorName})
    return response


def q2019Result(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.branchType != str(constant.BranchType.management):
        return HttpResponseRedirect('/go2/noright')
    qthis = {}
    quest = None
    keys = []
    assessCode = request.GET.get("assessCode")

    branches = utils.getCityBranch(login_teacher.cityId)
    branchId = request.GET.get("branchId")
    branch = None
    try:
        branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    except:
        branchId = None
        branch = None
    if not assessCode:

        qthis['title'] = u'老师问卷调查'

        return render(request, 'q2019Result.html',{"branches":branches})

    query = Q(branchId=branchId)&Q(assessCode=assessCode)
    if not branchId:
        query = Q(assessCode=assessCode)
    qs = Questionnaire.objects.filter(query)  # @UndefinedVariable

    qthis,quest = tools.questionnaire.readFileToJson('assess_'+assessCode+'_teacher.json')

    for qq in quest:
        keys.append(str(qq['sn']))

    all = []
    for q in qs:
        #rint q.answers
        an = {}
        key = q.answers.keys()

        for kk in key:
            an_str = q.answers[kk]

            ans = ''
            for aa in an_str:

                if aa in ['A','B','C','D','E','F']:

                  for qq in quest:
                    if qq['sn'] == kk:
                        for a in qq['ans']:
                            if a['code'] == aa:
                                ans = ans + a['text']
                  q.answers[kk] = ans




        all.append(q)

    count = int(qthis['questCount'])

    qs = all
    response = render(request, 'q2019Result.html',{"login_teacher":login_teacher,"assessCode":assessCode,"branch":branch,
                                                        "q":qthis,"quest":quest,"branchId":branchId,"keys":keys,
                                                        "teacherResults":qs,"branches":branches})
    #response.set_cookie("mainurl",'/go2/teacher/message')
    return response


#某个老师的转介二维码页面
def teacherQrcode(request):

    id = request.GET.get("id")
    teacher = None
    filepath = ''
    url1 = None

    try:
        teacher = Teacher.objects.get(id=id)  # @UndefinedVariable
        url = '/go_static/pages/fan.html?tid='+id
        qrurl = utils.makeQrcode(str(teacher.branch.id), None, 'teacher_qrcode.jpg',url)

    except:
        err = 1
    #print nbqrurl
    return render(request, 'teacherQrcode.html',{"url":url,"qrurl":qrurl,
                                              "id":id})
def noright(request):
    return render(request, 'noright.html')

def saveUser2Cookie(response,username,userid,name,name2,branchname,branchtel,rolename,role,branchid,cityid,city,page):
    response.set_cookie('username', username.lower())
    response.set_cookie('userid', userid)
    response.set_cookie('teacherName', name)
    response.set_cookie('name2', name2)
    response.set_cookie('branchName',branchname)
    response.set_cookie('branchTel',branchtel)
    response.set_cookie('roleName', rolename)
    response.set_cookie('role', role)
    response.set_cookie('branch', branchid)
    response.set_cookie('cityId', cityid)
    response.set_cookie('city', city)
    response.set_cookie('teacherPage', page)
                #request.session['user'] = res_login["user"]
    return response

def teacherAvail(request):
    return render(request, 'teacherAvail.html')

def markStep(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < constant.Role.master and login_teacher.branchType != str(constant.BranchType.management):
        return HttpResponseRedirect('/go2/noright')

    week = request.GET.get("week")
    month = request.GET.get("month")

    branchId = login_teacher.branch
    query = Q(branch=branchId)&Q(status__ne=-1)&Q(inReview=True)
    teachers = Teacher.objects.filter(query).order_by("id")  # @UndefinedVariable
    now = utils.getDateNow(8)
    thisWeekBegin = utils.getWeekBegin(now, False)
    thisWeekEnd = thisWeekBegin + datetime.timedelta(days=6)
    lastWeekBegin = thisWeekBegin - datetime.timedelta(days=7)
    lastWeekEnd = lastWeekBegin + datetime.timedelta(days=6)
    twoWeekBegin = lastWeekBegin - datetime.timedelta(days=7)
    twoWeekEnd = twoWeekBegin + datetime.timedelta(days=6)
    triWeekBegin = twoWeekBegin - datetime.timedelta(days=7)
    triWeekEnd = triWeekBegin + datetime.timedelta(days=6)
    weeks = []
    thisWeek = {"begin":thisWeekBegin.strftime("%Y-%m-%d"),"end":thisWeekEnd.strftime("%Y-%m-%d")}
    lastWeek = {"begin":lastWeekBegin.strftime("%Y-%m-%d"),"end":lastWeekEnd.strftime("%Y-%m-%d")}
    twoWeek = {"begin":twoWeekBegin.strftime("%Y-%m-%d"),"end":twoWeekEnd.strftime("%Y-%m-%d")}
    triWeek = {"begin":triWeekBegin.strftime("%Y-%m-%d"),"end":triWeekEnd.strftime("%Y-%m-%d")}

    weeks.append(thisWeek)
    weeks.append(lastWeek)
    weeks.append(twoWeek)
    weeks.append(triWeek)
    lastMonthBegin = utils.subtract_one_month(now)
    lastMonthEnd = utils.lastMonthLastDay(now)
    thisMonthBegin = utils.getThisMonthBegin(now)
    thisMonthEnd = utils.monthLastDay(now)

    months = []
    months.append(lastMonthBegin.strftime("%Y-%m"))
    months.append(now.strftime("%Y-%m"))

    month3begin,month3end = utils.month3day(now)
    month3 = []
    thisMonth3 = {"begin":month3begin.strftime("%Y-%m"),"end":month3end.strftime("%Y-%m")}
    month3.append(thisMonth3)

    yearBegin,yearEnd = utils.yearBeginEnd(None)
    years = []
    thisYear = {"begin":yearBegin.strftime("%Y-%m"),"end":yearEnd.strftime("%Y-%m")}
    years.append(thisYear)
    searchWeekBegin = lastWeekBegin
    searchWeekEnd = lastWeekEnd
    if week == thisWeekBegin.strftime("%Y-%m-%d"):
        searchWeekBegin = thisWeekBegin
        searchWeekEnd = thisWeekEnd
    if week == twoWeekBegin.strftime("%Y-%m-%d"):
        searchWeekBegin = twoWeekBegin
        searchWeekEnd = twoWeekEnd
    if week == triWeekBegin.strftime("%Y-%m-%d"):
        searchWeekBegin = triWeekBegin
        searchWeekEnd = triWeekEnd

    query = Q(beginDate__gte=searchWeekBegin)&Q(endDate__lte=searchWeekEnd)&Q(branchId=branchId)&Q(dateType='week')
    searchWeekSteps = TeacherStep.objects.filter(query).order_by("teacherId")  # @UndefinedVariable

    searchMonthBegin = lastMonthBegin
    searchMonthEnd = lastMonthEnd
    if month == thisMonthBegin.strftime("%Y-%m"):
        searchMonthBegin = thisMonthBegin
        searchMonthEnd = thisMonthEnd

    query = Q(beginDate__gte=searchMonthBegin)&Q(endDate__lte=searchMonthEnd)&Q(branchId=branchId)&Q(dateType='month')
    searchMonthSteps = TeacherStep.objects.filter(query).order_by("teacherId")  # @UndefinedVariable

    query = Q(beginDate__gte=month3begin)&Q(endDate__lte=month3end)&Q(branchId=branchId)&Q(dateType='month3')
    month3Steps = TeacherStep.objects.filter(query).order_by("teacherId")  # @UndefinedVariable

    query = Q(beginDate__gte=yearBegin)&Q(endDate__lte=yearEnd)&Q(branchId=branchId)&Q(dateType='year')
    yearSteps = TeacherStep.objects.filter(query).order_by("teacherId")  # @UndefinedVariable

    if len(searchWeekSteps) == 0:
        lastWeekSteps = None







    return render(request, 'markStep.html',{"searchWeekSteps":searchWeekSteps,"searchMonthSteps":searchMonthSteps,
                                            "month3Steps":month3Steps,"yearSteps":yearSteps,
                                            "teachers":teachers,"login_teacher":login_teacher,
                                            "months":months,"weeks":weeks,"month3":month3,"years":years,
                                            "searchWeekBegin":searchWeekBegin,"searchWeekEnd":searchWeekEnd,
                                            "searchMonthBegin":searchMonthBegin,"searchMonthEnd":searchMonthEnd,
                                            "GO_LEVEL":constant.GO_LEVEL})

def teacherSteps(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < constant.Role.master and login_teacher.branchType != str(constant.BranchType.management):
        return HttpResponseRedirect('/go2/noright')
    steps = None
    branchId = login_teacher.branch
    query = Q(branch=branchId)&Q(status__ne=-1)&Q(inReview=True)
    teachers = Teacher.objects.filter(query).order_by("id")  # @UndefinedVariable
    yearBegin,yearEnd = utils.yearBeginEnd(None)
    temp = []
    for t in teachers:
        tmap = {}
        tmap['name'] = t.name
        tmap['id'] = str(t.id)
        temp.append(tmap)
    temp2 = []
    for t in teachers:
        this = {}
        for tmap in temp:
            if tmap['id'] == str(t.id):
                this = tmap
                this['s1'] = 0
                this['s2'] = 0
                this['s3'] = 0
                this['s4'] = 0
                this['s5'] = 0
                this['s6'] = 0
                this['s7'] = 0
                this['s8'] = 0
                this['s9'] = 0
                this['s10'] = 0
                this['s11'] = 0
                this['s12'] = 0
                this['s13'] = 0
                this['s14'] = 0
                this['all'] = 0
        query = Q(beginDate__gte=yearBegin)&Q(endDate__lte=yearEnd)&Q(teacherId=str(t.id))

        steps = TeacherStep.objects.filter(query).order_by("dateType")  # @UndefinedVariable
        for s in steps:
            if s.item == u'正课试讲' and s.valid:
                this['s3'] = this['s3'] + 5
            if s.item == u'成交演练' and s.valid:
                this['s4'] = this['s4'] + 5
            if s.item == u'班级群反馈' and s.valid:
                this['s11'] = this['s11'] + 5
            if s.item == u'棋力月赛':
                this['s1'] = this['s1'] + int(s.value)
            if s.item == u'对弈' and s.valid:
                this['s2'] = this['s2'] + 10
            if s.item == u'朋友圈' and s.valid:
                this['s7'] = this['s7'] + 10
            if s.item == u'家长课堂' and int(s.value) >= 1:
                this['s12'] = this['s12'] + 30
            if s.item == u'集体活动' and s.valid:
                this['s13'] = this['s13'] + int(s.value)
            if s.item == u'主任分' and s.valid:
                this['s14'] = this['s14'] + int(s.value)
        num = getTrainings(t.id,yearBegin,yearEnd)
        this['s6'] = num * 10

        this['all'] = this['s1'] + this['s2'] + this['s3'] + this['s4'] + this['s5'] + this['s6'] + this['s7'] + this['s8'] + this['s9'] + this['s10'] + this['s11'] + this['s12'] + this['s13'] + this['s14']
        temp2.append(this)
    return render(request, 'teacherSteps.html',{"steps":temp2})

def cityTeacherSteps(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.branchType != str(constant.BranchType.management):
        return HttpResponseRedirect('/go2/noright')

    branches = utils.getCityBranch(login_teacher.cityId)
    i = 0
    for b in branches:
        if i == 0:
            query = Q(branch=b.id)
        else:
            query = query|Q(branch=b.id)
        i = i + 1
    query = (query)&Q(inReview=True)
    teachers = Teacher.objects.filter(query)  # @UndefinedVariable

    temp = []
    for t in teachers:
        tmap = {}
        tmap['name'] = t.name
        tmap['id'] = str(t.id)
        tmap['branch'] = t.branch.branchName
        temp.append(tmap)
    temp2 = []
    yearBegin,yearEnd = utils.yearBeginEnd(None)
    for t in teachers:
        this = {}
        for tmap in temp:
            if tmap['id'] == str(t.id):
                this = tmap
                this['s1'] = 0
                this['s2'] = 0
                this['s3'] = 0
                this['s4'] = 0
                this['s5'] = 0
                this['s6'] = 0
                this['s7'] = 0
                this['s8'] = 0
                this['s9'] = 0
                this['s10'] = 0
                this['s11'] = 0
                this['s12'] = 0
                this['s13'] = 0
                this['s14'] = 0
                this['all'] = 0
        query = Q(beginDate__gte=yearBegin)&Q(endDate__lte=yearEnd)&Q(teacherId=str(t.id))

        steps = TeacherStep.objects.filter(query).order_by("dateType")  # @UndefinedVariable

        for s in steps:
            if s.item == u'正课试讲' and s.valid:
                this['s3'] = this['s3'] + 5
            if s.item == u'成交演练' and s.valid:
                this['s4'] = this['s4'] + 5
            if s.item == u'班级群反馈' and s.valid:
                this['s11'] = this['s11'] + 5
            if s.item == u'棋力月赛':
                this['s1'] = this['s1'] + int(s.value)
            if s.item == u'对弈' and s.valid:
                this['s2'] = this['s2'] + 10
            if s.item == u'盆友圈' and s.valid:
                this['s7'] = this['s7'] + 10
            if s.item == u'家长课堂' and int(s.value) >= 1:
                this['s12'] = this['s12'] + 30
            if s.item == u'集体活动' and s.valid:
                this['s13'] = this['s13'] + int(s.value)
            if s.item == u'主任分' and s.valid:
                this['s14'] = this['s14'] + int(s.value)
        this['all'] = this['s1'] + this['s2'] + this['s3'] + this['s4'] + this['s5'] + this['s6'] + this['s7'] + this['s8'] + this['s9'] + this['s10'] + this['s11'] + this['s12'] + this['s13'] + this['s14']
        temp2.append(this)
    return render(request, 'cityTeacherSteps.html',{"yearBegin":yearBegin,"yearEnd":yearEnd,
                                            "teachers":teachers,"login_teacher":login_teacher,"steps":temp2,
                                            })

def api_markStep(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < constant.Role.master and login_teacher.branchType != str(constant.BranchType.management):
        return HttpResponseRedirect('/go2/noright')

    branchId = request.POST.get("branchId")
    cityId = request.POST.get("cityId")

    beginDateStr = request.POST.get("beginDateStr")
    dateType = request.POST.get("dateType")
    itemStr = request.POST.get("itemStr")

    items = itemStr.split("|")
    beginDate = None
    endDate = None
    try:

        if dateType == 'week':
            beginDate = datetime.datetime.strptime(beginDateStr+' 00:00:00','%Y-%m-%d %H:%M:%S')
            endDate = beginDate+datetime.timedelta(days=6)
        if dateType == 'month':
            beginDate = datetime.datetime.strptime(beginDateStr+'-01 00:00:00','%Y-%m-%d %H:%M:%S')
            endDate = utils.monthLastDay(beginDate)
        if dateType == 'month3':
            beginDate = datetime.datetime.strptime(beginDateStr+'-01 00:00:00','%Y-%m-%d %H:%M:%S')
            beginFate,endDate = utils.month3day(beginDate)
        if dateType == 'year':
            beginDate = datetime.datetime.strptime(beginDateStr+'-01 00:00:00','%Y-%m-%d %H:%M:%S')
            endDate = beginDate

            endDate = endDate.replace(year=beginDate.year+1)
            endDate = endDate.replace(month=8)
            endDate = endDate.replace(day=31)
            endDate = endDate.replace(hour=23)
            endDate = endDate.replace(minute=59)
            endDate = endDate.replace(second=59)
        endDateStr = endDate.strftime("%Y-%m-%d")+' 23:59:59'

    except:
        res = {"error":1,"msg":"date invalid"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    masterId = login_teacher.id
    try:
        master = Teacher.objects.get(id=login_teacher.id)  # @UndefinedVariable
    except:
        res = {"error":1,"msg":"master not found!"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    masterName = master.name
    query = Q(beginDate__gte=beginDate)&Q(endDate__lte=endDate)&Q(dateType=dateType)&Q(branchId=branchId)
    steps = TeacherStep.objects.filter(query)  # @UndefinedVariable
    for it in items:

        iss = it.split('-')
        step = TeacherStep()
        for s in steps:
            if s.beginDate.strftime("%Y%m%d") == beginDate.strftime("%Y%m%d") and s.teacherId == iss[0] and s.item == iss[1]:
                step = s

        try:
            step.branchId = branchId
            step.masterId = masterId
            step.masterName = masterName
            step.teacherId = iss[0]
            step.dateType = dateType
            try:

                t = Teacher.objects.get(id=step.teacherId)  # @UndefinedVariable
            except:
                res = {"error":1,"msg":"teacher not found!"}
                return http.JSONResponse(json.dumps(res, ensure_ascii=False))

            step.teacherName = t.name
            step.item = iss[1]

            step.value = iss[2]
            if iss[3] == 'true':
                step.valid = True
            else:
                step.valid = False
            try:
                step.score = int(iss[4])
            except:
                step.score = 0

            step.beginDate = beginDate
            step.endDate = endDate

            step.save()

        except Exception,e:
            print e
            res = {"error": 1, "msg":'save err'}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    res = {"error": 0, "msg":"OK"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def wxqrcodePic(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    millis = int(round(time.time() * 1000))
    tid = request.GET.get("tid")
    teacher = None
    try:
        teacher = Teacher.objects.get(id=tid)  # @UndefinedVariable
    except:
        return render(request, 'wxqrcodePic.html')
    qrcode = ''
    wxqrcode = USER_IMAGE_DIR+str(login_teacher.branch)+'/'+tid+'.jpg'
    if os.path.exists(BASE_DIR+wxqrcode):
        qrcode = wxqrcode
    else:
        qrcode = USER_IMAGE_DIR+'wxqrcode.jpg'



    qrfile = '/go_static/users/' + str(teacher.branch.id) + '/' + '20181111qrcode' + tid + '.jpg'
    url20181111 = '/web/luckyDraw2018a?tid='+tid
    userImagePath = BASE_DIR + qrfile

    isFile = os.path.isfile(userImagePath)
    url = None
    if not isFile:

        url = utils.makeQrcode(str(teacher.branch.id), None, '20181111qrcode'+tid+'.jpg',url20181111)



    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PicForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            uploadFile = request.FILES['picFile']
            si = uploadFile.size
            t,filedate,relaPath = utils.handle_uploaded_image(uploadFile,login_teacher.branch,None,8,None,tid)

            # redirect to a new URL:
            return render(request, 'wxqrcodePic.html', {'teacher':teacher,'tid':tid,'qrcode':wxqrcode,'millis':millis,'form':form})
            #return HttpResponseRedirect('/go2/teacher/reg?teacher_oid='+tid)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PicForm()
    return render(request, 'wxqrcodePic.html', {'teacher':teacher,'tid':tid,'form': form,'qrcode':qrcode,
                                                'url':url,'millis':millis})

def p20181111(request):
    bid = request.GET.get("bid")
    tid = request.GET.get("tid")
    return render(request, 'p20181111.html', {'bid':bid,'tid':tid})

def getTrainings(tid,bdate,edate):
    tid = str(tid)
    query = Q(teacher_oid=tid)&(Q(type=8)|Q(type=9))&Q(training_date__gte=bdate)&Q(training_date__lte=edate)
    trainings = Training.objects.filter(query)  # @UndefinedVariable

    num = 0
    try:
        num = len(trainings)
    except:
        num = 0
    return num


@csrf_exempt
def api_editTarget(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    itemstr = request.POST.get("items")
    target = None
    res = {"error":0,"msg":"OK"}
    items = itemstr.split("|")
    map = dict()

    for item in items:
        try:
            its = item.split("_")
            id = its[0]
            try:
                map[id] = map[id] + '|' + its[1]+'_'+its[2]
            except Exception,e:
                #print e
                map[id] = its[1]+'_'+its[2]
        except Exception,e:
            err = 1
            print e


    for key,value in map.items():
        vs = value.split('|')
        isValid = True
        for v in vs:
            vv = v.split('_')
            if vv[1] and len(vv[1]) > 0:
                continue
            else:
                isValid = False
                break

        if isValid:
            user = None
            try:
                user = Teacher.objects.get(id=key)  # @UndefinedVariable
            except Exception,e:
                res = {"error": 1,"msg":str(e)}
                return http.JSONResponse(json.dumps(res, ensure_ascii=False))

            targets = user.targets

            beginDate = None
            try:
                bds = vs[0].split('_')[1]
                beginDate = datetime.datetime.strptime(bds,"%Y-%m-%d")
            except Exception:
                err = 1
            for t in targets:
                try:
                  if str(t.userId) == key and t.beginDate == beginDate:
                    target = t
                    targets.remove(t)
                    break
                except:
                    err = 1

            if not target:
                target = Target()
            quarterTarget = None
            halfyearTarget = None
            yearTarget = None
            beginLevel = None
            endLevel = None
            try:
                beginLevel = vs[1].split('_')[1]
                quarterTarget = vs[2].split('_')[1]
                halfyearTarget = vs[3].split('_')[1]
                yearTarget = vs[4].split('_')[1]
                target.userId = str(user.id)
                target.beginDate = beginDate
                target.beginLevel = beginLevel
                target.quarterTarget = quarterTarget
                target.halfyearTarget = halfyearTarget
                target.yearTarget = yearTarget
                target.save()
                targets.append(target)

            except Exception,e:
                print e
                res = {"error": 1,"msg":str(e)}
                return http.JSONResponse(json.dumps(res, ensure_ascii=False))
            try:
                user.targets = targets
                user.beginLevel = target.beginLevel
                user.targetLevel1 = target.quarterTarget
                user.targetLevel2 = target.halfyearTarget
                user.targetLevel3 = target.yearTarget
                user.targetBeginDate = target.beginDate
                user.save()
            except Exception,e:
                res = {"error": 1,"msg":str(e)}
                return http.JSONResponse(json.dumps(res, ensure_ascii=False))



    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
def testUser(request):
    f = open('/data/go2/testUser.txt','r')
    st = f.read()
    users = []
    try:
        users = json.loads(st)
    except:
        err = 1
    return render(request, 'testUser.html', {'users':users})
@csrf_exempt
def api_resetTestPassword(request):
    pw1 = str(int(round(random.random(),6)*1000000))
    pw2 = str(int(round(random.random(),6)*1000000))
    pw3 = str(int(round(random.random(),6)*1000000))
    print pw1
    print pw2
    print pw3
    datenow = utils.getDateNow(8).strftime("%Y-%m-%d")
    users = [{"username":"test1","pw":pw1,"date":datenow},{"username":"test2","pw":pw2,"date":datenow},{"username":"test3","pw":pw3,"date":datenow}]
    userstr = json.dumps(users, ensure_ascii=False)
    f = open('/data/go2/testUser.txt','w')
    print userstr
    f.write(userstr)
    res = {"error":0,"pws":[{"username":"test1","pw":pw1},{"username":"test2","pw":pw2},{"username":"test3","pw":pw3}]}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
