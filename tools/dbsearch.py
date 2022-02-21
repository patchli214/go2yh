#!/usr/bin/env python
# -*- coding:utf-8 -*-
#from numpy import False_
from datetime import timedelta
from tools.utils import getDateNow
import student
from tools.constant import GradeClassType
from branch.models import City, Branch
import time
from contract.models import Income
__author__ = 'patch'
import constant,utils,datetime
from mongoengine.queryset.visitor import Q
from teacher.models import Teacher
from regUser.models import Student,TeacherRemind,Contract,ContractType,GradeClass
from gradeClass.models import Lesson
from statistic.models import BranchIncome
from operator import attrgetter
from statistic.models import LessonCheck
#假期班合同类型
def getHolidayContractType(city):
    query = Q(type=1)
    if city:
        query = query&Q(city=city.id)
    cts = ContractType.objects.filter(query) # @UndefinedVariable
    query = None
    i = 0
    for ct in cts:
        if i == 0:
            query = Q(contractType=ct.id)
        else:
            query = query|Q(contractType=ct.id)
        i = i + 1
    query = (query)
    return cts,query

#常规班合同类型及查询语句
#20200715--去掉网课类型
def getNormalContractTypes(city,valid=False):
    query = Q(type__ne=constant.ContractType.hc)&Q(type__ne=constant.ContractType.free)&Q(type__ne=constant.ContractType.onlineCourse)
    if city:
        query = query&Q(city=city.id)
    if valid:
        query = query&Q(deleted__ne=1)
    cts = ContractType.objects.filter(query).order_by("city","code")  # @UndefinedVariable
    query = None
    i = 0
    for ct in cts:
        print ct.code
        if i == 0:
            query = Q(contractType=ct.id)
        else:
            query = query|Q(contractType=ct.id)
        i = i + 1
    query = (query)
    return cts,query

#会员费合同类型查询
def getMemberFeeContractTypes(city,valid=False):
    query = Q(type=3)
    if city:
        query = query&Q(city=city.id)
    if valid:
        query = query&Q(deleted__ne=1)
    cts = ContractType.objects.filter(query).order_by("city","code")  # @UndefinedVariable
    query = None
    i = 0
    for ct in cts:
        if i == 0:
            query = Q(contractType=ct.id)
        else:
            query = query|Q(contractType=ct.id)
        i = i + 1
    query = (query)
    return cts,query


#赠课合同类型及查询语句
def getFreeContractTypes(city):
    query = Q(type=2)
    if city:
        query = query&Q(city=city.id)

    cts = ContractType.objects.filter(query)  # @UndefinedVariable
    query = None
    i = 0
    for ct in cts:
        if i == 0:
            query = Q(contractType=ct.id)
        else:
            query = query|Q(contractType=ct.id)
        i = i + 1
    query = (query)
    return cts,query

#获取集训班合同
def getBranchDealHoliday(branch,beginDate,endDate,holidayCT):
    queryDeal = Q(singDate__gte=beginDate)&Q(singDate__lte=endDate)&Q(status=0)&Q(contractType=holidayCT.id)
    if branch:
        queryDeal = queryDeal&Q(branch=branch)
    deal = Contract.objects.filter(queryDeal).order_by("-singDate")  # @UndefinedVariable
    return deal
 #获取集训班合同，包括网络
def getBranchDealHolidayNet(cityHeadquarter,branch,beginDate,endDate,holidayCT):
    holidayDeal = getBranchDealHoliday( branch, beginDate, endDate, holidayCT)
    holidayDealNet = []
    for c in holidayDeal:
        try:
            student = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
            if student and str(student.regBranch.id)==cityHeadquarter and student.netStatus != -1:
                holidayDealNet.append(c)
        except:
            student = None
    return holidayDeal,holidayDealNet

#获取常规班合同
def getBranchDealNormal(branch,beginDate,endDate,ctQuery):
    query = Q(singDate__gte=beginDate)&Q(singDate__lte=endDate)&Q(status=0)
    if ctQuery:
        query = query&ctQuery
    if branch:
        query = query&Q(branch=branch)
    deal = Contract.objects.filter(query).order_by("-singDate")  # @UndefinedVariable
    return deal
#获取常规班合同，包括网络
def getBranchDealNormalNet(cityHeadquarter,branch,beginDate,endDate,ctQuery):
    deal = getBranchDealNormal( branch, beginDate, endDate, ctQuery)
    dealNet = []
    for c in deal:
        try:
            student = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
            if student and str(student.regBranch.id)==cityHeadquarter and student.netStatus != -1:
                dealNet.append(c)
        except:
            student = None
    return deal,dealNet

#新生
def getBranchDealNew(branch,beginDate,endDate,ctQuery):
    b = None
    deal = None
    try:
        try:
            b = Branch.objects.get(id=branch)  # @UndefinedVariable
        except:
            b = Branch.objects.get(id=branch.id)  # @UndefinedVariable
        city = City.objects.get(id=b.city.id)  # @UndefinedVariable
        query = Q(singDate__gte=beginDate)&Q(singDate__lte=endDate)&Q(status__ne=constant.ContractStatus.delete)&(Q(multi=constant.MultiContract.newDeal))
        #query = query&Q(weeks__gte=city.dealDuration)
        query = query&Q(paid__gte=1000)
    #if ctQuery:
     #   query = query&ctQuery
        if branch:
            query = query&Q(branch=branch)
        deal = Contract.objects.filter(query).order_by("-singDate")  # @UndefinedVariable
    except Exception,e:
        print e
        err = 1
    return deal

#新生续费统计
def getBranchDealNew_redeal(branch,beginDate,endDate,ctQuery):
    deals = getBranchDealNew(branch,beginDate,endDate,ctQuery) #全部新生
    if not deals:
        deals = []
    i = 0
    studentsDone = [] #完成续费
    students = [] #全部续费目标

    for c in deals:

        if c.student_oid not in students:
            students.append(c.student_oid)
        if c.weeks >= constant.CONTRACT_DONE: #新生合同直接完成的
            if c.student_oid not in studentsDone:
                studentsDone.append(c.student_oid)
        else:
            query = Q(student_oid=c.student_oid)&Q(status__ne=constant.ContractStatus.delete)&Q(singDate__gte=beginDate)
            cs = Contract.objects.filter(query)  # @UndefinedVariable
            all = 0
            for c in cs:
                all = all + c.weeks
            if all >= constant.CONTRACT_DONE: #多个合同合计完成
                if c.student_oid not in studentsDone:
                    studentsDone.append(c.student_oid)

    return students,studentsDone

#老生续费统计
def getBranchDealOld_redeal(branch,beginDate,endDate,ctQuery):
    b = None
    deal = None
    try:
        try:
            b = Branch.objects.get(id=branch)  # @UndefinedVariable
        except:
            b = Branch.objects.get(id=branch.id)  # @UndefinedVariable
        #city = City.objects.get(id=b.city.id)  # @UndefinedVariable
        query = Q(singDate__gte=beginDate)&Q(singDate__lte=endDate)&Q(status__ne=constant.ContractStatus.delete)&(Q(multi=constant.MultiContract.oldRedeal))
        query = query&Q(weeks__gte=constant.OLD_REDEAL_DONE)
    #if ctQuery:
     #   query = query&ctQuery
        if branch:
            query = query&Q(branch=branch)
        deal = Contract.objects.filter(query).order_by("-singDate")  # @UndefinedVariable
    except Exception,e:
        print e
        err = 1
    return deal


