#!/usr/bin/env python
# -*- coding:utf-8 -*-
#from numpy import False_
from student.models import Suspension
__author__ = 'patch'

import sys,hashlib, os, time, datetime
import xlrd,re,xlwt
from bson import ObjectId
from mongoengine.queryset.visitor import Q
from operator import attrgetter
from regUser.models import *
from teacher.models import Teacher,Login_teacher,Message
from branch.models import Branch
from gradeClass.models import Lesson
from statistic.models import StatStudent,BranchIncome,UserStat
from go2.settings import BASE_DIR,USER_IMAGE_DIR,ALLOWED_HOSTS
import logging
from datetime import timedelta
from tools import constant, utils


def getBranchIncome(branch,beginDate,endDate,teacher_oid=None,teacherName=None):
    query = Q(branch=branch)&Q(lessons__gt=0)
    if teacher_oid:
        query = query&Q(teacher=teacher_oid)
    students = Student.objects.filter(query)
    sum = 0
    alllesson = 0
    for s in students:
        query = Q(student=str(s.id))&(Q(type=1)|Q(type=3))&Q(lessonTime__gt=beginDate)&Q(lessonTime__lt=endDate)
        lessons = Lesson.objects.filter(query)  # @UndefinedVariable
        price = 300
        for c in s.contract:
            try:  
                if c.status == 0:
                    if c and c.weeks > 0:
                        try:
                            price = c.paid/c.weeks
                            break
                        except:
                            err = 0
            except:
                err = 1          
        for l in lessons:
            value = 1
            if l.value and l.value == 0:
                value = 0
            if l.value and l.value > 0:
                value = l.value
            alllesson = alllesson + value
            sum = sum + value * 1 * price
    i = BranchIncome()
    i.lessons = alllesson
    i.sum = sum
     
    if alllesson > 0:
        i.eve = int(sum/alllesson)
    m = None
    if beginDate:
        m = beginDate.strftime("%Y-%m")
    i.month = m
    i.teacherName = teacherName
    i.teacher_oid = teacher_oid
    return i
#不算成交的合同类型
def getNoneDealContractTypes(city):
    query = Q(duration__lt=city.dealDuration)&Q(duration__ne=1)&Q(city=city.id)
    excludeContract = ContractType.objects.filter(query)
    return excludeContract

#假期合同类型
def getVocationContractTypes(city):
    query = Q(duration=1)&Q(city=city.id)
    excludeContract = ContractType.objects.filter(query)
    return excludeContract

#假期合同类型
def getRedealCT(city):
    query = Q(duration=40)&Q(city=city.id)
    excludeContract = ContractType.objects.filter(query)

    return excludeContract

def getBranchRatio(NET_BRANCH,branch,searchBegin,searchEnd,net,excludeContract=None):
    stat = UserStat()
    queryReg = Q(callInTime__gte=searchBegin)&Q(callInTime__lt=searchEnd)
    if net and net == '1':
        queryReg = queryReg&Q(regBranch=NET_BRANCH)
    queryRegInvalid = queryReg&Q(netStatus=-1)
    queryDemo = Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(gradeClass_type=2)&Q(demoIsFinish__ne=-1)
    queryShow = queryDemo&Q(demoIsFinish=1)
    queryNotShow = queryDemo&Q(demoIsFinish__ne=1)&Q(demoIsFinish__ne=-1)
    queryDeal = Q(singDate__gte=searchBegin)&Q(singDate__lt=searchEnd)&Q(status=0)
    queryRefund = Q(endDate__gte=searchBegin)&Q(endDate__lt=searchEnd)&Q(status=2)
    for ec in excludeContract:
        queryDeal = queryDeal&Q(contractType__ne=ec.id)
    if branch:
        queryReg = queryReg&Q(branch=branch.id)
        queryRegInvalid = queryRegInvalid&Q(branch=branch.id)
        queryShow = queryShow&Q(branch=branch.id)
        queryNotShow = queryNotShow&Q(branch=branch.id)
        queryDeal = queryDeal&Q(branch=branch.id)
        queryRefund = queryRefund&Q(branch=branch.id)
        stat.title = branch.branchName 
    else:
        stat.title = 'all'
    reg = Student.objects.filter(queryReg)
    regInvalid = Student.objects.filter(queryRegInvalid)
    demoShow = GradeClass.objects.filter(queryShow)
    demoNotShow = GradeClass.objects.filter(queryNotShow)
    contract = Contract.objects.filter(queryDeal)
    refund = Contract.objects.filter(queryRefund)
    stat.reg = len(reg)
    stat.regValid = len(reg)-len(regInvalid)
    #stat.deal = len(contract)
    #stat.refund = len(refund)

    tempnum = 0
    sts = []
    #demo show
    for demo in demoShow:
        if demo.students and len(demo.students)>0:
            s = demo.students[0]
            if s not in sts:
              if branch:
                if type(s).__name__=='Student' and str(s.branch.id) == str(branch.id):
                    if net and net == '1':
                        if s.regBranch and str(s.regBranch.id) == NET_BRANCH:
                                sts.append(s)
                                tempnum = tempnum + 1
                    else:
                        sts.append(s)
                        tempnum = tempnum + 1
              else:
                if type(s).__name__=='Student':
                    if net and net == '1':
                        if s.regBranch:
                            if  str(s.regBranch.id) == NET_BRANCH:
                                sts.append(s)
                                tempnum = tempnum + 1
                    else:
                        sts.append(s)
                        tempnum = tempnum + 1 
    stat.show = tempnum
    tempnum = 0
    for demo in demoNotShow:
        if demo.students and len(demo.students)>0:
            s = demo.students[0]
            if s not in sts:
              if branch:
                if type(s).__name__=='Student' and str(s.branch.id) == str(branch.id):
                    if net and net == '1':
                        if s.regBranch and str(s.regBranch.id) == NET_BRANCH:
                                sts.append(s)
                                tempnum = tempnum + 1
                    else:
                            sts.append(s)
                            tempnum = tempnum + 1
              else:
                if type(s).__name__=='Student':
                    if net and net == '1':
                        if s.regBranch:
                            if  str(s.regBranch.id) == NET_BRANCH:
                                    sts.append(s)
                                    tempnum = tempnum + 1
                    else:
                            sts.append(s)
                            tempnum = tempnum + 1
    stat.notShow = tempnum
        
    tempnum = 0
    for c in contract:
        s = None
        try:
            s = Student.objects.get(id=c.student_oid)
        except:
            continue
        has = False
        try:
          if s.contract and len(s.contract)>0:
            for cexist in s.contract:
                if cexist.status != 4 and cexist.singDate < searchBegin:
                    has = True
                    break
        except:
            err = 1
        if not has:
          if branch:
            if str(s.branch.id) == str(branch.id):
                if net and net == '1':
                    if s.regBranch and str(s.regBranch.id) == NET_BRANCH:
                        tempnum = tempnum + 1
                else:
                    tempnum = tempnum + 1
          else:
            if net and net == '1':
                if s and s.regBranch:
                    if str(s.regBranch.id) == NET_BRANCH:
                        tempnum = tempnum + 1
            else:
                    tempnum = tempnum + 1
    stat.deal = tempnum
        
    tempnum = 0
    for c in refund:
        s = None
        try:
                s = Student.objects.get(id=c.student_oid)
        except:
                continue
        if branch:
            if str(s.branch.id) == str(branch.id):
                if net and net == '1':
                    if str(s.regBranch.id) == NET_BRANCH:
                        tempnum = tempnum + 1
                else:
                    tempnum = tempnum + 1
        else:
            if net and net == '1':
                if s.regBranch:
                    if str(s.regBranch.id) == NET_BRANCH:
                        tempnum = tempnum + 1
            else:
                    tempnum = tempnum + 1
    stat.refund = tempnum
        
    stat = fillStat(stat,None)

    return stat


