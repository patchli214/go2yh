#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'patch'

from django.views.decorators.csrf import  csrf_exempt
from regUser.models import SourceType, StudentTrack
from webpage.models import Webpage
import time
from itertools import chain
from django.conf.locale import cs
from mongoengine.queryset.visitor import Q
import json,os,datetime
from operator import attrgetter
from datetime import timedelta
from go2.settings import BASE_DIR,USER_IMAGE_DIR
from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template import RequestContext
from tools import http,utils,data, util3
from branch.models import City,Branch,Stat,Vocation, Reimburse, ReimburseItem
from branch.forms import PicForm , ReimburseForm
from regUser.models import Student,StudentFile,SourceType,SourceCategory,Source,ContractType
from teacher.models import Login_teacher,Teacher
from django.views.decorators.csrf import ensure_csrf_cookie
from tools.utils import checkCookie,getDateNow,getWeekBegin, makeQrcode
from tools.http import pageVisit
from tools import constant
from statistic.models import PageVisit,VisitIp
from django.views.decorators.csrf import  csrf_exempt
# Create your views here.

def reg(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cities = City.objects.all()  # @UndefinedVariable
    branch = None
    branchId = request.GET.get("branchId")
    if branchId:
        try:
            branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
        except Exception,e:
            print e
    payBranches = None
    if login_teacher.username != 'admin':
    #if login_teacher.role != 9:
        cities = City.objects.filter(id=login_teacher.cityId)  # @UndefinedVariable
    elif branch:
        query = Q(city__ne=branch.city.id)&(Q(type=1)|Q(type=2))
        payBranches = Branch.objects.filter(query)  # @UndefinedVariable


    rooms = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15]
    millisecond = int(round(time.time() * 1000))
    return render(request, 'branchReg.html',{"rooms":rooms,"login_teacher":login_teacher,"tag":millisecond,
                                             "payBranches":payBranches,"branch":branch,"cities":cities})