#新生，包括网络
def getBranchDealNewNet(searchBranchId,branch,beginDate,endDate,holidayCT,headquarter=None):
    deal = getBranchDealNew(branch, beginDate, endDate, holidayCT)
    dealNet = []
    students = []
    for c in deal:
        try:
            student = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
            if student not in students:
                students.append(student)
                if student and student.regBranch.type == 2 and headquarter == 'all':  #非校区来源的其他全部来源招生
                    dealNet.append(c)
                elif student and str(student.regBranch.id) == searchBranchId:#某个市场部门的来源招生，比如网络部、市场部，或者校区自己招生
                    dealNet.append(c)
        except:
            student = None
    return deal,dealNet

#续费
def getBranchDeal(branch,beginDate,endDate,ctQuery,multi):
    query = Q(singDate__gte=beginDate)&Q(singDate__lte=endDate)&Q(status=0)&Q(multi=multi)
    if ctQuery:
        query = query&ctQuery
    if branch:
        query = query&Q(branch=branch)
    deal = Contract.objects.filter(query).order_by("-singDate")  # @UndefinedVariable
    return deal
#续费，包括网络
def getBranchDealNet(cityHeadquarter,branch,beginDate,endDate,holidayCT,multi):
    deal = getBranchDeal(branch, beginDate, endDate, holidayCT,multi)
    dealNet = []
    for c in deal:
        try:
            student = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
            if student and str(student.regBranch.id)==cityHeadquarter and student.netStatus != -1:
                dealNet.append(c)
        except:
            student = None
    return deal,dealNet

def getBranchDealFree(branch,beginDate,endDate,freeCTquery):
    query = Q(singDate__gte=beginDate)&Q(singDate__lte=endDate)&Q(status=0)
    if freeCTquery:
        query = query&freeCTquery
    if branch:
        query = query&Q(branch=branch)
    deal = Contract.objects.filter(query).order_by("-singDate")  # @UndefinedVariable
    return deal

def getRemind(branch,searchBegin,searchEnd,teacherId=None):
    now = utils.getDateNow()
    queryTime = None
    if searchBegin:
        queryTime = Q(remindTime__gte=searchBegin)
    if searchEnd:
        if queryTime:
            queryTime = queryTime&Q(remindTime__lte=searchEnd)
        else:
            queryTime = Q(remindTime__lt=searchEnd)
    query = Q(branch=str(branch.id))&queryTime&Q(isDone__ne=1)
    if teacherId:
        query = query&Q(remindTeachers=teacherId)
    reminds = TeacherRemind.objects.filter(query).order_by("branch")  # @UndefinedVariable
    #===========================================================================
    # temp = []
    # if len(reminds) > 0:
    #     for r in reminds:
    #         try:
    #             s = Student.objects.get(id=r.student.id)  # @UndefinedVariable
    #             temp.append(r)
    #         except:
    #             r.delete()
    # reminds = temp
    #===========================================================================

    return reminds
#提醒校区的网络部数据数
def getRemindNet(branch,searchBegin,searchEnd,netBranchId=None):
    reminds = getRemind(branch,searchBegin,searchEnd)
    temp = []
    for r in reminds:
        try:
            regBranch = r.student.regBranch
            if netBranchId:
                if str(regBranch.id) == netBranchId:
                    temp.append(r)
            elif regBranch and regBranch.type == 1:
                temp.append(r)
        except:
            err = 1
    return temp

#提醒网络部的各校区数据跟踪数
def getRemindNetNet(branch,searchBegin,searchEnd,netBranchId):
    now = utils.getDateNow()
    queryTime = None
    if searchBegin:
        queryTime = Q(remindTime__gte=searchBegin)
    if searchEnd:
        if queryTime:
            queryTime = queryTime&Q(remindTime__lte=searchEnd)
        else:
            queryTime = Q(remindTime__lt=searchEnd)
    query = queryTime&Q(isDone__ne=1)
    if branch:
        query = query&Q(branch=str(branch.id))
    if netBranchId:
        teachers = Teacher.objects.filter(branch=netBranchId)  # @UndefinedVariable
        i = 0
        tq = None
        for t in teachers:
            if i == 0:
                tq = Q(remindTeachers=t.id)
            else:
                tq = tq|Q(remindTeachers=t.id)
            i = i + 1
        query = query&(tq)
    reminds = TeacherRemind.objects.filter(query)  # @UndefinedVariable
    return reminds

#获取所有曾经有效现在失效的合同,按结束日期倒序
def getPastValidContracts(studentId):
    query = Q(student_oid=studentId)&Q(status__ne=constant.ContractStatus.delete)
    contracts = Contract.objects.filter(query).order_by("-endDate")  # @UndefinedVariable
    return contracts

#检查是否有当前有效合同
def getNowValidContract(studentId,cid):
    query = Q(student_oid=studentId)&Q(status=constant.ContractStatus.sign)
    if cid:
        query = query&Q(id__ne=cid)
    contracts = Contract.objects.filter(query)  # @UndefinedVariable
    return contracts

#检查是否有当前有效的新生续费合同
def getNowValidNewRedealContract(studentId,cid):
    query = Q(student_oid=studentId)&Q(status=constant.ContractStatus.sign)&Q(multi=constant.MultiContract.newRedeal)
    if cid:
        query = query&Q(id__ne=cid)
    contracts = Contract.objects.filter(query)  # @UndefinedVariable
    return contracts

#检查是否有当前有效的老生续费合同
def getNowValidOldRedealContract(studentId,cid):
    query = Q(student_oid=studentId)&Q(status=constant.ContractStatus.sign)&Q(multi=constant.MultiContract.oldRedeal)
    if cid:
        query = query&Q(id__ne=cid)
    contracts = Contract.objects.filter(query)  # @UndefinedVariable
    return contracts

#检查是符合否新生续费、老生续费、新招生条件：给定签约日期，查询之前上过的收费合同课时数，如果少于5则认为是新生续费，否则老生。
#前一个结束合同结束日期后一年，算新招生
def checkMultiContractStatus(studentId,signDate,nowValidContracts,nrc,orc):
    hasNowValidContract = False #当前是否有有效合同
    isNewRedeal = False
    isOldRedeal = False
    isNew = False #新招生

    if nowValidContracts and len(nowValidContracts) > 0: #此学生存在有效合同

        hasNowValidContract = True
        isNew = False
        query = Q(student=studentId)&Q(lessonTime__lte=signDate)&(Q(type=1)|Q(type=3))&Q(value__gt=0)
        lessons = Lesson.objects.filter(query)  # @UndefinedVariable
        if lessons and len(lessons) > 4:
            isNewRedeal = False
            isOldRedeal = True

        else: #上课次数未超过4次，且上个合同有效期内\
            if (nrc and len(nrc)>0) or (orc and len(orc)>0):# 有续费合同
                isNewRedeal = False
                isOldRedeal = False
            else: #无续费合同，算新生续费
                isNewRedeal = True
                isOldRedeal = False
    else:
        hasNowValidContract = False
        isNewRedeal = False
        isOldRedeal = False
        pastValidContracts = getPastValidContracts(studentId)
        if pastValidContracts and len(pastValidContracts) > 0:
            pvc = pastValidContracts[0]
            try:
                if pvc.endDate + timedelta(days=constant.LAST_CONTRACT_EXPIRE_DAY) <= signDate:
                    isNew = True
                else: #非期限外，算老生续费
                    isNew = False
                    isOldRedeal = True
            except:
                isNew = False
        else:
            isNew = True

    return hasNowValidContract,isNewRedeal,isOldRedeal,isNew