def fillStat(stat,title=None):
        stat.reservation = stat.show + stat.notShow
        stat.dealPure = stat.deal - stat.refund
           
        #有效咨询率
        if stat.reg > 0:
            try:
                stat.regValidRatio = int(float(stat.regValid)/float(stat.reg)*100)
            except:
                stat.regValidRatio = 0
        else:
            stat.regValidRatio = 0
        #有效咨询预约率
        if stat.regValid > 0:
            try:
                stat.reserationRatio = int(float(stat.reservation)/float(stat.regValid)*100)
            except:
                stat.reserationRatio = 0
        else:
            stat.reserationRatio = 0
        #预约到场率
        if stat.reservation > 0:
            try:
                stat.showRatio = int(float(stat.show)/float(stat.reservation)*100)
            except:
                stat.showRatio = 0
        else:
            stat.showRatio = 0
        #预约成交率
        if stat.reservation > 0:
            try:
                stat.dealRatio = int(float(stat.deal)/float(stat.reservation)*100)
            except:
                stat.dealRatio = 0
        else:
            stat.dealRatio = 0
        #到场成交率
        if stat.show > 0:
            try:
                stat.showDealRatio = int(float(stat.deal)/float(stat.show)*100)
            except:
                stat.showDealRatio = 0
        else:
            stat.showDealRatio = 0
        #有效咨询最终成交率
        if stat.regValid > 0:
            try:
                stat.regValidDealRatio = int(float(stat.dealPure)/float(stat.regValid)*100)
            except:
                stat.regValidDealRatio = 0
        else:
            stat.regValidDealRatio = 0
        if title:
            stat.title = title
        
        return stat

#获得校区学籍数 
def getBranchStudent(branch):
    res = 0
    query = Q(status=1)&Q(branch=branch)&Q(siblingId=None)
    students = Student.objects.filter(query)
    sus = getBranchSus(branch)

    res = len(students)
    susRes = len(sus)
    #if students and len(students) > 0 and sus and len(sus) > 0:
     #   res = len(students) - len(sus)
      
    return res,susRes

#获取校区当前休学学生
def getBranchSus(branch):
    #===========================================================================
    # sss = Suspension.objects.all()  # @UndefinedVariable
    # for ss in sss:
    #     if ss.student:
    #         student = Student.objects.get(id=ss.student)
    #         if student and student.branch:
    #             try:
    #                 ss.branch = str(student.branch.id)
    #                 ss.save()
    #             except:
    #                 err = 1
    #===========================================================================
                
    sus = None
    now = utils.getDateNow()
    query = Q(branch=branch)&Q(beginDate__lte=now)&Q(endDate__gte=now)
    try:
        sus = Suspension.objects.filter(query)  # @UndefinedVariable

    except Exception,e:
        print e
        sus = None
    return sus

#不包括网络的所有拜访  
def getBranchReg(branch,searchBegin,searchEnd):
    queryReg = Q(callInTime__gte=searchBegin)&Q(callInTime__lt=searchEnd)&Q(regBranch=branch)
    reg = Student.objects.filter(queryReg)
    return reg

#拜访和转介
def getBranchRegB(branch,searchBegin,searchEnd):
    queryReg = Q(callInTime__gte=searchBegin)&Q(callInTime__lt=searchEnd)&Q(regBranch=branch)&(Q(sourceType='B')|Q(sourceType='C'))
    reg = Student.objects.filter(queryReg)
    return reg

#不包括校区拜访
def getBranchRegNet(NET_BRANCH,branch,searchBegin,searchEnd):
    queryReg = Q(callInTime__gte=searchBegin)&Q(callInTime__lt=searchEnd)&Q(branch=branch)&Q(regBranch=NET_BRANCH)
    reg = Student.objects.filter(queryReg)
    queryReg = Q(callInTime__gte=searchBegin)&Q(callInTime__lt=searchEnd)&Q(branch=branch)&Q(regBranch=NET_BRANCH)&Q(netStatus__ne=-1)
    regValid = Student.objects.filter(queryReg)
    return reg,regValid


def getBranchUnshow(branch,searchBegin,searchEnd):
    queryNotShow = Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(demoIsFinish__ne=1)&Q(demoIsFinish__ne=-1)&Q(branch=branch)&Q(gradeClass_type=2)
    unshow = GradeClass.objects.filter(queryNotShow)
    return unshow

def getBranchUnshowNet(NET_BRANCH,branch,searchBegin,searchEnd):
    unshows = getBranchUnshow(branch,searchBegin,searchEnd)
    netUnshows = []
    for g in unshows:
        try:
            if g.students and len(g.students)>0:
                if str(g.students[0].regBranch.id) == NET_BRANCH and g.students[0].netStatus != -1:
                    netUnshows.append(g)
        except:
            err = 1
    return unshows,netUnshows

