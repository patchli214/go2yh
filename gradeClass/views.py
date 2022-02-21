#!/usr/bin/env python
# -*- coding:utf-8 -*-
from branch.models import Branch
from student.models import Suspension
from tools.data import saveLesson
import time
__author__ = 'bee'
import json, datetime
from itertools import chain
from operator import attrgetter
from mongoengine.queryset.visitor import Q
from django.shortcuts import render
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from tools import http, utils, constant, util2, data, util3, dbsearch
from tools.utils import checkCookie,getDateNow
from regUser.models import GradeClass, Classroom
from teacher.models import Teacher
from teacher.models import Login_teacher
from regUser.models import Student
from branch.models import Branch
from django.http import HttpResponse,HttpResponseRedirect
from gradeClass.models import *
from datetime import timedelta 
from statistic.models import LessonCheck
from django.views.decorators.csrf import  csrf_exempt
# Create your views here.
def edit_gradeClass(request, gradeClass_type, gradeClass_oid):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    mainurl = request.COOKIES.get('mainurl','')
    branchs = Branch.objects.all()
    branch = Branch.objects.get(id=login_teacher.branch)
    gradeClass_type = int(gradeClass_type)

    classrooms = []
    for i in range(1,branch.branchRooms+1):
        classrooms.append(i)
    teachers = Teacher.objects.filter(Q(branch=login_teacher.branch)&Q(status=0))
    no_class_students = utils.getNoClassStudent(login_teacher.branch)  # 没有班，但已签约学生
    #no_sign_students = Student.objects.filter(branch=login_teacher.branch).filter(status__ne=constant.StudentStatus.sign)  # 没有签约学生
    student_oid = request.GET.get("student_oid")
    thisStudent = None
    in_class_students = []#Student.objects.filter(gradeClass__ne=None)  # 有班的学生
    if student_oid:
        thisStudent = Student.objects.get(id=student_oid)
    
    week_list = range(1, 8)

    gradeClass = None
    if gradeClass_oid:
        try:
            gradeClass = GradeClass.objects.get(id=gradeClass_oid)
        except:
            gradeClass = None

    return render(request, 'editGradeClass.html',
                  {"thisStudent":thisStudent,"login_teacher":login_teacher,"branchs":branchs,
                   "classrooms": classrooms, "teachers": teachers, "no_class_students": no_class_students,
                   "in_class_students": in_class_students, 
                   "mainurl":mainurl,
                   "week_list": week_list, "gradeClass": gradeClass, "gradeClass_type": gradeClass_type})

#进入补课页面
def extraLesson(request):
    
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    gradeClass_oid = request.GET.get("id")
    gradeClass_type = '2'
    branchs = Branch.objects.all()
    branch = Branch.objects.get(id=login_teacher.branch)
    gradeClass_type = int(gradeClass_type)
    
    classrooms = []
    for i in range(1,branch.branchRooms+1):
        classrooms.append(i)
    teachers = Teacher.objects.filter(Q(branch=login_teacher.branch)&Q(status=0))

    week_list = range(1, 8)

    gradeClass = None
    classLessons = None
    studentLessons = None
    extraLessons = None
    if gradeClass_oid:
        try:
            gradeClass = GradeClass.objects.get(id=gradeClass_oid)
            
            query = Q(gradeClass=gradeClass_oid)
            classQuery = query&Q(type=0)
            studentQuery = query&Q(type=1)
            extraQuery = query&Q(type=3)
            classLessons = Lesson.objects.filter(classQuery).order_by("-lessonTime")
            
            lessLessons = []
            
            for student in gradeClass.students:
                if student.siblingId:
                    try:
                        sib = Student.objects.get(id=student.siblingId)
                        if sib and sib.contract:
                            student.contract = sib.contract
                    except:
                        err = 1
                
        except Exception,e:
            print e
            gradeClass = None

    return render(request, 'extraLesson.html',
                  {"login_teacher":login_teacher,"branchs":branchs,
                   "classrooms": classrooms, "teachers": teachers, 
                   "classLessons":classLessons,"lessLessons":lessLessons,
                   
                   "week_list": week_list, "gradeClass": gradeClass, "gradeClass_type": gradeClass_type})