def getMultiContracts(cityId):
    branches = utils.getCityBranch(cityId)

    for branch in branches:

        query = Q(status__ne=constant.ContractStatus.delete)&Q(branch=branch.id)
        cs = Contract.objects.filter(query).order_by('student_oid','singDate')  # @UndefinedVariable
        lastStudent = None
        lastContract = None
        i = 0
        j = 0
        for c in cs:

            if c.student_oid == lastStudent:
                i = i + 1


                try:
                    if i > 0:
                        j = j + 1

                        nowValidContracts = getNowValidContract(c.student_oid,c.id)
                        nrc = getNowValidNewRedealContract(c.student_oid,c.id)
                        orc = getNowValidOldRedealContract(c.student_oid,c.id)
                        hasNowValidContract,isNewRedeal,isOldRedeal,isNew = checkMultiContractStatus(c.student_oid, c.singDate,nowValidContracts,nrc,orc)
                        if isNewRedeal:
                            c.multi = constant.MultiContract.newRedeal
                        elif isOldRedeal:
                            c.multi = constant.MultiContract.oldRedeal
                        elif isNew:
                            c.multi = constant.MultiContract.newDeal
                    else:
                        c.multi = constant.MultiContract.newDeal

                    c.save()


                except:
                    err = 1

            else:
                i = 0
            if lastStudent == None:
                lastStudent = c.student_oid
            if i == 0:
                c.multi = constant.MultiContract.newDeal
                c.save()

            if c.student_oid != lastStudent and lastStudent != None:

                lastStudent = c.student_oid
                i = 0

            try:
                err = 0

            except:
                print 'ERR'
                err = 1
            lastContract = c

    print '[DONE]'

#获得时间区间内校区全部已上课程
def branchLessons(branchId,beginDate,endDate):
    if not beginDate or not endDate:
        return
    query = Q(branch=branchId)&Q(gradeClass_type=1)
    classes = GradeClass.objects.filter(query)  # @UndefinedVariable

    query = Q(lessonTime__lt=endDate)&Q(lessonTime__gte=beginDate)&(Q(type=1)|Q(type=3))&Q(checked=True)&Q(value__ne=0)&Q(student__ne=None)
    if classes and len(classes) > 0:
        queryClass = Q(gradeClass=classes[0].id)
    else:
        return
    i = 0
    for c in classes:
        if i > 0:
            queryClass = queryClass|Q(gradeClass=c.id)
        i = i + 1
    query = query&(queryClass)
    lessons = Lesson.objects.filter(query).order_by("student","-lessonTime")  # @UndefinedVariable

    return lessons

#获取学生全部合同，不包括集训班
#20190603--也不包括会员合同
def getStudentContracts(student_oid,exclude=None,holidayCT=None,endDate=None):
    student = Student.objects.get(id=student_oid)  # @UndefinedVariable

    memberCT = None
    notMemberCT = None
    try:
        query = Q(city=student.branch.city.id)&Q(type=constant.ContractType.memberFee)
        memberCTs = ContractType.objects.filter(query)# @UndefinedVariable

        memberCT = memberCTs[0]
        memberCT = Q(contractType=memberCTs[0].id)
        notMemberCT = Q(contractType__ne=memberCTs[0].id)
        i = 0
        for mct in memberCTs:
            if i > 0:
                memberCT = memberCT|Q(contractType=mct.id)
                notMemberCT = notMemberCT&Q(contractType__ne=mct.id)
            i = i + 1
    except Exception,e:
        print e
        memberCT = None



    #获取除集训外全部合同
    query = Q(student_oid=student_oid)&Q(status__ne=constant.ContractStatus.delete)
    if endDate:
        query = query&Q(singDate__lte=endDate)#endDate之后的合同不算
    if holidayCT:
        query = query&Q(contractType__ne=holidayCT.id)

    if notMemberCT:
        query = query&notMemberCT&Q(multi__ne=constant.MultiContract.memberLesson)
    contracts = Contract.objects.filter(query).order_by("singDate")  # @UndefinedVariable
    if student_oid == '594e0c3b97a75d6a95e08dab':
        print '[GOT THIS STUDENT CONTRACTS LEN]'
        print contracts._query
        print len(contracts)
    return contracts

#会员合同和季度学费合同查询，2019-06-03 增加截止日期
def MemberContracts(student_oid,cityId,endDate=None):

    query = Q(city=cityId)&Q(type=constant.ContractType.memberFee)
    memberCTs = ContractType.objects.filter(query)# @UndefinedVariable
    if student_oid == '5baa0431e5c5e649b67687fd':
            print memberCTs._query
    memberCT = memberCTs[0]
    memberCT = Q(contractType=memberCTs[0].id)

    i = 0
    for mct in memberCTs:
            if i > 0:
                memberCT = memberCT|Q(contractType=mct.id)

            i = i + 1
    query = Q(student_oid=student_oid)&(Q(status=constant.ContractStatus.refundWaiting)|Q(status=constant.ContractStatus.sign))
    query = query&Q(singDate__lte=endDate)
    q1 = query&(memberCT)&Q(multi__ne=constant.MultiContract.memberLesson)
    mcs = Contract.objects.filter(q1).order_by("singDate")  # @UndefinedVariable
    q2 = query&Q(multi=constant.MultiContract.memberLesson)&Q(paid__gt=0)
    mfs = Contract.objects.filter(q2).order_by("singDate")  # @UndefinedVariable
    #mcs--会员合同， mfs--季度学费合同
    return mcs,mfs

def getBeforeLessons(student_oid,searchDate):
    query0 = Q(student=student_oid)&Q(value__ne=0)&(Q(type=1)|Q(type=3))&Q(checked=True)
    query = query0&Q(lessonTime__lt=searchDate)
    lessonsBefore = Lesson.objects.filter(query)  # @UndefinedVariable
    return lessonsBefore

def getFirst4_2(before,this):
    first4 = 0
    if before >= 4:
        return 0,this
    thisValue = before + this - 4
    if thisValue < 0:
        first4 = before + this
        thisValue = 0
    else:
        first4 = 4
    return first4,thisValue