#包括网络拜访
def getBranchShow(branch,searchBegin,searchEnd):
    queryShow = Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(demoIsFinish=1)&Q(gradeClass_type=2)
    if branch:
        queryShow = queryShow&Q(branch=branch)
    show = GradeClass.objects.filter(queryShow)
    
    return show

#包括网络拜访include enddate
def getBranchShow2(branch,searchBegin,searchEnd):
    queryShow = Q(start_date__gte=searchBegin)&Q(start_date__lte=searchEnd)&Q(demoIsFinish=1)&Q(gradeClass_type=2)
    if branch:
        queryShow = queryShow&Q(branch=branch)
    show = GradeClass.objects.filter(queryShow)
    #print show._query
    
    return show
#总到场，网络到场，拜访到场（不包括社会）
def getBranchShowNet(NET_BRANCH,branch,searchBegin,searchEnd):
    
    shows = getBranchShow2(branch,searchBegin,searchEnd)
    #if str(branch) == '58be19f997a75d39e020087c':
        #print len(shows)
    showAll = []  
    temp = []
    temp1 = []
    
    for g in shows:
        try:
            if g.students and len(g.students)>0:
                #if str(branch) == '58be19f997a75d39e020087c':
                    #print '-st-' + g.students[0].sourceType + "-reg branch-" + str(g.students[0].regBranch.id) + '-net status-' + str(g.students[0].netStatus)
                if str(g.students[0].regBranch.id) == NET_BRANCH and g.students[0].netStatus != -1:
                    #if branch.branchCode == 'gz':
                        
                     #   print g.students[0].prt1mobile
                    temp.append(g)
                    showAll.append(g)
                elif g.students[0].sourceType == 'B' or g.students[0].sourceType == 'C' or g.students[0].sourceType == 'D':
                    temp1.append(g)
                    showAll.append(g)  
        except Exception,e:
            err = 1

    return showAll,temp,temp1

def getBranchDeal(branch,searchBegin,searchEnd,excludeContract=None,holidayCT=None):
    queryDeal = Q(singDate__gte=searchBegin)&Q(singDate__lte=searchEnd)&Q(status__ne=4)&Q(contractType__ne=holidayCT)
    if branch:
        queryDeal = queryDeal&Q(branch=branch)
    if excludeContract:
        for ec in excludeContract:
            queryDeal = queryDeal&Q(contractType__ne=ec.id)
    deal = Contract.objects.filter(queryDeal).order_by("-singDate")
    return deal

def getBranchDealHoliday(branch,searchBegin,searchEnd,excludeContract=None,holidayCT=None):
    ct = holidayCT
    if not ct:
        return None
    queryDeal = Q(singDate__gte=searchBegin)&Q(singDate__lte=searchEnd)&Q(status=0)&Q(contractType=holidayCT)
    if branch:
        queryDeal = queryDeal&Q(branch=branch)
    deal = Contract.objects.filter(queryDeal).order_by("-singDate")
    return deal

def getBranchDealHolidayNet(NET_BRANCH,branch,searchBegin,searchEnd,excludeContract=None,holidayCT=None):
    ct = holidayCT
    if not ct:
        return None
    queryDeal = Q(singDate__gte=searchBegin)&Q(singDate__lte=searchEnd)&Q(status=0)&Q(contractType=holidayCT)
    if branch:
        queryDeal = queryDeal&Q(branch=branch)
    deal = Contract.objects.filter(queryDeal).order_by("-singDate")
    temp = []
    for c in deal:
        try:
            student = Student.objects.get(id=c.student_oid)
            if student and str(student.regBranch.id)==NET_BRANCH and student.netStatus != -1:
                temp.append(c)
        except:
            student = None
    return temp


#包括网络拜访，不返回网络数据
def getBranchDealDiv(branch,searchBegin,searchEnd,excludeContract=None,holidayCT=None,redealCT=None):
    deal = getBranchDeal(branch,searchBegin,searchEnd,excludeContract,holidayCT)
    newdeal = []
    redeal = []
    redealNew = []
    redealOld = []
    if deal and len(deal)>0: 
        newStudent = []
        for c in deal:
            c2 = []
            if not c:
                continue
            if c.student_oid in newStudent:
                continue
            query = Q(student_oid=c.student_oid)&Q(status__ne=4)&Q(id__ne=c.id)&Q(singDate__lt=searchBegin)
            try:
                c2 = Contract.objects.filter(query)
            except Exception,e:
                print e

            if redealCT and c.contractType in redealCT:
                redeal.append(c)
            elif len(c2)==0:
                newStudent.append(c.student_oid)
                newdeal.append(c)
            else:
                redeal.append(c)
        
    return newdeal,redeal

#返回全部
def getBranchDealNet(NET_BRANCH,branch,searchBegin,searchEnd,excludeContract=None,holidayCT=None,redealCT=None):
    newdeal,redeal = getBranchDealDiv(branch,searchBegin,searchEnd,excludeContract,holidayCT,redealCT)
    newdealNet = []
    redealNet = []
    
    for c in newdeal:
        try:
            student = Student.objects.get(id=c.student_oid)
            if student and str(student.regBranch.id)==NET_BRANCH and student.netStatus != -1 and c not in newdealNet:
                newdealNet.append(c)
        except:
            student = None
    
    for c in redeal:
        try:
            student = Student.objects.get(id=c.student_oid)
            if student and str(student.regBranch.id)==NET_BRANCH and student.netStatus != -1 and c not in redealNet:
                
                redealNet.append(c)
        except:
            student = None     
    return newdeal,redeal,newdealNet,redealNet   
                     
def getBranchRefund(branch,searchBegin,searchEnd,excludeContract=None):

    queryDeal = Q(endDate__gte=searchBegin)&Q(endDate__lte=searchEnd)&Q(status=2)&Q(multi=constant.MultiContract.newDeal)
    if branch:
        queryDeal = queryDeal&Q(branch=branch)
    if excludeContract:
        for ec in excludeContract:
            queryDeal = queryDeal&Q(contractType__ne=ec.id)
    deal = Contract.objects.filter(queryDeal)
    return deal

