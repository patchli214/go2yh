#!/usr/bin/env python
# -*- coding:utf-8 -*-
from __future__ import unicode_literals
import json,datetime,time,itertools
import sys,operator,urllib

from bson import ObjectId
from mongoengine.queryset.visitor import Q
from go2.settings import BASE_DIR,USER_IMAGE_DIR
from regUser.models import Student,StudentFile,Source
from branch.models import Branch
from teacher.models import Teacher
from webpage.models import *
from regUser.forms import PicForm
from itertools import chain
from operator import attrgetter
from django.shortcuts import render,render_to_response
from django.http import HttpResponse,HttpResponseRedirect
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from tools.utils import checkCookie,getDateNow
from django.http import HttpResponse,HttpResponseRedirect
from tools import http, utils, constant,questionnaire
from tools.sign import Sign
import urllib2
from go2 import settings
import random
import string


def uploadPic(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    student_oid = request.GET.get("student_oid")
    teacher_oid = request.GET.get("teacher_oid")
    type = request.GET.get("type")
    branch = None
    if type == '3':
        branch = login_teacher.branch

    if request.method == 'POST':
        # create a form instance and populate it with data from the request:
        form = PicForm(request.POST, request.FILES)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            files = request.FILES.getlist('picFile')
            for uploadFile in files:
              #uploadFile = request.FILES['picFile']
              si = uploadFile.size
              t,filedate,relaPath = utils.handle_uploaded_image(uploadFile,login_teacher.branch,student_oid,type)
              if not t:
                  return HttpResponseRedirect('/web/pages?type='+type+'&student_oid='+student_oid+'&err='+str(filedate))
              try:
                if type == '3':
                    studentFile = StudentFile.objects.get(fileType=3,branch=branch,filename=t)  # @UndefinedVariable
                else:
                    studentFile = StudentFile.objects.get(student=student_oid,filename=t)  # @UndefinedVariable
                return HttpResponseRedirect('/web/pages?type='+type+'&student_oid='+student_oid)
              except:
                studentFile = StudentFile()
                try:
                    student = Student.objects.get(id=student_oid)  # @UndefinedVariable
                except:
                    student = None 
                    
                try:
                    teacher = Teacher.objects.get(id=teacher_oid)  # @UndefinedVariable
                except:
                    teacher = None
                studentFile.student = student

                if student: 
                    studentFile.studentName = student.name

                if not teacher and student:
                    teacher = studentFile.student.teacher
                if not teacher and student:
                    teacher = studentFile.student.regTeacher
                teacherId = None
                if teacher:
                    teacherId = str(teacher.id)
                if teacherId:
                    studentFile.teacher = teacherId
                studentFile.filename = t
                if type != '3':
                    branch = login_teacher.branch
                    #branch = str(studentFile.student.branch.id)
                studentFile.filepath = branch+'/'
                
                if type != '3':
                    studentFile.filepath = studentFile.filepath+student_oid+'/'
                studentFile.fileCreateTime = filedate
                
                studentFile.branch = branch
                studentFile.fileType = type
                
                studentFile.save()
            
            # redirect to a new URL:
            paras = "type="+type+"&student_oid="+student_oid
            return HttpResponseRedirect('/web/pages?'+paras)

    # if a GET (or any other method) we'll create a blank form
    else:
        form = PicForm()
        form.student_oid=student_oid
        form.type=type
    return render(request, 'upload.html', {'student_oid':student_oid,
                                              'type':type,
                                              'form': form})

def pages(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    type = request.GET.get("type")
    err = request.GET.get("err")
    student_oid = request.GET.get("student_oid")
    try:
        student = Student.objects.get(id=student_oid)  # @UndefinedVariable
    except:
        student = None
    pageId = request.GET.get("pageId")
    editPage = None
    try:
        editPage = Webpage.objects.get(id=pageId)  # @UndefinedVariable
    except:
        editPage = None
    pages = []
    files = []
    if type == '3':#brahch page list
        query = Q(branch=login_teacher.branch)&Q(fileType=3)
        pages = Webpage.objects.filter(query)  # @UndefinedVariable
        query = query&Q(fileType=3)
        query = query&Q(filename__ne='refundApp.jpg')
        files = StudentFile.objects.filter(query).order_by("order")  # @UndefinedVariable
        if editPage and editPage.pics and len(editPage.pics)>0:
          all = []
          for p in pages:
            if str(p.id) != pageId:
                for f in p.pics:
                    if f not in all:
                        all.append(f)
          temp = []
          for f in files:
            if f in all:
                continue
            else:
                temp.append(f)
          myfiles = editPage.pics
          for f in myfiles:
            if f not in temp:
                temp.append(f)
          files = temp
    else:
        student_oid = request.GET.get("student_oid")
        query1 = Q(student=student_oid)&Q(fileType=1)
        query = Q(student=student_oid)
        pages = Webpage.objects.filter(query1)  # @UndefinedVariable
        temp = []
        for p in pages:
            if not p.teacher:
                try:
                    p.teacher = str(Student.objects.get(id=p.student).teacher.id)  # @UndefinedVariable
                except:
                    p.teacher = login_teacher.id

            temp.append(p)
        pages = temp
        query = query&Q(filename__ne='refundApp.jpg')
        files = StudentFile.objects.filter(query).order_by("order")  # @UndefinedVariable
    
    sortedPics = None
    if editPage:
        temp = []
        sortedPics = editPage.sortedPics
        goDelete = False
        deleteList = []
        for tuple in sortedPics:
            file = None
            try:
                file = StudentFile.objects.get(id=tuple[0])  # @UndefinedVariable
                file.order = int(tuple[1])
            except:
                if file:
                    file.order = None
            if file:
                temp.append(file)
            else:
                goDelete = True
                deleteList.append(tuple)
                
        if goDelete:
            for d in deleteList:
                sortedPics.remove(d)
            editPage.sortedPics = sortedPics
            editPage.save()   
        sortedPics = temp
        
        temp = []
        inList = False
        for f in files:
            for p in sortedPics:
                if f.id == p.id:
                    inList = True
                    break
            if not inList:
                temp.append(f)
            inList = False
        files = temp
    tid = ''
    try:
            tid = str(student.teacher.id)
    except:
            tid = ''
    millis = int(round(time.time() * 1000))
    return render(request, 'pages.html',{"login_teacher":login_teacher,
                                         "tid":tid,"err":err,
                                         "pages":pages,"files":files,
                                         "editPage":editPage,
                                         "student":student,
                                         "type":type,"student_oid":student_oid,
                                         "imagePath":USER_IMAGE_DIR,
                                         "sortedPics":sortedPics,
                                         "millis":millis
                                         })

def removePage(request):
    login_teacher = checkCookie(request)
    res = ''
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))    