def getFirst4(lessonsBefore,lessons):
    first4 = 4 #如未上完四次课，头四次课累计
    lbvalue = 0 #beginDate以前消费课时
    lvalue = 0 #beginDate到endDate消费课时
    if lessonsBefore:
        for l in lessonsBefore:
            if l.value and l.value > 0:
                lbvalue = lbvalue + l.value
            elif not l.value:
                lbvalue = lbvalue + 1
    if lbvalue > 0:
        first4 = 4 - lbvalue
        if first4 < 0:
            first4 = 0

    for l in lessons: #本周期上过的课
            if l.value and l.value > 0:
                lvalue = lvalue + l.value
            elif not l.value:
                lvalue = lvalue + 1
    lvalue0 = lvalue #本周期上过总课数
    if first4 > 0 and lvalue > 0: #本周期前未上完4次课
        lvalue = lvalue - first4
        if lvalue < 0: #本周期结束还未上够4次课
            lvalue = 0
            first4 = lvalue0
    if lvalue0 <= 0:
        first4 = 0
    return first4,lvalue0,lbvalue

def contractGroup(cps,mcs=None,mfs=None):
    newWeeks = 0
    newPaid = 0.0
    consume = 0
    contracts = []
    clessons = [] #每个合同阶段的上课数
    lessons = 0
    firstNewDeal = None #新生合同
    firstNewRedeal = None #新生续费
    student_oid = None

    if len(cps) > 0:
    #for cp in cps:

        if cps[0].student_oid == '594e0c3b97a75d6a95e08dab':
            print '[got my boy22222222222]------------------'
        newDeal = None #新生合同
        newRedeal = None #新生续费
        ors = [] # 非送课合同
        fs = [] # 送课合同

        for c in cps:
            if not student_oid:
                student_oid = c.student_oid
            if student_oid == '594e0c3b97a75d6a95e08dab':
                print '[got my boy]------------------'
            if c.contractType and c.contractType.type == constant.ContractType.free:
                fs.append(c)
            elif c.multi == 0:
                newWeeks = c.weeks
                newPaid = c.paid
                if newDeal:
                    ors.append(c)
                else:
                    newDeal = c
                    if not firstNewDeal:
                        firstNewDeal = c
            elif c.multi == 1:
                if c.weeks:
                    c.weeks = c.weeks + newWeeks
                if c.paid:
                    c.paid = c.paid + newPaid
                if newRedeal:
                    ors.append(c)
                #elif c.contractType:
                else:
                    if not c.paid and c.contractType.discountPrice:
                        c.paid = c.contractType.discountPrice
                    if not c.weeks and c.contractType.duration:
                        c.weeks = c.contractType.duration

                    newRedeal = c
                    if newDeal:
                        newDeal.paid = 0
                        newDeal.weeks = 0
                    if not firstNewRedeal:
                        firstNewRedeal = c


            elif c.multi == 2:
                ors.append(c)
        if newDeal and not newRedeal:
            contracts.append(newDeal)
            lessons = lessons + newDeal.weeks
            clessons.append(lessons)
        if newRedeal:
            contracts.append(newRedeal)
            lessons = lessons + newRedeal.weeks
            clessons.append(lessons)
        if ors and len(ors)>0:
            for c in ors:
                contracts.append(c)
                lessons = lessons + c.weeks
                clessons.append(lessons)
        if fs and len(fs)>0:
            for c in ors:
                contracts.append(c)
                lessons = lessons + c.weeks
                clessons.append(lessons)
    mcLessons = 0
    mcPaid = 0
    mcg = None
    if student_oid == '594e0c3b97a75d6a95e08dab':
        print 'got my boy------------------'
        print len(cps)
    if len(mcs) > 0:
      if student_oid == '594e0c3b97a75d6a95e08dab':
            print 'got my boy 2------------------'
            print len(mcs)
      for mc in mcs:
          if not  mc.weeks:
              mc.weeks = mc.contractType.duration
          mcLessons = mcLessons + mc.weeks
          mcPaid = mcPaid + mc.paid
          mcg = mc
          mcg.paid = mcPaid
          mcg.weeks = mcLessons
      try:
          print mcg.weeks
      except:
          print mcg.id
      mfLessons = 0
      mfPaid = 0
      mfg = None
      for mf in mfs:
          mfLessons = mfLessons + mf.weeks
          mfPaid = mfPaid + mf.paid
          mfg = mf
      ml = None
    #有限会员合同
      if mfLessons <= mcLessons and mfLessons > 0:
          mfg.weeks = mfLessons
          mfg.paid = mfPaid + float(mcPaid)/float(mcLessons)*float(mfLessons)
          lessons = lessons + mfLessons
          clessons.append(lessons)
          contracts.append(mfg)

          if mfLessons < mcLessons:
              mcg.avprice = float(mcPaid)/float(mcLessons)
              mcg.weeks = mcLessons - mfLessons
              mcg.paid = mcg.avprice * mcg.weeks

              lessons = lessons + mcg.weeks
              clessons.append(lessons)
              contracts.append(mcg)
      elif mfLessons <= mcLessons and mfLessons == 0:


            lessons = lessons + mcg.weeks
            clessons.append(lessons)
            contracts.append(mcg)

    #无限会员合同，已经超过合同设定期限还在交季度学费
      else:
          ml = mfg
          ml.weeks = mfLessons - mcLessons
          ml.paid = mfPaid - mcPaid
          ml.avprice = float(ml.paid)/float(ml.weeks)
          lessons = lessons + ml.weeks
          clessons.append(lessons)
          contracts.append(ml)

      if student_oid == '594e0c3b97a75d6a95e08dab':
            print 'got my boy 3------------------'
            print mfg
            print mcg
      if len(cps) == 0:
          print 'cps is none-----------------------------------'
          if mfg:
              firstNewDeal = mfg
          elif mcg:
              firstNewDeal = mcg

    try:
        if firstNewDeal.contractType.type == constant.ContractType.memberFee:
            print 'firstNewDeal is ---------------------'+str(firstNewDeal.contractType.type)
    except Exception,e:
        print e

    return contracts,clessons,firstNewDeal,firstNewRedeal

#本月前已上并已消课次数，即已发放课时工资的课时次数
def paidLessonBeforeThisMonth(sid,monthBeginDate):
    paidBefore = 0
    query = Q(student=sid)&(Q(type=1)|Q(type=3))&Q(value__gt=0)&Q(lessonTime__lt=monthBeginDate)
    try:
        paidBefore = Lesson.objects.filter(query).count()  # @UndefinedVariable
    except:
        paidBefore = 0
    return paidBefore

#学生课消统计，2019.6.1改为不统计欠费课时
#lbvalue lessons before this month
#lvalue lessons this month NOT include first 4
#lvalue0 lessons this month include first 4

