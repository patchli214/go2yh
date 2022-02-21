#!/usr/bin/env python
# -*- coding:utf-8 -*-
#from numpy import False_
from contract.models import Income, Y19Income
from django.template.defaulttags import now
from webpage.models import Webpage
import os
__author__ = 'patch'

from student.models import Suspension
from tools.constant import GradeClassType
from tools.templatetags.filter_gradeClass import get_gradeClass_type
import time
from bson.objectid import ObjectId
from go2.settings import BASE_DIR
import datetime
from tools import constant,utils,http, util3
from regUser.models import *
from gradeClass.models import *
from student.models import Suspension
from branch.models import Vocation
import jpush,urllib,sys

#获取校区全部收入
def getBranchRevenue(branchId,bDate,eDate):
    #合同收入
    sum = getBranchContractIncome(branchId, bDate, eDate)
    sum = sum + getBranchOtherIncome(branchId, bDate, eDate)
    
    return sum

#其他收入
def getBranchOtherIncome(branchId,bDate,eDate):
    query = Q(branchId=str(branchId))&Q(payDate__gte=bDate)&Q(payDate__lt=eDate)&Q(status__ne=constant.ContractStatus.delete)
    query = query&Q(type__ne=constant.IncomeType.outLevel)
    cs = Income.objects.filter(query)  # @UndefinedVariable
    paid = 0
    for c in cs:
        if c.paid != None:
            paid = paid + c.paid
    return paid        
 
#网课收入
def getOnlineRevenue(bDate,eDate):
    query = Q(type=constant.ContractType.onlineCourse)
    cts = ContractType.objects.filter(query)
    query = None
    i = 0
    for ct in cts:
        if i == 0:
            query = Q(contractType=ct.id)
        else:
            query = query|Q(contractType=ct.id)
        i = i + 1
    query = (query)&Q(paid__gt=0)&Q(singDate__gte=bDate)&Q(singDate__lt=eDate)&Q(status__ne=constant.ContractStatus.delete)
    cs = Contract.objects.filter(query)
    return cs 

    #合同收入 
def getBranchContractIncome(branchId,bDate,eDate):
    query = Q(branch=branchId)&Q(singDate__gte=bDate)&Q(singDate__lt=eDate)&Q(status__ne=constant.ContractStatus.delete)
    cs = Contract.objects.filter(query).order_by('singDate')
    if str(branchId) == '5867c3883010a518ac189d41':
        print cs._query
    paid = 0
    for c in cs:
        if c.contractType.type == constant.ContractType.onlineCourse:
            continue
        if c.paid != None:
            paid = paid + c.paid
        elif c.contractType and c.contractType.fee and c.contractType.fee > 0:
            paid = paid + c.contractType.fee
   
    return paid

def getBranchRefund(branchId,bDate,eDate):
    query = Q(branch=branchId)&Q(endDate__gte=bDate)&Q(endDate__lt=eDate)&Q(status=constant.ContractStatus.refund)
    cs = Contract.objects.filter(query)
    paid = 0
    for c in cs:
        if c.refund != None:
            paid = paid + c.refund
        elif c.paid and c.paid > 0:
            paid = paid + c.paid
    return paid
    
def getVocations(cityId):
    now = utils.getDateNow()
    query = Q(city=cityId)
    vocations = Vocation.objects.filter(query).order_by("-beginDate")  # @UndefinedVariable
    return vocations

def getSuspensions(studentId):
    now = utils.getDateNow()
    query = Q(student=studentId)
    sus = Suspension.objects.filter(query).order_by("-beginDate")  # @UndefinedVariable
    return sus

def getLessonCheckDeadline(studentId):
    endDate = utils.getDateNow()
    beginDate = None
    days = 0
    query = Q(student_oid=studentId)&Q(status=constant.ContractStatus.sign)
    contracts = Contract.objects.filter(query).order_by("beginDate")

    if len(contracts) == 0:
        try:
            student = Student.objects.get(id=studentId)
            if student and student.siblingId:

                student = Student.objects.get(id=student.siblingId)
                studentId = str(student.id)
                query = Q(student_oid=studentId)&Q(status=constant.ContractStatus.sign)
                contracts = Contract.objects.filter(query).order_by("beginDate")
     
        except:
            err = 1
    if contracts and len(contracts) > 0:
        if contracts and len(contracts)>0:
            beginDate = contracts[0].beginDate
            if not beginDate:
                beginDate = contracts[0].singDate
            if not beginDate:
                beginDate = endDate
            weeks = 0
            days = 0
            for c in contracts:
                cweeks = 0
                try:
                    cweeks = c.weeks
                    if not c.weeks:
                        cweeks = c.contractType.duration
                    
                except:
                    cweeks = 0
                weeks = cweeks + weeks
            days = (weeks - 1) * 7 + constant.END_DATE_EXTEND

            endDate = beginDate + datetime.timedelta(days=days)
    learnDays = 0
    try:
        learnDays = (utils.getDateNow(8) - beginDate).days
        if learnDays < 0:
            learnDays = 0
    except:
        learnDays = 0
    
    return beginDate,endDate,days,learnDays

def getEndDateAddVocation(beginDate,endDate,cityId,learnDays=0): 
    datenow = utils.getDateNow(8)
    if not beginDate:
        print '[no beginDate]'

        return endDate
    if not endDate:
        print '[no endDate]'

        return endDate
    vocations = getVocations(cityId)
    days = 0
    interval = None
    for v in vocations:
        if v.beginDate > endDate or beginDate > v.endDate: 
            doNothing = True
        else:
            if beginDate <= v.beginDate and endDate >= v.endDate:
                interval = v.endDate - v.beginDate
            elif beginDate > v.beginDate and endDate >= v.endDate:
                interval = v.endDate - beginDate
            elif beginDate <= v.beginDate and endDate < v.endDate:
                interval = endDate - v.beginDate
            days = days + interval.days
        
        if v.beginDate > datenow or beginDate > v.endDate: 
            doNothing = True
        else:
            if beginDate <= v.beginDate and datenow >= v.endDate:
                interval = v.endDate - v.beginDate
            elif beginDate > v.beginDate and datenow >= v.endDate:
                interval = v.endDate - beginDate
            elif beginDate <= v.beginDate and datenow < v.endDate:
                interval = endDate - v.beginDate
            learnDays = learnDays - interval.days 
            
    if days < 0:
        days = 0
    
    endDate = endDate + datetime.timedelta(days=days)
    return endDate,learnDays