def api_reg(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    branchId = request.POST.get("branchId")
    branchName = request.POST.get("branchName")
    branchAddr = request.POST.get("branchAddr")
    branchTel = request.POST.get("branchTel")
    branchCode = request.POST.get("branchCode")
    branchRooms = request.POST.get("branchRooms")
    cityid = request.POST.get("city")
    typeStr = request.POST.get("type")
    deleted = request.POST.get("deleted")
    isY19 = request.POST.get("isY19")
    payBranch = request.POST.get("payBranch")

    if isY19 == 'true':
        isY19 = True
    else:
        isY19 = False
    if deleted == 'true':
        deleted = True
    else:
        deleted = False
    type = 0
    try:
        type = int(typeStr)
    except:
        type = 0
    city = City()
    city = City.objects.get(id=cityid)  # @UndefinedVariable
    sn = request.POST.get("sn")
    if not branchName:
        res = {"error": 1, "msg": "信息不全"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    if branchId:
        branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    else:
        branchs = Branch.objects.filter(branchName=branchName)  # @UndefinedVariable
        if branchs.count() >= 1:
            res = {"error": 1, "msg": "校区已存在"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        branch = Branch()
    branch.branchName = branchName
    branch.branchAddr = branchAddr
    branch.branchTel = branchTel
    branch.branchCode = branchCode
    if branchRooms:
        branch.branchRooms = int(branchRooms)
    branch.city = city
    branch.sn = sn
    branch.type = type
    branch.deleted = deleted
    branch.isY19 = isY19
    if payBranch:
        paybranches = []
        paybranches.append(payBranch)
        branch.payBranch = paybranches

    try:
        branch.save()
        res = {"error": 0, "msg": "校区保存成功"}
    except Exception,e:
        res = {"error": 1, "msg": "校区保存失败"}
        print e

    #===========================================================================
    # students = Student.objects.filter(branch=branchId)  # @UndefinedVariable
    # for s in students:
    #     if s.branchName != branchName:
    #         s.branchName = branchName
    #         s.save()
    #===========================================================================

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def branch_remove(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branchId = request.POST.get("branchId")
    if branchId:
        try:
            Branch.objects.get(id=branchId)  # @UndefinedVariable
        except:
            a=2
    res = {"error": 0, "msg": "成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def branch_list(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branchs = utils.getBranches(login_teacher,True)

    bs = []
    for b in branchs:
        if not b.branchCode:
            b.branchCode = ''
        b.excel = os.path.isfile(BASE_DIR+USER_IMAGE_DIR+b.branchCode+'.xls')
        if not b.excel:
            b.excel = os.path.isfile(BASE_DIR+USER_IMAGE_DIR+b.branchCode+'.xlsx')
        query = Q(branch=b.id)&Q(role=7)&Q(status=0)
        masters = Teacher.objects.filter(query)  # @UndefinedVariable
        b.masters = masters
        bs.append(b)

    return render(request, 'branchList.html', {"login_teacher":login_teacher,"branchs": bs})

#各校区好吗来源统计
def statistics(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    branchs = utils.getCityBranch(login_teacher.cityId)
    type = request.GET.get("dateType")

    now = utils.getDateNow(8)
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
            if type == 'week':
                bDate = utils.getWeekBegin(bDate, False)
                eDate = bDate + timedelta(days=7)
            if type == 'month':
                bDate = utils.getThisMonthBegin(bDate)
                eDate = utils.monthLastDay(bDate)

                eDate = eDate + timedelta(days=1)
                eDate = utils.getThisMonthBegin(eDate)
        except:
            bDate = None
    #===========================================================================
    # if endDate:
    #     try:
    #         eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
    #         eDate = eDate + timedelta(days=1)
    #     except:
    #         eDate = None
    #===========================================================================
    print 'GET DATES'
    print bDate
    print eDate
    if not bDate and not eDate:
        #=======================================================================
        # eDate = now
        # endDate = eDate.strftime("%Y-%m-%d")
        # now = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        # if login_teacher.branchType != '0':
        #     bDate = getWeekBegin(now)
        #     bDate = bDate + timedelta(days=-1)
        # else:
        #     bDate = now + timedelta(days=-90)
        #=======================================================================
        now = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        bDate = utils.getWeekBegin(now, False)
        eDate = bDate + datetime.timedelta(days=7)
        beginDate = bDate.strftime("%Y-%m-%d")

    bs = []

    for b in branchs:
        stat = Stat()
        stat.branch = b
        #网络
        stat.online = Student.objects.filter(branch=b.id).filter(regTime__gte=bDate).filter(regTime__lt=eDate).filter(sourceType='A').filter(regBranch=constant.NET_BRANCH).count()  # @UndefinedVariable
        #拜访
        stat.visit = Student.objects.filter(branch=b.id).filter(regTime__gte=bDate).filter(regTime__lt=eDate).filter(sourceType='B').count()  # @UndefinedVariable


        query = Q(branch=b.id)&Q(regTime__gte=bDate)&Q(regTime__lt=eDate)&Q(sourceType='D')
        stat.walkin = Student.objects.filter(query).count()  # @UndefinedVariable
        query = Q(branch=b.id)&Q(regTime__gte=bDate)&Q(regTime__lt=eDate)&Q(sourceType='C')&Q(source__ne='5b246e6797a75dec6f15be20')
        #转介
        stat.refer = Student.objects.filter(query).count()  # @UndefinedVariable
        #周年庆
        stat.refer2 = Student.objects.filter(branch=b.id).filter(regTime__gte=bDate).filter(regTime__lt=eDate).filter(source='5b246e6797a75dec6f15be20').count()  # @UndefinedVariable

        #stat.album = StudentFile.objects.filter(branch=str(b.id)).filter(fileCreateTime__gte=searchBegin).filter(fileCreateTime__lte=searchEnd).count()  # @UndefinedVariable




        bs.append(stat)

    reg,beginDate,endDate = util3.getWeekReg(login_teacher.cityId,bDate,eDate)
    map = {}
    if reg:
      for m in reg.regs:
        try:
            d = map[str(m['branchSN'])]
        except:
            map[str(m['branchSN'])] = {'regAll':0,'regMorning':0,'regEvening':0}
        map[str(m['branchSN'])]['regAll'] = map[str(m['branchSN'])]['regAll'] + m['regAll']
        map[str(m['branchSN'])]['regMorning'] = map[str(m['branchSN'])]['regMorning'] + m['regMorning']
        map[str(m['branchSN'])]['regEvening'] = map[str(m['branchSN'])]['regEvening'] + m['regEvening']
        #print map[str(m['branchSN'])]
    temp = []
    for key,value in map.iteritems():
        #print key

        map[key] = {'regAll':round(value['regAll'],0),'regMorning':round(value['regMorning'],0),'regEvening':round(value['regEvening'],0)}
        #print map[key]
        for stat in bs:
            if stat.branch.sn == int(key):
                stat.visit = map[key]['regAll']
                stat.visit2 = map[key]['regMorning']
                stat.visit3 = map[key]['regEvening']
                temp.append(stat)
    query = Q(trackTime__lt=eDate)&Q(trackTime__gte=bDate)
    cs = StudentTrack.objects.filter(query).order_by('branch')  # @UndefinedVariable
    print cs.count()
    print cs._query
    ma = {}
    for c in cs:
        try:
            d = ma[c.branch]
        except:
            ma[c.branch] = 0
        ma[c.branch] = ma[c.branch] + 1
    temp2 = []
    for  key,value in ma.iteritems():
        for stat in temp:
            if str(stat.branch.id) == key:
                stat.c = value
                temp2.append(stat)
    return render(request, 'statistics.html', {"login_teacher":login_teacher,
                                               "stats": temp2,
                                               "dateType":type,
                                               "beginDate":beginDate.strftime("%Y-%m-%d")})

def branch_info(request, branch_oid):
    try:
        branch = Branch.objects.get(id=branch_oid)  # @UndefinedVariable
    except:
        branch = None
    return render(request, 'branchInfo.html', {"branch": branch})

def tweet2019(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch = None
    try:
        branch = Branch.objects.get(id=login_teacher.branch)  # @UndefinedVariable
    except:
        branch = None
        return render(request,"tweet2019.html",{"qrcode":''})
    qrcode = makeQrcode(login_teacher.branch,None,"tweet2019.jpg",'/go2/student/tweet?bid='+branch.branchCode)
    print qrcode
    return render(request,"tweet2019.html",{"qrcode":qrcode})


def city(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cities = City.objects.all()  # @UndefinedVariable
    cityId = request.GET.get("cityId")
    city = None
    print(1)
    if cityId:
        try:
            city = City.objects.get(id=cityId)  # @UndefinedVariable
            print (city.id)
        except:
            city = None
    print (2)
    query = Q(status__ne=-1)&(Q(role=9)|Q(branch=constant.BJ_CAIWU))
    financialAdmins = None
    financialRefunds = None

    try:
        financialAdmins = Teacher.objects.filter(query).order_by("city")  # @UndefinedVariable
        print(financialAdmins[0].id)
    except:
        financialAdmins = None
    print(3)
    query = Q(status__ne=-1)&Q(role=8)
    try:
        financialRefunds = Teacher.objects.filter(query).order_by("city")  # @UndefinedVariable
    except:
        financialRefunds = None
    print(4)
    return render(request, 'cityReg.html',{"login_teacher":login_teacher,
                                           "cities":cities,"financialAdmins":financialAdmins,
                                           "financialRefunds":financialRefunds,
                                           "city":city})


def api_city(request):
  res = None
  try:
    cityName = request.POST.get("cityName")
    sn = request.POST.get("sn")
    if not cityName:
        res = {"error": 1, "msg": "信息不全"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    id = request.POST.get("id")
    faId = request.POST.get("financialAdmin")
    frId = request.POST.get("financialRefund")
    rtId = request.POST.get("financialReceipt")
    rbId = request.POST.get("financialReimburse")
    rb2Id = request.POST.get("financialReimburse2")

    FA = None
    FR = None
    RT = None
    RB = None
    RB2 = None
    try:
        FA = Teacher.objects.get(id=faId)  # @UndefinedVariable
    except:
        FA = None
    try:
        FR = Teacher.objects.get(id=frId)  # @UndefinedVariable
    except:
        FR = None
    try:
        RT = Teacher.objects.get(id=rtId)  # @UndefinedVariable
    except:
        RT = None
    try:
        RB = Teacher.objects.get(id=rbId)  # @UndefinedVariable
    except:
        RB = None
    try:
        RB2 = Teacher.objects.get(id=rb2Id)  # @UndefinedVariable
    except:
        RB2 = None
    faId = None
    if FA and FA.id:
        faId = str(FA.id)
    frId = None
    if FR and FR.id:
        frId = str(FR.id)
    rtId = None
    if RT and RT.id:
        rtId = str(RT.id)
    if RB and RB.id:
        rbId = str(RB.id)
    if RB2 and RB2.id:
        rb2Id = str(RB2.id)
    city = None
    try:
        city = City.objects.get(id=id)  # @UndefinedVariable
    except:
        city = City()
    cities = City.objects.filter(cityName=cityName)  # @UndefinedVariable
    if id and cities.count() >= 2:
        res = {"error": 1, "msg": "城市已存在"}
        render_to_response("foo.html", RequestContext(request, {}))
    if not id and cities.count() >= 1:
        res = {"error": 1, "msg": "城市已存在"}
        render_to_response("foo.html", RequestContext(request, {}))
    dealDuration = request.POST.get("dealDuration")
    try:
        dd = int(dealDuration)
    except:
        dd = 10
    city.cityName = cityName
    city.dealDuration = dd
    city.sn = sn
    city.financialAdmin = faId
    city.financialRefund = frId
    city.financialReceipt = rtId
    city.financialReimburse = rbId
    city.financialReimburse2 = rb2Id
    city.save()

    res = {"error": 0, "msg": "城市添加成功"}
  except Exception,e:
      print e
      res = {"error": 1, "msg": str(e)}

  return http.JSONResponse(json.dumps(res, ensure_ascii=False))


def city_list(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cities = City.objects.all()  # @UndefinedVariable

    # 页码设置
    paginator = Paginator(cities, 10)
    page = request.GET.get('page')

    try:
        cities = paginator.page(page)

    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        cities = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        cities = paginator.page(paginator.num_pages)
    return render(request, 'cityList.html', {"login_teacher":login_teacher,"cities": cities, 'pages': paginator.page_range})

def branchPic(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    from tools import utils

    branch_oid = request.GET.get("branch_oid")
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PicForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            uploadFile = request.FILES['picFile']
            si = uploadFile.size
            t,filedate,relaPath = utils.handle_uploaded_image(uploadFile,login_teacher.branch,None)

            # redirect to a new URL:
            return HttpResponseRedirect('/go2/branch/reg?branchId='+branch_oid)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PicForm()
    return render(request, 'schoolPic.html', {'branch_oid':branch_oid,
                                              'form': form})
def netUser(request):
    changeBranch = 1
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch_oid = request.POST.get("bid")
    notAdd = request.POST.get("notAdd")
    na = None
    if notAdd == '1':
        na = True
    filepath = request.POST.get("filepath")
    index = data.getNetUser(filepath, branch_oid,na,changeBranch)
    res = {"error": 0, "msg": str(index)+"条记录保存成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def api_editCategory(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    deleted = request.POST.get("deleted")
    name = request.POST.get("sourceCategoryName")
    code = request.POST.get("sourceCategoryCode")
    category = None
    try:
        category = SourceCategory.objects.get(id=id)  # @UndefinedVariable
    except:
        category = None
    if category:
        if name:
            category.categoryName = name
        if code:
            category.categoryCode = code
        if deleted:
            category.deleted = deleted
        category.save()
        res = {"error": 0, "msg": "保存成功"}
    else:
        res = {"error": 1, "msg": "未找到"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def editCategory(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.GET.get("id")
    category = SourceCategory.objects.get(id=id)  # @UndefinedVariable
    return render(request, 'editCategory.html', {"login_teacher":login_teacher,
                                                  "category":category})
def cityContract(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityId = request.GET.get("city")
    city = City.objects.get(id=cityId)  # @UndefinedVariable
    cityContracts = ContractType.objects.filter(city=cityId).order_by("code")  # @UndefinedVariable
    temp = []
    for c in cityContracts:
        if not c.discountPrice:
            c.discountPrice = c.fee
        c.eve = int(c.discountPrice/(c.duration))
        temp.append(c)
    return render(request, 'cityContract.html', {"login_teacher":login_teacher,
                                                 "city":city,
                                                 "cityContracts":temp})
#修改城市合同页面
def editContract(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.GET.get("id")
    cityId = request.GET.get("city")
    cityContract = None
    city = None
    if id:
        cityContract = ContractType.objects.get(id=id)  # @UndefinedVariable

        city = cityContract.city
    else:
        city = City.objects.get(id=cityId)  # @UndefinedVariable
    return render(request, 'editContract.html', {"login_teacher":login_teacher,
                                                 "cityContract":cityContract,
                                                 "city":city})

@csrf_exempt
def api_editContract(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    typeStr = request.POST.get("type")
    deleted = request.POST.get("deleted")
    fee = request.POST.get("fee")
    tuition = request.POST.get("tuition")
    discountPrice = request.POST.get("discountPrice")
    memo = request.POST.get("memo")
    code = request.POST.get("code")
    cityId = request.POST.get("cityId")
    duration = request.POST.get("duration")
    type = 0
    try:
        type = int(typeStr)
    except:
        type = 0
    ct = None
    try:
        ct = ContractType.objects.get(id=id)  # @UndefinedVariable
    except:
        ct = ContractType()
    if True:
    #try:
        ct.city = City.objects.get(id=cityId)  # @UndefinedVariable
        ct.duration = int(duration)
        ct.fee = int(fee)
        try:
            ct.tuition = int(tuition)
        except:
            ct.tuition = 0

        if discountPrice:
            ct.discountPrice = int(discountPrice)
        ct.memo = memo
        if deleted:
            ct.deleted = int(deleted)
        ct.code = code
        ct.type = type
        ct.save()

        res = {"error": 0, "msg": "保存成功"}
    #except Exception,e:
     #   print e
      #  res = {"error": 1, "msg": e}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


def api_editSource(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    deleted = request.POST.get("deleted")
    name = request.POST.get("sourceName")
    code = request.POST.get("sourceCode")
    contact = request.POST.get("contact")
    mobile = request.POST.get("mobile")
    weixin = request.POST.get("weixin")
    categoryCode = request.POST.get("categoryCode")
    source = None
    try:
        source = Source.objects.get(id=id)  # @UndefinedVariable
    except:
        source = None
    if source:
        if name:
            source.sourceName = name
        if code:
            source.sourceCode = code
        if deleted:
            source.deleted = deleted
        else:
            source.deleted = None
        if contact:
            source.contact = contact
        if mobile:
            source.mobile = mobile
        if categoryCode:
            source.categoryCode = categoryCode
        if weixin:
            source.weixin = weixin
        source.save()
        res = {"error": 0, "msg": "保存成功"}
    else:
        res = {"error": 1, "msg": "未找到"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def editSource(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.GET.get("id")
    source = Source.objects.get(id=id)  # @UndefinedVariable
    categoryName = None
    try:
        c = SourceCategory.objects.filter(categoryCode=source.categoryCode)  # @UndefinedVariable
        if c and len(c)>0:
            categoryName = c[0].categoryName
        else:
            c = SourceCategory.objects.filter(id=source.categoryCode)  # @UndefinedVariable
            if c and len(c)>0:
                categoryName = c[0].categoryName
    except:
        categoryName = None
    categories = SourceCategory.objects.all()   # @UndefinedVariable
    return render(request, 'editSource.html', {"login_teacher":login_teacher,
                                             "source":source,
                                             "categoryName":categoryName,
                                             "categories":categories})

def sources(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branchId = login_teacher.branch
    sourceTypes = SourceType.objects.all()  # @UndefinedVariable
    sourceCategories = SourceCategory.objects.filter(branch=branchId)  # @UndefinedVariable
    sources = Source.objects.filter(branch=branchId)  # @UndefinedVariable


    query = Q(source='5b246e6797a75dec6f15be20')
    students = Student.objects.filter(query)  # @UndefinedVariable

    for s in students:
        s.sourceType = 'C'
        s.save()
    print len(students)

    return render(request, 'setting.html', {"login_teacher":login_teacher,
                                             "sourceTypes": sourceTypes,
                                             "sourceCategories":sourceCategories,
                                             "sources":sources})
#报销单列表
def reimburses(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branchId = login_teacher.branch
    teachers = None
    query = Q(status__ne=-1)&Q(branch=login_teacher.branch)
    if login_teacher.role < 4:
        query = query&Q(id=login_teacher.id)
    teachers = Teacher.objects.filter(query).order_by('-role')  # @UndefinedVariable
    reimburses = None

    query = Q(branch=branchId)

    searchStatusStr = request.GET.get("searchStatus")
    searchTeacherStr = request.GET.get("searchTeacher")
    searchType = request.GET.get("searchType")
    searchKW = request.GET.get("searchKW")
    beginDateStr = request.GET.get("beginDate")
    endDateStr = request.GET.get("endDate")

    beginDate = None
    endDate = None
    searchStatus = None
    searchTeacher = None
    try:
        searchTeacher = Teacher.objects.get(id=searchTeacherStr)  # @UndefinedVariable
    except:
        searchTeacher = None
    try:
        searchStatus = int(searchStatusStr)
    except:
        searchStatus = None

    dateQuery = None
    try:
        beginDate = datetime.datetime.strptime(beginDateStr,'%Y-%m-%d')
        endDate = datetime.datetime.strptime(endDateStr,'%Y-%m-%d')+datetime.timedelta(days=1)
    except:
        beginDate = None
    try:
        endDate = datetime.datetime.strptime(endDateStr,'%Y-%m-%d')+datetime.timedelta(days=1)
    except:
        endDate = None
    if not beginDate:
        beginDate = utils.getDateNow()+datetime.timedelta(days=-30)
        beginDateStr = (beginDate).strftime("%Y-%m-%d")
    if not endDate:
        endDate = utils.getDateNow()
        endDateStr = endDate.strftime("%Y-%m-%d")
        endDate = endDate+datetime.timedelta(days=1)
    dateQuery = Q(appDate__gte=beginDate)&Q(appDate__lt=endDate)

    if searchType and len(searchType) == 0:
        searchType = None

    if login_teacher.role < 4:
        searchTeacher = Teacher.objects.get(id=login_teacher.id)  # @UndefinedVariable
        query = query&Q(applicant=str(searchTeacher.id))
    elif searchTeacher:
        query = query&Q(applicant=str(searchTeacher.id))
    if searchType:
        query = query&Q(type=searchType)
    temp = None
    temp0 = []
    temp4 = []
    temp1 = []
    temp2 = []
    temp3 = []

    if searchStatus is None or searchStatus == 0:
        query0 = query&Q(status=0)
        temp0 = Reimburse.objects.filter(query0)  # @UndefinedVariable

    if searchStatus is None or searchStatus == 4:
        query4 = query&Q(status=4)
        temp4 = Reimburse.objects.filter(query4)  # @UndefinedVariable

    if searchStatus is None or searchStatus == 1:
        query1 = query&Q(appDate__gte=beginDate)&Q(appDate__lt=endDate)&Q(status=1)
        temp1 = Reimburse.objects.filter(query1).order_by('-appDate')  # @UndefinedVariable

    if searchStatus is None or searchStatus == 2:
        query2 = query&Q(paidDate__gte=beginDate)&Q(paidDate__lt=endDate)&Q(status=2)
        temp2 = Reimburse.objects.filter(query2).order_by('-paidDate','-status')  # @UndefinedVariable

    if searchStatus is None or searchStatus == 3:
        query3 = query&Q(paidDate__gte=beginDate)&Q(paidDate__lt=endDate)&Q(status=3)
        temp3 = Reimburse.objects.filter(query3).order_by('-paidDate','-status')  # @UndefinedVariable



    reimburses = chain(temp0,temp4,temp1,temp3,temp2)
    temp = []
    ids = []
    for r in reimburses:
        if str(r.id) not in ids:
                ids.append(str(r.id))
                temp.append(r)
        if r.borrowId:
            borrow = Reimburse.objects.get(id=r.borrowId)  # @UndefinedVariable
            if r.borrowId in ids:
                temp.remove(borrow)
                ids.remove(r.borrowId)
            try:
                    temp.append(borrow)  # @UndefinedVariable
                    ids.append(r.borrowId)
            except:
                    err = 1
    reimburses = temp
    temp = []
    for r in reimburses:
        if r.isClear:
            r.statusName = u'已清'
            r.typeName = u'请款'
            r.color = constant.BGCOLOR.GREEN
            r.op = 'show("'+str(r.id)+'")'
            r.opName = u'查看'
        elif r.borrowId and r.status == constant.ReimburseStatus.waiting:
            r.statusName = u'已提交财务'
            r.typeName = u'清借款'
            r.op = 'show("'+str(r.id)+'")'
            r.opName = u'打印'
            r.color = constant.BGCOLOR.GRAY
        elif r.borrowId and r.status == constant.ReimburseStatus.saved:
            r.statusName = u'未提交'
            r.typeName = u'清借款'
            r.color = constant.BGCOLOR.WHITE
            r.op = 'go("'+str(r.id)+'")'
            r.opName = u'修改提交'
        elif r.borrowId and r.status == constant.ReimburseStatus.waitBranchApprove:
            r.statusName = u'部门审批'
            r.typeName = u'清借款'
            r.color = constant.BGCOLOR.WHITE
            r.op = 'show("'+str(r.id)+'")'
            if login_teacher.role == 7:
                r.opName = u'审批'
        elif r.borrowId and r.status == constant.ReimburseStatus.reject:
            r.statusName = u'驳回'
            r.typeName = u'清借款'
            r.color = constant.BGCOLOR.RED
            r.op = 'go("'+str(r.id)+'")'
            r.opName = u'修改提交'
        elif r.borrowId and r.status == constant.ReimburseStatus.approved:
            r.statusName = u'已清'
            r.typeName = u'清借款'
            r.color = constant.BGCOLOR.GREEN
            r.op = 'show("'+str(r.id)+'")'
            r.opName = u'查看'
        elif r.isBorrow and not r.borrowId and r.status == constant.ReimburseStatus.saved:
            r.statusName = u'未提交'
            r.typeName = u'请款'
            r.color = constant.BGCOLOR.WHITE
            r.op = 'go("'+str(r.id)+'")'
            r.opName = u'修改提交'
        elif r.isBorrow and not r.borrowId and r.status == constant.ReimburseStatus.reject:
            r.statusName = u'驳回'
            r.typeName = u'请款'
            r.color = constant.BGCOLOR.RED
            r.op = 'go("'+str(r.id)+'")'
            r.opName = u'修改提交'
        elif r.isBorrow and not r.borrowId and r.status == constant.ReimburseStatus.waitBranchApprove:
            r.statusName = u'部门审批'
            r.typeName = u'请款'
            r.color = constant.BGCOLOR.WHITE
            r.op = 'show("'+str(r.id)+'")'
            if login_teacher.role == 7:
                r.opName = u'审批'
        elif r.isBorrow and not r.borrowId and r.status == constant.ReimburseStatus.waiting:
            r.statusName = u'已提交财务'
            r.typeName = u'请款'
            r.color = constant.BGCOLOR.GRAY
            r.op = 'show("'+str(r.id)+'")'
            r.opName = u'打印'
            r.color = constant.BGCOLOR.GRAY
        elif r.isBorrow and not r.borrowId and r.status == constant.ReimburseStatus.approved:
            r.statusName = u'已借'
            r.typeName = u'请款'
            r.color = constant.BGCOLOR.YELLOW
            r.op = 'goReturn("'+str(r.id)+'")'
            r.opName = u'清借款'

            try:
                rr = Reimburse.objects.get(borrowId=str(r.id))  # @UndefinedVariable
                if rr and rr.isClear:
                    r.statusName = u'已清'
                    r.color = constant.BGCOLOR.GREEN
                    r.op = 'show("'+str(r.id)+'")'
                    r.opName = u'查看'
                if rr and not rr.isClear:
                    r.statusName = u'清借款中'
                    r.color = constant.BGCOLOR.YELLOW
                    r.op = 'show("'+str(r.id)+'")'
                    r.opName = u'查看'

            except:
                err = 1

        elif not r.isBorrow and r.status == constant.ReimburseStatus.reject:
            r.statusName = u'驳回'
            r.typeName = u''
            r.color = constant.BGCOLOR.RED
            r.op = 'go("'+str(r.id)+'")'
            r.opName = u'修改提交'
        elif not r.isBorrow and r.status == constant.ReimburseStatus.approved:
            r.statusName = u'已报'
            r.typeName = u''
            r.color = constant.BGCOLOR.GREEN
            r.op = 'show("'+str(r.id)+'")'
            r.opName = u'查看'
        elif not r.isBorrow and r.status == constant.ReimburseStatus.saved:
            r.statusName = u'未提交'
            r.typeName = u''
            r.color = constant.BGCOLOR.WHITE
            r.op = 'go("'+str(r.id)+'")'
            r.opName = u'修改提交'
        elif not r.isBorrow and r.status == constant.ReimburseStatus.waitBranchApprove:
            r.statusName = u'部门审批'
            r.typeName = u''
            r.color = constant.BGCOLOR.WHITE
            r.op = 'show("'+str(r.id)+'")'
            if login_teacher.role == 7:
                r.opName = u'审批'
        elif not r.isBorrow and r.status == constant.ReimburseStatus.waiting:
            r.statusName = u'已提交财务'
            r.typeName = u''
            r.color = constant.BGCOLOR.GRAY
            r.op = 'show("'+str(r.id)+'")'
            r.opName = u'打印'
        r.memo = ''
        query = Q(rid=str(r.id))
        ris = ReimburseItem.objects.filter(query)  # @UndefinedVariable
        #print ris._query
        if ris and len(ris) > 0:
            #print 'has'
            for ri in ris:
                r.memo = r.memo+'['+ri.typeName+'-'+ri.itemName+']'
        temp.append(r)
    reimburses = temp

    return render(request, 'reimburses.html', {"login_teacher":login_teacher,
                                               "teachers":teachers,
                                               "types":constant.REIMBURSE_TYPE,
                                               "searchStatus":searchStatus,
                                               "searchTeacher":searchTeacher,
                                               "searchType":searchType,
                                               "beginDate":beginDateStr,"endDate":endDateStr,
                                             "reimburses": reimburses})

#获取部门待审批报销数量，用于badge显示
def reimburseNum_api(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < 7:
       return HttpResponseRedirect('/login')
    query = Q(branch=login_teacher.branch)&Q(status=constant.ReimburseStatus.waitBranchApprove)

    reimburses = Reimburse.objects.filter(query)  # @UndefinedVariable

    res = {"error": 0, "num": 0}
    if reimburses and len(reimburses) > 0:
        res = {"error": 0, "num": len(reimburses)}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


#填写报销单
def reimburse(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    adate = utils.getDateNow(8)
    reimburse = None
    res = None
    i1 = None
    i2 = None
    i3 = None
    i4 = None
    i5 = None
    id = request.GET.get("id")
    borrowId = request.GET.get("borrowId")
    if borrowId and len(borrowId) < 10:
        borrowId = None
    borrowReim = None
    borrow = 0.0
    try:
        reimburse = None
        if id:
            reimburse = Reimburse.objects.get(id=id)  # @UndefinedVariable

        elif borrowId:
            reimburse = Reimburse.objects.get(id=borrowId)  # @UndefinedVariable
        if reimburse.borrowId:
            borrow = Reimburse.objects.get(id=reimburse.borrowId).sum  # @UndefinedVariable
        else:
            borrow = reimburse.sum
        if reimburse.items[0]:
            i1 = reimburse.items[0]
        if reimburse.items[1]:
            i2 = reimburse.items[1]
        if reimburse.items[2]:
            i3 = reimburse.items[2]
        if reimburse.items[3]:
            i4 = reimburse.items[3]
        if reimburse.items[4]:
            i5 = reimburse.items[4]
    except:
        err = 1
    branchId = login_teacher.branch
    branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    branches = None

    bn = int(login_teacher.branchType)
    if bn == constant.BranchType.function or login_teacher.id == '587430a197a75d50a4e4d550':#总部职能部门和鲁玉祥可能给其他部门报销
        qu = Q(city=login_teacher.cityId)|Q(payBranch='5ab86f5397a75d3c74041a69')
        branches = Branch.objects.filter(qu).order_by("sn")  # @UndefinedVariable


    else:
        branches = Branch.objects.filter(id=branchId)  # @UndefinedVariable
    query = Q(branch=branchId)&(Q(role=constant.Role.master)|Q(role=constant.Role.operator))
    teachers = Teacher.objects.filter(query)  # @UndefinedVariable
    types = constant.REIMBURSE_TYPE
    saveDone = False
    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = ReimburseForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            applicant = form.cleaned_data.get('applicant')
            payBranchId = form.cleaned_data.get('payBranch')
            appDate = form.cleaned_data.get('appDate')


            payBranch = None
            try:
                payBranch = Branch.objects.get(id=payBranchId)  # @UndefinedVariable
            except:
                err = 1
            oid = form.cleaned_data.get('oid')
            borrowId = form.cleaned_data.get('borrowId')
            if borrowId == 'None':
                borrowId = None

            if not appDate:
                appDate = utils.getDateNow(8)
            print appDate
            hasReceipt = form.cleaned_data.get('hasReceipt')
            budget = form.cleaned_data.get('budget')
            isBorrow = form.cleaned_data.get('isBorrow')

            try:
                reimburse = Reimburse.objects.get(id=oid)  # @UndefinedVariable
            except Exception,e:
                print e
                reimburse = None
            applicantName = ''
            try:
                applicantName = Teacher.objects.get(id=applicant).name  # @UndefinedVariable
            except Exception,e:
                print e
                return HttpResponseRedirect('/go2/branch/reimburseErr?applicant')

            type1 = form.cleaned_data.get('type1')
            type2 = form.cleaned_data.get('type2')
            type3 = form.cleaned_data.get('type3')
            type4 = form.cleaned_data.get('type4')
            type5 = form.cleaned_data.get('type5')

            item1 = form.cleaned_data.get('item1')
            item2 = form.cleaned_data.get('item2')
            item3 = form.cleaned_data.get('item3')
            item4 = form.cleaned_data.get('item4')
            item5 = form.cleaned_data.get('item5')

            amount1 = 0.0
            amount2 = 0.0
            amount3 = 0.0
            amount4 = 0.0
            amount5 = 0.0

            count1 = 0
            count2 = 0
            count3 = 0
            count4 = 0
            count5 = 0

            sum = 0.0

            appmemo = None
            try:
                appmemo = form.cleaned_data.get('appmemo')
            except Exception,e:
                err = 1
            try:
                amount1 = float(form.cleaned_data.get('amount1'))
                if len(form.cleaned_data.get('amount2')) > 0:
                    amount2 = float(form.cleaned_data.get('amount2'))
                if len(form.cleaned_data.get('amount3')) > 0:
                    amount3 = float(form.cleaned_data.get('amount3'))
                if len(form.cleaned_data.get('amount4')) > 0:
                    amount4 = float(form.cleaned_data.get('amount4'))
                if len(form.cleaned_data.get('amount5')) > 0:
                    amount5 = float(form.cleaned_data.get('amount5'))
                sum = float(form.cleaned_data.get('sum'))
            except:
                return HttpResponseRedirect('/go2/branch/reimburseErr?sum')
            try:
                count1 = int(form.cleaned_data.get('count1'))
                count2 = int(form.cleaned_data.get('count2'))
                count3 = int(form.cleaned_data.get('count3'))
                count4 = int(form.cleaned_data.get('count4'))
                count5 = int(form.cleaned_data.get('count5'))
            except:
                err = 1
            if not reimburse:
                reimburse = Reimburse()
                reimburse.status = constant.ReimburseStatus.saved
            reimburse.applicantName = applicantName
            reimburse.appDate = None
            reimburse.applicant = applicant

            reimburse.status = constant.ReimburseStatus.saved
            reimburse.finmemo = None
            reimburse.hasReceipt = hasReceipt
            reimburse.budget = budget
            reimburse.isBorrow = isBorrow
            if borrowId and borrowId != 'None':
                reimburse.borrowId = borrowId
            reimburse.appmemo = appmemo
            reimburse.sum = sum
            reimburse.branch = branch
            reimburse.payBranch = payBranch
            reimburse.appDate = appDate
            reimburse.save()
            saveDone = True
            rid = str(reimburse.id)
            id = rid

            try:
                uploadFile = request.FILES['proof']

                si = uploadFile.size
                t,filedate,relaPath = utils.handle_uploaded_image(uploadFile,login_teacher.branch,rid,constant.FileType.reimburseProof,2000)
                if not t:
                    res = filedate
                reimburse.proof = t
                reimburse.save()
            except:
                err = 1

            items = []
            toSave = False
            if amount1 > 0.0 or amount2 > 0.0 or amount3 > 0.0 or amount4 > 0.0 or amount5 > 0.0:
                its = ReimburseItem.objects.filter(rid=rid)  # @UndefinedVariable
                for i in its:
                    i.delete()
            if amount1 > 0.0:
                ritem = ReimburseItem()
                ritem.rid = rid
                ritem.amount = amount1
                ritem.type = type1

                ritem.typeName = constant.REIMBURSE_TYPE.get(ritem.type,None)

                ritem.itemName = item1
                ritem.count = count1
                ritem.status = constant.ReimburseStatus.saved
                ritem.appDate = reimburse.appDate
                ritem.applicant = reimburse.applicant
                ritem.branch = reimburse.branch
                ritem.paidDate = reimburse.paidDate
                ritem.save()
                items.append(ritem)
                toSave = True
            if amount2 > 0.0:
                ritem = ReimburseItem()
                ritem.rid = rid
                ritem.amount = amount2
                ritem.type = type2
                ritem.typeName = constant.REIMBURSE_TYPE.get(ritem.type,None)
                ritem.itemName = item2
                ritem.count = count2
                ritem.status = constant.ReimburseStatus.saved
                ritem.appDate = reimburse.appDate
                ritem.applicant = reimburse.applicant
                ritem.branch = reimburse.branch
                ritem.paidDate = reimburse.paidDate
                ritem.save()
                items.append(ritem)
                toSave = True
            if amount3 > 0.0:
                ritem = ReimburseItem()
                ritem.rid = rid
                ritem.amount = amount3
                ritem.type = type3
                ritem.typeName = constant.REIMBURSE_TYPE.get(ritem.type,None)
                ritem.itemName = item3
                ritem.count = count3
                ritem.status = constant.ReimburseStatus.saved
                ritem.appDate = reimburse.appDate
                ritem.applicant = reimburse.applicant
                ritem.branch = reimburse.branch
                ritem.paidDate = reimburse.paidDate
                ritem.save()
                items.append(ritem)
                toSave = True
            if amount4 > 0.0:
                ritem = ReimburseItem()
                ritem.rid = rid
                ritem.amount = amount4
                ritem.type = type4
                ritem.typeName = constant.REIMBURSE_TYPE.get(ritem.type,None)
                ritem.itemName = item4
                ritem.count = count4
                ritem.status = constant.ReimburseStatus.saved
                ritem.appDate = reimburse.appDate
                ritem.applicant = reimburse.applicant
                ritem.branch = reimburse.branch
                ritem.paidDate = reimburse.paidDate
                ritem.save()
                items.append(ritem)
                toSave = True
            if amount5 > 0.0:
                ritem = ReimburseItem()
                ritem.rid = rid
                ritem.amount = amount5
                ritem.type = type5
                ritem.typeName = constant.REIMBURSE_TYPE.get(ritem.type,None)
                ritem.itemName = item5
                ritem.count = count5
                ritem.status = constant.ReimburseStatus.saved
                ritem.appDate = reimburse.appDate
                ritem.applicant = reimburse.applicant
                ritem.branch = reimburse.branch
                ritem.paidDate = reimburse.paidDate
                ritem.save()
                items.append(ritem)
                toSave = True
            if toSave:
                reimburse.items = items
                reimburse.save()
                try:
                    if reimburse.items[0]:
                        i1 = reimburse.items[0]
                    if reimburse.items[1]:
                        i2 = reimburse.items[1]
                    if reimburse.items[2]:
                        i3 = reimburse.items[2]
                    if reimburse.items[3]:
                        i4 = reimburse.items[3]
                    if reimburse.items[4]:
                        i5 = reimburse.items[4]
                except:
                    err = 1
        else:
            err = 1
            print form.errors
            res = form.errors

    else:
        form = ReimburseForm()

    millisecond = int(round(time.time() * 1000))
    remain = None
    if reimburse:
        remain = borrow - reimburse.sum
    if reimburse and reimburse.appDate:
        adate = reimburse.appDate
    if reimburse and reimburse.proof:
        tags = reimburse.proof.split('.')
        tag = ''
        for t in tags:
            tag = t
        tag = tag.lower()
        if tag != 'jpg' and tag != 'png' and tag != 'gif' and tag != 'jpeg':
            reimburse.proofType = 1
    dateNow = utils.getDateNow(8)
    earliestDate = dateNow - timedelta(days=30)
    latestDate = dateNow
    return render(request, 'reimburse.html', {"login_teacher":login_teacher,
                                               "teachers":teachers,"form":form,
                                               "reimburse":reimburse,"id":id,"saveDone":saveDone,
                                               "i1":i1,"i2":i2,"i3":i3,"i4":i4,"i5":i5,
                                               "branches":branches,"res":res,
                                               "millisecond":millisecond,
                                               "borrowId":borrowId,"borrow":borrow,"remain":remain,
                                               "adate":adate,"earliestDate":earliestDate,
                                               "latestDate":latestDate,
                                             "types": types})


def reimburseShow(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    reimburse = None
    i1 = None
    i2 = None
    i3 = None
    i4 = None
    i5 = None
    id = request.GET.get("id")
    try:
        reimburse = Reimburse.objects.get(id=id)  # @UndefinedVariable
        if not reimburse.payBranch:
            reimburse.payBranch = reimburse.branch
            reimburse.save()
        if reimburse.items[0]:
            i1 = reimburse.items[0]
        if reimburse.items[1]:
            i2 = reimburse.items[1]
        if reimburse.items[2]:
            i3 = reimburse.items[2]
        if reimburse.items[3]:
            i4 = reimburse.items[3]
        if reimburse.items[4]:
            i5 = reimburse.items[4]
    except:
        err = 1
    millisecond = int(round(time.time() * 1000))
    reimurl = request.COOKIES.get('reimurl','')
    remain = None
    borrow = 0.0
    if reimburse.borrowId:
        try:
            borrow = Reimburse.objects.get(id=reimburse.borrowId).sum  # @UndefinedVariable
        except:
            borrow = 0.0
    if reimburse:
        remain = borrow - reimburse.sum
    dateNow = utils.getDateNow(8)
    return render(request, 'reimburseShow.html', {"login_teacher":login_teacher,"borrow":borrow,"remain":remain,
                                               "reimburse":reimburse,"reimurl":reimurl,
                                               "millisecond":millisecond,"dateNow":dateNow,
                                               "i1":i1,"i2":i2,"i3":i3,"i4":i4,"i5":i5})
@csrf_exempt
def api_submitReimburse(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    res = {"error": 0, "msg": "ok"}
    id = request.POST.get("id")
    statusStr = request.POST.get("status")
    memo = request.POST.get("memo")
    openId = None

    try:
            status = int(statusStr)
            r = Reimburse.objects.get(id=id)  # @UndefinedVariable
            r.status = status
            if status == constant.ReimburseStatus.waiting: #提交财务
                if not r.appDate:
                    r.appDate = utils.getDateNow()
                r.branchLeader = login_teacher.id
                r.branchLeaderName = login_teacher.teacherName

            if status == constant.ReimburseStatus.reject:#驳回
                r.finmemo = memo
                r.paidDate = utils.getDateNow()

            if status == constant.ReimburseStatus.waitBranchApprove:#提交部门审批
                r.finmemo = None
                query = Q(branch=login_teacher.branch)&Q(status__ne=-1)&Q(role=constant.Role.master)
                leaders = Teacher.objects.filter(query)  # @UndefinedVariable

                for t in leaders:
                    if t.openId and len(t.openId) > 10:

                        openId = t.openId
                        res['openId'] = openId
                        mobile = None
                        try:
                            tea = Teacher.objects.get(id=login_teacher.id)  # @UndefinedVariable
                            mobile = tea.mobile
                        except:
                            mobile = None
                        if mobile and len(mobile) > 3:
                            res['tel'] = mobile
                        break


            if status == constant.ReimburseStatus.approved:#已报
                payDate = request.POST.get("payDate")

                paidDate = None
                if payDate:
                    try:
                        paidDate = datetime.datetime.strptime(payDate,"%Y-%m-%d")
                    except:
                        paidDate = utils.getDateNow()

                r.paidDate = paidDate
                if r.borrowId:
                    rr = Reimburse.objects.get(id=r.borrowId)  # @UndefinedVariable
                    if rr:
                        rr.isClear = True
                        rr.save()
            r.save()
    except Exception,e:
        print e
        err = 1

    rr = None
    try:
        rr = json.dumps(res, ensure_ascii=False)
    except Exception,e:
        print e
    return http.JSONResponse(rr)

def reimburseErr(request):
    return render(request, 'reimburseErr.html')

@csrf_exempt
def reimburseRemove_api(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    res = {"error": 0, "msg": "ok"}
    id = request.POST.get("id")
    try:
        r = Reimburse.objects.get(id=id)  # @UndefinedVariable
        r.delete()
        its = ReimburseItem.objects.filter(rid=id)  # @UndefinedVariable
        for i in its:
            i.delete()
    except Exception,e:
        res = {"error": 1, "msg": str(e)}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


def jointDate(request):
    branch = request.POST.get("branch")
    pgs = PageVisit.objects.filter(branch=branch).order_by("student","page","-visitTime")  # @UndefinedVariable
    lastDate = None
    lastPage = None
    lastStudent = None
    lastP = None
    index = 0
    i = 0
    for pg in pgs:
        i = i + 1
        if pg.visitTime and pg.student and lastDate == pg.visitTime.date() and lastStudent == pg.student and lastP == pg.page:
            lastPage.visit = pg.visit + lastPage.visit
            lastPage.save()
            index = index + 1
            pg.delete()

            continue

        if pg.visitTime and pg.student:
            if lastDate != pg.visitTime.date() or lastStudent != pg.student or lastP !=pg.page:
                lastPage = pg
                lastDate = pg.visitTime.date()
                lastStudent = pg.student
                lastP = pg.page

    res = {"error": 0, "msg": "ok"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def vocations(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityId = login_teacher.cityId
    query = Q(city=cityId)
    vocations = Vocation.objects.filter(query).order_by("-beginDate")  # @UndefinedVariable

    return render(request, 'vocations.html', {"login_teacher":login_teacher,
                                             "vocations": vocations,
                                             })
@csrf_exempt
def api_vocation(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable

    beginDateStr = request.POST.get("beginDate")
    endDateStr = request.POST.get("endDate")

    beginDate = None
    endDate = None

    try:
        beginDate = datetime.datetime.strptime(beginDateStr,"%Y-%m-%d")
        endDate = datetime.datetime.strptime(endDateStr,"%Y-%m-%d")
    except:
        res={'error':3,'msg':'wrong date'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    if city:
        sus = Vocation(city=city.id)
        sus.beginDate = beginDate
        sus.endDate = endDate
        sus.save()
        res = {"error": 0,'msg':u'保存假期成功'}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def api_delVocation(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    sus = None
    if not id:
        res = {"error": 1,"msg":"no id"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    try:
        sus = Vocation.objects.get(id=id)  # @UndefinedVariable

    except Exception,e:
        res = {"error": 2,"msg":'No Item'}
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