def getStudentConsume(lbvalue,lvalue,lvalue0,contracts,clessons,firstNewDeal,firstNewRedeal,first4):
    csr = []
    cls = 0
    sid = None
    for c in contracts:
        if not sid:
            sid = c.student_oid
        if c.contractType.type == constant.ContractType.memberFee and c.multi != 3:
            continue
        csr.append(c)
        if c.weeks:
            cls = cls + c.weeks
        elif c.contractType and c.contractType.duration:
            cls = cls + c.contractType.duration
    contracts = csr
    if sid == '594e0c3b97a75d6a95e08dab':
        print '594e0c3b97a75d6a95e08dab--------all contract lessons is:'
        print cls
        print 'lesson left is:-----------------'
        ll = cls - lbvalue
        print ll
    #paidBefore = paidLessonBeforeThisMonth(contracts[0].student_oid,beginDate)
    i = 0
    consume = 0
    left = 0
    got = False #本月以前未上过
    if lbvalue == 0:
        got = True
        left = lvalue
    avprice = 0
    for lessons in clessons:
      try:

        if not contracts[i].paid:
            contracts[i].paid = contracts[i].contractType.discountPrice
        if not contracts[i].weeks:
            contracts[i].weeks = contracts[i].contractType.duration

        if contracts[i].contractType.type == constant.ContractType.memberFee and contracts[i].multi != 3:
            avprice = float(contracts[i].paid) / float(contracts[i].weeks)
            if contracts[i].student_oid == '594e0c3b97a75d6a95e08dab':
                print 'GOT---------594e0c3b97a75d6a95e08dab'
                print contracts[i].paid
                print contracts[i].weeks
                print avprice
            i = i + 1

        if got and left > 0: #本月以前未上过，本月有计费课消

            left0 = left
            left = left - contracts[i].weeks
            if contracts[i].student_oid == '594e0c3b97a75d6a95e08dab':
                print left
            if left > 0: #合同不够消了
                consume = consume + contracts[i].paid #消掉全部合同金额
            else: #合同够消
                consume = consume + int(left0 * contracts[i].paid / contracts[i].weeks)
                break
        if not got:

            if lessons >= lbvalue:
                got = True
                thisLeft = lessons - lbvalue
                if thisLeft >= lvalue:
                    if contracts[i].student_oid == '594e0c3b97a75d6a95e08dab':
                        print 'thisleft--------------'
                    consume = consume + int(lvalue * contracts[i].paid / contracts[i].weeks)
                else:
                    left = lvalue - thisLeft
                    if contracts[i].student_oid == '594e0c3b97a75d6a95e08dab':
                        print 'left--------------'
                    consume = consume + int(thisLeft * contracts[i].paid / contracts[i].weeks)


        i = i + 1
      except:
          err = 1
    consumeFirst4 = 0

    if first4 > 0 and lbvalue + lvalue0 >= 4:
        try:
            if firstNewDeal.contractType.type == constant.ContractType.memberFee:
                print 'firstDealType------'+str(firstNewDeal.contractType.type)
        except Exception,e:
            print e
            print '----------------------------firstDealTyoe Rong'
        if firstNewRedeal:
            consumeFirst4 = int(4 * firstNewRedeal.paid / firstNewRedeal.weeks)

        elif firstNewDeal:
            consumeFirst4 = int(4 * firstNewDeal.paid / firstNewDeal.weeks)
        if firstNewDeal.contractType.type == constant.ContractType.memberFee:
             consumeFirst4 = int(4 * avprice)

    return consume,consumeFirst4