def getBranchRefundNet(NET_BRANCH,branch,searchBegin,searchEnd,excludeContract=None):
    refunds = getBranchRefund(branch,searchBegin,searchEnd,excludeContract)
    refundsNet = []
    for c in refunds:
        try:
            student = Student.objects.get(id=c.student_oid)
            if student and str(student.regBranch.id)==NET_BRANCH and student.netStatus != -1:
                refundsNet.append(c)
                
        except:
            student = None
    return refunds,refundsNet

def BFshare(student):
    co_t = []
    if student.regTeacher:
        co_t.append(student.regTeacher)
    if student.co_teacher and len(student.co_teacher)>0:
        for t in student.co_teacher:
            if t not in co_t:
                co_t.append(t)
    res = 0
    if len(co_t) > 0:
        res = 1/float(len(co_t))
    return res,co_t

#===============================================================================
# 获得老师各项工作成绩：
# 校区拜访和转介 stat.reg
# add 20190606 stat.
# 拜访到场 stat.show
# 老师招生 stat.deal
# 试听课 stat.demo
# 试听成交 stat.demoDeal
# 转介成交 stat.refer
# 成交率 stat.dealRatio
#===============================================================================
def teacherStat2(teacher,searchBegin,searchEnd,branchDeal):
    stat = UserStat(title=teacher.name)
    
    #reg
    queryReg = (Q(regTeacher=teacher)|Q(co_teacher=teacher))&(Q(sourceType='B')|Q(sourceType='C'))
    queryRegDate = queryReg&Q(callInTime__lt=searchEnd)&Q(callInTime__gte=searchBegin)
    BF = Student.objects.filter(queryRegDate)
    temp = 0.0
    tempM = 0.0
    tempE = 0.0
    for student in BF:
        res,co_t = BFshare(student)
        temp = temp + res
        if student.Bsub == u'早':
            tempM = tempM + res
        elif student.Bsub == u'晚':
            tempE = tempE + res
    
    #校区拜访和转介
    stat.reg = round(temp,1)
    stat.regNet = round(tempM,1)
    stat.regAll = round(tempE,1)
    queryRegShow = queryReg&Q(isDemo=1)
    regShow = Student.objects.filter(queryRegShow)
    queryRegShowDate = Q(demoIsFinish=1)&Q(gradeClass_type=2)&Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)
    stat.show = 0
    i = 0
    q = None
    if len(regShow) > 0:
        for student in regShow:
            if i == 0:
                q = Q(students=student.id)
            else:
                q = q|Q(students=student.id)
            i = i + 1
            
        regShowDate = GradeClass.objects.filter(queryRegShowDate&(q))
        
        temp = 0.0
        for gc in regShowDate:
            for student in gc.students:
                res,co_t = BFshare(student)
                temp = temp + res
        #拜访到场
        stat.show = round(temp,1)
        
    queryRegDeal = queryReg&Q(status__ne=0)
    regDeal = Student.objects.filter(queryRegDeal)
    #print regDeal._query
    if str(teacher.id) == '5a14fb0097a75dc36adba67f':
        print 'niu'
        #print len(regDeal)
    stat.deal = 0
    stat.refund = 0
    for student in regDeal:
        
        has = False
        hasEarly = False
        if student.contract and len(student.contract)>0:
            for c in student.contract:
                try: 
                    if c.singDate >= searchBegin and c.singDate < searchEnd and c.status != 4 and c.multi == constant.MultiContract.newDeal:
                        
                        res,co_t = BFshare(student)
                        
                        stat.deal = stat.deal + res
                        
                        if c.status == constant.ContractStatus.refund:
                            stat.refund = stat.refund + 1
                        break
                except:
                    err = 1             
    #老师招生
    stat.deal = round(stat.deal,1)
              
    queryDemoTeacher = Q(teacher=teacher.id)&Q(demoIsFinish=1)&Q(gradeClass_type=2)
    queryDemoTeacherDate = queryDemoTeacher&Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)
    demo = GradeClass.objects.filter(queryDemoTeacherDate)
    
    #试听课
    stat.demo = len(demo)
    
    stat.demoDeal = 0
    demoDealStudents = []
    allDemo = GradeClass.objects.filter(queryDemoTeacher)
    for d in allDemo:
        if d.students and len(d.students) > 0:
            for s in d.students:
              if str(s.id) not in demoDealStudents:  
                try:  
                  if s.contract and len(s.contract) > 0:
                    for c in s.contract:
                        if c.status != 4 and c.multi == constant.MultiContract.newDeal and c.singDate >= searchBegin and c.singDate < searchEnd:
                            
                            stat.demoDeal = stat.demoDeal + 1
                            demoDealStudents.append(str(s.id))

                except:
                  err = 1
                  
    
    queryRefer = Q(regTeacher=str(teacher.id))&Q(contract__ne=None)&Q(sourceType='C')
    refer = 0
    try:
      refers = Student.objects.filter(queryRefer)
      
      for r in refers:
        for c in r.contract:
            if c.status != 4 and c.multi == constant.MultiContract.newDeal:
                if c.singDate >= searchBegin and c.singDate <= searchEnd:
                    if str(teacher.id) == '5a14fb0097a75dc36adba67f':
                        print '[niu refer]'+c.student_oid
                    refer = refer + 1
                    break
                
    except Exception,e:
        print e
        err = 1
    #转介成交
    stat.refer = refer
    if stat.demo > 0:
        #成交率
        stat.dealRatio = int(round((float)(stat.demoDeal)/(float)(stat.demo)*100,0))
    return stat