def getEndDateAddSuspension(beginDate,endDate,studentId,learnDays=0):
    datenow = utils.getDateNow(8)
    sus = getSuspensions(studentId)
    interval = None
    days = 0

    for v in sus:

        if v.beginDate > endDate or beginDate > v.endDate: 
            doNothing = True

        else:
            if beginDate <= v.beginDate and endDate >= v.endDate:
                interval = v.endDate - v.beginDate
            elif beginDate > v.beginDate and endDate >= v.endDate:
                interval = v.endDate - beginDate
            elif beginDate <= v.beginDate and endDate < v.endDate:
                interval = v.endDate - v.beginDate
            days = days + interval.days
            
        if v.beginDate > datenow or beginDate > v.endDate: 
            doNothing = True
        else:
            if beginDate <= v.beginDate and datenow >= v.endDate:
                interval = v.endDate - v.beginDate
            elif beginDate > v.beginDate and datenow >= v.endDate:
                interval = v.endDate - beginDate
            elif beginDate <= v.beginDate and datenow < v.endDate:
                interval = endDate - v.beginDate
            learnDays = learnDays - interval.days 

    if days < 0:
        days = 0
    endDate = endDate + datetime.timedelta(days=days) 
    return endDate,learnDays

def getBranch(branchId):
    branch = None
    try:
        branch = Branch.objects.get(id=branchId)
    except:
        branch = None
    return branch

def canSign(studentId,mobile):
    can = False
    contracts = []
    has = False
    allFinish = True
    now = utils.getDateNow()
    query = (Q(prt1mobile=mobile)|Q(prt2mobile=mobile))&Q(id__ne=studentId)
    students = Student.objects.filter(query)
    query = Q(type=constant.ContractType.hc)
    excludeCTs = ContractType.objects.filter(query)
    queryCT = Q(contractType__ne=excludeCTs[0])
    if students and len(students)>0:
        for s in students:
            queryStudent = Q(student_oid=str(s.id))
            query = (queryStudent)&queryCT
            cs = Contract.objects.filter(query)
            for c in cs:
                if c.contractType.type == constant.ContractType.normal:
                    has = True
                if c.status == constant.ContractStatus.sign:
                    allFinish = False
                if c.contractType.type == constant.ContractType.normal and c.status == constant.ContractStatus.sign:
                    contracts.append(c)
                
    if has and allFinish:
        can = True
    if not has:
        can = True
    return can,contracts

def sendPush(msg,ids=None):
    app_key = '0bacefa3cef6051e5a87551d'
    master_secret = 'f127e0e5136b9a717fc0237f'
    _jpush = jpush.JPush(app_key, master_secret)
    push = _jpush.create_push()
# if you set the logging level to "DEBUG",it will show the debug logging.
    _jpush.set_logging("DEBUG")
    if not ids:
        push.audience = jpush.all_
    else:
        push.audience = jpush.audience(jpush.registration_id(ids))
    push.notification = jpush.notification(alert=msg)
    push.platform = jpush.all_
    try:
        response=push.send()
    except common.Unauthorized:
        raise common.Unauthorized("Unauthorized")
    except common.APIConnectionException:
        raise common.APIConnectionException("conn error")
    except common.JPushFailure:
        print ("JPushFailure")
    except:
        print ("Exception")

def pushTest():
        
        openId = '123'
        first = u'上海'
        keyword2 = u'甜馨巧'
        keyword3 = '13500001112'
        keyword4 = '2017-11-15 15:34:32'
        keyword5 = u'槐房万达校区'
        wrongMess = first + '|' + keyword2 + '|' + keyword3 + '|' + keyword4 + '|' + keyword5
        #=======================================================================
        url = u'http://www.go2crm.cn/go2/teacher/api_push?mess='
        mess = urllib.quote(wrongMess.encode('utf8'), ':/')
        url = url + mess   
        print url
        req2 = urllib.urlopen(url)
        rest2 = req2.read()
        print rest2
        
def job_fixStudentLessons():
    query = Q(status=1)&(Q(lessons=None)|Q(lessons=0))&(Q(lessonLeft=0)|Q(lessonLeft=None))&Q(contract__ne=None)&Q(siblingId=None)
    students = Student.objects.filter(query)
    print len(students)
    i = 0
    for student in students:
        if student.contract and len(student.contract) > 0:
            i = i + 1
            allLessons,sd,lessonLeft = utils.getLessonLeft(student)
            student.lessons = allLessons - lessonLeft
            student.lessonLeft = lessonLeft
            student.save()
    print '[DONE]' + str(i)

def job_dupResolvedChange():
    dups = Student.objects.filter(resolved=-1)
    i = 0
    print len(dups)
    for s in dups:
        q1 = None
        q2 = None
        query = None
        if s.prt1mobile and len(s.prt1mobile) > 0:
            q1 = (Q(prt1mobile=s.prt1mobile)|Q(prt2mobile=s.prt1mobile))
        if s.prt2mobile and len(s.prt2mobile) > 0:
            q2 = (Q(prt1mobile=s.prt2mobile)|Q(prt2mobile=s.prt2mobile))
        if q1 and not q2:
            query = q1
        if q2 and not q1:
            query = q2
        if q1 and q2:
            query = q1|q2
        if query:
            query = Q(id__ne=s.id)&(query)
        oppos = Student.objects.filter(query)

        if oppos and len(oppos)>0:
            for o in oppos:
                if o.resolved != -1:
                    o.resolved = -1
                    o.save()
                    i = i + 1
    print i

def job_fixBranchStudentLessons(branchCode):
    branch = Branch.objects.get(branchCode=branchCode)
    
    query=Q(branch=branch.id)&Q(deleted=1)
    deletedClasses = GradeClass.objects.filter(query)
    i = 0
    j = 0
    for gc in deletedClasses:
        query = Q(gradeClass=gc.id)
        lessons = Lesson.objects.filter(query)
        
        for l in lessons:
            l.delete()
            i = i + 1
        
        gc.delete()
        j = j + 1
    query = Q(branch=branch.id)&Q(status=1)
    ss = Student.objects.filter(query)
    k = 0
    for s in ss:
        try:
            gc = GradeClass.objects.get(s.gradeClass)
        except:
            s.gradeClass = None
            s.save()
            k = k + 1
            
    print '[remove]'+str(i)+' lessons, '+str(j)+' classes, '+str(k)+' studentsClass'
    query = Q(status=1)&Q(contract__ne=None)&Q(branch=branch.id)
    students = Student.objects.filter(query)
    print '[student no]'+str(len(students))
    i = 0
    for student in students:
        if student.contract and len(student.contract) > 0:
            i = i + 1
            allLessons,sd,lessonLeft = utils.getLessonLeft(student)

    print '[DONE]' + str(i)
    