#获取期限内校区课时收入
#（返回每个学生课时消费和每个老师课时消费的两个集合）
def branchIncome2(branchId,beginDate,endDate,teacherOnly=None,r=None):
    branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    cityId = branch.city.id
    teacherIncomes = [] #老师上课课时
    branchData = dict()

    holidayCT = None #集训合同
    try:
                        query = Q(city=cityId)&Q(type=constant.ContractType.hc)
                        holidayCTs = ContractType.objects.filter(query)  # @UndefinedVariable
                        print holidayCTs._query
                        print len(holidayCTs)
                        holidayCT = holidayCTs[0]

    except Exception,e:
                        print e
                        holidayCT = None


    year = beginDate.strftime("%Y")
    month = beginDate.strftime("%m")
    query = Q(year=year)&Q(month=month)&Q(branchId=str(branchId))
    lc = None
    lcs = LessonCheck.objects.filter(query).order_by("-updateTime")  # @UndefinedVariable
    if len(lcs) > 0:
        if not r:
          lc = lcs[0]
          if not lc.updateCheckinTime or lc.updateTime >= lc.updateCheckinTime:
            teacherIncomes = lc.teacherCheckin
            branchData = lc.branchIncome
            return teacherIncomes,branchData
        else:
            lc = LessonCheck()
    else:
        lc = LessonCheck()


    millis0 = int(round(time.time() * 1000))
    gcs = None #所有班级
    query = Q(branch=branchId)&Q(gradeClass_type=1)
    gcs = GradeClass.objects.filter(query)  # @UndefinedVariable

    teachers = utils.getTeachers(branchId,None,True)
    if teacherOnly:
        teachers = []
        teachers.append(Teacher.objects.get(id=teacherOnly))  # @UndefinedVariable

    query = Q(status=constant.StudentStatus.sign)&Q(branch=branchId)
    allStudents = Student.objects.filter(query)  # @UndefinedVariable
    ss = {}#有课时的学生
    newSs = dict() #之前未满四次课新生

    branchData['lessons'] = 0.0
    branchData['consume'] = 0.0
    temp = []
    for t in teachers:

        lastStudent = None
        lastLesson = None
        lastClass = None
        lastLessonWeekday = None
        studentConsume = [] #某老师的本月全部学生课时消费
        query = Q(teacher=t.id)&Q(lessonTime__lt=endDate)&Q(lessonTime__gte=beginDate)&(Q(type=1)|Q(type=3))&Q(checked=True)&Q(value__ne=0)&Q(student__ne=None)
        teacherLessons = Lesson.objects.filter(query).order_by('gradeClass','student','lessonTime')  # @UndefinedVariable

        slessons = [] #某个学生的本月上过的课
        for tl in teacherLessons:

            if lastStudent != None and tl.student != lastStudent:
                s = dict()
                s['id'] = lastStudent
                s['lessons'] = slessons
                s['classname'] = lastLesson
                s['classid'] = lastClass
                s['weekday'] = lastLessonWeekday
                studentConsume.append(s)
                slessons = []
                lastStudent = tl.student
                lastLesson = tl.gradeClass.name
                lastClass = str(tl.gradeClass.id)
                lastLessonWeekday =  tl.gradeClass.school_day
            if lastStudent == None:
                lastStudent = tl.student
                lastLesson = tl.gradeClass.name
                lastClass = str(tl.gradeClass.id)
                lastLessonWeekday =  tl.gradeClass.school_day
            #print tl.student

            slessons.append(tl)

        s = dict() #每个学生课时统计
        s['id'] = lastStudent
        s['lessons'] = slessons
        s['classname'] = lastLesson
        s['classid'] = lastClass
        #print s['classid']
        s['weekday'] = lastLessonWeekday
        studentConsume.append(s)
        tt = dict() #每个老师课时统计
        tt['name'] = t.name
        tt['sc'] = studentConsume #此老师的所有学生消课集合
        tt['consume'] = 0.0 #此老师课时消费额
        tt['consumeFirst4'] = 0.0
        tt['lessons'] = 0.0
        tt['ratio'] = t.payRatio
        tt['duePay'] = 0.0
        teacherIncomes.append(tt)
    for tt in teacherIncomes:

        for s in tt['sc']:
            student = None
            try:
                for ssss in allStudents:
                    if str(ssss.id) == s['id']:
                        student = ssss
                if not student:
                    student = Student.objects.get(id=s['id'])  # @UndefinedVariable
                thisLessons = 0.0
                for sls in s['lessons']:
                    thisLessons = thisLessons + sls.value
                s['thisLessons'] = thisLessons
                s['beforeLessons'] = student.lessons - thisLessons
                #查询月份以后的课时，要减掉
                query = Q(lessonTime__gte=endDate)&(Q(type=1)|Q(type=3))&Q(checked=True)&Q(value__ne=0)&Q(student=s['id'])
                afterLessons = Lesson.objects.filter(query)  # @UndefinedVariable
                #print afterLessons._query
                #print len(afterLessons)
                for al in afterLessons:
                    s['beforeLessons'] = s['beforeLessons'] - al.value
                #if student.lessonLeft > 0 and student.lessons > 0:

                try:
                  if newSs[str(student.id)]: #前面已出现此学生

                    ls = newSs[str(student.id)]
                    if ls['first4'] == 4 or ls['first4'] == 0:
                        s['first4'] = 0
                        s['thisPure'] = 0#s['thisLessons']
                    else:
                        s['first4'], s['thisPure']= getFirst4_2(s['beforeLessons'],s['thisLessons']+ls['thisLesson'])

                except: #未出现过

                    s['first4'], s['thisPure']= getFirst4_2(s['beforeLessons'],s['thisLessons'])

                if s['first4'] > 0:
                    newSs[str(student.id)] = s


            except Exception,e:

                print e
                student = None
            if student:

                s['name'] = student.name
                s['consume'] = 0
                s['consumeFirst4'] = 0
                if True:
                #try:
                    csid = str(student.id)
                    if student.siblingId:
                        csid = str(student.siblingId)
                    mcs,mfs = MemberContracts(csid,cityId,endDate)
                    if csid == '594e0c3b97a75d6a95e08dab':
                        print '[got my boy first]------------------'

                    contracts,clessons,firstNewDeal,firstNewRedeal = contractGroup(getStudentContracts(csid,None,holidayCT,endDate),mcs,mfs)
                    if csid == '594e0c3b97a75d6a95e08dab':
                        for c in contracts:
                            print 'GOT THIS STUDENT CONTRACT'
                            print c.paid
                            print c.singDate
                            print 'GOT THIS STUDENT CONTRACT END--------'
                    s['consume'],s['consumeFirst4'] = getStudentConsume(s['beforeLessons'],s['thisPure'],s['thisLessons'],contracts,clessons,firstNewDeal,firstNewRedeal,s['first4'])

                    branchData['lessons'] = branchData['lessons'] + s['thisPure']
                    branchData['consume'] = branchData['consume'] + s['consume']
                    if s['first4'] == 4:
                        branchData['lessons'] = branchData['lessons'] + 4
                        branchData['consume'] = branchData['consume'] + s['consumeFirst4']
                    if student.gradeClass:
                        for gc in gcs:
                            if str(gc.id) == student.gradeClass:
                                s['class'] = gc.name



                    tt['lessons'] = tt['lessons'] + s['thisPure']
                    tt['consume'] = tt['consume'] + s['consume']
                    if s['consumeFirst4'] > 0:
                        tt['consumeFirst4'] = tt['consumeFirst4'] + s['consumeFirst4']

                #except Exception,e:
                 #   print e



        if tt['lessons'] > 0:
            try:
                tt['duePay'] = tt['consume'] * tt['ratio']/100
            except:
                tt['duePay'] = 0.0
            temp.append(tt)


    millis1 = int(round(time.time() * 1000))


    print millis1 - millis0

    year = beginDate.strftime("%Y")
    month = beginDate.strftime("%m")

    lc.branchId = branchId
    lc.year = year
    lc.month = month
    lc.teacherCheckin = temp
    lc.branchIncome = branchData
    lc.updateTime = utils.getDateNow(8)
    if not teacherOnly:
        lc.save()

    return temp,branchData

#


#学生课时消费统计
def studentLessonConsume(student_oid,beginDate=None,endDate=None):
    first4 = 4
    student = Student()
    try:
        student = Student.objects.get(id=student_oid)  # @UndefinedVariable
    except:
        return
    holidayCT = None #集训合同
    try:
        query = Q(delete__ne=1)&Q(city=student.branch.city.id)&Q(type=constant.ContractType.hc)
        holidayCT = ContractType.objects.filter(query)[0]  # @UndefinedVariable
    except:
        holidayCT = None
    #获取除集训外全部合同
    query = Q(student_oid=student_oid)&Q(status__ne=constant.ContractStatus.delete)
    if holidayCT:
        query = query&Q(contractType__ne=holidayCT.id)
    contracts = Contract.objects.filter(query).order_by("singDate")  # @UndefinedVariable

    #以新生合同为标志，把合同分为几组，每组有一个新生合同及其以后的所有其他合同
    cps = []
    cp = []
    i = 0
    for c in contracts:
        if c.multi == 0 and i > 0:
            cps.append(cp)
            cp = []

        cp.append(c)
        i = i + 1

    cps.append(cp)

    #获取时间段内已上课时
    query0 = Q(student=student_oid)&Q(value__ne=0)&(Q(type=1)|Q(type=3))&Q(checked=True)
    query = query0
    if beginDate:
        query = query&Q(lessonTime__gte=beginDate)
    if endDate:
        query = query&Q(lessonTime__lte=endDate)
    lessons = Lesson.objects.filter(query)  # @UndefinedVariable
    lessonsBefore = None
    #获取时间段以前已上课时
    if beginDate:
        query = query0&Q(lessonTime__lt=beginDate)
        lessonsBefore = Lesson.objects.filter(query)  # @UndefinedVariable
    lbvalue = 0 #beginDate以前消费课时
    lvalue = 0 #beginDate到endDate消费课时
    if lessonsBefore:
        for l in lessonsBefore:
            if l.value and l.value > 0:
                lbvalue = lbvalue + l.value
            elif not l.value:
                lbvalue = lbvalue + 1
    if lbvalue > 0:
        first4 = 4 - lbvalue
        if first4 < 0:
            first4 = 0

    for l in lessons:
            if l.value and l.value > 0:
                lvalue = lvalue + l.value
            elif not l.value:
                lvalue = lvalue + 1
    lvalue0 = lvalue
    if first4 > 0 and lvalue > 0:
        lvalue = lvalue - first4
        if lvalue < 0:
            lvalue = 0
            first4 = lvalue0
    if lvalue0 <= 0:
        first4 = 0
    #lvalue = lvalue0
    consume = 0
    contracts = []
    clessons = []
    lessons = 0
    firstNewDeal = None #新生合同
    firstNewRedeal = None #新生续费
    for cp in cps:
        newDeal = None #新生合同
        newRedeal = None #新生续费
        ors = [] #
        fs = [] #

        for c in cp:
            if c.contractType.type == constant.ContractType.free:
                fs.append(c)
            elif c.multi == 0:
                if newDeal:
                    ors.append(c)
                else:
                    newDeal = c
                    if not firstNewDeal:
                        firstNewDeal = c
            elif c.multi == 1:
                if newRedeal:
                    ors.append(c)
                else:
                    c.paid = c.contractType.discountPrice
                    c.weeks = c.contractType.duration
                    newRedeal = c
                    if newDeal:
                        newDeal.paid = 0
                        newDeal.weeks = 0
                    if not firstNewRedeal:
                        firstNewRedeal = c


            elif c.multi == 2:
                ors.append(c)
        if newDeal and not newRedeal:
            contracts.append(newDeal)
            lessons = lessons + newDeal.weeks
            clessons.append(lessons)
        if newRedeal:
            contracts.append(newRedeal)
            lessons = lessons + newRedeal.weeks
            clessons.append(lessons)
        if ors and len(ors)>0:
            for c in ors:
                contracts.append(c)
                lessons = lessons + c.weeks
                clessons.append(lessons)
        if fs and len(fs)>0:
            for c in ors:
                contracts.append(c)
                lessons = lessons + c.weeks
                clessons.append(lessons)

    i = 0
    left = 0
    got = False
    if lbvalue == 0:
        got = True
        left = lvalue
    for lessons in clessons:
        if not contracts[i].paid:
            contracts[i].paid = contracts[i].contractType.discountPrice
        if not contracts[i].weeks:
            contracts[i].weeks = contracts[i].contractType.duration
        if got and left > 0:
            left0 = left
            left = left - contracts[i].weeks
            if left > 0:
                consume = consume + contracts[i].paid
            else:
                consume = consume + int(left0 * contracts[i].paid / contracts[i].weeks)
                break
        if not got:
            if lessons >= lbvalue:
                got = True
                thisLeft = lessons - lbvalue
                if thisLeft >= lvalue:
                    consume = consume + int(lvalue * contracts[i].paid / contracts[i].weeks)
                else:
                    left = lvalue - thisLeft
                    consume = consume + int(thisLeft * contracts[i].paid / contracts[i].weeks)

        i = i + 1
    consumeFirst4 = 0
    if first4 > 0 and lbvalue + lvalue0 > 4:
        if firstNewRedeal:
            consumeFirst4 = int(4 *  firstNewRedeal.paid / firstNewRedeal.weeks)
        elif firstNewDeal:
            consumeFirst4 = int(4 *  firstNewDeal.paid / firstNewDeal.weeks)

    return consume,consumeFirst4,lvalue0,first4