def rotatePic(request):
    login_teacher = checkCookie(request)
    
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    res = {'error':0}
    file_oid = request.POST.get("file_oid")

    filename = ''
    try:
        file = StudentFile.objects.get(id=file_oid)
        filename = BASE_DIR + USER_IMAGE_DIR + file.filepath + file.filename
        utils.imageRotage(filename)
    except Exception,e:
        res = {'error':1,'msg':str(e)}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))    

def removePic(request):
    import os
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    student_oid = request.GET.get("student_oid")
    branch = request.GET.get("branch")
    type = request.GET.get("type")
    if not branch:
        branch = login_teacher.branch
    file_oid = request.GET.get("file_oid")
    try:
        studentFile = StudentFile.objects.get(id=file_oid)  # @UndefinedVariable
        if studentFile:
            if type == '3':
                filepath = BASE_DIR+USER_IMAGE_DIR+branch+'/'+studentFile.filename
            else:
                filepath = BASE_DIR+USER_IMAGE_DIR+login_teacher.branch+'/'+student_oid+'/'+studentFile.filename
            studentFile.delete()
            os.remove(filepath)
    except Exception,e:
        errormsg = 1
        
    return HttpResponseRedirect('/web/pages?type='+type+'&student_oid='+student_oid)

def showPage(request,sn):
    ip = http.getVisitIp(request)
    teacherId = request.GET.get("teacherId")
    tid = teacherId
    to = None
    try:
        to = Teacher.objects.get(id=teacherId)  # @UndefinedVariable
        
    except Exception,e:
        print e
    try:
        intsn = int(sn)
    except:
        intsn = -1
    if intsn > 0:
        page = Webpage.objects.get(sn=intsn)  # @UndefinedVariable
    pageType = 'branchShare'
    student = ''
    s = None
    if page.student:
        try:
            s = Student.objects.get(id=page.student)  # @UndefinedVariable
            student = str(s.id)
            pageType = "userShare"
        except:
            student = ''
    teacher = ''
    if teacherId:
        try:
            t = Teacher.objects.get(id=teacherId)  # @UndefinedVariable
            teacher = str(t.id)
        except:
            teacher = ''
    introBG = "eeeeee"
    if page.background == 'b3' or page.background == 'b4':
        introBG = "ffffff"
      
    http.pageVisit(str(page.branch.id),student,teacher,pageType,ip,page)
    teacherId = None
    if pageType == 'userShare':
        try:
            teacherId = s.teacher.id
        except:
            teacherId = None
    temp = []
    i = 0
    for tuple in page.sortedPics:
        temp.append(tuple[0])
        i = 1
    if i > 0:
        page.pics = temp
    else:
        try:
            pics = sorted(page.pics, key=attrgetter('order'),reverse=False)
        except:
           pics = page.pics
        page.pics = pics
    iconUrl = '/go_static/img/logo.png'
    if page.pics and len(page.pics)>0:
        pic = page.pics[0]
        try:
            iconUrl = USER_IMAGE_DIR+pic.filepath+pic.filename
        except:
            print page.id
            iconUrl = None
         
    #token = http.getAccessToken()
    res = http.getJieli360WXToken()
    token = res['access_token']
    ticket = http.getJsapiTicket(token)
    if not teacherId:
        teacherId = teacher
    url = 'http://rang.jieli360.com/page/'+sn+'/?teacherId='+str(teacherId)
    fromMessage = request.GET.get("from")
    if fromMessage:
        url = url + '&from=' + fromMessage
    #print '[URLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLL]'+url
    sign = Sign(ticket, url)
    res,string1 = sign.sign()
    
    return render(request, 'page.html', {"page":page,
                                         "iconUrl":iconUrl,
                                         "ticket":ticket,
                                         "introBG":introBG,
                                         "teacherId":teacherId,"to":to,
                                         "student":s,'res':res,"string1":string1,
                                         "appId":constant.APPID,"url":url,
                                         "imagePath":USER_IMAGE_DIR})