def job_fixRefundStudent():
    i = 0
    query = Q(status=constant.ContractStatus.refund)
    contracts = Contract.objects.filter(query)
    for c in contracts:
        student = None
        try:
            student = Student.objects.get(id=c.student_oid)
        except:
            student = None
        if student:
            query = Q(student_oid=student.id)&Q(status=constant.ContractStatus.sign)
            validContracts = Contract.objects.filter(query)  # @UndefinedVariable
            if validContracts and len(validContracts) > 0:
                donothing = 1
            elif student.status != constant.StudentStatus.refund:
                student.status = constant.StudentStatus.refund
                student.save()
                i = i + 1
    print i

def job_remind():
    print '[remind]' 
    reminds = TeacherRemind.objects.all().order_by('student')
    lastStudent = None
    dup = 0
    i = 0
    real = 0
    lastR = None
    for r in reminds:
        i = i + 1
        try:

            s = Student.objects.get(id=r.student.id)  # @UndefinedVariable
            real = real + 1
            if r.student == lastStudent:
                dup = dup + 1
                if r.remindTime > lastR.remindTime:
                    lastR.delete()
                else:
                    r.delete()
            else:
                lastStudent = r.student
                lastR = r
        except Exception,e:
            print e
            r.delete()
            
        
    print '[all]'+str(i)
    print '[real]'+str(real)
    print '[dup]'+str(dup)    

def job_remindToStudent():
    print '[remind to student]' 
    reminds = TeacherRemind.objects.all().order_by('remindTime')
    i = 0
    j = 0
    for r in reminds:
        try:
            r.student.remind_txt = r.remind_txt
            r.student.remindTime = r.remindTime
            r.student.isDone = r.isDone
            r.student.remindTeacher = r.remindTeachers[0]
            r.student.save()
            i = i + 1
        except:
            j = j + 1
    print i
    print j

def job_trackToStudent():
    print 'track'
    query = Q(branch=None)&Q(regBranch__ne=None)
    students = Student.objects.filter(query).order_by("id")
    i = 1
    j = 0
    index = 0
    try:
      #=========================================================================
      # for s in students:
      #   if utils.addTrackToStudent(s):
      #       i = i + 1
      #   if i%100 == 0:
      #       j = j + 1
      #       print j
      #   index = index + 1
      #=========================================================================
      branches = Branch.objects.all()
      for b in branches:
          query = Q(branch=b.id)
          students = Student.objects.filter(query).order_by("id")
          for s in students:
              if utils.addTrackToStudent(s):
                  i = i + 1
                  if i%100 == 0:
                      j = j + 1
                      print j
              index = index + 1
    except Exception,e:
        print e
        
    print '[deal]'+str(i)
    print '[all]'+str(index)
        
def job_ownBranchDup():
    branches = Branch.objects.all()
    for b in branches:
        print b.branchCode
        tels = []
        query = Q(regBranch=b.id)&Q(prt1mobile__ne=None)
        students = Student.objects.filter(query).order_by("prt1mobile")
        for s in students:
            if s.prt1mobile not in tels:
                tels.append(s.prt1mobile)
                if s.prt2mobile and len(s.prt2mobile) > 6:
                    if s.prt2mobile not in tels:
                        tels.append(s.prt2mobile)
                    else:
                        print s.prt2mobile
            else:
                print s.prt1mobile         

def job_checkin_removeDup(branchId):
    try:
        branch = Branch.objects.get(id=branchId)
        query = Q(type=1)&Q(checked=True)&Q(student__ne=None)&Q(lessonTime__ne=None)
        lessons = Lesson.objects.filter(query).order_by('student','lessonTime')
        lastStudent = None
        lastTime = None
        lastId = None
        i = 0
        for l in lessons:
            if i < 10:

                if l.lessonTime and l.student:
                    print l.student + '||' + l.lessonTime.strftime("%Y%m%d %H%M")
            
            i = i + 1
            
            if l.student != 'checkall' and l.student == lastStudent and l.lessonTime == lastTime:
                try:
                    last = Lesson.objects.get(id=lastId)
                    if l.gradeClass and l.gradeClass.deleted == 1:
                        
                        s = Student.objects.get(id=l.student)
                        #print '0--' + str(l.gradeClass.id) + '|' + s.branchName + '|' + s.name + '||' + l.lessonTime.strftime("%Y%m%d")
                        l.delete() 
                    elif last and last.gradeClass and last.gradeClass.deleted == 1:
                        s = Student.objects.get(id=last.student)
                        #print '1--' + str(last.gradeClass.id) + '|' + s.branchName + '|' + s.name + '||' + last.lessonTime.strftime("%Y%m%d")
                        last.delete()
                except:
                    err = 1
            if l.student != lastStudent:
                lastStudent = l.student
            if l.lessonTime != lastTime:
                lastTime = l.lessonTime 
            if lastId != l.id:
                lastId = l.id
    except Exception,e:
        print e    

    return

def job_addContractDeadline():
    query = Q(status=1)
    students = Student.objects.filter(query)
    i = 0
    for s in students:
        days = 0
        endDate = None
        deadline = None
        if s.contract and len(s.contract) > 0:
            beginDate,endDate,days,learnDays = getLessonCheckDeadline(str(s.id))
            deadline = getEndDateAddVocation(beginDate, endDate, s.branch.city.id,learnDays)
            deadline = getEndDateAddSuspension(beginDate, deadline, str(s.id),learnDays)
            s.contractDeadline = deadline
            s.save()  
        i = i + 1 
        if i%100 == 0:
            print i 
            print s.id
            print days
            print endDate
            print deadline
    print '[DONE]' + str(i)
    return

def job_addRegBranchToRemind():
    reminds = TeacherRemind.objects.all()
    i = 0
    j = 0
    for r in reminds:
        try:
            r.regBranch = str(r.student.regBranch.id)
            if r.regBranch:
                r.save()
                i = i + 1
        except Exception,e:
            print e
            r.delete()
            
            j = j + 1
        k = i%500 
        if k == 0:
            print i 
    print i
    print j
    