def getTeacherIncome(teacher,beginDate,endDate):
    i = BranchIncome()
    i.teacher_oid = str(teacher.id)
    i.teacherName = teacher.name
    i.lessons = 0
    i.sum = 0
    i.first4 = 0
    i.sumFirst4 = 0
    classes = utils.getTeacherClasses(teacher.id)
    studentConsume = []
    for c in classes:
        classname = None
        for s in c.students:
            consume,consumeFirst4,lvalue,first4 = studentLessonConsume(str(s.id), beginDate, endDate)
            sc = BranchIncome()
            sc.student = s
            sc.first4 = first4
            sc.lessons = lvalue
            sc.sum = consume
            sc.sumFirst4 = consumeFirst4
            if classname != c.name:
                classname = c.name
                sc.teacherName =  s.name + '-' + c.name
            else:
                sc.teacherName = s.name
            studentConsume.append(sc)

            i.lessons = i.lessons + lvalue
            i.sum = i.sum + consume
            i.sumFirst4 = i.sumFirst4 + consumeFirst4

    if i.lessons > 0:
        i.eve = int(i.sum / i.lessons)
    return i,studentConsume


def getBranchDeposit(branchId,bDate,eDate,paymethod,company=1,depositStatus=None):

    sum = 0.0
    query = Q(branch=branchId)&Q(depositDate__gte=bDate)&Q(depositDate__lt=eDate)&Q(deposit__gt=0)
    if paymethod:
        query = query&Q(dopositWay=paymethod)
    query = query&Q(depositCompany=company)
    if depositStatus == 0:
        query = query&Q(depositStatus=depositStatus)
    if depositStatus == 1:
        query = query&Q(depositStatus=depositStatus)
    if depositStatus == 2:
        query = query&Q(depositStatus=depositStatus)
    ss = Student.objects.filter(query)  # @UndefinedVariable
    for s in ss:
        sum = sum + s.deposit

    return sum,len(ss)

#其他收入（星级考、零售、杂费等，不包括社会考级）
def getBranchAllOtherIncomeItemNumber(branchId,bDate,eDate):
    level = 0
    sale = 0
    other = 0
    outLevel = 0
    levels = []
    sales = []
    others = []
    outLevels = []
    query = Q(branchId=str(branchId))&Q(status__ne=constant.ContractStatus.delete)&Q(payDate__gte=bDate)&Q(payDate__lt=eDate)
    incomes = Income.objects.filter(query)  # @UndefinedVariable
    for income in incomes:
        if income.type == constant.IncomeType.level:
            level = level + 1
            levels.append(income)
        elif income.type == constant.IncomeType.sale:
            sale = sale + 1
            sales.append(income)
        elif income.type == constant.IncomeType.other:
            other = other + 1
            others.append(income)
        elif income.type == constant.IncomeType.outLevel:
            outLevel = outLevel + 1
            outLevels.append(income)
    return level,sale,other,levels,sales,others,outLevel,outLevels