def weixinTXT(request):
    return render(request, 'MP_verify_khiOZqwCFngYL7Tg.txt',{})

def savePage(request):
    if constant.DEBUG:
        print '1'
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    title = request.POST.get("title")
    text = request.POST.get("text")
    publishDate = request.POST.get("publishDate")
    student_oid = request.POST.get("student_oid")
    teacher_oid = request.POST.get("teacher_oid")
    type = request.POST.get("type")
    pics = request.POST.get("pics")
    picList = pics.split(',')
    if constant.DEBUG:
        print pics
    if pics == '':
        picList = []
        #print picList
    

    allPics  = request.POST.get("allPics")
    allPicList = allPics.split(',') 
    try:
        memos = request.POST.get("memos")
        memoList = memos.split('||')
        
    except Exception,e:
        print 'memos'
        print e
    try:    
        orders  = request.POST.get("orders")
        orderList = orders.split(',')
    except Exception,e:
        print 'orders'
        print e

    bg = request.POST.get("bg")
    allMap = dict()
    i = 0
    if constant.DEBUG:
        print '2'
    for id in allPicList:
        allMap[id] = orderList[i]
        pic = StudentFile.objects.get(id=ObjectId(id))  # @UndefinedVariable
        pic.memo = memoList[i]
        try:
            pic.order = int(orderList[i])
        except:
            pic.order = None
        pic.save()
        i = i + 1
        
    
    pageMap = dict()
    try:
      if constant.DEBUG:
        print '3'  
      for pic in picList:
        try:
            pageMap[ObjectId(pic)] = int(allMap[pic])
        except Exception,e:
            print e
            pageMap[ObjectId(pic)] = 0
            print 'err0'
      if constant.DEBUG:
        print '31'
      sortedList = sorted(pageMap.items(), key=operator.itemgetter(1))
      if constant.DEBUG:
        print '32'
    except Exception,e:
        print 'err1'
        print e
    if constant.DEBUG:
        print '4'
    student = None
    teacher = None
    try:
        if student_oid:
            student = Student.objects.get(id=student_oid)  # @UndefinedVariable
        if teacher_oid:
            teacher = Teacher.objects.get(id=teacher_oid)  # @UndefinedVariable
    except Exception,e:
        print e
        err = 1
    if constant.DEBUG:
        print '5'
    for p in picList:
        try:
            pic = StudentFile.objects.get(id=p)  # @UndefinedVariable
        except Exception,e:
            print e
            pic = None
    if constant.DEBUG:
        print '6'
    try:
        fileType = int(type)
    except Exception,e:
        print e
        fileType = 3
    if constant.DEBUG:
        print '7'
    branchId = login_teacher.branch
    try:
        branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    except Exception,e:
        print e
        branch = None
    if constant.DEBUG:
        print '8'
    id = request.POST.get("id")
    page = None
    try:
        page = Webpage.objects.get(id=id)  # @UndefinedVariable
    except Exception,e:
        #print e
        page = Webpage()
        all = Webpage.objects.all().order_by("-sn")  # @UndefinedVariable
        if all and len(all)>0:
            sn = all[0].sn+1
        #sn = Webpage.objects.all().count()+1
            page.sn = sn
    if constant.DEBUG:
        print '9'
    page.title = title
    page.text = text
    page.publishDate = publishDate
    page.branch = branch
    page.fileType = fileType
    page.sortedPics = sortedList
    page.background = bg
    if student:
        page.student = str(student.id)
    page.teacher = login_teacher.id
    if page.title:
        page.save()
    if constant.DEBUG:
        print '10'
    res = {"error": 0, "msg": "保存学籍成功"}
    if constant.DEBUG:
        print res
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def zenweiqiNews(request):
    news = http.getZenweiiNews()
    return render(request, 'zenweiqiNews.html', {"news":news})

def cmb2017(request):
    year = [3,4,5,6,7,8,9,10]
    month = [1,2,3,4,5,6,7,8,9,10,11]
    return render(request, 'cmb2017.html', {"year":year,"month":month})