#老师个人数据统计
def teacherReg0(teacher,searchBegin,searchEnd):
    stat = UserStat()
    #branch all show
    #queryShow = Q(teacher=teacher)&Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(demoIsFinish=1)&Q(gradeClass_type=2)
    query = (Q(regTeacher=teacher.id)|Q(co_teacher=str(teacher.id)))&(Q(sourceType='B')|Q(sourceType='C'))
    queryDate = (query)&Q(callInTime__gte=searchBegin)&Q(callInTime__lt=searchEnd)
    
    temp = 0.0
    reg = Student.objects.filter(queryDate)

    for student in reg:

        n = 0
        yes = False
        if student.regTeacher:
            n = 1
        if student.co_teacher and len(student.co_teacher)>0:
            n = n + len(student.co_teacher)
        temp = temp + 1/float(n)
    #print 'got reg'
    stat.reg = round(temp,1)
    #print stat.reg
    
    temp = 0.0
    regAll = Student.objects.filter(query)
    queryDemo = Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(demoIsFinish=1)
    queryStudent = None
    i = 0
    for s in regAll:
        if i == 0:
            queryStudent = Q(students=s.id)
        else:
            queryStudent = queryStudent|Q(students=s.id)
        i = i + 1
    queryDemoAll = queryDemo&(queryStudent)
    allDemos = []
    if i > 0:
        allDemos = GradeClass.objects.filter(queryDemoAll)
    dateDemos = []
    queryStudent = None
    i = 0
    for s in reg:
        if i == 0:
            queryStudent = Q(students=s.id)
        else:
            queryStudent = queryStudent|Q(students=s.id)
        i = i + 1
    if i > 0:
        queryDemoDate = queryDemo&(queryStudent)
        dateDemos = GradeClass.objects.filter(queryDemoDate)
        
    for demo in allDemos:
        n = 0
        yes = False
        try:
          if demo.students and len(demo.students)>0:
            s = demo.students[0]
            if s.regTeacher:
                n = 1
            if s.regTeacher == teacher and s.sourceType == 'B':
                yes = True
            if s.co_teacher and len(s.co_teacher)>0:
                n = n + len(s.co_teacher)
            if teacher in s.co_teacher and s.sourceType == 'B':
                yes = True
            if yes:
                temp = temp + 1/float(n)
        except:
            err = 1
    stat.show = round(temp,1)
    #print 'got show'
    temp = 0.0
    
    for demo in dateDemos:
        n = 0
        yes = False
        try:
          if demo.students and len(demo.students)>0:
            s = demo.students[0]
            if s.regTeacher:
                n = 1
            if s.regTeacher == teacher and s.sourceType == 'B':
                yes = True
            if s.co_teacher and len(s.co_teacher)>0:
                n = n + len(s.co_teacher)
            if teacher in s.co_teacher and s.sourceType == 'B':
                yes = True
            if yes:
                temp = temp + 1/float(n)
        except:
            err = 1
    stat.demo = round(temp,1)#漏斗数据
    #print 'got demo'
    return stat
    
#老师个人数据统计
def teacherStat(teacher,searchBegin,searchEnd,reg,show,deal,refund,net=None,excludeContract=None):
    stat = UserStat()
    #branch all show
    queryShow = Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(demoIsFinish=1)&Q(gradeClass_type=2)
    if net != '1':
        #teacher demo
        queryDemo = queryShow&Q(teacher=teacher.id)
        demos = GradeClass.objects.filter(queryDemo)
        stat.demo = len(demos)
        demoDeal = 0
    
    temp = 0.0
    for student in reg:
        n = 0
        yes = False
        if student.regTeacher:
            n = 1
            if student.regTeacher == teacher:
                yes = True
        if student.co_teacher and len(student.co_teacher)>0:
            n = n + len(student.co_teacher)
            if teacher in student.co_teacher:
                yes = True
        if yes:
            temp = temp + 1/float(n)
        
    stat.reg = round(temp,1)
    
    temp = 0.0
    for demo in show:
        n = 0
        yes = False
        try:
          if demo.students and len(demo.students)>0:
            s = demo.students[0]
            if s.regTeacher:
                n = 1
            if s.regTeacher == teacher and s.sourceType == 'B':
                yes = True
            if s.co_teacher and len(s.co_teacher)>0:
                n = n + len(s.co_teacher)
            if teacher in s.co_teacher and s.sourceType == 'B':
                yes = True
            if yes:
                temp = temp + 1/float(n)
        except:
            err = 1
    stat.show = round(temp,1)
    
    temp = 0.0

    i = 0
    sc = []
    for contract in deal:
        
        try:
            student = Student.objects.get(id=contract.student_oid)
            if student.demo and len(demo)>0:
                for d in student.demo:
                    demo = GradeClass.objects.get(id=d)
                    if demo and demo.teacher == teacher and demo.demoIsFinish == 1:
                        demoDeal = demoDeal + 1
            i = i + 1
            yes = False

            n = 0
            if student.regTeacher:
                n = 1
            if student.regTeacher == teacher and student.sourceType == 'B':
                yes = True
                
                
            if student.co_teacher and len(student.co_teacher) > 0:
                n = n + len(student.co_teacher)
                if teacher in student.co_teacher and student.sourceType == 'B':
                    yes = True

            if yes:
                if student not in sc:
                    sc.append(student)
                    temp = temp + 1 / float(n)
                    
        except Exception,e:
            student = None
    stat.deal = round(temp,1)
    stat.demoDeal = demoDeal
    temp = 0
    if stat.demo > 0:
        stat.dealRatio = int(round((float)(stat.demoDeal)/(float)(stat.demo)*100,0))
    
    query = Q(regTeacher=str(teacher.id))&Q(contract__ne=None)&Q(sourceType='C')
    refer = 0
    try:
      refers = Student.objects.filter(query)
      
      for r in refers:
        for c in r.contract:
            if c.status != 4:
                if c.singDate >= searchBegin and c.singDate <= searchEnd:
                    refer = refer + 1
                    break
                
    except Exception,e:
        print e
        err = 1
    stat.refer = refer  
    return stat