def getBranchAllDeal(branchId,bDate,eDate,dealDuration):


    newDeal = 0 #新招生数量
    newDealNet = 0 #新招生中网络来源数量
    newDealSchool = 0 #新招生中校区来源数量
    newRedeal = 0 #新生续费数量
    oldRedeal = 0 #老生续费数量
    lessonFee = 0 #季度课时费
    holiday = 0 #集训班数量
    holidayDeal = 0 #集训班中算成交的数量（3600元以上）
    holidayDealNet = 0 #集训班中算成交网络来源的数量（3600元以上）
    free = 0 #增课合同数量
    newContractsSchool = dict() #新生合同map
    newContractsNet = dict() #网络来源新生合同map
    newRedealContracts = dict() #新生续费合同map
    oldRedealContracts = dict() #老生续费合同map
    lessonFeeContracts = dict() #季度课时费合同map

    newContractList = [] #新生合同集合
    newRedealContractList = [] #新生续费合同集合
    oldRedealContractList = [] #老生续费合同集合
    lessonFeeContractList = [] ##季度课时费合同集合
    holidayDeals = [] #集训班合同集合


    holidayDealStudents = [] #集训班成交学生
    query = Q(branch=branchId)&Q(singDate__gte=bDate)&Q(singDate__lt=eDate)&Q(status__ne=constant.ContractStatus.delete)

    cs = Contract.objects.filter(query)  # @UndefinedVariable

    for c in cs:

        ct = None
        try:
            ct = c.contractType.type
        except:
            ct = None

        if ct == constant.ContractType.free:
            continue
        if ct == constant.ContractType.onlineCourse:
            print '------------GOT ONLINE'
            continue
        tag = 'school'
        try:
                s = Student.objects.get(id=c.student_oid)  # @UndefinedVariable

                tag = 'net'
                if s.regBranch.type == constant.BranchType.school:
                    tag = 'school'
        except:
                tag = 'school'


        if c.multi == constant.MultiContract.memberLesson:

            lessonFee = lessonFee + 1
            lessonFeeContractList.append(c)
            try:
                if lessonFeeContracts[str(c.paid)] > 0:
                    lessonFeeContracts[str(c.paid)] = lessonFeeContracts[str(c.paid)] + 1
            except:
                lessonFeeContracts[str(c.paid)] = 1


        elif c.multi == constant.MultiContract.newDeal and ct != constant.ContractType.free and ct != constant.ContractType.hc and ct != constant.ContractType.onlineCourse:

            newDeal = newDeal + 1

            newContractList.append(c)
            try:
                if tag == 'net':
                    if newContractsNet[str(c.paid)] > 0:
                        newContractsNet[str(c.paid)] = newContractsNet[str(c.paid)] + 1
                else:
                    if newContractsSchool[str(c.paid)] > 0:
                        newContractsSchool[str(c.paid)] = newContractsSchool[str(c.paid)] + 1
            except Exception,e:
                if tag == 'net':
                    newContractsNet[str(c.paid)] = 1
                else:
                    newContractsSchool[str(c.paid)] = 1
            if tag == 'net':
                newDealNet = newDealNet + 1
            else:
                newDealSchool = newDealSchool + 1

        elif c.multi == constant.MultiContract.newRedeal and c.paid > 0  and ct != constant.ContractType.free and ct != constant.ContractType.hc and ct != constant.ContractType.onlineCourse:
            newRedeal = newRedeal + 1
            newRedealContractList.append(c)
            try:
                if newRedealContracts[str(c.paid)] > 0:
                    newRedealContracts[str(c.paid)] = newRedealContracts[str(c.paid)] + 1
            except:
                newRedealContracts[str(c.paid)] = 1


        elif c.multi == constant.MultiContract.oldRedeal and c.paid > 0  and ct != constant.ContractType.free and ct != constant.ContractType.hc  and ct != constant.ContractType.onlineCourse:
            oldRedeal = oldRedeal + 1
            oldRedealContractList.append(c)
            #===================================================================
            # try:
            #     if oldRedealContracts[str(c.weeks*2)] > 0:
            #         oldRedealContracts[str(c.weeks*2)] = oldRedealContracts[str(c.weeks)] + 1
            # except:
            #     oldRedealContracts[str(c.weeks*2)] = 1
            #===================================================================

            try:
                if oldRedealContracts[str(c.paid)] > 0:
                    oldRedealContracts[str(c.paid)] = oldRedealContracts[str(c.paid)] + 1
            except:
                oldRedealContracts[str(c.paid)] = 1


        elif ct == constant.ContractType.free and c.paid == 0:
            free = free + 1
        elif ct == constant.ContractType.hc and c.paid > 0:
            holidayDeals.append(c)
            holiday = holiday + 1 #假期班
            if c.student_oid not in holidayDealStudents:
                isDeal,dealDate,allpaid = checkHolidayDeal(c.student_oid,eDate,c.contractType)

                if isDeal and bDate <= dealDate:#成交日期在查询日期区间内，算入假期成交
                    holidayDealStudents.append(c.student_oid)
                    holidayDeal = holidayDeal + 1
                    if tag == 'net':
                        holidayDealNet = holidayDealNet + 1
                        newDealNet = newDealNet + 1
                    else:
                        newDealSchool = newDealSchool + 1

                    try:
                        if tag == 'net':
                            newContractsNet[u'集训'] = newContractsNet[u'集训'] + 1
                        else:
                            newContractsSchool[u'集训'] = newContractsSchool[u'集训'] + 1
                    except Exception,e:
                        if tag == 'net':
                            newContractsNet[u'集训'] = 1
                        else:
                            newContractsSchool[u'集训'] = 1
        tag = ''


    return newDeal,newRedeal,oldRedeal,holiday,holidayDeal,holidayDealNet,free,newDealSchool,newDealNet,newContractsSchool,newContractsNet,newRedealContracts,oldRedealContracts,newContractList,newRedealContractList,oldRedealContractList,holidayDeals,lessonFeeContractList,lessonFeeContracts,lessonFee

#某学生本期集训交款总额，第一次超过3600的日期算1个招生
#4-9夏季集训班，10-3冬季集训班
def checkHolidayDeal(studentId,end,contractType,cityId=constant.BEIJING):
    dealDuration = 4
    city = City.objects.get(id=cityId)  # @UndefinedVariable

    if city:
        dealDuration = city.dealDuration
    isDeal = False
    dealDate = None
    now = utils.getDateNow(8)
    begin = None
    if not end:
        end = now

    month = int(now.strftime("%m"))
    if month > 9 or month < 4:

        if month > 9:
            begin = datetime.datetime.strptime(now.strftime("%Y")+'1001','%Y%m%d')
        else:
            y = int(now.strftime("%Y"))-1
            begin = datetime.datetime.strptime(str(y)+'1001','%Y%m%d')
    else:

        begin = datetime.datetime.strptime(now.strftime("%Y")+'0401','%Y%m%d')
    query = Q(student_oid=studentId)&Q(contractType__ne=contractType)&Q(singDate__lte=end)&Q(weeks__gte=dealDuration)
    cs = Contract.objects.filter(query)  # @UndefinedVariable
    if cs and len(cs) > 0:
        return False,None,None
    query = Q(student_oid=studentId)&Q(contractType=contractType)&Q(singDate__gte=begin)&Q(singDate__lte=end)
    contracts = Contract.objects.filter(query).order_by('-singDate')  # @UndefinedVariable

    paid = 0
    for c in contracts:

        if c.paid > 0:
            paid = c.paid + paid
        elif c.contractType.discountPrice > 0:
            paid = c.contractType.discountPrice + paid
        if paid >= 3600:
            dealDate = c.singDate
            isDeal = True

    return isDeal,dealDate,paid

def getGoneStudents(branchId,begin,end):
    gone = 0
    students = []
    sids = []
    query = Q(branch=branchId)&Q(endDate__gte=begin)&Q(endDate__lt=end)
    contracts = Contract.objects.filter(query).order_by("student_oid")  # @UndefinedVariable
    try:
        for c in contracts:
            if c.student_oid not in sids:
                try:
                    s = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
                    sids.append(str(s.id))
                    students.append(s)
                except:
                    continue
    except:
        err = 1
    return students

if __name__ == "__main__":
    end = utils.getDateNow()-timedelta(days=0)
    begin = end - timedelta(days=30)

    begin = datetime.datetime.strptime('2018-05-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    end = datetime.datetime.strptime('2018-06-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    #branchIncome2("5867c0c33010a51fa4f5abe6",begin,end)
    checkHolidayDeal(None,None)