def cmb2017res(request):
    prt1mobile = request.POST.get("prt1mobile")
    gender = request.POST.get("gender")
    ageYear = request.POST.get("ageYear")
    ageMonth = request.POST.get("ageMonth")
    if constant.DEBUG:
        print 'cmb2017-year-month'
        print ageYear
        print ageMonth
    name = request.POST.get("name")
    birthday = None
    now = getDateNow()
    if ageYear:
        try:
            days = int(ageYear)*365
            if ageMonth:
                days = days+int(ageMonth)*30
            
            birthday = now - datetime.timedelta(days=days)
        except Exception,e:
            print e 
            birthday = None
    if constant.DEBUG:
        print birthday
    student = Student()
    if prt1mobile and len(prt1mobile) > 7:
        if True:
        #try:
            queryTel = Q(prt1mobile=prt1mobile)|Q(prt2mobile=prt1mobile)
            query = Q(type=1)&Q(city=constant.BEIJING)
            netBranch = Branch.objects.get(query)  # @UndefinedVariable
            queryNet = (queryTel)&Q(regBranch=netBranch.id)
            students = Student.objects.filter(queryNet) #网络部是否有录入这个电话 @UndefinedVariable
            if students and len(students) > 0:
                student = students[0]
            queryBranch = (queryTel)&Q(regBranch__ne=netBranch.id)
            studentsBranch = Student.objects.filter(queryBranch) # 校区是否有录入这个电话 @UndefinedVariable
            if studentsBranch and len(studentsBranch) > 0:
                student.dup = -1
                student.resolved = -1
        #except Exception,e:
            
         #   return render(request, 'cmb2017res.html', {"err":1,"res":str(e)})
        student.name = name
        student.gender = gender
        student.sourceType = 'A'
        
        student.regBranch = netBranch
        student.prt1mobile = prt1mobile
        student.memo = u'招行员工专属优惠报名:原价9000元/30次的课程优惠价7200元'
        source = Source.objects.get(id=ObjectId('5a290c9697a75dee6ab49472'))  # @UndefinedVariable
        if source:
            student.source = source 
            student.code = source.sourceCode + now.strftime(("%Y%m%d"))
        student.regTime = now
        student.callInTime = now   
        student.birthday = birthday
        student.save()
        openIds = []
        query = Q(branch=netBranch.id)&Q(role__gt=3)&Q(role__lt=8)&Q(status__ne=-1)
        toTeachers = Teacher.objects.filter(query)  # @UndefinedVariable
        if toTeachers:
            if len(toTeachers)>0:        
                for t in toTeachers:
                    #print 'toTeacher-'+t.branch.branchName+t.name
                    if t.openId:
                        openIds.append(t.openId)
            
    else:
        res = u"没有填写手机号"
        err = 1
        return render(request, 'cmb2017res.html', {"err":err,"res":res})
    return render(request, 'cmb2017res.html', {"err":0,"student":student,"openIds":openIds})

import re, urlparse

def urlEncodeNonAscii(b):
    return re.sub('[\x80-\xFF]', lambda c: '%%%02x' % ord(c.group(0)), b)

def iriToUri(iri):
    parts= urlparse.urlparse(iri)
    return urlparse.urlunparse(
        part.encode('idna') if parti==1 else urlEncodeNonAscii(part.encode('utf-8'))
        for parti, part in enumerate(parts)
    )