#校区渠道统计
def branchSourceStat(branch,searchBegin,searchEnd):
    sources = Source.objects.filter(branch=branch.id).filter(deleted__ne=1)
    temp = []
    for source in sources:
        stat = UserStat(title=source.sourceName)
        stat.sid = source.id
        stat.deal = 0
        stat.demo = 0
        stat.show = 0
        stat.refund = 0
        queryReg = Q(regBranch=branch.id)&Q(source=source.id)&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
        regs = Student.objects.filter(queryReg).order_by("-callInTime")
        stat.reg = len(regs)
        temp.append(stat)
    statA = UserStat(title=u'校区渠道总计')
    statA.type = 1
    statA.isSum = 1
    statA.deal = 0
    statA.demo = 0
    statA.show = 0
    statA.refund = 0
    queryReg = Q(regBranch=branch.id)&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
    regs = Student.objects.filter(queryReg).order_by("-callInTime")
    statA.reg = len(regs)
    statB = UserStat(title=u'拜访合计')
    statB.type = 1
    statB.deal = 0
    statB.demo = 0
    statB.show = 0
    statB.refund = 0
    queryReg = Q(regBranch=branch.id)&Q(sourceType='B')&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
    regs = Student.objects.filter(queryReg).order_by("-callInTime")
    statB.reg = len(regs)
    statC = UserStat(title=u'转介')
    statC.type = 1
    statC.deal = 0
    statC.demo = 0
    statC.show = 0
    statC.refund = 0
    queryReg = Q(regBranch=branch.id)&Q(sourceType='C')&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
    regs = Student.objects.filter(queryReg).order_by("-callInTime")
    statC.reg = len(regs)
    statD = UserStat(title=u'社会')
    statD.type = 1
    statD.deal = 0
    statD.demo = 0
    statD.show = 0
    statD.refund = 0
    queryReg = Q(regBranch=branch.id)&Q(sourceType='D')&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
    regs = Student.objects.filter(queryReg).order_by("-callInTime")
    statD.reg = len(regs)
    
    queryDeal = Q(branch=branch.id)&Q(singDate__gte=searchBegin)&Q(singDate__lt=searchEnd)&(Q(status__ne=4))&Q(multi=constant.MultiContract.newDeal)
    deals = Contract.objects.filter(queryDeal)

    queryDemo = Q(branch=branch.id)&Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(demoIsFinish=1)
    demos = GradeClass.objects.filter(queryDemo)
    for c in deals:
        try:
            student = Student.objects.get(id=c.student_oid)
            
            if student.regBranch.id == branch.id:
                query = Q(student_oid=c.student_oid)&Q(singDate__lt=searchBegin)&Q(status__ne=4)
                existContracts = Contract.objects.filter(query)
                if len(existContracts) == 0:
                    statA.deal = statA.deal + 1
            if student.sourceType == 'B':
                query = Q(student_oid=c.student_oid)&Q(singDate__lt=searchBegin)&Q(status__ne=4)
                existContracts = Contract.objects.filter(query)
                if len(existContracts) == 0:
                    statB.deal = statB.deal + 1
            elif student.sourceType == 'C':
                query = Q(student_oid=c.student_oid)&Q(singDate__lt=searchBegin)&Q(status__ne=4)
                existContracts = Contract.objects.filter(query)
                if len(existContracts) == 0:
                    statC.deal = statC.deal + 1
            elif student.sourceType == 'D':
                query = Q(student_oid=c.student_oid)&Q(singDate__lt=searchBegin)&Q(status__ne=4)
                existContracts = Contract.objects.filter(query)
                if len(existContracts) == 0:
                    statD.deal = statD.deal + 1
            
            for stat in temp:
                if student.source.id == stat.sid:
                    if c.status != 4:
                        query = Q(student_oid=c.student_oid)&Q(singDate__lt=searchBegin)&Q(status__ne=4)
                        existContracts = Contract.objects.filter(query)
                        if len(existContracts) == 0:                        
                            stat.deal = stat.deal + 1
                            
                    if c.status == 2:
                        stat.refund = stat.refund + 1
        except Exception,e:
            err =1 
    
    for demo in demos:
        try:
            if demo.students and len(demo.students)>0:
                s = demo.students[0]
                
                if type(s).__name__=='Student' and s.regBranch.id == branch.id:
                    statA.show = statA.show + 1
                if type(s).__name__=='Student' and s.sourceType == 'B':
                    statB.show = statB.show + 1
                if type(s).__name__=='Student' and s.sourceType == 'C':
                    statC.show = statC.show + 1
                elif type(s).__name__=='Student' and s.sourceType == 'D':
                    statD.show = statD.show + 1
                else: 
                  for stat in temp:
                    if type(s).__name__=='Student' and str(s.source.id) == str(stat.sid):
                    
                        stat.show = stat.show + 1
                        
        except:
            err = 1
    temp.append(statB)
    temp.append(statC)
    temp.append(statD)
    temp.append(statA)
    return temp

#网络部渠道数据统计
def getNetBranSourceStat(branch,searchBegin,searchEnd):
    query = Q(branch=branch)&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
    regs = Student.objects.filter(query)
    
    #print regs.count()
    valid = 0
    for r in regs:
        if r.netStatus != 1:
            valid = valid + 1
    #print 'valid'
    #print valid
    
    
    queryDemo = Q(branch=branch)&Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(gradeClass_type=2)
    demos = GradeClass.objects.filter(queryDemo)
    
    #print demos._query
    #print demos.count()
    queryDeal = Q(branch=branch)&Q(singDate__gte=searchBegin)&Q(singDate__lt=searchEnd)&Q(status__ne=4)&Q(multi=constant.MultiContract.newDeal)
    deals = Contract.objects.filter(queryDeal)
    #print 'deals'
    #print deals.count()
    
    qq = Q(branch=constant.NET_BRANCH)
    scs = SourceCategory.objects.filter(qq)
    temp = []
    for sc in scs:
        stat = UserStat(title=sc.categoryName)
        stat.sc = sc.id
        stat.sid = sc.id
        stat.code = sc.categoryCode
        stat.deal = 0
        stat.demo = 0
        stat.show = 0
        stat.refund = 0
        stat.reg = 0
        stat.regValid = 0
        temp.append(stat)
    
    for student in regs: 
        try:
            for stat in temp:
                if student.sourceCategory.id == stat.sid:
                    stat.reg = stat.reg + 1 
                    if student.netStatus != -1:
                        stat.regValid = stat.regValid + 1                        
        except Exception,e:
            err =1
    
    for demo in demos:  
        try:
            student = demo.students[0]
            for stat in temp:
                if student.sourceCategory.id == stat.sid and student.netStatus != -1:
                    if demo.demoIsFinish==1:
                        stat.show = stat.show + 1
                    if demo.demoIsFinish != -1:
                        stat.demo = stat.demo + 1                           
        except Exception,e:
            err =1
    for c in deals:  
        try:
            student = Student.objects.get(id=c.student_oid)
            for stat in temp:
                if student.sourceCategory.id == stat.sid:
                    stat.deal = stat.deal + 1                           
        except Exception,e:
            err =1
    return temp

