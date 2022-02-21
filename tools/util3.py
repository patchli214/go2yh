#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
from tools import utils, zhenpustat, constant
from statistic.models import WeekReg
from teacher.models import Teacher
#from datetime import datetime
__author__ = 'patch'

from mongoengine.queryset.visitor import Q
from go2 import settings
from regUser.models import GradeClass
from gradeClass.models import Lesson


def delClassLessons(gcId,sId):
    query = None
    if gcId and not sId:
        query = Q(gradeClass=gcId)
    if sId and not gcId:
        query = Q(student=sId)
    if sId and gcId:
        query = Q(gradeClass=gcId)&Q(student=sId)
    if not gcId and not sId:
        return 0
    lessons = Lesson.objects.filter(query)  # @UndefinedVariable
    i = 0
    for l in lessons:
        try:
            #print l.lessonTime
            l.delete()
            i = i + 1
        except Exception,e:
            print e
            err = 1
            
    print i
    return i

def getWeekReg(cityid,beginDate=None,endDate=None):
    cid = str(cityid)
    print beginDate
    print endDate
    if not beginDate:
        endDate = utils.getDateNow(8)
        beginDate = utils.getWeekBegin(endDate, False)
    query = Q(cityId=cid)&Q(beginDate=beginDate)&Q(endDate=endDate)
    w = None
    try:
        ws = WeekReg.objects.filter(query)  # @UndefinedVariable
        print ws._query
        print len(ws)
        w = ws[0]
    except Exception,e:
        print e
        err = 1

    return w,beginDate,endDate

#保存周期内的拜访统计数据
def statWeekReg(cityid,beginDate=None,endDate=None):
    now = utils.getDateNow(8)
    if not endDate and not beginDate:
        endDate = now
        beginDate = utils.getWeekBegin(endDate, False)
    w = WeekReg()
    w.beginDate = beginDate
    w.cityId = str(cityid)
    branches = utils.getCityBranch(cityid)
    query = None
    i = 0
    for b in branches:
        if i == 0:
            query = Q(branch=b)
        else:
            query=query|Q(branch=b)
        i = i + 1
    query = (query)&Q(status__ne=-1)&Q(role__lt=9)
    teachers = Teacher.objects.filter(query)  # @UndefinedVariable
    all = []
    deals = []
    i = 0
    for teacher in teachers:
        #if i > 0:
         #   break
        i = i + 1
        stat = zhenpustat.teacherStat2(teacher,beginDate,endDate,deals)
        s = {}
        s['teacherName'] = teacher.name
        s['teacherId'] = teacher.id
        s['branchSN'] = teacher.branch.sn
        s['branchName'] = teacher.branch.branchName
        s['regAll'] = stat.reg
        s['regMorning'] = stat.regNet
        s['regEvening'] = stat.regAll
        s['show'] = stat.show
        s['showThis'] = stat.demo
        
        all.append(s)
    
    query = Q(beginDate=beginDate)&Q(endDate=endDate)
    try:
        w = WeekReg.objects.filter(query)[0]  # @UndefinedVariable
    except:
        err = 1
    w.endDate = endDate
    w.cityId = str(cityid)
    w.regs = all
    w.updateDate = now
    w.save()
    print beginDate.strftime('%Y%m%d') + '--DONE:' + str(i)

def statPastWeekReg(cityId,beginDate,endDate):
    thisBegin = utils.getWeekBegin(endDate, False)
    thisEnd = thisBegin + datetime.timedelta(days=7)
    statWeekReg(cityId,thisBegin,thisEnd)
    thisEnd = thisBegin - datetime.timedelta(days=1)
    while thisBegin > beginDate:
        thisBegin = utils.getWeekBegin(thisEnd, False)
        thisEnd = thisBegin + datetime.timedelta(days=7)
        statWeekReg(cityId,thisBegin,thisEnd)
        thisEnd = thisBegin - datetime.timedelta(days=1)
        

if __name__ == "__main__":
    #gcId = GradeClass.objects.get(id='5ad6aa9b97a75d891fa03082').id  # @UndefinedVariable
    #sId = '5977f78497a75d5d9908152e'
    #delClassLessons(gcId, sId)
    #statWeekReg(constant.BEIJING)
    begin = datetime.datetime.strptime("20190601","%Y%m%d")
    end = datetime.datetime.strptime("20190701","%Y%m%d")
    statWeekReg(constant.BEIJING,begin,end)