def netReg(request):
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    if constant.DEBUG:
        print 'in net reg----------'
    mobile = request.POST.get("mobile")
    gender = request.POST.get("gender")
    year = request.POST.get("year")
    month = request.POST.get("month")
    name = request.POST.get("name")
    pageFrom = request.POST.get("pageFrom")
    if not pageFrom:
        pageFrom = ''
    city = request.POST.get("city")
    
    if not pageFrom:
        pageFrom = ''
    if not gender:
        gender = ''
    if not city:
        cith = ''
    if not year:
        year = ''
    if not month:
        month = ''
    student = Reg()
    if mobile and len(mobile) > 7:
        query = Q(id=constant.NET_BRANCH)
        netBranch = Branch.objects.get(query)  # @UndefinedVariable
        student.name = name
        student.gender = gender
        student.source = pageFrom
        student.city = city
        student.mobile = mobile
        student.year = year
        student.month = month
        student.regTime = getDateNow(8)
        student.branch = str(netBranch.id)
        student.save()
        if constant.DEBUG:
            print 'save done'
        openIds = []
        query = Q(branch=netBranch.id)&Q(role__gt=3)&Q(role__lt=8)&Q(status__ne=-1)
        if constant.DEBUG:
            print 'before get tacher'
        toTeachers = Teacher.objects.filter(query)  # @UndefinedVariable
        if constant.DEBUG:
            print 'got teacher'
        i = 0
        if toTeachers:
            if len(toTeachers)>0:
                if constant.DEBUG:
                    print 'has teacher'        
                for t in toTeachers:
                    i = i + 1
                    #t.email = 'patch@jieli360.com'
                    #try:
                    if t.email and t.email.find('@') > -1:
                        email = 'email='+t.email
                        
                        email = email+u'&pageFrom='+pageFrom+u'&name='+name+u'&mobile='+mobile+u'&gender='+gender+u'&year='+year+u'&month='+month+u'&city='+city
                        #email = urllib.quote(email.encode('utf8'), ':/')
                        if constant.DEBUG:
                            print 'email:'+email

                        if constant.DEBUG:
                                print 'begin email'
                        url = u'http://jieli360.com/API/util/mail.jsp?'+email
                        url = iriToUri(url)
                        http.http_get(url)
                        if constant.DEBUG:
                                print 'email done'
                    #except Exception,e:
                     #   print e
        res = {"error": 0}   
    else:
        res = {"error": 1,"res":u"没有填写手机号"}
        
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def regList(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginStr = request.POST.get('beginDate')
    endStr = request.POST.get('endDate')
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    bDate = None
    eDate = None
    now = utils.getDateNow()
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + datetime.timedelta(days=1)
        except:
            eDate = None
    if not bDate and not eDate:
        eDate = now + datetime.timedelta(days=1)
        endDate = now.strftime("%Y-%m-%d")
        now = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        bDate = now + datetime.timedelta(days=-90)
        beginDate = bDate.strftime("%Y-%m-%d")
    
    list = None
    searchBranch = None
    #if login_teacher.cityId != constant.BEIJING:
    if True:
        searchBranch = login_teacher.branch
    query = Q(regTime__gte=beginDate)&Q(regTime__lt=endDate)&Q(branch=searchBranch)
    query = Q(branch=searchBranch)&Q(type__ne='20181111luck')
    list = Reg.objects.filter(query).order_by('-regTime')
    isTest = 0
    showTest = 0
    if 'test.go2crm.cn' in request.META['HTTP_HOST'] or  '127' in request.META['HTTP_HOST']:
        isTest = 1
    
    if login_teacher.branch == constant.NET_BRANCH and isTest:
        showTest = 1
    return render(request, 'regList.html', {"err":0,"list":list,"login_teacher":login_teacher,
                                            "beginDate":beginDate,"showTest":showTest,
                                             "endDate":endDate,})

def api_done(request):

    login_teacher = checkCookie(request)
    if not (login_teacher):
        res = {"error":1,"msg":"未登录"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    regId = request.POST.get('id')
    done = request.POST.get('done')
    memo = request.POST.get('memo')

    reg = Reg.objects.get(id=regId)  # @UndefinedVariable

    msg = ''
    if reg:
        if memo != None:
            reg.memo = memo
            msg = u'备注修改成功'
        if done == '1':
            reg.done = True
            msg = u'已处理'
        elif done == '2':
            reg.done = False
            msg = u'未处理'
        reg.save()

        res = {"error": 0,"msg":msg}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def send_template_message(request):
    filename_err = settings.BASE_DIR+'/log/mail_err'
    openId = request.POST.get('openId')
    keyword1 = request.POST.get('keyword1')
    keyword2 = request.POST.get('keyword2')
    keyword3 = request.POST.get('keyword3')  # mobile number
    keyword5 = request.POST.get('keyword5')
    first = request.POST.get('first')
    if first is None:
        first = "您有一个新预约"
    url = request.POST.get('url')
    
    if url == 'zenweiqi' or url == 'http://www.go2crm.cn':
        if url == 'zenweiqi':
            urlSetting = ""
            
        else:
            urlSetting = url
    first_color = "#173177"
    res = send_weixin(first, keyword1, keyword2, keyword3, keyword5, openId, urlSetting, first_color)
    
    print 'sendWX URL----------------------------'
    print url
    #print keyword1+','+keyword2+','+keyword3+','+keyword5
    if keyword1 == u'真朴围棋课程':
    #if True:
            try:
                print 'SEND MAIL BEGIN'
                #鲁玉祥－oRcnlt1bXoO0Qxp_Jlhc_E1aPKBY
#温婧－oRcnlt0bP6D04GDKrIDakmmIuRkg
#倩倩－oRcnlt5I-aMTaZyZCymPrqyxP4RQ
#patch-oRcnlt2T_M0N8ohsHTcoAPiQCtO0
#张广秀-oRcnlt5VlLIuZZc1HVgUU0qL2NWM
                toBox = ''
                if openId == 'oRcnlt0bP6D04GDKrIDakmmIuRkg':
                    toBox = 'wenjing@zhenpuedu.com'
                if openId == 'oRcnlt1bXoO0Qxp_Jlhc_E1aPKBY':
                    toBox = 'luyuxiang@zhenpuedu.com'
                if openId == 'oRcnlt5I-aMTaZyZCymPrqyxP4RQ':
                    toBox = 'xuqianqian@zhenpuedu.com'
                if openId == 'oRcnlt5VlLIuZZc1HVgUU0qL2NWM':
                    toBox = 'zhangguangxiu@zhenpuedu.com'
                if openId == 'oRcnlt2T_M0N8ohsHTcoAPiQCtO0':
                    toBox = 'zhenpu@jieli360.com'
                receivers = [toBox]
                http.sendMail(receivers,first,keyword2+','+keyword3+','+keyword5,'zhenpu')
                print 'SEND MAIL DONE'
            except Exception,e:
                try:
                    utils.save_log(filename_err,'sentErr:'+str(e))
                except:
                    utils.save_log(filename_err,'save sentErr err')

                print e
                print 'SEND MAIL ERR!'
    
    return http.JSONResponse(res)

def send_weixin(first, keyword1, keyword2, keyword3, keyword5, openId, url, first_color):
  res = None
  filename_err = settings.BASE_DIR+'/log/weixin_reg_err'
  try:  
    keyword4 = str(utils.now2datetime(True))
    #website = "http://jieli360.com/weixin/getToken.jsp?from=jielibang"
    #req = None
    #content = None
    token = None
    try:
        #req = urllib2.urlopen(website)
        #content = req.read()
        #token = json.loads(content)["token"]
        res = http.getJieli360WXToken()
        token = res['access_token']
    except Exception,e:
        #utils.save_log(filename_err,'WRONG TOKEN:'+str(e)+'|'+str(content))
        print 'err get TOKEN'

    weixinUrl = "https://api.weixin.qq.com/cgi-bin/message/template/send?access_token=" + token
    try:
        utils.save_log(filename_err,'TOKEN:'+str(token))
    except:
         utils.save_log(filename_err,'SAVE TOKEN ERR')
    data = json.dumps({"touser": openId,
                       "template_id": "JmUvMNo30eoPUj1g4E1_0uWtRwZqWbebjoSzdRfT-mk",
                       "url": url,
                       "topcolor": "#FF0000",
                       "data": {
                           "first": {
                               "value": first,
                               "color": first_color
                           },
                           "keyword1": {
                               "value": keyword1,
                               "color": "#173177"
                           },
                           "keyword2": {
                               "value": keyword2,
                               "color": "#173177"
                           },
                           "keyword3": {
                               "value": keyword3,
                               "color": "#173177"
                           },
                           "keyword4": {
                               "value": keyword4,
                               "color": "#173177"
                           },
                           "keyword5": {
                               "value": keyword5,
                               "color": "#173177"
                           },
                           "remark": {
                               "value": "请您及时登录后台系统处理客户预约消息。",
                               "color": "#FF0000"
                           }
                       }
                       })
    try:
        req = urllib2.urlopen(weixinUrl, data)
        rest = req.read()
    except Exception,e:
        try:
            utils.save_log(filename_err,'sentErr:'+str(e))
        except:
            utils.save_log(filename_err,'save sentErr err')
        print 'err send WX'

    filename_err = settings.BASE_DIR+'/log/weixin_reg_err'
    filename_ok = settings.BASE_DIR+'/log/weixin_reg_ok'
    res = json.loads(rest)
    wrongMess = first + '|' + keyword2 + '|' + keyword3 + '|' + keyword4 + '|' + keyword5

    mess = urllib.quote(wrongMess.encode('utf8'), ':/')

    if res['errcode'] == 0:
        utils.save_log(filename_ok, "[OK][time]" + utils.now2datetime().strftime("%Y-%m-%d %H:%M:%S") + "[code]" + str(
            res['errcode']) + "[openId]" + str(openId) + "[tel]" + keyword3)
        #=======================================================================
        # wrongMess = u'微信成功｜' + wrongMess
        # pushurl = u'http://www.go2crm.cn/go2/teacher/api_push?mess='
        # mess = urllib.quote(wrongMess.encode('utf8'), ':/')
        # pushurl = pushurl + mess + u'&openId=' + openId
        #=======================================================================

    else:
        req = urllib2.urlopen(weixinUrl, data)
        rest = req.read()
        res = json.loads(rest)
        if res['errcode'] != 0:
            try:
                utils.save_log(filename_err,
                       "[ERR][time]" + utils.now2datetime().strftime("%Y-%m-%d %H:%M:%S") + "[code]" + str(
                            res['errcode']) + "[openId]" + str(openId) + "[first]"+first+"[keyword1]"+keyword1+"[name]" + keyword2 + "[tel]" + keyword3)

            except Exception,e:
                utils.save_log(filename_err,'wrong encode')
            fromurl = 'zenweiqi.com'
            if first.find(u'上海') > -1:
                fromurl = 'shanghai'

  except Exception,e:
      try:
          utils.save_log(filename_err, "[ERR][time]" + utils.now2datetime().strftime("%Y-%m-%d %H:%M:%S") + '[err]' + str(e))
      except:
          utils.save_log(filename_err,'ERR')
  return res
  
def luckyDraw2018a(request):#抽奖首页
    now = utils.getDateNow(8)
    startdate = datetime.datetime.strptime("2018-11-06 10:00:00","%Y-%m-%d %H:%M:%S")
    enddate = datetime.datetime.strptime("2018-11-11 23:00:00","%Y-%m-%d %H:%M:%S")
    isStart = 0
    seconds = (startdate-now).seconds
    
    hours = seconds/3600
    minutes = seconds%3600/60
    seconds = seconds%3600%60
    
    if now >= startdate and now < enddate:
        isStart = 1
    elif now >= enddate:
        isStart = 2
    tid = request.GET.get("tid")
    t = None
    try:
        t = Teacher.objects.get(id=tid)  # @UndefinedVariable
    except:
        t = None
    if not t:
        t = Teacher.objects.get(id='587430a197a75d50a4e4d550')#鲁玉祥 @UndefinedVariable
    t.cityId = str(t.branch.city.id)
    branches = utils.getBranches(t, None,constant.BranchType.school)
    return render(request, 'luckyDraw2018a.html', {"branches":branches,"tid":tid,"isStart":isStart,
                                                   "now":now,"minutes":minutes,"hours":hours,"seconds":seconds})

def luckyDraw2018b(request):#抽奖后填号码页面
    print '0000000000000000000000'
    ip = None
    if request.META.has_key('HTTP_X_FORWARDED_FOR'):
        ip =  request.META['HTTP_X_FORWARDED_FOR']
    else:
        ip = request.META['REMOTE_ADDR']
    print '0000000000000000000001'
    reload(sys)  
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    tid = request.POST.get("tid")
    print tid
    mobile = request.POST.get("mobile")
    isStaff = False
    try:
        teachers =Teacher.objects.filter(mobile=mobile)
        if len(teachers) > 0:
            isStaff = True
    except:
        isStaff = False
    print '0000000000000000000002'
    selectBranch = request.POST.get("branch")
    name = request.POST.get("name")
    isStudent = request.POST.get("isStudent")

    msg = None
    t = None
    branch = None
    branchName = None
    city = None
    reg = None
    
    query = Q(mobile=mobile)&Q(type='20181111luck')
    try:
        regs = Reg.objects.filter(query)
        print regs._query
        if len(regs) > 0:
            reg = regs[0]
            msg = u'本号码已抽过奖'
            return render(request, 'luckyDraw2018b.html', {"reg":reg,"msg":msg})
    except:
        reg = Reg()
        reg.mobile = mobile
    print '0000000000000000000003'
    canDo = False
    print ip
    if ip:
        query = Q(key='20181111luckyDrawIP')&Q(value=ip)
        ips = None
        try:
            ips = Short.objects.get(query)
            print '0000000000000000000004'
        except:
            ips = Short()
            ips.key='20181111luckyDrawIP'
            ips.value=ip
            ips.value2='0'
            print '0000000000000000000041'
        try:
            print '0000000000000000000005'
            if ips and int(ips.value2) < 3:
                canDo = True
                ips.value2 = str(int(ips.value2) + 1)
                ips.save()
        except:
            ips.value2='1'
            ips.save()
    print '222'
    if not canDo:
        msg = u'请勿多次抽奖'
    
    if not msg:
        try:
            print '333'
            try:
                
                print tid
                t = Teacher.objects.get(id=tid)  # @UndefinedVariable
                print 'tea000000001'
            except:
                t = None
            print 'tea000000002'
            if t:
                print t
                print 'tea000000003'
                branch = str(t.branch.id)
                print 'tea000000004'
                branchName = t.branch.branchName
                print 'tea000000005'
                city = str(t.branch.city.id)
                print 'tea000000006'
                if not reg:
                    reg = Reg()
                try:
                    reg.teacher = str(t.id)
                except Exception,e:
                    print e
                print 'tea000000007'
                reg.teacherName = t.name
                print 'tea000000008'
                reg.city = city
                print 'tea000000009'
                reg.branch = branch
                print 'tea0000000010'
                reg.branchName = branchName
        except:
            print 'NO REF TEACHER'

        print '333333333333330'
        if not reg:
            reg = Reg()
        reg.type='20181111luck'
        print name
        reg.name = name
        print mobile
        reg.mobile = mobile
        reg.selectBranch = selectBranch
        print selectBranch
        reg.regTime = utils.getDateNow(8)
        print '333333333333331'
        try:
            reg.memo = lucky(isStaff)
        except Exception,e:
            reg.memo = '211'
            print e
        print '333333333333332'
        reg.source = ''
        hasCode = True
        print '444'
        while hasCode:
            m = ''.join(random.choice( string.digits) for _ in range(6))
            query = Q(source=m)
            rcode = Reg.objects.filter(query)
            if rcode and len(rcode) > 0:
                continue
            else:
                reg.source = m
                break
        
        print '555'
        reg.isStudent = isStudent
        reg.save()
        param = ''.join(reg.memo+u'元(验证码:'+reg.source+')')
        res = questionnaire.sendMiaoDiSMS("841740907", param, mobile)
        print '666'
        utils.save_log('sms20181111', '['+utils.getDateNow(8).strftime("%Y%m%d-%H:%M:%S")+']['+mobile+']'+res)#print res
    print '777'
    try:
        reg.mobile = reg.mobile[0:3]+'*****'+reg.mobile[8:11]
    except:
        err = 1
    
    return render(request, 'luckyDraw2018b.html', {"reg":reg,"msg":msg})


#输入概率p，返回是否抽中
def luckyDraw2018(p):# 抽奖方法

    if p > 100:
        return True
    if p <= 0:
        return False
    res = random.randint(1,100)
    if res <= p:
        return True
    else:
        return False
    #print res


def lucky(isStaff):
        has1111 = False
        memo = '11'
        luck1111 = False
        now = utils.getDateNow(8)
        b = utils.getDayBegin(now)
        all1111 = 0
        query = Q(memo='1111')
        try:
            all1111 = len(Reg.objects.filter(query))
        except:
            all1111 = 0
        
        luck211 = False
        luck511 = False
        luck11 = False
        if all1111 < 5:
            try:
                query = Q(regTime__gte=b)&Q(memo='1111')
                has1111 = len(Reg.objects.filter(query))>0
            except:
                has1111 = False
        
        if not isStaff and not has1111:
            luck1111 = luckyDraw2018(5)
        luck1111 = False
        if not luck1111:
            luck211 = luckyDraw2018(40)
            if not luck211:
                luck511 = luckyDraw2018(33)
            if not luck511 and not luck211:
                luck11 = True
        
        if luck11:
            memo = '11'
        elif luck211:
            memo = '211'
        elif luck511:
            memo = '511'
        elif luck1111:
            memo = '511'
        if memo == '1111':
            memo = '511'
        return memo

def regList2(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    keyword = request.GET.get('kw')
    
    
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    bDate = None
    eDate = None
    now = utils.getDateNow()
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + datetime.timedelta(days=1)
        except:
            eDate = None
    if not bDate and not eDate:
        eDate = now + datetime.timedelta(days=1)
        endDate = now.strftime("%Y-%m-%d")
        now = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        bDate = now + datetime.timedelta(days=-90)
        beginDate = bDate.strftime("%Y-%m-%d")
    
    list = None
    searchBranch = None
    #if login_teacher.cityId != constant.BEIJING:
    if True:
        searchBranch = login_teacher.branch
    query = Q(regTime__gte=beginDate)&Q(regTime__lt=endDate)&Q(branch=searchBranch)
    query = Q(branch=searchBranch)|Q(selectBranch=login_teacher.branchName)
    if keyword and len(keyword) > 0:
        query = Q(mobile=keyword)|Q(source=keyword)
    query = (query)&Q(type='20181111luck')
    list = Reg.objects.filter(query).order_by('branch')
    temp = []
    for r in list:
        if r.studentId:
            try:
                s = Student.objects.get(id=r.studentId)
                r.studentName = s.name
                r.studentMobile = s.prt1mobile
                
            except Exception,e:
                print e
                err = 1
        temp.append(r)
    return render(request, 'regList2.html', {"err":0,"list":temp,"login_teacher":login_teacher,
                                             "kw":keyword,
                                            "beginDate":beginDate,
                                             "endDate":endDate,})

def useVoucher(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    voucher = request.GET.get("voucher")
    value = request.GET.get("value")
    keyword = request.GET.get("keyword")

    query = Q(branch=login_teacher.branch)
    query2 = Q(name__icontains=keyword)|Q(name2__icontains=keyword)|Q(prt1mobile__contains=keyword)|Q(prt2mobile__contains=keyword)
    query3 = query&(query2)
    students = Student.objects.filter(query3)
    try:
        if not students:
            students = []
    except:
        students = []
 
    return render(request, 'useVoucher.html', {"login_teacher":login_teacher,"students":students,
                                             "voucher":voucher,"keyword":keyword,
                                            "value":value})

def  checkVoucher(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    
    res = {"error":0}
    sid = request.POST.get("sid")
    voucher = request.POST.get("voucher")

    query = Q(studentId=sid)
    reg = Reg.objects.filter(query)
    if reg and len(reg) > 0:
        res = {"error":1,"msg":"此学生已兑过奖"}
    query = Q(source=voucher)&Q(done=True)
    reg = Reg.objects.filter(query)
    print reg._query    
    if reg and len(reg) > 0:
        res = {"error":1,"msg":"此码已兑过奖"}
    response = http.JSONResponse(json.dumps(res, ensure_ascii=False))
    return response

if __name__ == "__main__":
    a1 = 0
    a2 = 0
    a3 = 0
    a4 = 0
    for i in range(20):
        l = lucky(False) 
        if l == '1111':
            a1 = a1 + 1
        if l == '511':
            a2 = a2 + 1
        if l == '211':
            a3 = a3 + 1
        if l == '11':
            a4 = a4 + 1
    print '1111--'+str(a1)
    print '511--'+str(a2)
    print '211--'+str(a3)
    print '11--'+str(a4)
    
    
def library20181215(request):
    page = None
    student = None
    page = Webpage()
    branch = Branch.objects.get(id='5867c0c33010a51fa4f5abe6')
    page.branch = branch
    student = Student()
    student.branch = branch
    return render(request, 'library20181215.html', {"student":student,
                                             "page":page})   
    
def getJieli360WXToken(request):
    res = http.getJieli360WXToken()
    
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))    