#网络部渠道数据统计
def getNetSourceStat(NET_BRANCH,city,searchBegin,searchEnd,excludeContract=None,branch=None,headquarter=None):
    branches = []
    if branch:
        branches.append(branch)
    else:
        queryBranch = Q(city=city)&Q(type__ne=1)&Q(sn__lt=9000)
        branches = Branch.objects.filter(queryBranch)  # @UndefinedVariable
    query = Q(deleted__ne=1)
    qq = None

    if headquarter == 'all':
        qu = Q(type=1)&Q(city=city)
        headbranches = Branch.objects.filter(qu) # @UndefinedVariable\

        i = 0
        for b in headbranches:
            if i == 0:
                qq = Q(branch=b.id)
            else:
                qq = qq|Q(branch=b.id)
            i = i + 1
        query = query&(qq)
    else:    
        query = query&Q(branch=NET_BRANCH)
        qq = Q(branch=NET_BRANCH)
    sources = Source.objects.filter(query)
    scs = SourceCategory.objects.filter(qq)

    
    queryDeal = Q(branch__in=branches)&Q(singDate__gte=searchBegin)&Q(singDate__lt=searchEnd)&Q(status__ne=4)&Q(multi=constant.MultiContract.newDeal)
    deals = Contract.objects.filter(queryDeal)
    queryDealRefund = Q(branch__in=branches)&Q(endDate__gte=searchBegin)&Q(endDate__lt=searchEnd)&Q(status=2)
    dealsRefund = Contract.objects.filter(queryDealRefund)
    queryDemo = Q(branch__in=branches)&Q(start_date__gte=searchBegin)&Q(start_date__lt=searchEnd)&Q(demoIsFinish__ne=-1)
    demos = GradeClass.objects.filter(queryDemo)    
    
    temp = []
    temp2 = []
    if headquarter != 'all' or NET_BRANCH == None:
      for sc in scs:
        stat = UserStat(title=sc.categoryName)
        stat.sc = sc.id
        stat.sid = ''
        stat.code = sc.categoryCode
        stat.deal = 0
        stat.demo = 0
        stat.show = 0
        stat.refund = 0
        stat.reg = 0
        stat.regValid = 0
        temp2.append(stat)
    for source in sources:
        stat = UserStat(title=source.sourceName)
        stat.sid = source.id
        stat.sc = source.categoryCode
        try:
            co = SourceCategory.objects.get(id=source.categoryCode)
            stat.code = co.categoryCode
        except:
            stat.code = ''
        stat.deal = 0
        stat.demo = 0
        stat.show = 0
        stat.refund = 0
        
        if headquarter == 'all':
            qq = None
            i = 0
            for b in headbranches:
                if i == 0:
                    qq = Q(regBranch=b.id)
                else:
                    qq = qq|Q(regBranch=b.id)
            i = i + 1
        else:
            qq = Q(regBranch=NET_BRANCH)
        queryReg = (qq)&Q(source=source.id)&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
        if branch:
            queryReg = queryReg&Q(branch=branch.id)
        regs = Student.objects.filter(queryReg).order_by("-callInTime")

        queryRegValid = queryReg&Q(netStatus__ne=-1)
        regsValid = Student.objects.filter(queryRegValid)
        stat.reg = len(regs)
        stat.regValid = len(regsValid)
        
        temp.append(stat)
    
    temp = sorted(temp, key=attrgetter('code'),reverse=False)
    
    for c in deals:  
        try:
            student = Student.objects.get(id=c.student_oid)
            regBranch = student.regBranch

            if headquarter == 'all' and regBranch.type == 1 or headquarter != 'all' and str(regBranch.id) == NET_BRANCH:
              for stat in temp:
                if student.source.id == stat.sid:
                    
                    stat.deal = stat.deal + 1
                                
        except Exception,e:
            err =1 

    for c in dealsRefund:  
        try:
            student = Student.objects.get(id=c.student_oid)
            regBranch = student.regBranch
            if headquarter == 'all' and regBranch.type == 1 or headquarter != 'all' and str(regBranch.id) == NET_BRANCH:
              for stat in temp:
                if student.source.id == stat.sid:
                    stat.refund = stat.refund + 1
 
        except Exception,e:
            err =1 
    
    sts = []
    for demo in demos:
        try:
            if demo.students and len(demo.students)>0:
                s = demo.students[0]
                for stat in temp:
                    if type(s).__name__=='Student' and str(s.source.id) == str(stat.sid) and s.netStatus != -1:
                    #sts.append(s)
                    
                        if demo.demoIsFinish != -1:
                            #if str(s.source.id) == '5888557f97a75d6f9fa8cf88' or str(s.source.id) == '58dceab097a75d2479929e43':
                             #   print s.id
                            stat.demo = stat.demo + 1
                        if demo.demoIsFinish == 1:
                            
                            stat.show = stat.show + 1
        except Exception,e:
            err =1
    statAll = UserStat(title=u'渠道总计')
    statAll.type = 1
    statAll.isSum = 1
    statAll.deal = 0
    statAll.demo = 0
    statAll.refund = 0
    statAll.reg = 0
    statAll.regValid = 0
    statAll.show = 0
    for stat in temp:
        stat.dealPure = stat.deal - stat.refund
    for stat in temp2:
        for s in temp:
            s1 = 's1'
            s2 = 's2'
            try:
                s1 = str(stat.sc)
                s2 = str(s.sc)
            except:
               err = 1
            if s1 == s2:
                stat.reg = stat.reg + s.reg
                stat.regValid = stat.regValid + s.regValid
                stat.demo = stat.demo + s.demo
                stat.show = stat.show + s.show
                stat.deal = stat.deal + s.deal
                    
                stat.refund = stat.refund + s.refund
                statAll.reg = statAll.reg + s.reg
                statAll.regValid = statAll.regValid + s.regValid
                statAll.demo = statAll.demo + s.demo
                statAll.show = statAll.show + s.show
                statAll.deal = statAll.deal + s.deal
                statAll.refund = statAll.refund + s.refund
        stat.dealPure = stat.deal - stat.refund
    statAll.dealPure = statAll.deal - statAll.refund
    temp2.append(statAll)
    
    return temp2,temp