def del_contracts(branch_oid):
    query = Q(branch=branch_oid)&(Q(singDate=None)|Q(beginDate=None)|Q(paid=None))
    contracts = Contract.objects.filter(query)
    print len(contracts)
    for c in contracts:
        try:
            s = Student.object.get(id=c.student_oid)
            s.status = 0
            s.contract = []
            s.save()
        except:
            err = 1
        c.delete()
        if c.student_oid == '5a17c8c497a75df575ce720e':
            print '[[[[[--------------------------------------------------------------REMOVE CONTRACT!!!!'
    
    
    print '[del contract done]'
    query = Q(branch=branch_oid)&Q(status=constant.StudentStatus.sign)
    students = Student.objects.filter(query)
    i = 0
    for s in students:
        cs = []
        if s.contract and len(s.contract) > 0:
            for c in s.contract:
                try:
                    contract = Contract.objects.get(id=c.id)
                    if contract.paid and contract.status == constant.ContractStatus.sign:
                        cs.append(contract)
                except:
                    err = 1
                    
            if len(cs) > 0:
                s.contract = cs
            else:
                s.contract = cs
                s.status = 0
                i = i + 1
        else:
            s.status = 0
            i = i + 1
            
        s.save()
    print '[delete student]' + str(i)       

def del_classes(branch_oid):
    query = Q(branch=branch_oid)&Q(gradeClass_type=1)
    gcs = GradeClass.objects.filter(query)
    i = 0 #改变状态的学生数
    j = 0 #删除班级数
    for g in gcs:
        
        students = []
        hasContract = False
        for s in g.students:
            try:
                sss = Student.objects.get(id=s.id)
            except:
                continue
            sibling = None
            try:
                sibling = Student.objects.get(id=s.siblingId)
            except:
                sibling = None
            try:
                sc = s.contract
            except:
                sc = None
            if sc:
              if s.contract and len(s.contract) > 0:
                hasContract = True
                students.append(s)
              elif sibling and sibling.contract and len(sibling.contract) > 0: #共用学籍
                hasContract = True
                students.append(s)
            if not hasContract:
                s.status = constant.StudentStatus.finish
                i = i + 1
                s.save()

        if hasContract:
            g.students = students
            g.save()
        else:
            j = j + 1
            try:
                g.delete()
            except Exception,e:
                print e
    print 'student change to finish:' + str(i)
    print 'total del class:'+str(j)

def deleteStudentAllData(students):
    for s in students:
        query = Q(prt1mobile=s.prt1mobile)&Q(branchName=s.branchName)
        try:
            student = Student.objects.get(query)
            query = Q(student=str(student.id))
            lessons = Lesson.objects.filter(query)
            i = 0
            for l in lessons:
                l.delete()
                i = i + 1
            print '[del lessons]'+str(i)
            query = Q(students=student.id)
            gcs = GradeClass.objects.filter(query)
            i = 0
            for gc in gcs:
                temp = []
                for st in gc.students:
                    if st.id != student.id:
                        temp.append(st)
                if len(temp) == 0:
                    gc.delete()
                    i = i + 1
                else:
                    gc.students = temp
                    gc.save()
                    i = i + 1
            print '[del gc]'+str(i)
            query = Q(student_oid=str(student.id))
            contracts = Contract.objects.filter(query)
            i = 0
            for c in contracts:
                c.delete()
                i = i + 1
            print '[del contracts]'+str(i)
            print '[change to not sign]'+student.name
            student.status = constant.StudentStatus.normal
            student.gradeClass = None
            student.contract = None
            student.lessons = None
            student.lessonLeft = None
            student.demo = None
            student.save()
        except Exception,e:
            print e
def job_delStudentDate():
        students = []
        s = Student()
        s.prt1mobile = '13816686125'
        s.branchName = u'联洋'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '13818195829'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '18501605850'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '13918115995'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '13918570400'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '13761807110'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '13818903338'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '18501638498'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '13918858860'
        students.append(s)
        s = Student()
        s.branchName = u'联洋'
        s.prt1mobile = '18610496056'
        students.append(s)
        
        deleteStudentAllData(students)
      
def job_deleteContractStudent(branchCode):
    branch = Branch.objects.get(branchCode='fl')  # @UndefinedVariable
    del_contracts(branch.id)
    del_classes(branch.id)
    print '[DONE]'
    return

def job_delTeacherStudent(teacherLogin):
    teacher = Teacher.objects.get(username=teacherLogin)
    query = Q(teacher=teacher.id)&Q(gradeClass_type=constant.GradeClassType.normal)
    gcs = GradeClass.objects.filter(query)
    j = 0
    k = 0
    i = 0
    for gc in gcs:
        query = Q(gradeClass=gc.id)
        lessons = Lesson.objects.filter(query)
        
        for l in lessons:
            l.delete()
            i = i + 1
        
        
        for s in gc.students:
            s.gradeClass = None
            s.lessons = None
            s.lessonLeft = None
            s.save()
            k = k + 1
        
        gc.delete()
        j = j + 1
    print '[del lessons]'+str(i)
    print '[move out students]'+str(k)
    print '[del class]'+str(j)
    return