#添加补课信息
@csrf_exempt
def api_extraLesson(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch = login_teacher.branch
    id = request.POST.get("id")
    classId = request.POST.get("classId")
    teacherId = request.POST.get("teacherId")
    classroomStr = request.POST.get("classroom")
    lessonTimeStr = request.POST.get("lessonTime")
    #students = request.POST.get("students")
    studentTargets_str = request.POST.get("studentTargets")

    studentTargets = studentTargets_str.split(",")

    students = None
    s = []
    for st in studentTargets:
        sid = st.split("_")[0]
        if sid not in s:
            s.append(sid)
            students = ","+sid
    if students[0:1] == ',':
        students = students[1:len(students)]

    sss = s[0]
    i = 0
    for ss in s:
        if i > 0:
           sss = sss + ',' + ss
        i = i + 1

    students = sss
    gradeClass = None
    teacher = None

    classroom = 0
    try:
        classroom = int(classroomStr)
    except:
        res = {"error": 1, "msg": "教室未安排"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        gradeClass = GradeClass.objects.get(id=classId)
    except:
        res = {"error": 1, "msg": "班级未找到"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        teacher = Teacher.objects.get(id=teacherId)
    except:
        res = {"error": 1, "msg": "老师未找到"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    lessonTime = datetime.datetime.strptime(lessonTimeStr,"%Y-%m-%d %H:%M")
    lesson = Lesson()
    if id:
        try:
            lesson = Lesson.objects.get(id=id)

        except:

            lesson = Lesson()

    lesson.lessonTime = lessonTime
    lesson.type = 2
    lesson.student = students
    lesson.gradeClass = gradeClass
    lesson.classroom = classroom
    lesson.teacher = teacher
    lesson.branch = branch
    lesson.oriLessons = studentTargets

    lesson.save()

    res = {"error": 0, "msg": "成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def api_save_gradeClass(request, gradeClass_type):
    gradeClass_type = int(gradeClass_type)
    gradeClass_oid = request.POST.get("gradeClass_oid")
    name = request.POST.get("name")
    start_date = request.POST.get("start_date")
    school_day = request.POST.get("school_day")
    school_time = request.POST.get("school_time")
    try:
        st = datetime.datetime.strptime(school_time, "%H:%M")
    except:
        res = {"error": 1, "msg": "时间格式错误！"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    classroom_oid = int(float(request.POST.get("classroom_oid")))
    teacher_oid = request.POST.get("teacher_oid")
    students_oid = request.POST.get("students_oid")
    info = request.POST.get("info")
    branch_oid = request.POST.get("branch_oid")

    gradeClass = utils.get_gradeClass_from_oid(gradeClass_oid)
    if not gradeClass:
        res = {"error": 1, "msg": "gradeClass错误"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    old_students = []
    if gradeClass_type == constant.GradeClassType.normal:
        old_students = gradeClass.students

    if teacher_oid:
        teacher = utils.get_teacher_from_oid(teacher_oid)
    
    if branch_oid:
        branch = utils.get_branch_from_oid(branch_oid)
    gradeClass.name = name
    gradeClass.gradeClass_type = gradeClass_type
    gradeClass.start_date = start_date
    if gradeClass_type == constant.GradeClassType.normal:
        gradeClass.school_day = school_day
    gradeClass.school_time = school_time
    gradeClass.info = info
    if classroom_oid:
        gradeClass.classroom = classroom_oid
    gradeClass.teacher = teacher
    gradeClass.branch = branch



# 正常课程 清空旧的
    for student in old_students:
        try:
            student = Student.objects.get(id=student.id)
            #student.teacher = None
            student.gradeClass = None
            student.save()
        except Exception,e:
            print e
            #res = {"error": 1, "msg": "学生错误"}
            #gradeClass.delete()
            #return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    gradeClass.created_at = utils.now2datetime()
    gradeClass.save()


# 改学生状态
    students = []
    student_oid_list = json.loads(students_oid)
    for student_oid in student_oid_list:
        try:
            student = Student.objects.get(id=student_oid)
            
            # 正常
            if student:
                students.append(student)
                if gradeClass_type == constant.GradeClassType.normal:
                    student.teacher = teacher
                    student.teacherName = teacher.name
                    student.gradeClass = str(gradeClass.id)
                elif gradeClass_type == constant.GradeClassType.demo:
                    demos = []
                    has = 0
                    for c in student.demo:
                        if c == gradeClass.id:
                            has = 1
                    if has== 0:
                        demos.append(str(gradeClass.id))
                    student.demo = demos
 
            student.save()
            #students.append(student)
        except Exception,e:
            print e
            # res = {"error": 1, "msg": "学生错误"}
            # return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    gradeClass.students = students
    gradeClass.save()

    res = {"error": 0, "msg": "保存成功"}
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


@csrf_exempt
def api_remove_gradeClass(request):
    gradeClass_oid = request.POST.get("gradeClass_oid")
    info =  request.POST.get("info")
    gradeClass = utils.get_gradeClass_from_oid(gradeClass_oid)
    if not gradeClass:
        res = {"error": 1, "msg": "未找到要删除的班级"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        gradeClass.info = info
        if gradeClass.gradeClass_type == constant.GradeClassType.normal:
            # 清空学生数据里的课程oid
            students = gradeClass.students
            for student in students:
                try:
                    gc = student.gradeClass
                    if gc == gradeClass_oid:
                        student.gradeClass = None
                        student.teacher = None
                        student.teacherName = None
                        student.save()
                except:
                    i = 1

            gradeClass.deleted = 1
            gradeClass.students = []
            gradeClass.save()
            res = {"error": 0, "msg": "删除成功"}
        else:
            res = {"error": 1, "msg": "未找到要删除的班级"}
        
    except:
        res = {"error": 1, "msg": "删除失败"}
    
    
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def api_cancel_demo(request):
    mainurl = request.COOKIES.get('mainurl','')
    gradeClass_oid = request.POST.get("gradeClass_oid")
    demo_info =  request.POST.get("demo_info")
    gradeClass = utils.get_gradeClass_from_oid(gradeClass_oid)
    msg = ''
    if not gradeClass:
        res = {"error": 1, "msg": "未找到要取消的试听课"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        gradeClass.info = demo_info
        if gradeClass.gradeClass_type == constant.GradeClassType.demo:
            gradeClass.demoIsFinish = -1
            gradeClass.save()
            msg = u"取消成功"
            res = {"error": 0, "msg": msg,"url":mainurl}
        else:
            res = {"error": 1, "msg": "未找到要取消的试听课"}
    except:
        res = {"error": 1, "msg": "取消失败"}
    students = []
    
    students = gradeClass.students

# 修改学生数据里的试听课状态
    for student in students:
        try:
            if gradeClass.gradeClass_type == constant.GradeClassType.demo:
                for dd in student.demo:

                            demo0 = GradeClass.objects.get(id=dd)

                            if demo0.demoIsFinish != 1 and demo0.demoIsFinish != -1:
                                student.isDemo = None
                                break
                            if demo0.demoIsFinish == 1:
                                student.isDemo = 1
                                break
                            if demo0.demoIsFinish == -1:
                                student.isDemo = -1
                                break
                student.save()
        except:
            i = 1
    
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def gradeClass_list(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    if login_teacher.role >3:
        gradeClasses = GradeClass.objects.filter(branch=login_teacher.branch).filter(gradeClass_type=constant.GradeClassType.normal).filter(deleted__ne=1).order_by("start_date")
    else:
        gradeClasses = GradeClass.objects.filter(teacher=login_teacher.id).filter(branch=login_teacher.branch).filter(gradeClass_type=constant.GradeClassType.normal).filter(deleted__ne=1).order_by("start_date")
    temp = []
    
    datenow = utils.getDateNow(8)
    i = 0
    for c in gradeClasses:
        i = i + 1
        old = 0
        young = 36500
        #query = Q(gradeClass=c.id)&Q(checked=True)&Q(type=0)
        #checkinCount = Lesson.objects.filter(query).count()
        #print i
        #c.checkinCount = checkinCount
        for s in c.students:
            birthday = s.birthday
            if birthday:
                days = (datenow-birthday).days
                
                if days < young:
                    young = days
                if days > old:
                    old = days
        y = old/365
        m = old%365/30
        c.old = str(y)+'.'+str(m)
        y = young/365
        m = young%365/30
        c.young = str(y)+'.'+str(m)
        temp.append(c)
        
    response = render(request, 'gradeClassList.html', {"login_teacher":login_teacher,"gradeClasses": temp})
    response.set_cookie("mainurl",'/go2/gradeClass/gradeClassList')
    return response

#已删除班级列表
def deletedClass_list(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    query = None
    if login_teacher.role >3:
        query = Q(branch=login_teacher.branch)&Q(gradeClass_type=constant.GradeClassType.normal)&Q(deleted=1)
        gradeClasses = GradeClass.objects.filter(query).order_by("start_date")
    else:
        query = Q(teacher=login_teacher.id)&Q(branch=login_teacher.branch)&Q(gradeClass_type=constant.GradeClassType.normal)&Q(deleted=1)
        gradeClasses = GradeClass.objects.filter(query).order_by("start_date")
    
    
    response = render(request, 'deletedClassList.html', {"login_teacher":login_teacher,"gradeClasses": gradeClasses})#, 'pages': paginator.page_range})
    response.set_cookie("mainurl",'/go2/gradeClass/gradeClassList')
    return response

#恢复已删除班级
@csrf_exempt
def api_restore_gradeClass(request):
    gradeClass_oid = request.POST.get("gradeClass_oid")
    try:
        gc = GradeClass.objects.get(id=gradeClass_oid)
        gc.deleted = 0
        gc.save()
        res = {"error": 0, "msg": "恢复成功"}
    except Exception,e:
        res = {"error": 1, "msg": str(e)}
    
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


def gradeClass_info(request, gradeClass_oid):
    try:
        gradeClass = GradeClass.objects.get(id=gradeClass_oid)
    except:
        gradeClass = None
    return render(request, 'gradeClassInfo.html', {"gradeClass": gradeClass})


# 日程
def schedule_list(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch = request.GET.get("branch")
    if branch is None:
        branch = login_teacher.branch 
    now = utils.now2datetime()
    now_day = now.isoweekday()  # 今天是本周第几天
    delte = 1 - now_day
    firstDay = now + datetime.timedelta(days=delte)  # 本周第一天

    week_list = []
    for i in range(0, 7):
        # 正常课程
        gradeClasses = GradeClass.objects.filter(branch=branch).filter(school_day=i + 1).filter(
        gradeClass_type=constant.GradeClassType.normal).order_by("school_time")
        # 计算日程时间区域
        start_day = firstDay + datetime.timedelta(days=i)  # 当天
        start_time_str = start_day.strftime("%Y-%m-%d") + " 00:00:00"
        end_time_str = start_day.strftime("%Y-%m-%d") + " 23:59:59"
        start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        # 日程
        schedules = GradeClass.objects.filter(branch=branch).filter(gradeClass_type__ne=constant.GradeClassType.normal).filter(
            start_date__gte=start_time).filter(start_date__lte=end_time)
        day_list = chain(gradeClasses, schedules)
        day_list = sorted(day_list, key=attrgetter("school_time"))
        week_list.append(day_list)

    return render(request, 'scheduleList.html', {"login_teacher":login_teacher,"week_list": week_list})

def getDayClasses(branch,weekday,start_time,end_time,rooms,div_height=None,div_ratio=None):
        millis0 = int(round(time.time() * 1000))
    
        
        day_list2 = []
        #改期正课
        query = Q(branch=branch)&Q(type=0)&Q(lessonTime__gte=start_time)&Q(lessonTime__lte=end_time)
        changeToLessons = Lesson.objects.filter(query)
        temp = []
        print '1-'+str(int(round(time.time() * 1000)) - millis0)
        millis0 = int(round(time.time() * 1000))
        for el in changeToLessons:
            gc = el.gradeClass
            gc.start_date = el.lessonTime
            gc.school_time = el.lessonTime.strftime("%H:%M")
            gc.teacher = el.teacher
            gc.classroom = el.classroom
            temp.append(gc)
        changeToLessons = temp
        # 正常课程
        query = Q(branch=branch)&Q(school_day=weekday + 1)&Q(gradeClass_type=constant.GradeClassType.normal)&Q(deleted__ne=1)&Q(start_date__lte=start_time)
        gradeClasses = GradeClass.objects.filter(query).order_by("school_time")
        temp = []
        print '2-'+str(int(round(time.time() * 1000)) - millis0)
        millis0 = int(round(time.time() * 1000))
        for gc in gradeClasses:
            query = Q(gradeClass=gc.id)&Q(type=0)&Q(oriTime__gte=start_time)&Q(oriTime__lte=end_time)
            changeLessons = Lesson.objects.filter(query)
            changeLesson = None
            if changeLessons and len(changeLessons)>0:
                changeLesson = changeLessons[0]
                oriTime = start_time+timedelta(days=gc.school_day-1)
                oriTime = datetime.datetime.strptime(oriTime.strftime("%Y-%m-%d")+" "+gc.school_time,"%Y-%m-%d %H:%M")
                if oriTime != changeLesson.oriTime:
                    has = True
            else:
                temp.append(gc)
        gradeClasses = temp
        # 试听课
        schedules = GradeClass.objects.filter(branch=branch).filter(gradeClass_type__ne=constant.GradeClassType.normal).filter(
            start_date__gte=start_time).filter(start_date__lte=end_time).filter(demoIsFinish__ne=-1)
        #补课
        extraLessons = Lesson.objects.filter(branch=branch).filter(type=2).filter(lessonTime__gte=start_time).filter(lessonTime__lte=end_time)
        temp = []
        print '3-'+str(int(round(time.time() * 1000)) - millis0)
        millis0 = int(round(time.time() * 1000))
        for el in extraLessons:
            gc = GradeClass()
            gc.start_date = el.lessonTime
            gc.school_time = el.lessonTime.strftime("%H:%M")
            gc.teacher = el.teacher
            gc.classroom = el.classroom
            gc.id = el.gradeClass.id
            sts = []
            ststr = el.student.split(",")
            for s in ststr:
                try:
                    st = Student.objects.get(id=s)
                    sts.append(st)
                except:
                    st = None
            gc.students = sts
            gc.gradeClass_type = 3
            temp.append(gc)
        day_list = chain(gradeClasses, schedules,temp,changeToLessons)
        day_list = sorted(day_list, key=attrgetter("school_time"))
        
        for r in rooms:
            
            if r == 'A':
                r = 10
            if r == 'B':
                r = 11
            if r == 'C':
                r = 12
            if r == 'D':
                r = 13
            if r == 'E':
                r = 14
            if r == 'F':
                r = 15
            
            room_clist = []
            lastTimeStr = '08:00'
            lastTime = datetime.datetime.strptime(lastTimeStr, '%H:%M')
            lastClass = 0
            ii = 0            
            for c in day_list:
                
                if c.classroom==r:
                    newTime = None
                    try:
                        c.school_time = c.school_time.replace(u"：",u":")
                        newTime = datetime.datetime.strptime(c.school_time, '%H:%M')
                    except Exception,e:
                        print e
                    timespace = timeDiff(newTime,lastTime)
                    lastTimeStr = c.school_time
                    lastTime = datetime.datetime.strptime(lastTimeStr, '%H:%M')
                    
                    if ii>0:
                        c.fromLast = (timespace - div_height)*div_ratio
                    else:
                        c.fromLast = timespace*div_ratio
                    timespace = timeDiff(datetime.datetime.strptime('21:00','%H:%M'),newTime)
                    c.toLast = (timespace - div_height)*div_ratio
                    room_clist.append(c)
                    
                    ii = ii+1
                    
            day_list2.append(room_clist)
        print '4-'+str(int(round(time.time() * 1000)) - millis0)
        millis0 = int(round(time.time() * 1000))
        return day_list2    
def getIntWeekDay(day):
    i = 0
    if day == 'Mon':
        i = 1
    if day == 'Tue':
        i = 2
    if day == 'Wed':
        i = 3
    if day == 'Thu':
        i = 4
    if day == 'Fri':
        i = 5
    if day == 'Sat':
        i = 6
    if day == 'Sun':
        i = 7
    return i
def getWeekClasses(branch,start_time,end_time,rooms,div_height,div_ratio):
    week_list = []
    
    dayList = []
    millis0 = int(round(time.time() * 1000))
    
    #改期正课
    query = Q(branch=branch)&Q(type=0)&Q(lessonTime__gte=start_time)&Q(lessonTime__lte=end_time)
    changeToLessons = Lesson.objects.filter(query)
    temp = []

    for el in changeToLessons:
            gc = el.gradeClass
            gc.start_date = el.lessonTime
            gc.school_time = el.lessonTime.strftime("%H:%M")
            gc.teacher = el.teacher
            gc.classroom = el.classroom
            temp.append(gc)
    changeToLessons = temp
    
    # 正常课程
    
    query = Q(branch=branch)&Q(gradeClass_type=constant.GradeClassType.normal)&Q(deleted__ne=1)&Q(start_date__lte=end_time)
    gradeClasses = GradeClass.objects.filter(query).order_by("school_time")

    temp = []

    query = Q(type=0)&Q(oriTime__gte=start_time)&Q(oriTime__lte=end_time)
    gcQuery = None
    i = 0
    for gc in gradeClasses:
        if i == 0:
            gcQuery = Q(gradeClass=gc.id)
        else:
            gcQuery = gcQuery|Q(gradeClass=gc.id)
        i = i + 1

    changeLessons = Lesson.objects.filter(query&(gcQuery))
    
    for gc in gradeClasses:

            changed = False
            changeLesson = None
            for cl in changeLessons:
                
                if str(cl.gradeClass.id) == str(gc.id):
                    changed= True
                    break
                
            if not changed:

                temp.append(gc)
                
            
    gradeClasses = temp
    
     # 试听课
    schedules = GradeClass.objects.filter(branch=branch).filter(gradeClass_type__ne=constant.GradeClassType.normal).filter(
            start_date__gte=start_time).filter(start_date__lte=end_time).filter(demoIsFinish__ne=-1)
        #补课
    extraLessons = Lesson.objects.filter(branch=branch).filter(type=2).filter(lessonTime__gte=start_time).filter(lessonTime__lte=end_time)
    
    temp = []
    
    
    for el in extraLessons:
            gc = GradeClass()
            gc.start_date = el.lessonTime
            gc.school_time = el.lessonTime.strftime("%H:%M")
            gc.teacher = el.teacher
            gc.classroom = el.classroom
            gc.id = el.gradeClass.id
            sts = []
            ststr = el.student.split(",")
            for s in ststr:
                try:
                    #st = Student.objects.get(id=s)
                    #sts.append(st)
                    sts.append(s)
                except:
                    st = None
            gc.students = sts
            gc.gradeClass_type = 3
            temp.append(gc)
    
    dayList = chain(gradeClasses, schedules,temp,changeToLessons)
    dayList = sorted(dayList, key=attrgetter("school_day"))
    dls = []
    dl = []
    for i in range(7):
        dl = []
        for d in dayList:
            if d.school_day == i+1:
                dl.append(d)
            elif d.gradeClass_type != 1 and getIntWeekDay(d.start_date.strftime("%a")) == i+1:
                #print d.school_time
                dl.append(d) 
        dl = sorted(dl, key=attrgetter("school_time"))
        dls.append(dl)
    
    
    for dayList in dls:
        day_list2 = []
        for r in rooms:
            
            if r == 'A':
                r = 10
            if r == 'B':
                r = 11
            if r == 'C':
                r = 12
            if r == 'D':
                r = 13
            if r == 'E':
                r = 14
            if r == 'F':
                r = 15
            
            room_clist = []
            lastTimeStr = '08:00'
            lastTime = datetime.datetime.strptime(lastTimeStr, '%H:%M')
            lastClass = 0
            ii = 0            
            for c in dayList:
                
                if c.classroom==r:
                    newTime = None
                    try:
                        c.school_time = c.school_time.replace(u"：",u":")
                        newTime = datetime.datetime.strptime(c.school_time, '%H:%M')
                    except Exception,e:
                        print e
                    timespace = timeDiff(newTime,lastTime)
                    lastTimeStr = c.school_time
                    lastTime = datetime.datetime.strptime(lastTimeStr, '%H:%M')
                    
                    if ii>0:
                        c.fromLast = (timespace - div_height)*div_ratio
                    else:
                        c.fromLast = timespace*div_ratio
                    timespace = timeDiff(datetime.datetime.strptime('21:00','%H:%M'),newTime)
                    c.toLast = (timespace - div_height)*div_ratio
                    room_clist.append(c)

                    ii = ii+1
    
            day_list2.append(room_clist)
        week_list.append(day_list2)
    return week_list


def schedule(request):
    millis0 = int(round(time.time() * 1000))
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    div_height = 90
    div_ratio = 0.5
    branch = request.GET.get("branch")
    if branch is None:
        branch = login_teacher.branch 
    try:
        b = Branch.objects.get(id=branch)
    except:
        b=Branch()
    firstDay_str = request.GET.get("firstDay")
    #firstDay_str = '20170325'
    firstDay = None
    lastDay = None
    if firstDay_str:
        try:
            firstDay = datetime.datetime.strptime(firstDay_str,"%Y-%m-%d")
            lastDay = firstDay + datetime.timedelta(days=7)
        except:
            firstDay = None
    #===========================================================================
    # if not firstDay:
    #     now = utils.now2datetime()
    #     now_day = now.isoweekday()  # 今天是本周第几天
    #     delte = 1 - now_day
    #     firstDay = now + datetime.timedelta(days=delte)  # 本周第一天
    #     lastDay = firstDay + datetime.timedelta(days=7)
    #===========================================================================
        
        
    firstDay,lastDay,lastWeekFirstDay,nextWeekFirstDay = utils.getWeekFirstDay(firstDay,True)
    
        
        
    #lastWeekFirstDay = firstDay + datetime.timedelta(days=-7)
    #nextWeekFirstDay = firstDay + datetime.timedelta(days=7) 
    #rooms = Classroom.objects.all().order_by("sn")
    rooms = []
    for i in range(1,b.branchRooms+1):
        if i<10:
            rooms.append(i)
        else:
            r = ''
            if i == 10:
                r = 'A' 
            if i == 11:
                r = 'B'
            if i == 12:
                r = 'C'
            if i == 13:
                r = 'D'
            if i == 14:
                r = 'E'
            if i == 15:
                r = 'F'
            rooms.append(r)
    day_list2 = []
    room_clist = []

    week_list = []

    begin_date = firstDay
    end_date = firstDay + datetime.timedelta(days=7)
    title = ''
    isThisWeek = False
    lastDay = lastDay.replace(hour=23)
    lastDay = lastDay.replace(minute=59)
    lastDay = lastDay.replace(second=59)
    lastDay = lastDay.replace(microsecond=999999)
    week_list = getWeekClasses(branch,firstDay,lastDay,rooms,div_height,div_ratio)
    
    if isThisWeek:
        title = u'本周'
    else:
        title = begin_date.strftime("%Y-%m-%d")+u'到'+lastDay.strftime("%Y-%m-%d")
    
    dates = {}
    dates['0'] = begin_date
    for i in range(7):
        begin_date = begin_date + timedelta(days=1)
        if i < 6:
            dates[str(i+1)] = begin_date

    response = render(request, 'schedule.html', {"title":title,
                                             "lastWeekFirstDay":lastWeekFirstDay,
                                             "nextWeekFirstDay":nextWeekFirstDay,
                                             "branch":b,
                                             "beginDate":begin_date,
                                             "rooms":rooms,
                                             "dates":dates,
                                             "login_teacher":login_teacher,
                                             "week_list": week_list})
    response.set_cookie("mainurl",'/go2/gradeClass/schedule')
    return response

def timeDiff(newTime,lastTime):
  try:
    ttt = str(newTime-lastTime)

    tlen = len(ttt)
    if tlen>8:
        ttt = ttt[tlen-8:tlen] 
      
    tt = ttt.split(":")
    timespace = 0
    iii = 1
    sp = 0
    for t in tt:
        if iii == 1:
            sp = int(float(t))*iii*60
        if iii == 0:
            sp = int(float(t))
        timespace = timespace + sp  
        sp = 0
        iii = iii -1
  except:
    timespace = 90
  return timespace

def edit_schedule(request, gradeClass_oid):
    return render(request, 'editGradeClass.html')

#打开班级的签到表页面
def lessons(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    mainurl = request.COOKIES.get('mainurl','')
    gc = None
    id = request.GET.get("id")
    if id:
        gc = GradeClass.objects.get(id=id)
    
    query1 = Q(gradeClass=id)&Q(type=1)&Q(checked=True)
    allNormalLessons = Lesson.objects.filter(query1).order_by("-lessonId")
    query0 = Q(gradeClass=id)&Q(type=0)
    allNormalLesson = Lesson.objects.filter(query0).order_by("-lessonId")
    map = {}
    classStudents = []
    for nls in allNormalLessons:
        if nls.student not in classStudents:
            classStudents.append(nls.student)

    css = {}
    for cs in classStudents:
        try:
            s = Student.objects.get(id=cs)
            css[cs] = s.name

        except:
            
            err = 1
    for nl in allNormalLesson:
        map[str(nl.id)] = ''
    
    for nls in allNormalLessons:
      try:
        if map[str(nls.lessonId)] == '':
            map[str(nls.lessonId)] = css[nls.student]
        else:    
            map[str(nls.lessonId)] = map[str(nls.lessonId)] + ',' + css[nls.student]
      except:
          err = 1
    query = Q(gradeClass=id)&(Q(type=0)|Q(type=2))
    lessons = Lesson.objects.filter(query).order_by("-lessonTime")
    temp = []
    for lesson in lessons:
      try:
        if lesson.type == 2:
            s = lesson.student.split(",")

            students = ''
            for st in s:
                if len(st) > 10:
                    students = students + " " + Student.objects.get(id=st).name
                

            lesson.student = students
        else:
            try:
            
                lesson.student = map[str(lesson.id)]
                
            except:
                err = 1
        temp.append(lesson)
      except Exception,e:
          print e

    lessons = temp

    return render(request, 'lessons.html',{"login_teacher":login_teacher,"gc":gc,"lessons":lessons,"mainurl":mainurl})

def studentLessons(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    lessons = None
    student = None
    sus = None
    id = request.GET.get("id")
    gradeClass = None
    query2 = None
    endDate = None
    
    if id:  
        city = None 
        try:
            city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
            print city.cityName
        except:
            city = None
        ct = None
        try:
            cts,a = dbsearch.getHolidayContractType(city)
            ct = cts[0]
        except:
            ct = None
         
        student = Student.objects.get(id=id)
        if student.status == 1:
        #if not student.contractDeadline:

            beginDate,endDate,days,learnDays = util2.getLessonCheckDeadline(id)
            
            endDate,learnDays = util2.getEndDateAddVocation(beginDate, endDate, login_teacher.cityId,learnDays)
            
            endDate,learnDays = util2.getEndDateAddSuspension(beginDate, endDate, id,learnDays)
            student.contractDeadline = endDate
            
            
            if student.gradeClass:
                try:
                    mygc = GradeClass.objects.get(id=student.gradeClass)
                    hasThis = False
                    if mygc and mygc.students:
                        for stu in mygc.students:
                            if str(stu.id) == str(student.id):
                                hasThis = True
                                break
                    if not hasThis:
                        student.gradeClass = None
                except:
                    student.gradeClass = None
                    
            student.lessonStartDate = beginDate
            
            

            
            student.save()
            #print student.gradeClass
        else:
            lasted = None
            for c in student.contract:
                endDate = c.endDate
                if not endDate:
                    break
                if not lasted:
                    lasted = endDate
                else:
                    if endDate > lasted:
                        lasted = endDate
            endDate = lasted
             #= student.contractDeadline
        sibling = None
        if student.siblingId:
            try:
               sibling = Student.objects.get(id=student.siblingId)
               contracts = Contract.objects.filter(student_oid=student.siblingId).filter(status__lt=2)
            except:
                contracts = None
        else:
            query = Q(siblingId=id)
            siblings = Student.objects.filter(query)
            if siblings and len(siblings)>0:
                query2 = Q(student=str(siblings[0].id))
                i = 0
                for sib in siblings:
                    if i > 0:
                         query2 = query2|Q(student=str(sib.id))
                query2 = (query2)&(Q(type=1)|Q(type=3))
                
            cquery = Q(student_oid=id)&Q(status__lt=2)
            
            if ct:
                cquery = cquery&Q(contractType__ne=ct)
            contracts = Contract.objects.filter(cquery)
            
        temp = []
        remove = False
        for c in contracts:
            if not c.weeks:
                if c.contractType and c.contractType.duration and c.contractType.duration > 0:
                    c.weeks = c.contractType.duration
                    temp.append(c)
                else:
                    remove = True
                    c.delete()
            else:
                temp.append(c)
        contracts = temp
        if remove:
            student.contract = contracts
            student.save()          
               
        query = Q(student=id)&(Q(type=1)|Q(type=3))&Q(checked=True)
        lessons = Lesson.objects.filter(query).order_by("-lessonTime")
        student.lessons = 0
        temp = []
        for lesson in lessons:
          try:
            gc = GradeClass.objects.get(id=lesson.gradeClass.id)
            temp.append(lesson)
            if lesson.value == 0:
                student.lessons = student.lessons
            else:
                if not lesson.value:
                    lesson.value = 1
                sll = student.lessons + lesson.value
                student.lessons = float(sll)
            student.save()
          except:
            err = 'class not exist' 
        lessons = temp
        
        allLessons,sd,lessonLeft = utils.getLessonLeft(student)
        try:
            gradeClass = GradeClass.objects.get(id=student.gradeClass)
        except:
            gradeClass = None
            student.gradeClass = None
            student.save()
        student.singDate = sd
        student.allLessons = allLessons
        student.lessonLeft = lessonLeft
        student.save()
        query = Q(student=id)
        sus = Suspension.objects.filter(query).order_by('-beginDate')  # @UndefinedVariable
    
        shouldLesson = 0
        if learnDays > 0:
            shouldLesson = learnDays / 7 + 1
        if shouldLesson > student.allLessons:
            shouldLesson = student.allLessons 
    return render(request, 'studentLessons.html',{"student":student,"login_teacher":login_teacher,
                                                  "contracts":contracts,
                                                  "gradeClass":gradeClass,
                                                  "lessons":lessons,"shouldLesson":shouldLesson,
                                                  "sus":sus,"endDate":endDate
                                                  })
#super user delete lessons
def delLessons(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.isSuper != '1':
        res = {"error": 1, "msg": "无权限"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    res = {"error": 0, "msg": "成功"}
    gcId = request.POST.get("gcId")
    sId = request.POST.get("sId")
    if gcId:
        gc = GradeClass.objects.get(id=gcId)
        if not gc:
            res = {"error": 1, "msg": "班级未找到"}
            return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    num = util3.delClassLessons(gcId, sId)
    res = {"error": 0, "msg": "成功删除"+str(num)}
             
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))


#进入上课签到页面，列出所有孩子
def signLesson(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    
    #EXPIRE_HOUR = 100000#168七天 #过期多久不能再修改签到
    lesson = None
    id = request.GET.get("id")
    lessonTimeStr = request.GET.get("lessonTime")
    lessonTime = datetime.datetime.strptime(lessonTimeStr,"%Y-%m-%d %H:%M")
    temp = []
    students = []
    if id:
        lesson = Lesson.objects.get(id=id)
        if constant.DEBUG and lesson.value:
            print '[lesson value]' + str(lesson.value)
        query = Q(gradeClass=lesson.gradeClass)&Q(lessonTime=lessonTime)
        if lesson.type is 2:
            s = lesson.student.split(",")
            for st in s:
              if len(st) > 10:
                oriLessons = []
                oridates = []
                student = Student.objects.get(id=st)
                for ol in lesson.oriLessons:
                    ols = ol.split("-")
                    if str(student.id) == ols[0]:
                        oriLesson = Lesson.objects.get(id=ols[1])

                        odate = oriLesson.lessonTime

                        oriLessons.append(odate)
                    if len(oriLessons) == 0:

                        ols = ol.split('_')
                        if str(student.id) == ols[0]:

                            for i in range(len(ols)-1):
                                i = i + 1

                                od = datetime.datetime.strptime(ols[i],"%Y-%m-%d")
                                oriLessons.append(od)
                            
                student.oriLessons = oriLessons
                students.append(student)
            query = query&Q(type=3)
        else:
            students = lesson.gradeClass.students
            query = query&Q(type=1)
           
        lessons = Lesson.objects.filter(query)
        for student in students:
                student.memo = None
                for l in lessons:
                    if str(student.id) == l.student:
                        student.checked = True
                        if l.memo:
                            start = l.memo.find(u'[表现]')
                            if start >-1:
                                student.memo = l.memo[start+4:len(l.memo)]
                            else:
                                student.memo = ''
                        else:
                            student.memo = None
                #if not student.checked:
                 #   student.memo = None        
                temp.append(student)
        students = temp
    teachers = Teacher.objects.filter(Q(branch=login_teacher.branch)&Q(status=0))
    expireTime = None
    if lesson and lesson.lessonTime:
        expireTime = utils.getThisMonthBegin(utils.monthLastDay(lesson.lessonTime)+datetime.timedelta(days=1))+timedelta(days=constant.SIGN_CLASS_EXPIRE_DAY)
        
    expired = False
    if expireTime < getDateNow():
        expired = True
    ######################
    expired = False     
    ######################
    return render(request, 'signLesson.html',{"lesson":lesson,
                                              "students":students,
                                              "expired":expired,
                                              "teachers":teachers})
#生成下节课的签到表
@csrf_exempt
def makePassLessons(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    res = {"error": 0, "msg": "成功"}
    classId = request.POST.get("id")
    gc = GradeClass.objects.get(id=classId)
    if not gc:
        res = {"error": 1, "msg": "班级未找到"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    classDate = gc.start_date
    datestr = classDate.strftime("%Y-%m-%d")
    datenowStr = getDateNow().strftime("%Y-%m-%d")
    if datestr > datenowStr:
        res = {"error": 1, "msg": "还没到开班日！"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    
    data.makeLessons(gc)
             
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

#签到
@csrf_exempt
def checkin(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    id = request.POST.get("id")
    type = request.POST.get("type")
    teacherId = request.POST.get("teacher")
    students = request.POST.get("students")
    memos = request.POST.get("memos")
    lessonMemo = request.POST.get("memo")
    valueStr = request.POST.get("value")
    lessonTimeStr = request.POST.get("lessonTime")
    type0 = 0
    type1 = 1
    value = 1
    beginDate = None
    endDate = None
    try:
        value = float(valueStr)
    except:
        value = 1
    try:
        type0 = int(type)
    except:
        type0 = 0
    if type0 == 0:
        type1 = 1
    elif type0 == 2:
        type1 = 3
    lesson = Lesson.objects.get(id=id)

    if not lesson:
        res = {"error": 1, "msg": "班级未找到"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
        
    teacher = Teacher.objects.get(id=teacherId)
    lessonTime = datetime.datetime.strptime(lessonTimeStr,"%Y-%m-%d %H:%M")

    list = students.split('|')
    try:
        if len(list[0]) == 0:
            list = []
    except:
        list = []
    temp = []
    errs = []

    memoList = memos.split('|')
    temp2 = []
    i=0
    if value > 0:    #收费课要验证是否在有效期内，否则不能签到
      try:
        for studentId in list:
            
            beginDate,endDate,days,learnDays = util2.getLessonCheckDeadline(studentId)
            endDate,learnDays = util2.getEndDateAddVocation(beginDate, endDate, login_teacher.cityId,learnDays)
            endDate,learnDays = util2.getEndDateAddSuspension(beginDate, endDate, studentId,learnDays)
            stu = None
            try:
                stu = Student.objects.get(id=studentId)  
                if stu.contractDeadline != endDate:
                    stu.contractDeadline = endDate 
                    stu.save()
            except:
                err = 1
            if lessonTime > endDate:
                if stu:
                    errs.append(stu)
            else:
                temp.append(studentId)
                for m in memoList:
                    if studentId == m.split("_")[0]:
                        temp2.append(m)
                        
            i = i + 1
        list = temp
        memoList = temp2
      except Exception,e:
          print e
    lesson.lessonTime = lessonTime
    lesson.teacher = teacher
    gc = lesson.gradeClass
    
    if list and len(list)>0: #签到学生列表不为空
        saveLesson(gc,lessonTime,type0,teacher,lesson.id,None,True,value,None,lessonMemo)
        #班级签到，签到表上此次课已上
        less = Lesson.objects.filter(lessonId=id).filter(type=type1)
        for l in less:
            l.delete()
    else:
        less = Lesson.objects.filter(lessonId=id).filter(type=type1)
        for l in less:
            l.delete()
    
        lesson.checked = False
        lesson.save() #没有上课人，状态改为未签到，可以删除
        #saveLesson(gc,lessonTime,0,teacher,lesson.id,None,False,value,None,lessonMemo)
    
    
    if list and len(list)>0: #签到学生列表不为空
        lessons = []
        values = []
        for id in list:
            index = 0
            l = Lesson(id=id)
            oriLessons = []
            for memo in memoList:
            
                lid = memo[0:memo.find('_')]
     
                if id == lid:
                    mm = memo[memo.find('_')+1:len(memo)]
                    if len(mm)>0:
                        mm = u'[表现]'+mm                
                    l.memo = u'[上课]'+lessonMemo+mm
                    break 
            for ol in lesson.oriLessons:
                ids = ol.split('-')
                if ids[0] == str(l.id):
                    oriLessons.append(ids[1])
            l.oriLessons = oriLessons
            if l not in lessons:
                for id2 in list:
                    if id == id2:
                        index = index +1
                lessons.append(l)
                v = index * value
                values.append(v)
       
        i = 0
        for l in lessons:
            sid = str(l.id)
            m = l.memo
            saveLesson(gc,lessonTime,type1,teacher,lesson.id,sid,True,values[i],None,m,l.oriLessons)
            i = i+1

    try:
        #不管是否有上课人，都重新计算消课数
        for s in gc.students:
            allLessons,sd,lessonLeft = utils.getLessonLeft(s)
        if list and len(list)>0: #有学生上课
            
         
                #===============================================================
                # s.lessons = allLessons - lessonLeft
                # s.lessonLeft = lessonLeft
                # s.save()
                #===============================================================
            res = {"error": 0, "msg": "签到成功"}
        else:
            res = {"error": 0, "msg": "取消签到成功"}
        print 'LESSONCHECK HAS OR NOT?---0'
        year = lessonTime.strftime("%Y")
        month = lessonTime.strftime("%m")
        query = Q(year=year)&Q(month=month)&Q(branchId=str(teacher.branch.id))
        lc = None
        lcs = LessonCheck.objects.filter(query).order_by("-updateTime")  # @UndefinedVariable
        print 'LESSONCHECK HAS OR NOT?'
        print len(lcs)
        print lcs._query
        if len(lcs) > 0:
            lc = lcs[0]
            lc.updateCheckinTime = utils.getDateNow(8)
            lc.save()     
        
        if errs and len(errs)>0:
            msg = ''
            for e in errs:
                m = ''
                if e.name:
                    m = e.name
                if e.name2:
                    m = m + e.name2
                m = '['+m+']'
                msg = msg + m
            res = {"error": 0, "msg": msg + u'合同已到期不能再签到'}
    except Exception,e:
        print e 
  
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))




def studentDemo(request,student_oid):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    demo = None
    student = None
    demos = []
    studentBranch = None
    #student_oid = request.GET.get("student_oid")
    if True:
        student = Student.objects.get(id=student_oid)
        if student:
            if not student.branch:
                res = {"error": 1, "msg": "请先分配校区再预约试听课！"}
                return http.JSONResponse(json.dumps(res, ensure_ascii=False))
            studentBranch = student.branch.id
            demoIds = student.demo
            for demo_oid in demoIds:
                try:
                    demo = GradeClass.objects.get(id=demo_oid)
                except:
                    demo = None
                if demo:
                    demos.append(demo)
    query = Q(students__contains=student.id)&Q(gradeClass_type=2)   
    demos = GradeClass.objects.filter(query)   
    ts = Teacher.objects.filter(Q(branch=studentBranch)&Q(status=0))
    teachers = []
    for t in ts:
        teachers.append(t)
    for d in demos:
        t = d.teacher
        if t not in teachers:
            teachers.append(t)
    classrooms = []
    branch = Branch.objects.get(id=studentBranch)
    for i in range(1,branch.branchRooms+1):
        classrooms.append(i)
    datenow = utils.getDateNow(8)
    return render(request, 'studentDemo.html', {"login_teacher":login_teacher,
                                                "student": student,
                                                "demos":demos,"datenow":datenow,
                                                "classrooms":classrooms,
                                                "teachers":teachers})
@csrf_exempt
def api_save_demo(request):
    
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    mainurl = request.COOKIES.get('mainurl','')
    studentId = request.POST.get("student_oid")
    isDemo = request.POST.get("isDemo")
    demo_oid = request.POST.get("demo_oid")
    student = None
    try:
        student = Student.objects.get(id=studentId)
    except:
        res = {"error": 1, "msg": "孩子未找到！"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False)) 
    
    branch = student.branch
    branchid = branch.id
    
    demo_info = request.POST.get("demo_info")
    teacher = request.POST.get("teacher")
    classroom = request.POST.get("classroom")
    strStart_date = request.POST.get("start_date")
    start_date = datetime.datetime.strptime(strStart_date,'%Y-%m-%d')
    strSchool_time = request.POST.get("school_time")
    try:
        st = datetime.datetime.strptime(strSchool_time, "%H:%M")
    
    except:
        res = {"error": 1, "msg": "["+strSchool_time+"]时间格式错误！"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))    

    if isDemo:
        isDemo = 1
    demo = None
    try:
        demo = GradeClass.objects.get(id=demo_oid) #demo exist
    except:#not exist
        demo = GradeClass()
        isNew = True
        ss = []
        ss.append(student)
        demo.students = ss
    demo.classType = 2
    teacherObj = None
    try:
        teacherObj = Teacher.objects.get(id=teacher)
    
    except:
        teacherObj = None            
    if not student.teacher:
        student.teacher = teacherObj    
     
    query = Q(start_date=start_date)&Q(students=student.id)&Q(gradeClass_type=2)
    existDemos = GradeClass.objects.filter(query) 
    for d in existDemos:
        if d.id != demo.id:
            d.delete()
           
    demo.info = demo_info
    demo.demoIsFinish = isDemo
    demo.start_date = start_date
    demo.classroom = int(float(classroom))
    demo.teacher = teacherObj
    demo.school_time = strSchool_time
    demo.gradeClass_type = 2
    demo.branch = branch
    
    demo.save()
    
    query = Q(start_date=start_date)&Q(students=student.id)&Q(gradeClass_type=2)
    existDemos = GradeClass.objects.filter(query).order_by("-start_date")
    demos = []
    isSet = 0
    for d in existDemos:
        if d:
            demos.append(str(d.id))
            if isSet == 0 and d.demoIsFinish != -1:
                student.isDemo = d.demoIsFinish
                isSet = 1

    try:    
        student.demo = demos
        student.save()
    except Exception,e:
        print e
    res = {"error": 0, "msg": "保存成功","url":mainurl}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def saveLessonContent(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    lessonId = request.POST.get("lessonId")
    teacher = request.POST.get("teacher")
    lessonTime = request.POST.get("lessonTime")
    value = request.POST.get("value")
    memo = request.POST.get("memo")
    v = 1.0
    
    try:
        lesson = Lesson.objects.get(id=lessonId)
    except:
        res = {"error": 1, "msg": "课程不存在"}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    try:
        v = round(float(value),1)
    except:
        v = 1.0
    lesson.memo = memo
    lesson.value = v
    try:
        lesson.teacher = Teacher.objects.get(id=teacher)
    except:
        err = 1
    try:
        lesson.lessonTime = datetime.datetime.strptime(lessonTime,"%Y-%m-%d %H:%M")
    except:
        err = 1
    lesson.save()
    res = {"error": 0, "msg": "保存课程内容成功"}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

@csrf_exempt
def api_changeLesson(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    classId = request.POST.get("classId")
    classRoomStr = request.POST.get("classRoom")
    teacher = request.POST.get("teacher")
    time0 = request.POST.get("oriTime")
    time1 = request.POST.get("lessonTime")
    
    oriTime = datetime.datetime.strptime(time0,'%Y-%m-%d %H:%M')
    query = Q(gradeClass=classId)&Q(oriTime=oriTime)&Q(type=0)
    lessons = Lesson.objects.filter(query)
    for l in lessons:
        l.delete()
    
    
    lessonTime = None
    try:
        lessonTime = datetime.datetime.strptime(time1,"%Y-%m-%d %H:%M")
    except:
        lessonTime = None
    gc = None
    try:
        gc = GradeClass.objects.get(id=classId)
    except:
        gc = None
    if gc:
        try:
            classRoom = int(classRoomStr)
        except:
            classRoom = gc.classroom
    if not teacher:
        teacher = gc.teacher
    
    query = Q(gradeClass=classId)&Q(lessonTime=lessonTime)&Q(type=0)
    lessons = Lesson.objects.filter(query)
    lesson = Lesson()
    if lessons and len(lessons)>0:
        lesson = lessons[0]
    else:
        query = Q(gradeClass=classId)&Q(lessonTime=oriTime)&Q(type=0)
        lessons = Lesson.objects.filter(query)
        if lessons and len(lessons)>0:
            lesson = lessons[0]

    lesson.lessonTime = lessonTime
    lesson.oriTime = oriTime
    lesson.branch = login_teacher.branch
    lesson.teacher = teacher
    lesson.classroom = classRoom
    lesson.type = 0
    lesson.gradeClass = gc
    lesson.save()
    res = {"error": 0, "msg": "修改上课时间成功"}

    return http.JSONResponse(json.dumps(res, ensure_ascii=False))

def changeLesson(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    classId = request.GET.get("classId")
    beginDateStr = request.GET.get("beginDate")
    gc = GradeClass.objects.get(id=classId)
    beginDate = datetime.datetime.strptime(beginDateStr,"%Y-%m-%d")
    oriTime = beginDate+timedelta(days=gc.school_day-1)
    
    oriTime = datetime.datetime.strptime(oriTime.strftime("%Y-%m-%d ")+gc.school_time,"%Y-%m-%d %H:%M")
    
    return render(request, 'changeLesson.html', {"gc": gc,
                                                 "classId":classId,
                                                "oriTime":oriTime,
                                                "login_teacher":login_teacher})
@csrf_exempt
def api_removeLesson(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    id = request.POST.get("id")
    res = None
    try:
        lesson = Lesson.objects.get(id=id)
        canDelete = True
        query = Q(lessonId=id)|Q(oriLessons=id)
        if lesson.checked == True:
            canDelete = False
            res = {"error": 1, "msg": "已签到，不能删除"}
        lesson.delete()
        res = {"error": 0, "msg": "删除成功"}
    except:
        res = {"error": 1, "msg": "未找到"}
    
    return http.JSONResponse(json.dumps(res, ensure_ascii=False))