#老师拜访统计－漏斗数据
def teacherReg2(city,searchBegin,searchEnd):
    if not city:
        city = constant.BEIJING
    query = Q(city=city)&Q(sn__ne=0)&Q(sn__ne=9000)
    branches = Branch.objects.filter(query)  # @UndefinedVariable
    query = Q(branch=branches[0].id)
    i = 0
    for b in branches:
        if i > 0:
            query = query|Q(branch=b.id)
        i = i + 1
    query = (query)&Q(sourceType='B')&Q(regTime__gte=searchBegin)&Q(regTime__lte=searchEnd)&Q(regTeacher__ne=None)
    students = Student.objects.filter(query)
    ts = []
    for student in students:
        temp = 0
        if student.regTeacher:
            temp = len(student.co_teacher)+1
        else:
            temp = len(student.co_teacher)

        tid = student.regTeacher.id

        exist = [t for t in ts if t.id == tid]
        if len(exist) == 0:
            t = Teacher(id=tid)
            t.value = 1/float(temp)
            t.show = 0
            t.name=student.regTeacher.name
            t.branchName=student.regTeacher.branch.branchName
 
            ts.append(t)
        else:
            exist[0].value = exist[0].value + 1/float(temp)
        for tr in student.co_teacher:
            tid = tr.id

            exist = [t for t in ts if t.id == tid]
            if len(exist) == 0:
                t = Teacher(id=tid)
                t.value = 1/float(temp)
                t.show = 0
                t.name=tr.name
                t.branchName = tr.branch.branchName
            
                ts.append(t)
            else:
                exist[0].value = exist[0].value + 1/float(temp)
    
        if student.isDemo == 1 and len(student.demo) > 0:
                 try:
                         tid = student.regTeacher.id
                         exist = [t for t in ts if t.id == tid]
                         exist[0].show = exist[0].show + 1/float(temp)
                         for tr in student.co_teacher:
                             tid = tr.id
                             exist = [t for t in ts if t.id == tid]
                             exist[0].show = exist[0].show + 1/float(temp)
                 except:
                     err = 1
    ts = sorted(ts, key=attrgetter('value'),reverse=True)
      
    return ts
            

#拜访统计
def teacherReg(city,searchBegin,searchEnd):
    if not city:
        city = constant.BEIJING
    query = Q(city=city)&Q(sn__ne=0)&Q(sn__ne=9000)
    branches = Branch.objects.filter(query)  # @UndefinedVariable
    query = Q(branch=branches[0].id)
    i = 0
    for b in branches:
        if i > 0:
            query = query|Q(branch=b.id)
        i = i + 1
    query = (query)&Q(sourceType='B')&Q(regTime__gte=searchBegin)&Q(regTime__lte=searchEnd)&Q(regTeacher__ne=None)
    students = Student.objects.filter(query).order_by("regTeacher")
    res = []
    last = None
    t = None
    for s in students:
        if s.regTeacher != last and last != None:
            res.append(last)
            last = s.regTeacher
            last.value = 0
        if last == None:
            last = s.regTeacher
            last.value = 0
        last.value = last.value + 1
    res.append(last)
    return res
 
def checkDup():
    kids = Student.objects.all()
    temp = []
    i = 0
    try:
      for k in kids:
      
        if k.prt1mobile in temp:

            i = i + 1
        else:
            temp.append(k.prt1mobile)
    except:
        err  = 1   

def getChannelBranchStat(channel,branch,searchBegin,searchEnd):
    queryDeal = Q(branch=branch.id)&Q(singDate__gte=searchBegin)&Q(singDate__lt=searchEnd)&(Q(status__ne=4))&Q(multi=constant.MultiContract.newDeal)&Q(paid__gte=3000)
    deals = Contract.objects.filter(queryDeal)
    #if str(channel.id) == '5888555497a75d6f9fa8cf86': 
     #   print deals._query
        #print deals.count()
    
    queryDemo = Q(branch=branch.id)&Q(start_date__gte=searchBegin)&Q(start_date__lte=searchEnd)
    demos = GradeClass.objects.filter(queryDemo)
    
    queryReg = Q(regBranch=constant.NET_BRANCH)&Q(sourceCategory=channel.id)&Q(callInTime__gte=searchBegin)&Q(callInTime__lte=searchEnd)
    queryReg = queryReg&Q(branch=branch.id)
    regs = Student.objects.filter(queryReg).order_by("-callInTime")

    queryRegValid = queryReg&Q(netStatus__ne=-1)
    regsValid = Student.objects.filter(queryRegValid)
    
    queryDealRefund = Q(branch=branch.id)&Q(endDate__gte=searchBegin)&Q(endDate__lt=searchEnd)&Q(status=2)&Q(multi=constant.MultiContract.newDeal)&Q(paid__gte=3000)
    dealsRefund = Contract.objects.filter(queryDealRefund)
    
    stat = UserStat()
    stat.demo = 0
    stat.show = 0
    stat.deal = 0
    stat.reg = regs.count()
    stat.regValid = regsValid.count()
    stat.oid = channel.id
    stat.title = branch.branchName
    stat.dealPure = 0
    stat.refund = 0
    for demo in demos:  
        try:
            student = demo.students[0]
            if student.sourceCategory.id == stat.oid and student.netStatus != -1:
                    if demo.demoIsFinish==1:
                        stat.show = stat.show + 1
                        
                    if demo.demoIsFinish != -1:
                        stat.demo = stat.demo + 1
                        #if str(channel.id) == '5888555497a75d6f9fa8cf86':
                         #   print student.id                           
        except Exception,e:
            err =1
    for c in deals:  
        try:
            student = Student.objects.get(id=c.student_oid)
            if student.sourceCategory.id == stat.oid:
                stat.deal = stat.deal + 1                           
        except Exception,e:
            err =1
    
    for c in dealsRefund:  
        try:
            student = Student.objects.get(id=c.student_oid)
            if student.sourceCategory.id == stat.oid:
                    stat.refund = stat.refund + 1                           
        except Exception,e:
            err =1
    stat.dealPure = stat.deal - stat.refund
    return stat
    
    
if __name__ == "__main__":
    searchBegin = datetime.datetime.strptime('2017-08-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    searchEnd = datetime.datetime.strptime('2017-08-31 00:00:00',"%Y-%m-%d %H:%M:%S")
    checkDup()