def job_remindDone(branchCode):
    branch = Branch.objects.get(branchCode=branchCode)
    todayBegin = datetime.datetime.strptime(utils.getDateNow(8).strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    query = Q(branch=str(branch.id))
    query = query&Q(remindTime__lt=todayBegin)&Q(isDone__ne=1)
    rs = TeacherRemind.objects.filter(query)

    i = 0
    for r in rs:
        if r.student.probability == 'C':
            r.isDone = 1
            r.save()
            i = i + 1
    print 'hf[done]' + str(i)
    
def job_removeBranchOldStudent(code):#删除2018-3以前学生
    date = datetime.datetime.strptime('2018-03-01','%Y-%m-%d')
    branch = Branch.objects.get(branchCode=code)
    query = Q(singDate__lt=date)&Q(branch=branch.id)
    contracts = Contract.objects.filter(query)
    i = 0
    for c in contracts:
        try:
            c.delete()
            s = Student.objects.get(id=c.student_oid)
            s.gradeClass = None
            s.contract = None
            s.status = 0
            s.save()
            query = Q(student=str(s.id))
            lessons = Lesson.objects.filter(query)
            for l in lessons:
                l.delete()
            print s.name + str(c.weeks)
            i = i + 1
            
        except:
            c.delete()

            err = 1
        
    print i 
    
    del_classes(branch.id)
     
def job_allRemindDone():
    todayBegin = datetime.datetime.strptime(utils.getDateNow(8).strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    query = Q(remindTime__lt=todayBegin)&Q(isDone__ne=1)
    rs = TeacherRemind.objects.filter(query)
    print len(rs)
    i = 0
    j = 0
    for r in rs:
        try:
            if r.student.probability == 'C':
                r.isDone = 1
                r.save()
                i = i + 1
        except:
            r.delete()
            j = j + 1
    print '[done]' + str(i)
    print '[delete]' + str(j)
    

#s删除校区所有签到
def job_removeCheckinLessons(branchCode):
    branch = Branch.objects.get(branchCode=branchCode)
    if branch:
        query = Q(branch=branch.id)&Q(gradeClass_type=1)
        gcs = GradeClass.objects.filter(query)
        i = 0
        j = 0
        for gc in gcs:
            query = Q(gradeClass=gc.id)&Q(checked=True)
            lessons = Lesson.objects.filter(query)
            
            for l in lessons:
                l.delete()
                i = i + 1
        print '[del checkin]'+str(i)
        query = Q(branch=branch.id)&Q(status=constant.StudentStatus.sign)
        ss = Student.objects.filter(query)
        j = 0
        for s in ss:
            try:
                if s.lessons > 0:
                    if s.lessonLeft >= 0:
                        s.lessonLeft = s.lessonLeft + s.lessons
                    s.lessons = 0
                    s.save()
                    j = j + 1
            except:
                err = 0
        print '[change student]'+str(j)
    else:
        print 'branch is Wrong'

#10校区导入老学籍前的老合同    
def job_getOldContracts(branchCode):
    query = Q(branchCode=branchCode)
    branches = Branch.objects.filter(query)
    #millisecond = int(round(time.time() * 1000))
    filename = 'oldContracts-'+branchCode#+str(millisecond)
    print '[branches]'+branchCode
    for b in branches:
        i = 0
        query = Q(branch=b.id)&Q(singDate__ne=None)&(Q(weeks__gt=0)|Q(contractType__ne=None))
        contracts = Contract.objects.filter(query)
        for c in contracts:
            sdate = ''
            try:
                sdate = c.singDate.strftime("%Y-%m-%d")
            except:
                sdate = ''
            bdate = ''
            try:
                bdate = c.beginDate.strftime("%Y-%m-%d")
            except:
                bdate = ''
            tid = ''
            try:
                if c.teacher:
                    tid = str(c.teacher.id)
                else:
                    tid = ''
            except:
                tid = ''
            mem = ''
            try:
                if mem:
                    mem = c.memo
                else:
                    mem = ''
            except:
                mem = ''    
            ctid = ''
            try:
                ctid = str(c.contractType.id)
            except:
                ctid = ''
            weeks = ''
            try:
                weeks = str(c.weeks)
            except:
                weeks = ''
            paid = ''
            try:
                paid = str(c.paid)
            except:
                paid = ''
            brandid = ''
            try:
                brandid = str(c.branch.id)
            except:
                brandid= ''
            multi = ''
            try:
                multi = str(c.multi)
            except:
                multi = ''
            status = ''
            try:
                str(c.status)
            except:
                status = ''
            sid = ''
            try:
                sid = c.student_oid
            except:
                sid = ''
            info = ''
            try:
                info = sid+','+str(c.id)+','+brandid+','+sdate+','+bdate+','+ctid+','+paid+','+weeks+','+status+','+multi+','+mem+','+tid
            except:
                print sid
                print c.id
                print brandid
                print sdate
                print bdate
                print paid
                print weeks 
                print type(status)
                print type(multi)
                print type(mem)
                print type(tid)
                return


     
            utils.save_log(filename, info)
            i = i + 1
        print '['+b.branchName+']'+str(i)
                                    
    print '[DONE]'

def job_getDeletedContracts(branchCode):
    oldContracts = []
    filename = BASE_DIR+'/log/oldContracts-'+branchCode+'.log'
    fh = open(filename)
    for line in fh.readlines(): 
        oldContracts.append(line)
    query = Q(branchCode=branchCode)
    branches = Branch.objects.filter(query)

    filename2 = 'newContracts-'+branchCode
    print '[branches]'+str(len(branches))
    contracts = []
    for b in branches:
        i = 0
        query = Q(branch=b.id)&Q(singDate__ne=None)&(Q(weeks__gt=0)|Q(contractType__ne=None))
        cs = Contract.objects.filter(query)
        for c in cs:
            info = c.student_oid
            contracts.append(info)
            
            i = i + 1
        print '['+b.branchName+']'+str(i)
    print '------------------------------------'
    print len(contracts)
    i = 0
    
    for oc in oldContracts:
        ocs = oc.split(',') 
        cid = ocs[0].strip()
        has = False
        
        for ccid in contracts:
        
            if cid == ccid.strip():
                has = True
                break
        if not has:
            i = i + 1 
            oc = oc[0:len(oc)-1]
            utils.save_log(filename2, oc)
            print oc
                                        
    print '[DONE]' + str(i)

#将误删除的合同复原
def job_restoreContracts(branchCode):
    i = 0
    contracts = []
    
    filename = BASE_DIR+'/log/newContracts-'+branchCode+'.log'
    print filename
    #return
    fh = open(filename)
    for line in fh.readlines(): 
            
            cs = []
            try:
                cs = line.split(',')
            except Exception,e:
                print e
                cs = []
            if len(cs) > 1:
                c = Contract()
                c.student_oid = cs[0].strip()
                c.id = ObjectId(cs[1].strip())
                try:
                    c.branch = Branch.objects.get(id=cs[2].strip())
                except:
                    err = 0
                try:
                    c.singDate = datetime.datetime.strptime(cs[3].strip(),"%Y-%m-%d")
                except:
                    err = 1
                try:
                    c.beginDate = datetime.datetime.strptime(cs[4].strip(),"%Y-%m-%d")
                except:
                    err = 1
                try:
                    c.contractType = ContractType.objects.get(id=cs[5].strip())
                except:
                    err = 1
                try:
                    c.paid = int(cs[6].strip())
                except:
                    err = 1
                try:
                    c.weeks = int(cs[7].strip())
                except:
                    err = 1
                try:
                    c.status = int(cs[8].strip())
                except:
                    c.status = constant.ContractStatus.sign
                try:
                    c.multi = int(cs[9].strip())
                except:
                    c.multi = constant.MultiContract.newDeal
                c.memo = cs[10]
                try:
                    c.teacher = Teacher.objects.get(id=cs[11].strip())
                except:
                    err = 1
                
                s = None
                try: 
                    s = Student.objects.get(id=c.student_oid)
                except:
                    s = None
                if s:
                    utils.save_log('contractsRestore',str(s.id))
                    c.save()
                    i = i + 1
                    css = s.contract
                    if not css or len(css) == 0:
                        css = []
                    has = False
                    for cc in css:
                        if cc.id == c.id:
                            has = True
                            break
                    if not has:
                        css.append(c)
                        s.contract = css
                        if s.status != 1:
                            s.status = 1
                        s.save()
                
                contracts.append(line)
    print '[DONE]'+str(i)
    return

# 清理重复数据，不显示的不再标注为重复    
def dupRedeal():
    query = Q(dup=-1)&Q(resolved=-1)
    dups = Student.objects.filter(query)
    print 'total:'+str(len(dups))
    i = 0
    j = 0
    k = 0
    l = 0
    for s in dups:
        query = Q(prt1mobile=s.prt1mobile)|Q(prt2mobile=s.prt1mobile)
        if s.prt2mobile and len(s.prt2mobile) > 5:
            query = query|Q(prt1mobile=s.prt2mobile)|Q(prt2mobile=s.prt2mobile)
        dup = Student.objects.filter(query)
        if dup and len(dup) ==1:
            s1 = dup[0] 
            s1.dup = 0
            s1.resolved = 0
            s1.save()
            
            k = k + 1
        elif dup and len(dup) ==2:
            i = i + 1
            branch = None
            try:
                branch = str(dup[0].branch.id)
            except:
                branch = None
            branch2 = None
            try:
                branch2 = str(dup[0].branch2.id)
            except:
                branch2 = None
            branch3 = None
            try:
                branch3 = str(dup[0].branch3.id)
            except:
                branch3 = None
            branch4 = None
            try:
                branch4 = str(dup[0].branch4.id)
            except:
                branch4 = None
            dp = 0
            try:
                regBranch = dup[0].regBranch
            except:
                regBranch = None
            
            rb2 = None
            try:
                rb2 = dup[1].regBranch
            except:
                rb2 = None 
            if regBranch and branch and rb2:
                
                student = checkIfDup(dup[0],dup[1],dup[1],regBranch,branch,branch2,branch3,branch4)
                dp = student.dup
                if  dp != -1:
                    s1 = dup[0] 
                    s1.dup = 0
                    s1.resolved = 0
                    s1.save()
                    s1 = dup[1] 
                    s1.dup = 0
                    s1.resolved = 0
                    s1.save()

                    j = j + 1
            else:
                    s1 = dup[0] 
                    s1.dup = 0
                    s1.resolved = 0
                    s1.save()
                    if s1.prt1mobile == '18610567319':
                        print '[no regB saved]'+str(s1.id)
                        print s1.dup
                        
                    s1 = dup[1] 
                    s1.dup = 0
                    s1.resolved = 0
                    s1.save()
                    if s1.prt1mobile == '18610567319':
                        print '[no regB saved]'+str(s1.id)
                        print s1.dup
                        
                    l = l + 1
                
        elif dup and len(dup) >2:
            print s.prt1mobile
    print 'done:'+str(i)
    print 'not dup:'+str(j)
    print 'single:'+str(k)
    print 'no regBranch:'+str(l)
    return

def checkIfDup(student,st,s,regBranch,branch,branch2,branch3,branch4):
    #regBranch一方为网络部,一方branch校区，是另一方regBranch校区
    #print type(branch2)
    if student.prt1mobile == '18610567319':
        print 'IN-----------'
        print s.prt1mobile
    stbranch2 = None
    try:
        stbranch2 = st.branch2.id
    except:
        stbranch2 = st.branch2
    
    stbranch3 = None
    try:
        stbranch3 = st.branch3.id
    except:
        stbranch3 = st.branch3
        
    stbranch4 = None
    try:
        stbranch4 = st.branch4.id
    except:
        stbranch4 = st.branch4

    if str(st.regBranch.id) == constant.NET_BRANCH or str(regBranch.id) == constant.NET_BRANCH:
        
        if str(st.regBranch.id) == branch or str(regBranch.id) == str(st.branch.id):
            student.dup = -1
        elif str(st.regBranch.id) == branch2 or (stbranch2 and str(regBranch.id) == str(stbranch2)):
            student.dup = -1
        elif str(st.regBranch.id) == branch3 or (stbranch3 and str(regBranch.id) == str(stbranch3)):
            student.dup = -1
        elif str(st.regBranch.id) == branch4 or (stbranch4 and str(regBranch.id) == str(stbranch4)):
            student.dup = -1
    else:
        student.dup = 0
    if student.dup == -1:
        student.resolved = -1
        s.resolved = -1
        s.dup = -1
        s.save()
        print s.id
        print s.prt1mobile
        print s.dup
        if student.prt1mobile == '18610567319':
            print 'IN---IS DUP'
    else:
        student.dup = 0
        student.resolved = 0
        if student.prt1mobile == '18610567319':
            print 'IN---NOT DUP' 
        s.resolved = 0
        s.dup = 0
        s.save() 
    if student.prt1mobile == '18610567319':
            print '[18610567319]'
            print student.dup     
    return student 
def delTeacherCheckin(teacherLogin):
    teacher = None
    try:
        teacher = Teacher.objects.get(username=teacherLogin)
    except:
        teacher = None
    if not teacher:
        return
    query = Q(teacher=teacher.id)&Q(deleted__ne=-1)&Q(gradeClass_type=1)
    classes = GradeClass.objects.filter(query)
    students = []
    for c in classes:
        for s in c.students:
            query = Q(student=str(s.id))
            lessons = Lesson.objects.filter(query)
            for l in lessons:
                l.delete()
 
    for g in classes:
        query = Q(gradeClass=g.id)
        lessons = Lesson.objects.filter(query)
        print len(lessons)
        for l in lessons:
            l.delete()

def addInReview():
    query = Q(role=constant.Role.teacher)&Q(status__ne=-1)
    teachers = Teacher.objects.filter(query).order_by("branch")
    for t in teachers:
        if t.branch.type == constant.BranchType.school:
            t.inReview = True
            t.save()
            print t.branch.branchName+'|'+t.name 

def changeContractBug():
    j = 0
    for i in range(16):
        i = i + 1
        query = Q(status=0)&Q(contract__size=i)
        students = Student.objects.filter(query)
        print len(students)
        for s in students:
            for c in s.contract:
                try:
                    cc = Contract.objects.get(id=c.id)
                    if cc.status == constant.ContractStatus.sign and cc.contractType.type == constant.ContractType.normal:
                        s.status = constant.StudentStatus.sign
                        print s.id
                        s.save()
                        j = j + 1
                        break
                except:
                    err = 1
                    
    print '[total]'+str(j)
   
def countStudentSMSluckyDraw(cityId):
    mobiles = []
    branches = Branch.objects.filter(city=cityId)
    all = 0
    for b in branches:
      if str(b.id) == constant.NET_BRANCH:
        i = 0
        query = Q(regBranch=b.id)&Q(status=0)
        students = Student.objects.filter(query)
        for s in students:
            if s.prt1mobile not in mobiles:
                mobiles.append(s.prt1mobile)
                try:
                    if s.prt1mobile and len(s.prt1mobile) == 11:
                        utils.save_log('sms2', s.prt1mobile)
                except:
                    err = 1
                i = i + 1
                all = all + 1
        if i > 0:
            print '['+b.branchName+']'+str(i)
    print '[all]'+str(all)
    
def yuan19SMS(mobile):
    url="http://api.ihuyi.com/webservice/sms.php?method=Submit" 
    account="C72207447"
    password="2e5183137a95783907ae8e89ea4be247"
    content = '双十一送学费，最高3600元，百 分 百赠送。11月11日截止。活动地址:http://t.cn/EwFo3fu 回T退订'
    #content = '亲爱的主人，我是小元，很高兴，您终于来了。您的验证码是：135246。我会一直陪着您闯荡江湖，修炼成人人仰视的围棋高手。'
    data = {'account':account,'password':password,'mobile':mobile,'content':content}
    res = http.http_post(url, data)
    print res
    r1 = res.find('<code>')+6
    r2 = res.find('</code>')
    re1 = res[r1:r2]
    r1 = res.find('<smsid>')+7
    r2 = res.find('</smsid>')
    re1 =  str(mobile)+','+res[r1:r2]+','+re1
    #print re1
    now = utils.getDateNow(8)
    re1 = str(now)+','+re1
    utils.save_log('2018luckyDrawSMS', re1)

def changeBranch(fromBranch,toBranch):
    try:
        fb = Branch.objects.get(branchCode=fromBranch)
        tb = Branch.objects.get(branchCode=toBranch)
    except:
        print 'NO BRANCH FOUND!'
    query = Q(branch=fb.id)&Q(status=constant.StudentStatus.sign)
    students = Student.objects.filter(query)
    now = utils.getDateNow(8)
    nowStr = now.strftime("%Y%m")

    i = 0
    for s in students:
        i = i + 1
        s.branch = tb
        s.branchName = tb.branchName
        if not s.memo:
            s.memo = ''
        s.memo = '['+nowStr+u'从'+fb.branchName+u'合并到'+tb.branchName+']'+s.memo
        s.save()
        
    print 'STUDENT DONE ' + str(i)
    query2 = Q(branch=fb.id)
    contracts = Contract.objects.filter(query2)
    i = 0
    for c in contracts:
        i = i + 1
        c.branch = tb
        c.save()
        
    print 'CONTRACT DONE ' + str(i) 
    i = 0
    #===========================================================================
    # classes = GradeClass.objects.filter(query)
    # for c in classes:
    #     i = i + 1
    #     c.branch = tb
    #     c.save()
    #     
    # print 'CLASS DONE ' + str(i) 
    #===========================================================================
    pages = Webpage.objects.filter(query2)  # @UndefinedVariable
    i = 0
    for c in pages:
        i = i + 1
        c.branch = tb
        c.save()
    print 'PAGE DONE ' + str(i)    
    #===========================================================================
    #  
    # lessons = Lesson.objects.filter(branch=str(fb.id))
    # i = 0
    # for c in lessons:
    #     i = i + 1
    #     c.branch = str(tb.id)
    #     c.save()
    #     
    # print 'LESSON DONE ' + str(i) 
    #===========================================================================
    #===========================================================================
    # files = StudentFile.objects.filter(branch=str(fb.id))
    # i = 0
    # for c in files:
    #     i = i + 1
    #     c.branch = str(tb.id)
    #     c.save()
    #     
    # print 'FILE DONE ' + str(i) 
    #===========================================================================
    

def changeMember3monthFee():
    query = Q(type=3)
    cts = ContractType.objects.filter(query)
    q = None
    i = 0
    for ct in cts:
        if i==0:
            q = Q(contractType=ct.id)
        else:
            q = q|Q(contractType=ct.id)
        i = i + 1

    query = Q(multi=constant.MultiContract.memberLesson)&(Q(paid__lt=1200)|Q(paid=1200))
    contracts = Contract.objects.filter(query).order_by('student_oid','singDate')
    print len(contracts)
    last = None
    lastDue = None
    lastCT = None
    i = 0
    same = 1#
    for c in contracts:
        if last == c.student_oid:
            print c.student_oid+'--'+str(c.singDate)
            c.dueDate = utils.nextDueDate(lastDue)
            lastDue = c.dueDate
            if lastCT:
                c.contractId = str(lastCT.id)
            else:
                continue
            same = same + 1
        else:
            if lastCT:
                a = lastCT.weeks/12
                if a < 4:
                    a = 4
                times = a - same
                
                dueDate = lastDue
                for i in range(times):
                    dueDate = utils.nextDueDate(dueDate)
                    t = Contract()
                    t.dueDate = dueDate
                    t.contractId = str(lastCT.id)
                    t.branch = lastCT.branch
                    t.student_oid = lastCT.student_oid
                    t.shouldPay = 1200
                    t.beginDate = lastCT.beginDate
                    t.cid = lastCT.cid
                    t.multi = constant.MultiContract.memberLesson
                    t.weeks = 12
                    t.save()
                    #try:
                    
                    #except:
                     #   print 'ERR DUE DATE'
                      #  print dueDate
            same = 1
            last = c.student_oid
            lastDue = c.beginDate
            query = Q(student_oid=c.student_oid)&(q)
            try:
                ccc = Contract.objects.filter(query).order_by('-paid')
                print ccc._query
                lastCT = Contract.objects.filter(query).order_by('-paid')[0]
            except:
                err = 1
                print c.student_oid+'--no member contract!!!'
                continue
            c.contractId = str(lastCT.id)
            c.dueDate = lastDue
        c.shouldPay = 1200
        c.cid = lastCT.cid
        c.save()
        i = i + 1
    print 'DONE ' + str(i)
    #y19s = Y19Income.objects.all()  # @UndefinedVariable
    #for y in y19s:
     #   y.logDate = y.payDate
        #y.save()
    return

def changeContractBranch(fromBranch,toBranch):
    try:
        fb = Branch.objects.get(branchCode=toBranch)
        tb = Branch.objects.get(branchCode=fromBranch)
    except:
        print 'NO BRANCH FOUND!'
        return
    mem = u'从'+fb.branchName+u'合并到'+tb.branchName+']'
    
    query = Q(memo__icontains=mem)
    students = Student.objects.filter(query)
    print students._query
    print len(students)
    i = 0
    for s in students:
        query = Q(student_oid=str(s.id))
        contracts = Contract.objects.filter(query)
        if len(contracts) > 0:
            i = i + 1
            print i
            for c in contracts:
                c.branch = fb
                c.save()
    query = Q(student_oid='5c0caeafe5c5e6a4d4c14856')
    cs = Contract.objects.filter(query)
    for c in cs:
        c.branch = fb
        c.save()
    print '[DONE]'+str(i)
    return 

def removeShouldPay():
    query = Q(multi=3)&Q(status__ne=constant.ContractStatus.delete)
    pays = Contract.objects.filter(query).order_by("student_oid","dueDate")
    
    lastStudent = None
    i = 0
    j = 0
    k = 0
    for c in pays:
        
        if not lastStudent:
            lastStudent = c.student_oid
        elif c.student_oid != lastStudent:
            
            if i % 4 > 0:
                print lastStudent+'------'+str(i)
                j = j + 1
                if i > 1 and i % 4 == 1:
                    print lastStudent + '---' + str(i) 
                    k = k + 1
            i = 0
            lastStudent = c.student_oid
        i = i + 1
        
    print j
    print k
    return

def changeAppDone():
    query = Q(appDone=True)
    y19s = Y19Income.objects.filter(query)  # @UndefinedVariable
    for y in y19s:
        y.appFee = True
        y.appDone = False 
        y.save()
    return

def changeShouldPay():
    query = Q(multi=constant.MultiContract.memberLesson)&Q(paid__gte=1200)&Q(paid__lte=1400)
    cs = Contract.objects.filter(query).order_by("student_oid")
    print len(cs)
    students = []
    i = 0
    j = 0
    for c in cs:
        if c.student_oid not in students:
            print 'new--------------'+str(c.id)
            j = j + 1
            students.append(c.student_oid)
            query = Q(student_oid=c.student_oid)&Q(multi=constant.MultiContract.memberLesson)&Q(singDate=None)
            shouldPays = Contract.objects.filter(query)
            k = 0
            for s in shouldPays:
                s.shouldPay = c.paid
                s.save()
                #print s.id
                i = i + 1
                k = k + 1
            print str(k) + ' change to ' + str(c.paid)
    print 'totle student:'+str(j)
    print 'totle shouldPay:'+str(i)
    return
def location():
    
    query = Q(branch="5867c0c33010a51fa4f5abe6")&Q(status=1)
    students = Student.objects.filter(query).order_by('memo')
    i = 0
    for s in students:
        i = i + 1
        if not s.name:
            s.name = ''
        if not s.memo:
            s.memo = ''
        print str(i) + ':' + s.name + '--' + s.memo
    
    return

def statRegEveryday():
    now = utils.getDateNow(8)
    print now
    weekBegin = utils.getWeekBegin(now, False)
    weekEnd = weekBegin + datetime.timedelta(days=7)
    util3.statWeekReg(constant.BEIJING,weekBegin,weekEnd)
    print '[DONE WEEK]'
    monthBegin = utils.getThisMonthBegin(now)
    monthEnd = monthBegin + datetime.timedelta(days=32)
    monthEnd = utils.getThisMonthBegin(monthEnd)
    util3.statWeekReg(constant.BEIJING,monthBegin,monthEnd)
    print '[DONE MONTH]'

def hfAllLessons():
    query = Q(branch='5867c0c33010a51fa4f5abe6')&Q(status=1)
    students = Student.objects.filter(query)
    print len(students)
    map = {}
    for s in students:
        query = Q(student_oid=str(s.id))&Q(multi__ne=3)&Q(status=0)
        cs = Contract.objects.filter(query)
        al = 0
        for c in cs:
            al = al + c.weeks
        map[str(s.id)] = al
        if not s.name:
            s.name = ''
        if not s.name2:
            s.name2 = ''
        print s.name + '(' + s.name2 + ')' + ';' + str(al) + ';' + str(al - s.lessons)
    return

def hfAllmoney():
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    file = open(BASE_DIR+'/go_static/names.txt','r') 
    names = file.readlines() 
    query = Q(branch='5867c0c33010a51fa4f5abe6')&Q(status=1)
    students = Student.objects.filter(query)
    print len(students)
    map = {}
    for name in names:
        has = False
        for s in students:
         
          if s.name in name: 
            has = True
            query = Q(student_oid=str(s.id))&Q(paid__gt=0)&Q(status=0)&Q(contractType__ne='594743b797a75d5d53879a78')
            cs = Contract.objects.filter(query)
            al = 0
            str1 = s.name
            m = ''
            for c in cs:
                if m != '':
                    m = m + ',' + str(c.paid)
                else:
                    m = str(c.paid)
                al = al + c.paid
            if not s.name:
                s.name = ''
            if not s.name2:
                s.name2 = ''
            print str1 + ';' + m + u';' + str(al)
            break
        if not has:
            print name

def ul():
    file = '/Users/patch/Documents/UniversalLab.txt'
    file_r = open(file,"r")
    list = []
    res = []
    i = 0
    for l in file_r.readlines():       
        a = l.split("=")
        #print a[0]
        #print a[1]
        if a[1] not in list:
            list.append(a[1])
            res.append(l)
            i = i +1
            print str(i) + ': ' + l
    #file_w = open(file, "w")
    #file_w.write("\n" + txt)
    #file_w.close()
def makeAllBranchFolder():
    branchs = Branch.objects.all()
    #os.mkdir('/Users/patch/data/test/')
    for b in branchs:
        #os.mkdir('/Users/patch/data/test/'+str(b.id))
        try:
            os.mkdir('/data/go2/go_static/users/'+str(b.id))
        except Exception,e:
            print e
    return
        
if __name__ == "__main__":
    makeAllBranchFolder()
    #ul()
    #hfAllLessons()
    #countStudentSMSluckyDraw('5867c05d3010a51fa4f5abe5')
    #changeBranch('ft','gz')
    #changeMember3monthFee()
    #changeContractBranch('th','xbh')
    #removeShouldPay()
    #statRegEveryday()
    #util3.statWeekReg(constant.BEIJING,begin,end)
