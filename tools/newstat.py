#!/usr/bin/env python
# -*- coding:utf-8 -*-
#from numpy import False_
from datetime import timedelta
from tools.utils import getDateNow
import student
from tools.constant import GradeClassType
from branch.models import Branch
from tools import zhenpustat
__author__ = 'patch'
import constant,utils,datetime
from mongoengine.queryset.visitor import Q
from teacher.models import Teacher
from regUser.models import Student,TeacherRemind,Contract,ContractType,GradeClass
from gradeClass.models import Lesson
from statistic.models import BranchIncome
from operator import attrgetter

#全部老师拜访招生数据排行
def weekSaleEveryPerson(cityId,beginDate,endDate,excludeType1=True):
    q1 = Q(city=cityId)&Q(type__ne=1)&Q(type__ne=2)
    branches = Branch.objects.filter(q1)  # @UndefinedVariable
    query = Q(singDate__gte=beginDate)&Q(singDate__lt=endDate)&Q(status__ne=constant.ContractStatus.delete)&(Q(multi=constant.MultiContract.newDeal))
    queryBranch = None
    i = 0
    for b in branches:
        #print b.branchName
        if i == 0:
            queryBranch = Q(branch=b.id)
        else:
            queryBranch = queryBranch|Q(branch=b.id)
        i = i + 1
    query = query&(queryBranch)
    deals = Contract.objects.filter(query)  # @UndefinedVariable
    persons = {}
    refers = {}
    
    for d in deals:
        try:
            s = Student.objects.get(id=d.student_oid)  # @UndefinedVariable
            res,co_t = zhenpustat.BFshare(s)

            for t in co_t:
                isRef = False
                cando = True
                if excludeType1:
                    if t.branch.type == 1 or t.branch.type == 2:
                        cando = False
                    elif s.sourceType == constant.StudentSourceType.teacher or s.sourceType == constant.StudentSourceType.ref:
                        cando = True
                        if s.sourceType == constant.StudentSourceType.ref:
                            isRef = True
                        else:
                            isRef = False
                    else:
                        cando = False
                if cando:
                    a = t.branch.branchName + '_' + t.name + '_' + str(t.id)
                    try:
                        if persons[a] > 0:
                            persons[a] = persons[a] + res
                    except:
                        persons[a] = res
                    if isRef:
                        try:
                            if refers[a] > 0:
                                refers[a] = refers[a] + res
                        except:
                            refers[a] = res                                
        except Exception,e:
            print e
            #d.delete()

    res = []
    query = queryBranch&Q(status=0)
    teachers = Teacher.objects.filter(query)  # @UndefinedVariable
    
    i = 0
    for key, value in persons.iteritems():
        aa = key.split('_')
        t = BranchIncome()
        has = False

        i =  i + 1
        for ttt in teachers:

            if aa[2] == str(ttt.id):

                has = True
                break
        if has:
            t.teacher_oid = aa[0]
            t.teacherName = aa[1]
            t.duePay = round(value,1)
            try:
                t.first4 = round(refers[key],1)
            except:
                err = 1
            res.append(t) 
        #print key + ':' + str(value)
        
            
    
    
    
    
    for tt in teachers:
        key = tt.branch.branchName + '_' + tt.name + '_' + str(tt.id)
        try:
            value = persons[key]
        except:
            t = BranchIncome()
            t.teacher_oid = tt.branch.branchName
            t.teacherName = tt.name
            t.duePay = 0
            res.append(t)
    return res

if __name__ == "__main__":
    end = utils.getDateNow()
    begin = end + timedelta(days=-7)
    print begin
    persons = weekSaleEveryPerson(constant.BEIJING,begin,end)