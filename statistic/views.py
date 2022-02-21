#!/usr/bin/env python
# -*- coding:utf-8 -*-
import branch
from student.models import Question, Suspension
from webpage.models import Reg
import sys
__author__ = 'bee'
from mongoengine.queryset.visitor import Q
import os,datetime,json,time
import itertools

from operator import attrgetter
from django.http import HttpResponse,HttpResponseRedirect
from tools import http, util2, newstat, util3
from datetime import timedelta
from django.shortcuts import render,render_to_response
from django.template import RequestContext
from statistic.models import *
from branch.models import Branch,City, Vocation
from regUser.models import Student,StudentFile,GradeClass,Contract,ContractType,\
    StudentTrack, SourceCategory
from teacher.models import Login_teacher
from teacher.models import Teacher
from gradeClass.models import Lesson
from django.views.decorators.csrf import ensure_csrf_cookie
from tools import utils,dbsearch
from tools.utils import checkCookie,getDateNow,getWeekBegin,getTeachers
from tools.http import pageVisit
from tools.zhenpustat import getBranchRefund,getBranchShow,getNetSourceStat,getBranchIncome,getBranchRatio,fillStat,getNoneDealContractTypes,getBranchRefundNet,getBranchReg,getBranchRegB,getBranchRegNet,getBranchShowNet,getBranchUnshowNet
from tools import constant,zhenpustat
from django.views.decorators.csrf import  csrf_exempt
@ensure_csrf_cookie
# Create your views here.

#单个校区相册转介注册统计
def statStudent(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    teachers = Teacher.objects.filter(Q(branch=login_teacher.branch)&Q(status=0)).order_by("role")  # @UndefinedVariable
    teacherStats = []

    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    monthBegin = datetime.datetime.strptime(now.strftime("%Y-%m")+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    weekBegin = getWeekBegin(todayBegin)

    lastWeekBegin = weekBegin - timedelta(days=7)
    lastWeekEnd = weekBegin - timedelta(days=1)

    searchBegin = lastWeekBegin
    searchEnd = lastWeekEnd
    searchPeriod = request.GET.get("searchPeriod")
    sort = request.GET.get("sort")
    if not sort:
        sort = 'refer'
    if not searchPeriod:
        searchPeriod = 'lastWeek'
    if searchPeriod == 'today':
        searchBegin = todayBegin
        searchEnd = todayEnd
    if searchPeriod == 'thisWeek':
        searchBegin = weekBegin
        searchEnd = todayEnd
    if searchPeriod == 'lastWeek':
        searchBegin = lastWeekBegin
        searchEnd = lastWeekEnd
    if searchPeriod == 'thisMonth':
        searchBegin = monthBegin
        searchEnd = todayEnd
    b =  Branch.objects.get(id=login_teacher.branch)  # @UndefinedVariable

    stat = getStat(b,searchBegin,searchEnd,None)
    teacherStats.append(stat)
    for t in teachers:
        stat = getStat(b,searchBegin,searchEnd,t)
        teacherStats.append(stat)
    teacherStats = sorted(teacherStats, key=attrgetter(sort),reverse=True)
    return render(request, 'statStudent.html', {"login_teacher":login_teacher,
                                               "stats": teacherStats,
                                               "sort": sort,
                                               "searchPeriod":searchPeriod})

#register stat
def getStat(branch,searchBegin,searchEnd,teacher):
    stat = StatStudent()
    stat.branch = branch
    query = Q(branch=branch.id)&Q(regTime__gte=searchBegin)&Q(regTime__lte=searchEnd)
    queryShare = Q(page='userShare')&Q(branch=str(branch.id))&Q(visitTime__gte=searchBegin)&Q(visitTime__lte=searchEnd)
    queryBranchShare = Q(page='branchShare')&Q(branch=str(branch.id))&Q(visitTime__gte=searchBegin)&Q(visitTime__lte=searchEnd)
    queryReg = Q(page='register')&Q(branch=str(branch.id))&Q(visitTime__gte=searchBegin)&Q(visitTime__lte=searchEnd)
    queryAlbum = Q(branch=str(branch.id))&Q(fileCreateTime__gte=searchBegin)&Q(fileCreateTime__lte=searchEnd)
    if teacher:
        stat.teacher = teacher
        query = query&Q(regTeacher=teacher)
        queryShare = queryShare&Q(teacher=str(teacher.id))
        queryBranchShare = queryBranchShare&Q(teacher=str(teacher.id))
        queryReg = queryReg&Q(teacher=str(teacher.id))
        queryAlbum = queryAlbum&Q(teacher=str(teacher.id))
    stat.online = Student.objects.filter(query&Q(sourceType='A')).count() # @UndefinedVariable
    stat.visit = Student.objects.filter(query&Q(sourceType='B')).count() # @UndefinedVariable
    stat.refer = Student.objects.filter(query&Q(sourceType='C')).count()  # @UndefinedVariable

    stat.album = StudentFile.objects.filter(queryAlbum).count() # @UndefinedVariable


    pvs = PageVisit.objects.filter(queryShare)
    pv = 0
    for p in pvs:
        if p.visit:
            pv = p.visit + pv
    stat.pageShare = pv

    pv = PageVisit.objects.filter(queryShare).count()
    stat.pageNum = pv

    pvs = PageVisit.objects.filter(queryReg)
    pv = 0
    for p in pvs:
        if p.visit:
            pv = p.visit + pv
    stat.pageReg = pv

    pvs = PageVisit.objects.filter(queryBranchShare)
    pv = 0
    for p in pvs:
        if p.visit:
            pv = p.visit + pv
    stat.branchShare = pv

    pv = PageVisit.objects.filter(queryBranchShare).count()
    stat.branchPages = pv
    return stat

#admin分校区一周到场成交统计
def statDemoBranch(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    #redealCT = None
    ctQuery = None
    try:
        city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
        #excludeContract = getNoneDealContractTypes(city)
        #redealCT = zhenpustat.getRedealCT(city)
    except:
        #excludeContract = None
        ctQuery = None


    doSearch = request.GET.get("doSearch")
    if doSearch != '1':
        return render(request, 'statDemoBranch.html', {"login_teacher":login_teacher})
    searchWeekBegin = request.GET.get("searchWeekBegin")
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    weekBegin = getWeekBegin(todayBegin)
    title = u'本周'
    if searchWeekBegin == '1':
        weekBegin = weekBegin - timedelta(days=7)
        title = u'上周'
    branchStats = []
    total1 = 0
    total2 = 0
    total3 = 0
    total1net = 0
    total2net = 0
    total3net = 0
    dayStat = [Stats(),
               Stats(),
               Stats(),
               Stats(),
               Stats(),
               Stats(),
               Stats()]
    for stats in dayStat:
        stats.statBranch = UserStat()
        stats.statNet = UserStat()

    searchBegin = weekBegin
    searchEnd = now

    branches = utils.getCityBranch(login_teacher.cityId)

    lastBranch = None
    studentSum = 0
    studentSus = 0
    for branch in branches:
        days = []
        b1 = 0
        b2 = 0
        b3 = 0
        c1 = 0
        c2 = 0
        c3 = 0
        searchBegin = weekBegin
        for i in range(7):
            two = Stats()
            if i > 0:
                searchBegin = searchBegin+timedelta(days=1)
            searchEnd = datetime.datetime.strptime(searchBegin.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
            if lastBranch != branch:
                lastBranch = branch
            query = Q(branch=branch.id)
            stat = UserStat()
            statNet = UserStat()
            shows,showsNet,showB = getBranchShowNet(login_teacher.cityHeadquarter,branch,searchBegin,searchEnd)
            statNet.show = len(showsNet)
            stat.show = len(shows)
            unshows,unshowsNet = getBranchUnshowNet(login_teacher.cityHeadquarter,branch,searchBegin,searchEnd)
            statNet.reservation = statNet.show + len(unshowsNet)
            stat.reservation = stat.show + len(unshows)
            #newdeal,redeal,newdealNet,redealNet = getBranchDealNet(login_teacher.cityHeadquarter,branch,searchBegin,searchEnd,excludeContract,None,redealCT)
            newdeal,newdealNet = dbsearch.getBranchDealNewNet(login_teacher.cityHeadquarter, branch, searchBegin, searchEnd, ctQuery,'all')
            stat.newdeal = len(newdeal)
            stat.memo = branch.branchName
            statNet.newdeal = len(newdealNet)
            statNet.memo = branch.branchName
            two.statBranch = stat
            two.statNet = statNet
            days.append(two)
            two = None

            total1 = total1 + stat.show
            total2 = total2 + stat.reservation
            total3 = total3+ stat.newdeal
            total1net = total1net + statNet.show
            total2net = total2net + statNet.reservation
            total3net = total3net+ statNet.newdeal
            if dayStat[i].statBranch.show:
                dayStat[i].statBranch.show = dayStat[i].statBranch.show + stat.show
            else:
                dayStat[i].statBranch.show = stat.show
            if dayStat[i].statBranch.reservation:
                dayStat[i].statBranch.reservation = dayStat[i].statBranch.reservation + stat.reservation
            else:
                dayStat[i].statBranch.reservation = stat.reservation
            dayStat[i].statBranch.notShow = dayStat[i].statBranch.reservation - dayStat[i].statBranch.show
            if dayStat[i].statBranch.newdeal:
                dayStat[i].statBranch.newdeal = dayStat[i].statBranch.newdeal + stat.newdeal
            else:
                dayStat[i].statBranch.newdeal = stat.newdeal

            if dayStat[i].statNet.show:
                dayStat[i].statNet.show = dayStat[i].statNet.show + statNet.show
            else:
                dayStat[i].statNet.show = statNet.show
            if dayStat[i].statNet.reservation:
                dayStat[i].statNet.reservation = dayStat[i].statNet.reservation + statNet.reservation
            else:
                dayStat[i].statNet.reservation = statNet.reservation
            dayStat[i].statNet.notShow = dayStat[i].statNet.reservation - dayStat[i].statNet.show
            if dayStat[i].statNet.newdeal:
                dayStat[i].statNet.newdeal = dayStat[i].statNet.newdeal + statNet.newdeal
            else:
                dayStat[i].statNet.newdeal = statNet.newdeal

            b1 = b1 + stat.show
            b2 = b2 + stat.reservation
            b3 = b3+ stat.newdeal
            c1 = c1 + statNet.show
            c2 = c2 + statNet.reservation
            c3 = c3+ statNet.newdeal
            stat = None
            statNet = None
            if i == 6:
                two = Stats()
                stat = UserStat()
                statNet = UserStat()
                stat.show = b1
                stat.notShow = b2 - b1
                stat.reservation = b2
                stat.newdeal = b3
                stat.memo = branch.city.cityName + '-' + branch.branchName
                statNet.show = c1
                statNet.notShow = c2 - c1
                statNet.reservation = c2
                statNet.newdeal = c3
                statNet.memo = branch.city.cityName + '-' + branch.branchName
                two.statBranch = stat
                two.statNet = statNet
                try:
                    two.studentSum,two.sus = zhenpustat.getBranchStudent(str(branch.id))

                    studentSum = studentSum + two.studentSum
                    studentSus = studentSus + two.sus
                except Exception,e:
                    print e
                    two.studentNum = 0
                days.append(two)
                stat = None
                statNet = None
                two = None
                b1 = 0
                b2 = 0
                b3 = 0
                c1 = 0
                c2 = 0
                c3 = 0
            stat = None
            statNet = None

        branchStats.append(days)


        days = []
    total = StatStudent()
    totalNet = StatStudent()
    total.show = total1
    total.notshow = total2-total1
    total.reservation = total2
    total.newdeal = total3
    totalNet.show = total1net
    totalNet.notshow = total2net-total1net
    totalNet.reservation = total2net
    totalNet.newdeal = total3net
    two = Stats()
    two.statBranch = total
    two.statNet = totalNet
    two.studentSum = studentSum
    two.studentSus = studentSus
    dayStat.append(two)
    branchStats.append(dayStat)

    return render(request, 'statDemoBranch.html', {"login_teacher":login_teacher,
                                             "title":title,
                                             "total1":total1,
                                             "total2":total2,
                                             "total3":total3,
                                             "searchWeekBegin":searchWeekBegin,
                                             "studentSum":studentSum,
                                             "branches": branchStats})

#网络部一周分校区到场成交统计
def statDayDemoBranch(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    ctQuery = None
    try:
        city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
        cts2,ct2Query = dbsearch.getHolidayContractType(city)
        ctQuery = (ctQuery|ct2Query)
    except:
        ctQuery = None

    doSearch = request.GET.get("doSearch")
    if doSearch != '1':
        return render(request, 'statDayDemoBranch.html', {"login_teacher":login_teacher})
    searchWeekBegin = request.GET.get("searchWeekBegin")
    print searchWeekBegin
    weekBegin = None
    try:
        weekBegin = datetime.datetime.strptime(searchWeekBegin+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        print weekBegin
    except:
        print 'no searchBegin'
        now = getDateNow()
        todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        weekBegin = getWeekBegin(todayBegin,1)

    nextWeek = weekBegin + timedelta(days=7)
    lastWeek = weekBegin - timedelta(days=7)
    weekEnd = weekBegin + timedelta(days=6)
    nextWeekStr = nextWeek.strftime("%Y-%m-%d")
    lastWeekStr = lastWeek.strftime("%Y-%m-%d")
    weekBeginStr = weekBegin.strftime("%Y-%m-%d")
    weekEndStr = weekEnd.strftime("%Y-%m-%d")
    title = u'本周'

    branchStats = []
    total1 = 0
    total2 = 0
    total3 = 0
    dayStat = [UserStat(),UserStat(),UserStat(),UserStat(),UserStat(),UserStat(),UserStat()]

    #searchBegin = weekBegin
    #searchEnd = now

    branches = utils.getCityBranch(login_teacher.cityId)
    days = []
    b1 = 0
    b2 = 0
    b3 = 0
    lastBranch = None
    for branch in branches:
        searchBegin = weekBegin
        for i in range(7):
            if i > 0:
                searchBegin = searchBegin+timedelta(days=1)
            searchEnd = datetime.datetime.strptime(searchBegin.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
            if lastBranch != branch:
                lastBranch = branch
            #query = Q(branch=branch.id)
            stat = UserStat()
            shows,showsNet,showB = getBranchShowNet(login_teacher.branch,branch,searchBegin,searchEnd)
            stat.show = len(showsNet)
            unshows,unshowsNet = getBranchUnshowNet(login_teacher.branch,branch,searchBegin,searchEnd)
            stat.reservation = stat.show + len(unshowsNet)
            #newdeal,redeal,newdealNet,redealNet = getBranchDealNet(login_teacher.cityHeadquarter,branch,searchBegin,searchEnd,excludeContract,None,redealCT)
            newdeal,newdealNet = dbsearch.getBranchDealNewNet(login_teacher.branch, branch, searchBegin, searchEnd, ctQuery)
            stat.newdeal = len(newdealNet)

            stat.memo = branch.branchName
            days.append(stat)
            total1 = total1 + stat.show
            total2 = total2 + stat.reservation
            total3 = total3+ stat.newdeal
            if dayStat[i].show:
                dayStat[i].show = dayStat[i].show + stat.show
            else:
                dayStat[i].show = stat.show
            if dayStat[i].reservation:
                dayStat[i].reservation = dayStat[i].reservation + stat.reservation
            else:
                dayStat[i].reservation = stat.reservation
            dayStat[i].notShow = dayStat[i].reservation - dayStat[i].show
            if dayStat[i].newdeal:
                dayStat[i].newdeal = dayStat[i].newdeal + stat.newdeal
            else:
                dayStat[i].newdeal = stat.newdeal
            b1 = b1 + stat.show
            b2 = b2 + stat.reservation
            b3 = b3+ stat.newdeal
            if i == 6:
                stat = UserStat()
                stat.show = b1
                stat.notShow = b2 - b1
                stat.reservation = b2
                stat.newdeal = b3
                stat.memo = branch.city.cityName + '-' + branch.branchName
                days.append(stat)
                b1 = 0
                b2 = 0
                b3 = 0
            stat = None

        branchStats.append(days)
        days = []
    total = StatStudent()
    total.show = total1
    total.notshow = total2-total1
    total.reservation = total2
    total.newdeal = total3
    dayStat.append(total)
    branchStats.append(dayStat)
    return render(request, 'statDayDemoBranch.html', {"login_teacher":login_teacher,
                                             "title":title,
                                             "total1":total1,"weekEndStr":weekEndStr,
                                             "total2":total2,"weekBeginStr":weekBeginStr,
                                             "total3":total3,"nextWeekStr":nextWeekStr,"lastWeekStr":lastWeekStr,
                                             "searchWeekBegin":searchWeekBegin,
                                             "branches": branchStats})
#单个校区一周到场成交明细统计
def statDayBranch(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branch = login_teacher.branch
    branchObj = Branch.objects.get(id=branch)  # @UndefinedVariable
    branchName = branchObj.branchName  # @UndefinedVariable

    ctQuery = None
    try:
        city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
        cts,ctQuery = dbsearch.getNormalContractTypes(city)

    except:
        ctQuery = None

    doSearch = request.GET.get("doSearch")
    if doSearch != '1':
        return render(request, 'statDayBranch.html', {"login_teacher":login_teacher})
    searchWeekBegin = request.GET.get("searchWeekBegin")
    now = getDateNow()
    todayBegin = datetime.datetime.strptime(now.strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    weekBegin = getWeekBegin(todayBegin)
    title = u'本周'
    if searchWeekBegin == '1':
        weekBegin = weekBegin - timedelta(days=7)
        title = u'上周'
    dayStat = [UserStat(),UserStat(),UserStat(),UserStat(),UserStat(),UserStat(),UserStat()]

    searchBegin = weekBegin
    searchEnd = now

    days = []
    daysNet = []

    total = UserStat(None,None,None,0.0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
    totalNet = UserStat(None,None,None,0.0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0)
    total.redealNew = 0
    total.redealOld = 0
    total.deal = 0
    total.lessonFee = 0
    total.refund = 0
    total.level = 0
    total.outLevel = 0
    total.sale = 0
    total.other = 0
    total.levelSum = 0
    total.outLevelSum = 0
    total.saleSum = 0
    total.otherSum = 0
    total.hc = 0
    todayData = None
    total.newdealSum = 0
    total.newredealSum = 0
    total.oldredealSum = 0
    total.holidaydealSum = 0
    total.feedealSum = 0
    total.deposit = 0


    for i in range(7):
            two = Stats()

            if i > 0:
                searchBegin = searchBegin+timedelta(days=1)
            searchEnd = datetime.datetime.strptime(searchBegin.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")

            stat = UserStat()
            stat.date = searchBegin
            stat.redealNew = 0
            stat.redealOld = 0
            statNet = UserStat()
            statNet.redealNew = 0
            statNet.redealOld = 0
            shows,showsNet,showsB = getBranchShowNet(login_teacher.cityHeadquarter,branch,searchBegin,searchEnd)
            stat.show = len(shows)
            statNet.show = len(showsNet)
            regs = zhenpustat.getBranchRegB(branch,searchBegin,searchEnd)
            stat.reg = len(regs)
            unshows,unshowsNet = getBranchUnshowNet(login_teacher.cityHeadquarter,branch,searchBegin,searchEnd)

            stat.reservation = stat.show + len(unshows)
            statNet.reservation = statNet.show + len(unshowsNet)
            #newdeal,redeal,newdealNet,redealNet = getBranchDealNet(login_teacher.cityHeadquarter,branch,searchBegin,searchEnd,excludeContract,None,redealCT)
            newdeal0,newdealNet = dbsearch.getBranchDealNewNet(login_teacher.cityHeadquarter, branch, searchBegin, searchEnd, ctQuery,'all')
            deposit,dnum = dbsearch.getBranchDeposit(branchObj.id,searchBegin,searchEnd,None,1)

            stat.deposit = deposit

            #statNet.redeal = len(redealNet)
            newdeal,newredeal,oldredeal,holiday,holidayDeal,holidayDealNet,free,newDealSchool,newDealNet,newContractsSchool,newContractsNet,newRedealContracts,oldRedealContracts,newContractList,newRedealContractList,oldRedealContractList,holidayDeals,feeDeals,lessonFeeContracts,lessonFee = dbsearch.getBranchAllDeal(branchObj.id, searchBegin, searchEnd,city.dealDuration)
            level,sale,other,levels,sales,others,outLevel,outLevels = dbsearch.getBranchAllOtherIncomeItemNumber(branchObj.id,searchBegin,searchEnd)
            stat.newContractsSchool = newContractsSchool

            stat.newContractsNet = newContractsNet
            stat.newRedealContracts = newRedealContracts
            stat.oldRedealContracts = oldRedealContracts

            stat.lessonFeeContracts = lessonFeeContracts
            stat.lessonFee = lessonFee
            stat.feedealSum = 0

            stat.newdeal = newdeal
            #print stat.newdeal
            stat.newdealNet = newDealNet
            stat.newdealSchool = newDealSchool
            stat.redealNew = newredeal
            stat.redealOld = oldredeal
            stat.hc = holiday
            stat.holidayDeal = holidayDeal
            stat.holidayDealNet = holidayDealNet
            stat.newdeal = stat.newdeal + holidayDeal
            #stat.newdealNet = newDealNet + holidayDealNet
            stat.level = level
            stat.outLevel = outLevel
            stat.sale = sale
            stat.other = other

            stat.levelSum = 0
            stat.outLevelSum = 0
            stat.saleSum = 0
            stat.otherSum = 0

            for income in levels:
                stat.levelSum = stat.levelSum + income.paid
            for income in outLevels:
                stat.outLevelSum = stat.outLevelSum + income.paid
            for income in sales:
                stat.saleSum = stat.saleSum + income.paid
            for income in others:
                stat.otherSum = stat.otherSum + income.paid

            stat.newdealSum = 0
            stat.newredealSum = 0
            stat.oldredealSum = 0
            stat.holidaydealSum = 0

            #营收
            stat.deal = util2.getBranchRevenue(branchObj.id,searchBegin,searchEnd)
            #stat.deal = stat.deal + deposit
            #退费
            stat.refund = util2.getBranchRefund(branchObj.id,searchBegin,searchEnd)

            #stat.newdeal = len(newdeal)
            #stat.redeal = len(redeal)
            statNet.newdeal = newDealNet

            for c in newContractList:
                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.newdealSum = stat.newdealSum + paid


            for c in newRedealContractList:
                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.newredealSum = stat.newredealSum + paid

            for c in oldRedealContractList:

                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.oldredealSum = stat.oldredealSum + paid

            for c in holidayDeals:
                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.holidaydealSum = stat.holidaydealSum + paid
            for c in feeDeals:
                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.feedealSum = stat.feedealSum + paid



            stat.memo = branchName

            total.show = total.show + stat.show
            total.reg = total.reg + stat.reg
            total.reservation = total.reservation + stat.reservation
            total.newdeal = total.newdeal + stat.newdeal
            total.lessonFee = total.lessonFee + stat.lessonFee
            total.redealNew = total.redealNew + stat.redealNew
            total.redealOld = total.redealOld + stat.redealOld
            total.deal = total.deal + stat.deal
            total.deposit = total.deposit + stat.deposit
            total.refund = total.refund + stat.refund
            total.hc = total.hc + stat.hc

            total.level = total.level + stat.level
            total.outLevel = total.outLevel + stat.outLevel
            total.sale = total.sale + stat.sale
            total.other = total.other + stat.other

            total.levelSum = total.levelSum + stat.levelSum
            total.saleSum = total.saleSum + stat.saleSum
            total.otherSum = total.otherSum + stat.otherSum
            total.outLevelSum = total.outLevelSum + stat.outLevelSum

            total.newdealSum = total.newdealSum + stat.newdealSum
            total.newredealSum = total.newredealSum + stat.newredealSum
            total.oldredealSum = total.oldredealSum + stat.oldredealSum
            total.holidaydealSum = total.holidaydealSum + stat.holidaydealSum
            total.feedealSum = total.feedealSum + stat.feedealSum

            totalNet.show = totalNet.show + statNet.show
            totalNet.reservation = totalNet.reservation + statNet.reservation
            totalNet.newdeal = totalNet.newdeal + statNet.newdeal

            two.statBranch = stat
            two.statNet = statNet
            if i == 0:
                two.title = u'周二'
            if i == 1:
                two.title = u'周三'
            if i == 2:
                two.title = u'周四'
            if i == 3:
                two.title = u'周五'
            if i == 4:
                two.title = u'周六'
            if i == 5:
                two.title = u'周日'
            if i == 6:
                two.title = u'周一'

            if stat.date == todayBegin:

                todayData = stat

                todayData.netReservation = statNet.reservation
                todayData.netShow = statNet.show
                #todayData.netNewdeal = statNet.newdeal

            stat = UserStat()
            days.append(two)
    totals = Stats()
    totals.statBranch = total
    totals.statNet = totalNet
    studentTotal = 0
    try:
        studentTotal,sus = zhenpustat.getBranchStudent(login_teacher.branch)
    except:
        studentTotal = 0
    return render(request, 'statDayBranch.html', {"login_teacher":login_teacher,
                                             "title":title,"datenow":now.strftime("%-m.%-d"),
                                             "totals":totals,
                                             "searchWeekBegin":searchWeekBegin,
                                             "studentTotal":studentTotal,"sus":sus,
                                             "todayData":todayData,
                                             "days":days})

def indexStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    return render(request, 'indexStat.html', {"login_teacher":login_teacher})

#单个校区老师课时统计
#===============================================================================
# def branchIncome(request):
#     login_teacher = checkCookie(request)
#     if not (login_teacher):
#         return HttpResponseRedirect('/login')
#     #teachers = getTeachers(login_teacher.branch)
#     year = request.GET.get("year")
#     month = request.GET.get("month")
#     branch = request.GET.get("branch")
#     if not branch and login_teacher.cityHeadquarter != login_teacher.branch:
#         branch = login_teacher.branch
#     yearmonth = None
#     branchName = ''
#     b = None
#     if branch:
#         try:
#             b = Branch.objects.get(id=branch)  # @UndefinedVariable
#             branchName = b.branchName
#         except:
#             branch = None
#     searchBegin = None
#     searchEnd = None
#     branchs = []
#     branchs.append(b)
#     if login_teacher.role == constant.Role.admin or login_teacher.role == constant.Role.financial:
#         branchs = utils.getCityBranch(login_teacher.cityId)
#     if year and month and branch:
#         yearmonth = year+u'年'+month+u'月'
#         searchBegin = datetime.datetime.strptime(year+'-'+month+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
#
#         m = int(month)+1
#         y = int(year)
#         if m == 13:
#             y = y + 1
#             m = 1
#         searchEnd = datetime.datetime.strptime(str(y)+'-'+str(m)+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
#
#     else:
#         return render(request, 'branchIncome.html', {"login_teacher":login_teacher,
#                                                      "branchName":branchName,
#                                                      "branch":branch,"branchs":branchs})
#
#     all = []
#     branchMonth = BranchIncome() #getBranchIncome(login_teacher.branch,searchBegin,searchEnd)
#     branchMonth.eve = 0
#     branchMonth.sum = 0
#     branchMonth.lessons = 0
#     branchMonth.sumFirst4 = 0
#     teachers,students = dbsearch.branchIncome(branch,searchBegin,searchEnd)
#
#     for searchMonth in teachers:
#         if login_teacher.role > constant.Role.teacher or login_teacher.role == constant.Role.teacher and searchMonth.teacher_oid == login_teacher.id:
#           if searchMonth.sum:
#             searchMonth.duePay = int(searchMonth.payRatio * searchMonth.sum / 100)
#             if searchMonth.lessons-searchMonth.first4 > 0 :
#                 searchMonth.eve = int(searchMonth.sum/searchMonth.lessons-searchMonth.first4)
#           all.append(searchMonth)
#
#         branchMonth.sum = searchMonth.sum + branchMonth.sum + searchMonth.sumFirst4
#         branchMonth.lessons = searchMonth.lessons + branchMonth.lessons
#         branchMonth.sumFirst4 = branchMonth.sumFirst4 + searchMonth.sumFirst4
#         temp = []
#         for s in students:
#           if login_teacher.role > constant.Role.teacher or login_teacher.role == constant.Role.teacher and searchMonth.teacher_oid == login_teacher.id:
#             if s.teacher_oid == searchMonth.teacher_oid:
#                 s.teacher_oid = None
#                 temp.append(s)
#         temp = sorted(temp, key=attrgetter('teacherName'),reverse=False)
#         for s in temp:
#             all.append(s)
#
#     if branchMonth.lessons > 0:
#         branchMonth.eve = int(branchMonth.sum/branchMonth.lessons)
#     if login_teacher.role > constant.Role.teacher:
#         all.append(branchMonth)
#     return render(request, 'branchIncome.html', {"login_teacher":login_teacher,
#                                                  "all":all,"branchMonth":branchMonth,
#                                                  "year":year,
#                                                  "month":month,
#                                                  "branch":branch,"branchName":branchName,
#                                                  "branchs":branchs
#                                                  })
#===============================================================================

#单个校区老师课时统计2
def branchIncome2(request):
    reload(sys)
    sys.setdefaultencoding('utf8')  # @UndefinedVariable
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    #teachers = getTeachers(login_teacher.branch)
    year = request.GET.get("year")
    month = request.GET.get("month")
    branch = request.GET.get("branch")
    if not branch and login_teacher.cityHeadquarter != login_teacher.branch:
        branch = login_teacher.branch
    yearmonth = None
    branchName = ''
    b = None
    if branch:
        try:
            b = Branch.objects.get(id=branch)  # @UndefinedVariable
            branchName = b.branchName
        except:
            branch = None
    searchBegin = None
    searchEnd = None
    branchs = []
    branchs.append(b)
    if login_teacher.role == constant.Role.admin or login_teacher.branch == constant.BJ_CAIWU or login_teacher.branch == '5ab86f1f97a75d3c74041a68':
        branchs = utils.getCityBranch(login_teacher.cityId)
    if year and month and branch:
        yearmonth = year+u'年'+month+u'月'
        searchBegin = datetime.datetime.strptime(year+'-'+month+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")

        m = int(month)+1
        y = int(year)
        if m == 13:
            y = y + 1
            m = 1
        searchEnd = datetime.datetime.strptime(str(y)+'-'+str(m)+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")

    else:
        return render(request, 'branchIncome2.html', {"login_teacher":login_teacher,
                                                     "branchName":branchName,
                                                  "branch":branch,"branchs":branchs})
    teacherOnly = None
    if login_teacher.role == constant.Role.teacher and login_teacher.branchType == str(constant.BranchType.school):
        teacherOnly = login_teacher.id
    r = request.GET.get("r")
    teacherIncomes,branchData = dbsearch.branchIncome2(branch,searchBegin,searchEnd,teacherOnly,r)
    if login_teacher.role < 5:
        temp = []
        for tt in teacherIncomes:

            if tt['name'] == login_teacher.teacherName:
                temp.append(tt)
                break
        teacherIncomes = temp

    return render(request, 'branchIncome2.html', {"login_teacher":login_teacher,
                                                 "branchData":branchData,"teacherIncomes":teacherIncomes,
                                                 "year":year,
                                                 "month":month,
                                                 "branch":branch,"branchName":branchName,
                                                 "branchs":branchs
                                                 })

def branchIncomeDue(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    #teachers = getTeachers(login_teacher.branch)
    year = request.GET.get("year")
    month = request.GET.get("month")
    branch = request.GET.get("branch")
    if not branch and login_teacher.cityHeadquarter != login_teacher.branch:
        branch = login_teacher.branch

    cityId = Branch.objects.get(id=branch).city.id  # @UndefinedVariable

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

    yearmonth = None
    branchName = ''
    b = None
    if branch:
        try:
            b = Branch.objects.get(id=branch)  # @UndefinedVariable
            branchName = b.branchName
        except:
            branch = None


    searchBegin = None
    searchEnd = None
    if year and month and branch:
        yearmonth = year+u'年'+month+u'月'
        searchBegin = datetime.datetime.strptime(year+'-'+month+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")

        m = int(month)+1
        y = int(year)
        if m == 13:
            y = y + 1
            m = 1
        searchEnd = datetime.datetime.strptime(str(y)+'-'+str(m)+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")

    query = Q(branch=branch)&((Q(beginDate__lte=searchEnd)&Q(beginDate__gte=searchBegin))|(Q(endDate__lte=searchEnd)&Q(endDate__gte=searchBegin)))
    sus = Suspension.objects.filter(query)  # @UndefinedVariable
    susStudents = {}
    for s in sus:
        susStudents[s.student] = s
    teacherIncomes,branchData = dbsearch.branchIncome2(branch,searchBegin,searchEnd)
    student = {}
    i = 0
    j = 0
    wl = {}
    sf4 = None
    for a in range(7):
        wl[a+1] = 0
        wl[a+1],searchBegin,searchEnd = utils.getWeekLessons(searchBegin,searchEnd,a+1,b.city.id)
        a = a + 1

    for ti in teacherIncomes:
        for s in ti['sc']:
            try:
                if student[s['id']]:
                    j = j + 1
                    continue
            except:
                i = i + 1

                s['lessons'] = wl[s['weekday']]
                try:
                    if susStudents[s['id']]:
                        sle = utils.getWeekLessonsExSus(susStudents[s['id']],searchBegin,searchEnd,s['weekday'],b.city.id)
                        if s['lessons'] > sle:
                            s['lessons'] = sle
                            s['sus'] = susStudents[s['id']].beginDate.strftime("%Y-%m-%d")+u'到'+susStudents[s['id']].endDate.strftime("%Y-%m-%d")
                except:
                    err = 1

                csid = s['id']
                mcs,mfs = dbsearch.MemberContracts(csid,cityId,searchEnd)
                contracts,clessons,firstNewDeal,firstNewRedeal = dbsearch.contractGroup(dbsearch.getStudentContracts(csid,None,holidayCT,searchEnd),mcs,mfs)

                sf4, s['thisPure']= dbsearch.getFirst4_2(s['beforeLessons'],s['lessons'])
                s['consume'],s['consumeFirst4'] = dbsearch.getStudentConsume(s['beforeLessons'],s['thisPure'],s['lessons'],contracts,clessons,firstNewDeal,firstNewRedeal,s['first4'])
                if s['first4'] < 4:
                    s['consumeFirst4'] = 0
                s['thisPure'] = int(s['thisPure'])
                student[s['id']] = s

    return render(request, 'branchIncomeDue.html', {"login_teacher":login_teacher,
                                                 "year":year,
                                                 "month":month,"students":student,
                                                 "branch":branch,"branchName":branchName

                                                 })


#网络部分校区漏斗数据
def statRemainChannelBranch(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    channel = request.GET.get("channel")


#网络部分校区漏斗数据
def statRemainBranch(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    cityId = request.GET.get("city")

    net = request.GET.get("net")

    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            #eDate = eDate + timedelta(days=1)
            eDate = datetime.datetime.strptime(eDate.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
        except:
            eDate = None
    if not beginDate and not endDate:
        if not cityId:
            cityId = str(City.objects.get(sn=1).id)  # @UndefinedVariable
        return render(request, 'branchRemain.html', {"login_teacher":login_teacher,
                                                     "city":cityId,
                                                 "res":None})
    city = City.objects.get(id=cityId)  # @UndefinedVariable
    #redealCT = None
    #holidayC = None
    ctQuery = None
    excludeContract = None
    try:
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
        cts2,ct2Query = dbsearch.getHolidayContractType(city)
        ctQuery = (ctQuery|ct2Query)
        #holidayC = zhenpustat.getVocationContractTypes(city)[0]
        excludeContract = getNoneDealContractTypes(city)
        #redealCT = zhenpustat.getRedealCT(city)
    except:
        excludeContract = None
        ctQuery = None



    #query = Q(city=cityId)&Q(type__ne=1)&Q(sn__ne=9000)
    branches = utils.getCityBranch(cityId,None,1)
    res = []
    all = UserStat()
    all.regAll = 0
    all.regNet = 0
    all.deal = 0
    all.newdeal = 0
    all.newdealAll = 0
    all.refund = 0
    all.refundNet = 0
    all.newdealNet = 0
    all.newdealNetPure = 0
    all.dealPure = 0
    all.dealRatio = 0
    all.reg = 0
    all.regValid = 0
    all.regB = 0
    all.reservation = 0
    all.reservationAll = 0
    all.reservationNet = 0
    all.show = 0
    all.showNet = 0
    all.showAll = 0
    for branch in branches:
        stat = UserStat()
        regNet,regNetValid = getBranchRegNet(login_teacher.branch,branch,bDate,eDate)
        stat.regNet = len(regNet)
        stat.regValid = len(regNetValid)
        unshow,netUnshow = getBranchUnshowNet(login_teacher.branch,branch,bDate,eDate)
        show,netShow,showB = getBranchShowNet(login_teacher.branch,branch,bDate,eDate)
        #newdeal,redeal,newdealNet,redealNet = getBranchDealNet(login_teacher.cityHeadquarter,branch,bDate,eDate,excludeContract,holidayC.id,redealCT)
        newdeal,newdealNet = dbsearch.getBranchDealNewNet(login_teacher.branch, branch, bDate, eDate, ctQuery)
        refund,refundNet = getBranchRefundNet(login_teacher.branch,branch,bDate,eDate,excludeContract=None)
        #stat.show = len(show) - len(netShow)
        stat.showNet = len(netShow)
        #stat.showAll = stat.show + stat.showNet
        #stat.newdeal = len(newdeal)-len(newdealNet)
        stat.newdealNet = len(newdealNet)
        stat.reservationNet = len(netShow) + len(netUnshow)
        stat.refundNet = len(refundNet)
        stat.title = branch.branchName
        stat.oid = branch.id
        stat.teacher
        all.regNet = all.regNet + stat.regNet
        all.regValid = all.regValid + stat.regValid
        all.reservationNet = all.reservationNet + stat.reservationNet
        all.showNet = all.showNet + stat.showNet
        all.newdealNet = all.newdealNet + stat.newdealNet
        all.refundNet = all.refundNet + stat.refundNet
        stat.dealNetRatio = 0
        try:
            if stat.reservationNet>0:
                stat.dealNetRatio = int(float(stat.newdealNet)/float(stat.reservationNet)*100)
        except:
            err = 0

        stat.newdealNetPure = stat.newdealNet - stat.refundNet
        all.newdealNetPure = all.newdealNetPure + stat.newdealNetPure
        if stat.regNet > 0 or stat.regValid > 0 or stat.reservationNet > 0 or stat.showNet > 0 or stat.newdealNet > 0 or stat.dealNetRatio > 0 or stat.refundNet > 0 or stat.newdealNetPure > 0 or not branch.deleted:
            res.append(stat)
    if all.reservationNet > 0:
        all.dealNetRatio = 0
        try:
            all.dealNetRatio = int(float(all.newdealNet)/float(all.reservationNet)*100)
        except:
            err = 1


    return render(request, 'branchRemain.html', {"login_teacher":login_teacher,
                                                 "beginDate":beginDate,
                                                 "endDate":endDate,
                                                 "all":all,
                                                 "net":net,
                                                 "city":cityId,
                                                 "res":res})

#全部校区成交漏斗数据
def allRemainBranch(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    cityId = request.GET.get("city")
    cityName = None
    if cityId:
        cityName = City.objects.get(id=cityId).cityName  # @UndefinedVariable

    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            #eDate = eDate + timedelta(days=1)
            eDate = datetime.datetime.strptime(eDate.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
        except:
            eDate = None
    if not beginDate and not endDate:
        if not cityId:
            cityId = login_teacher.cityId  # @UndefinedVariable
            cityName = login_teacher.city

        return render(request, 'allRemainBranch.html', {"login_teacher":login_teacher,
                                                     "city":cityId,"cityName":cityName,
                                                 "res":None,"all":None})
    city = City.objects.get(id=cityId)  # @UndefinedVariable
    excludeContract = None
    ctQuery = None
    #holidayC = None
    #redealCT = None
    try:
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
        excludeContract = getNoneDealContractTypes(city)
        holidayC = zhenpustat.getVocationContractTypes(city)
        #redealCT = zhenpustat.getRedealCT(city)
    except:
        excludeContract = None
        ctQuery = None



    #query = Q(city=cityId)&Q(type__ne=1)&Q(type__ne=2)
    branches = utils.getCityBranch(cityId)
    res = []
    all = UserStat()
    all.regAll = 0
    all.regNet = 0
    all.deal = 0
    all.newdeal = 0
    all.newdealAll = 0
    all.refund = 0
    all.refundNet = 0
    all.newdealNet = 0
    all.dealPure = 0
    all.dealRatio = 0
    all.reg = 0
    all.regB = 0
    all.reservation = 0
    all.reservationAll = 0
    all.reservationNet = 0
    all.show = 0
    all.showB = 0
    all.showNet = 0
    all.showAll = 0
    for branch in branches:
        stat = UserStat()
        stat.reg = len(getBranchReg(branch,bDate,eDate))

        stat.regB = len(getBranchRegB(branch,bDate,eDate))
        regNet,regNetValid = getBranchRegNet(login_teacher.cityHeadquarter,branch,bDate,eDate)
        stat.regNet = len(regNet)
        stat.regValid = len(regNetValid)



        stat.regAll = stat.reg + stat.regNet

        unshow,netUnshow = getBranchUnshowNet(login_teacher.cityHeadquarter,branch,bDate,eDate)
        show,netShow,showB = getBranchShowNet(login_teacher.cityHeadquarter,branch,bDate,eDate)
        #newdeal,redeal,newdealNet,redealNet = getBranchDealNet(login_teacher.cityHeadquarter,branch,bDate,eDate,excludeContract,holidayC.id,redealCT)
        newdeal,newdealNet = dbsearch.getBranchDealNewNet(login_teacher.cityHeadquarter, branch, bDate, eDate, ctQuery,'all')
        refund,refundNet = getBranchRefundNet(login_teacher.cityHeadquarter,branch,bDate,eDate,excludeContract=holidayC)
        stat.show = len(show) - len(netShow)
        stat.showB = len(showB)
        stat.showNet = len(netShow)
        stat.showAll = stat.show + stat.showNet
        stat.newdeal = len(newdeal)-len(newdealNet)
        stat.newdealNet = len(newdealNet)
        stat.reservation = stat.show + len(unshow)
        stat.reservationNet = len(netShow) + len(netUnshow)
        stat.reservationAll = stat.reservation + stat.reservationNet
        stat.newdealAll = len(newdeal)

        stat.refund = len(refund)
        stat.refundNet = len(refundNet)
        sn = str(branch.sn)
        if branch.sn < 10:
            sn = '0' + sn
        stat.title = sn + branch.branchName
        all.regAll = all.regAll + stat.regAll
        all.reg = all.reg + stat.reg
        all.regB = all.regB + stat.regB
        all.regNet = all.regNet + stat.regNet
        all.reservation = all.reservation + stat.reservation
        all.reservationNet = all.reservationNet + stat.reservationNet
        all.reservationAll = all.reservationAll + stat.reservationAll
        all.show = all.show + stat.show
        all.showB = all.showB + stat.showB
        all.showNet = all.showNet + stat.showNet
        all.showAll = all.showAll + stat.showAll
        all.newdeal = all.newdeal + stat.newdeal
        all.newdealAll = all.newdealAll + stat.newdealAll
        all.newdealNet = all.newdealNet + stat.newdealNet
        all.refund = all.refund + stat.refund
        all.refundNet = all.refundNet + stat.refundNet
        try:
            if stat.show>0:
                stat.dealRatio = int(float(stat.newdeal)/float(stat.show)*100)
            if stat.showNet>0:
                stat.dealNetRatio = int(float(stat.newdealNet)/float(stat.showNet)*100)
            if stat.showNet+stat.show>0:
                stat.dealAllRatio = int(float(stat.newdealNet+stat.newdeal)/float(stat.showNet+stat.show)*100)
        except:
            err = 0
        stat.dealPure = stat.newdealAll - stat.refund
        res.append(stat)
    if all.reservation > 0:
        try:
            all.dealRatio = int(float(all.newdeal)/float(all.reservation)*100)
            all.dealNetRatio = int(float(all.newdealNet)/float(all.reservationNet)*100)
        except:
            err = 1
    try:
        if all.show>0:
            all.dealRatio = int(float(all.newdeal)/float(all.show)*100)
        if all.showNet>0:
            all.dealNetRatio = int(float(all.newdealNet)/float(all.showNet)*100)
        if all.showNet+all.show>0:
            all.dealAllRatio = int(float(all.newdealNet+all.newdeal)/float(all.showNet+all.show)*100)

        all.dealPure = all.newdealAll - all.refund
    except Exception,e:
        print e


    return render(request, 'allRemainBranch.html', {"login_teacher":login_teacher,
                                                 "beginDate":beginDate,
                                                 "endDate":endDate,
                                                 "all":all,
                                                 "city":cityId,"cityName":cityName,
                                                 "res":res})


def allBranchRevenue(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    cityId = request.GET.get("city")
    cityName = None
    if cityId:
        cityName = City.objects.get(id=cityId).cityName  # @UndefinedVariable

    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not beginDate and not endDate:
        if not cityId:
            cityId = login_teacher.cityId  # @UndefinedVariable
            cityName = login_teacher.city
        bDate = utils.getDateNow(8)
        eDate = bDate
        beginDate = bDate.strftime("%Y-%m-%d")
        endDate = beginDate
        #return render(request, 'allBranchRevenue.html', {"login_teacher":login_teacher,
         #                                            "city":cityId,"cityName":cityName,
          #                                       "res":None,"all":None})
    city = City.objects.get(id=cityId)  # @UndefinedVariable
    cts,ctQuery = dbsearch.getNormalContractTypes(city)

    query = Q(city=cityId)&Q(type__ne=1)&Q(sn__ne=9000)
    branches = utils.getCityBranch(cityId,None,1)#Branch.objects.filter(query).order_by("sn") # @UndefinedVariable
    res = []

    for branch in branches:
        stat = UserStat()
        stat.deal = 0
        stat.dualPure = 0
        sn = str(branch.sn)
        if branch.sn < 10:
            sn = '0' + sn
        stat.sn = sn
        stat.title = branch.branchName
        stat.deal = util2.getBranchRevenue(branch.id,bDate,eDate)
        stat.refund = util2.getBranchRefund(branch.id,bDate,eDate)

        #deals = dbsearch.getBranchDealNew(branch.id,bDate,eDate,ctQuery)
        newdeal,newredeal,oldredeal,holiday,holidayDeal,holidayDealNet,free,newDealSchool,newDealNet,newContractsSchool,newContractsNet,newRedealContracts,oldRedealContracts,newContractList,newRedealContractList,oldRedealContractList,holidayDeals,feeDeals,lessonFeeContracts,lessonFee = dbsearch.getBranchAllDeal(branch.id, bDate, eDate,city.dealDuration)
        level,sale,other,levels,sales,others,outLevel,outLevels = dbsearch.getBranchAllOtherIncomeItemNumber(branch.id,bDate,eDate)
        goneStudents = dbsearch.getGoneStudents(branch.id,bDate,eDate)
        deposit,dnum = dbsearch.getBranchDeposit(branch.id,bDate,eDate,None,1,0)

        stat.lessonFeeContracts = lessonFeeContracts
        stat.lessonFee = lessonFee
        stat.feedealSum = 0
        for c in feeDeals:
                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.feedealSum = stat.feedealSum + paid
                if str(c.branch.id) == '58c1343b97a75d4702a2d5e1':
                    print '[fz feesum now]'+str(stat.feedealSum)

        stat.deposit = deposit
        #stat.deal = stat.deal + deposit
        stat.newdeal = newdeal
        stat.newdealSchool = newDealSchool
        stat.newdealNet = newDealNet
        stat.redealNew = newredeal
        stat.redealOld = oldredeal
        stat.hc = holiday
        stat.level = 0
        stat.outLevel = 0
        stat.sale = 0
        stat.other = 0
        stat.holidayDeal = holidayDeal
        stat.holidayDealNet = holidayDealNet
        stat.newdeal = stat.newdeal + holidayDeal
        stat.newdealNet = newDealNet
        stat.gone = len(goneStudents)

        stat.newdealSum = 0
        stat.newredealSum = 0
        stat.oldredealSum = 0
        stat.holidaydealSum = 0

        for income in levels:
            stat.level = stat.level + income.paid
        for income in outLevels:
            stat.outLevel = stat.outLevel + income.paid
        for income in sales:
            stat.sale = stat.sale + income.paid
        for income in others:
            stat.other = stat.other + income.paid



        for c in newContractList:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.newdealSum = stat.newdealSum + paid


        for c in newRedealContractList:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.newredealSum = stat.newredealSum + paid

        for c in oldRedealContractList:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.oldredealSum = stat.oldredealSum + paid
        for c in holidayDeals:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.holidaydealSum = stat.holidaydealSum + paid


        if stat.newdealSum > 0 or stat.newredealSum > 0 or stat.oldredealSum > 0 or stat.deposit > 0 or stat.feedealSum > 0 or stat.holidaydealSum > 0 or stat.sale > 0 or stat.level > 0 or stat.outLevel > 0 or stat.other > 0 or stat.refund > 0 or not branch.deleted:
            res.append(stat)

    stat2 = UserStat()
    stat2.deal = 0
    stat2.online = 0

    stat2.sn = '99'
    #stat2.title = u'9.9转化网课'
    cs = util2.getOnlineRevenue(bDate,eDate)
    for c in cs:
        #print c.student_oid + '[]'+str(c.paid)
        stat2.deal = stat2.deal + c.paid
        stat2.online = stat2.online + 1

    return render(request, 'allBranchRevenue.html', {"login_teacher":login_teacher,
                                                     "stat2":stat2,
                                                 "beginDate":beginDate,
                                                 "endDate":endDate,
                                                 "city":cityId,"cityName":cityName,
                                                 "res":res})



#全部校区收入数据v2
def allBranchRevenue2(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    cityId = request.GET.get("city")
    cityName = None
    if cityId:
        cityName = City.objects.get(id=cityId).cityName  # @UndefinedVariable

    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not cityId:
        cityId = login_teacher.cityId  # @UndefinedVariable
        cityName = login_teacher.city
    city = City.objects.get(id=cityId)  # @UndefinedVariable
    NB = ''
    try:
        NB = Branch.objects.get(id=constant.NET_BRANCH).branchName
    except Exception,E:
        NB = '网络'
    if not beginDate and not endDate:
        #=======================================================================
        # if not cityId:
        #     cityId = login_teacher.cityId  # @UndefinedVariable
        #     cityName = login_teacher.city
        # bDate = utils.getDateNow(8)
        # eDate = bDate
        # beginDate = bDate.strftime("%Y-%m-%d")
        # endDate = beginDate
        #=======================================================================

        return render(request, 'allBranchRevenue2.html', {"login_teacher":login_teacher,"NB":NB,
                                                 "beginDate":None,"city":city.id,"cityName":city.cityName,
                                                 "endDate":None})

    cts,ctQuery = dbsearch.getNormalContractTypes(city)

    query = Q(city=cityId)&Q(type__ne=1)&Q(sn__ne=9000)
    branches = utils.getCityBranch(cityId,None)#Branch.objects.filter(query).order_by("sn") # @UndefinedVariable

    bsum = branches.count()

    return render(request, 'allBranchRevenue2.html', {"login_teacher":login_teacher,
                                                 "beginDate":beginDate,"NB":NB,
                                                 "endDate":endDate,
                                                 "city":cityId,"cityName":cityName,
                                                 "bsum":bsum,
                                                 "branches":branches})


#某校区收入数据
@csrf_exempt
def oneBranchRevenue(request):
    res = None
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginDate = request.POST.get("beginDate")
    endDate = request.POST.get("endDate")
    cityId = request.POST.get("city")
    branchId = request.POST.get("branchId")
    branch = None
    cityName = None
    try:
        branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    except:
        branch = None

    try:
        cityName = City.objects.get(id=cityId).cityName  # @UndefinedVariable
    except:
        cityName = None

    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not beginDate and not endDate:
        if not cityId:
            cityId = login_teacher.cityId  # @UndefinedVariable
            cityName = login_teacher.city
        bDate = utils.getDateNow(8)
        eDate = bDate
        beginDate = bDate.strftime("%Y-%m-%d")
        endDate = beginDate
        #return render(request, 'allBranchRevenue.html', {"login_teacher":login_teacher,
         #                                            "city":cityId,"cityName":cityName,
          #                                       "res":None,"all":None})
    city = City.objects.get(id=cityId)  # @UndefinedVariable
    cts,ctQuery = dbsearch.getNormalContractTypes(city)


    #for branch in branches:

    if branch:
      try:

        stat = UserStat()
        stat.deal = 0
        stat.dualPure = 0
        sn = str(branch.sn)
        if branch.sn < 10:
            sn = '0' + sn
        stat.sn = sn
        stat.title = branch.branchName

        stat.deal = util2.getBranchRevenue(branch.id,bDate,eDate)
        stat.refund = util2.getBranchRefund(branch.id,bDate,eDate)

        #deals = dbsearch.getBranchDealNew(branch.id,bDate,eDate,ctQuery)
        newdeal,newredeal,oldredeal,holiday,holidayDeal,holidayDealNet,free,newDealSchool,newDealNet,newContractsSchool,newContractsNet,newRedealContracts,oldRedealContracts,newContractList,newRedealContractList,oldRedealContractList,holidayDeals,feeDeals,lessonFeeContracts,lessonFee = dbsearch.getBranchAllDeal(branch.id, bDate, eDate,city.dealDuration)
        level,sale,other,levels,sales,others,outLevel,outLevels = dbsearch.getBranchAllOtherIncomeItemNumber(branch.id,bDate,eDate)
        goneStudents = dbsearch.getGoneStudents(branch.id,bDate,eDate)
        deposit,dnum = dbsearch.getBranchDeposit(branch.id,bDate,eDate,None,1)



        stat.lessonFeeContracts = lessonFeeContracts
        stat.lessonFee = lessonFee
        stat.feedealSum = 0


        for c in feeDeals:
                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.feedealSum = stat.feedealSum + paid


        stat.deposit = deposit
        #stat.deal = stat.deal + deposit
        stat.newdeal = newdeal
        stat.newdealSchool = newDealSchool
        stat.newdealNet = newDealNet
        stat.redealNew = newredeal
        stat.redealOld = oldredeal
        stat.hc = holiday
        stat.level = 0
        stat.outLevel = 0
        stat.sale = 0
        stat.other = 0
        stat.holidayDeal = holidayDeal
        stat.holidayDealNet = holidayDealNet
        stat.newdeal = stat.newdeal + holidayDeal
        stat.newdealNet = newDealNet
        stat.gone = len(goneStudents)

        stat.newdealSum = 0
        stat.newredealSum = 0
        stat.oldredealSum = 0
        stat.holidaydealSum = 0

        for income in levels:
            stat.level = stat.level + income.paid
        for income in outLevels:
            stat.outLevel = stat.outLevel + income.paid
        for income in sales:
            stat.sale = stat.sale + income.paid
        for income in others:
            stat.other = stat.other + income.paid



        for c in newContractList:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.newdealSum = stat.newdealSum + paid


        for c in newRedealContractList:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.newredealSum = stat.newredealSum + paid

        for c in oldRedealContractList:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.oldredealSum = stat.oldredealSum + paid


        for c in holidayDeals:
            paid = 0
            if c.paid > 0:
                paid = c.paid
            elif c.contractType.discountPrice > 0:
                paid = c.contractType.discountPrice
            stat.holidaydealSum = stat.holidaydealSum + paid


        if stat.newdealSum > 0 or stat.newredealSum > 0 or stat.oldredealSum > 0 or stat.deposit > 0 or stat.feedealSum > 0 or stat.holidaydealSum > 0 or stat.sale > 0 or stat.level > 0 or stat.outLevel > 0 or stat.other > 0 or stat.refund > 0 or not branch.deleted:
            res = stat
      except Exception,e:
          print e

    res = {"error": 0, "sn":branch.sn}
    res['sn'] = stat.sn
    res['title'] = stat.title
    res["newdeal"] = stat.newdeal
    res["newdealNet"] = stat.newdealNet
    res["redealNew"] = stat.redealNew
    res["redealOld"] = stat.redealOld
    res["gone"] = stat.gone
    res["newdealSum"] = stat.newdealSum
    res["newredealSum"] = stat.newredealSum
    res["oldredealSum"] = stat.oldredealSum
    res["feedealSum"] = stat.feedealSum
    res["holidaydealSum"] = stat.holidaydealSum
    res["level"] = stat.level
    res["sale"] = stat.sale
    res["other"] = stat.other
    res["deal"] = stat.deal
    res["outLevel"] = stat.outLevel
    res["deposit"] = stat.deposit
    res["refund"] = stat.refund


    return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    #return render(request, 'allBranchRevenue.html', {"login_teacher":login_teacher,
     #                                            "beginDate":beginDate,
      #                                           "endDate":endDate,
       #                                          "city":cityId,"cityName":cityName,
        #                                         "res":res})

#全部校区报表数据
def allBranchReport(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    cityId = request.GET.get("city")
    cityName = None
    if cityId:
        cityName = City.objects.get(id=cityId).cityName  # @UndefinedVariable

    bDate = None
    eDate = None
    if beginDate:
        try:
            bDate = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        except:
            bDate = None
    if endDate:
        try:
            eDate = datetime.datetime.strptime(endDate,"%Y-%m-%d")
            eDate = eDate + timedelta(days=1)
        except:
            eDate = None
    if not beginDate and not endDate:
        if not cityId:
            cityId = login_teacher.cityId  # @UndefinedVariable
            cityName = login_teacher.city
        bDate = utils.getDateNow(8)
        eDate = bDate
        beginDate = bDate.strftime("%Y-%m-%d")
        endDate = beginDate
        #return render(request, 'allBranchRevenue.html', {"login_teacher":login_teacher,
         #                                            "city":cityId,"cityName":cityName,
          #                                       "res":None,"all":None})
    city = City.objects.get(id=cityId)  # @UndefinedVariable
    cts,ctQuery = dbsearch.getNormalContractTypes(city)

    query = Q(city=cityId)&Q(type__ne=1)&Q(sn__ne=9000)
    branches = utils.getCityBranch(cityId,None,1)#Branch.objects.filter(query).order_by("sn") # @UndefinedVariable
    res = []

    for branch in branches:
        stat = UserStat()
        stat.deal = 0
        stat.dualPure = 0
        sn = str(branch.sn)
        if branch.sn < 10:
            sn = '0' + sn
        stat.sn = sn
        stat.title = branch.branchName
        stat.deal = util2.getBranchRevenue(branch.id,bDate,eDate)
        stat.refund = util2.getBranchRefund(branch.id,bDate,eDate)

        #deals = dbsearch.getBranchDealNew(branch.id,bDate,eDate,ctQuery)
        newdeal,newredeal,oldredeal,holiday,holidayDeal,holidayDealNet,free,newDealSchool,newDealNet,newContractsSchool,newContractsNet,newRedealContracts,oldRedealContracts,newContractList,newRedealContractList,oldRedealContractList,holidayDeals,feeDeals,lessonFeeContracts,lessonFee = dbsearch.getBranchAllDeal(branch.id, bDate, eDate,city.dealDuration)
        level,sale,other,levels,sales,others,outLevel,outLevels = dbsearch.getBranchAllOtherIncomeItemNumber(branch.id,bDate,eDate)
        deposit,dnum = dbsearch.getBranchDeposit(branch.id,bDate,eDate,None,1)


        stat.lessonFeeContracts = lessonFeeContracts
        stat.lessonFee = lessonFee
        stat.feedealSum = 0
        for c in feeDeals:
                paid = 0
                if c.paid > 0:
                    paid = c.paid
                elif c.contractType.discountPrice > 0:
                    paid = c.contractType.discountPrice
                stat.feedealSum = stat.feedealSum + paid

        stat.deposit = deposit
        #stat.deal = stat.deal + deposit
        stat.newdeal = newdeal
        stat.newdealSchool = newDealSchool
        stat.newdealNet = newDealNet
        stat.redealNew = newredeal
        stat.redealOld = oldredeal
        stat.hc = holiday
        stat.level = level
        stat.outLevel = outLevel
        stat.sale = sale
        stat.holidayDeal = holidayDeal
        stat.holidayDealNet = holidayDealNet
        stat.newdeal = stat.newdeal + holidayDeal
        stat.newdealNet = newDealNet
        stat.other = other
        if stat.newdeal > 0 or stat.redealNew > 0 or stat.redealOld > 0 or stat.hc > 0 or stat.feedealSum > 0 or stat.sale > 0 or stat.level > 0 or stat.outLevel > 0 or stat.other > 0 or stat.refund > 0 or not branch.deleted:
            res.append(stat)


    return render(request, 'allBranchReport.html', {"login_teacher":login_teacher,
                                                 "beginDate":beginDate,
                                                 "endDate":endDate,
                                                 "city":cityId,"cityName":cityName,
                                                 "res":res})
#网络部总转化率表
def statRatioBranch(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    net = request.GET.get("net")
    year = request.GET.get("year")
    month = request.GET.get("month")
    cityId = request.GET.get("city")
    if not year:
        return render(request, 'branchRatio.html', {"login_teacher":login_teacher,
                                                     "city":"5867c05d3010a51fa4f5abe5",
                                                     "year":"2017"
                                              })
    try:
        city = City.objects.get(id=cityId)  # @UndefinedVariable
    except:
        city = None
    excludeContract = None
    try:
        excludeContract = getNoneDealContractTypes(city)
        redealCT = zhenpustat.getRedealCT(city)
    except:
        excludeContract = None
    yearmonth = ''
    searchBegin = None
    searchEnd = None
    m = 13
    y = int(year)
    if year:
        yearmonth = year
    if month:
        yearmonth = yearmonth + '-' + month
        m = int(month)
    else:
        m=13
        yearmonth = year + '-01'
    try:
        searchBegin = datetime.datetime.strptime(yearmonth+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    except:
        searchBegin = None
    m = m + 1
    if m == 13:
        y = y + 1
        m = 1
    try:
        searchEnd = datetime.datetime.strptime(str(y)+'-'+str(m)+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
    except:
        searchEnd = None

    res = []

    if not month:
        endMonth = int(getDateNow().strftime("%m"))
        yearStat = UserStat()
        for i in range(endMonth):
            m = i+1
            nm = m+1
            searchBegin = datetime.datetime.strptime(searchBegin.strftime("%Y")+'-'+str(m)+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
            searchEnd = datetime.datetime.strptime(searchBegin.strftime("%Y")+'-'+str(nm)+'-01 00:00:00',"%Y-%m-%d %H:%M:%S")
            stat = getBranchRatio(login_teacher.cityHeadquarter,None,searchBegin,searchEnd,net,excludeContract)
            stat.title = str(m)+u'月'
            if yearStat.reg:
                yearStat.reg = yearStat.reg + stat.reg
            else:
                yearStat.reg = stat.reg
            if yearStat.regValid:
                yearStat.regValid = yearStat.regValid + stat.regValid
            else:
                yearStat.regValid = stat.regValid
            if yearStat.show:
                yearStat.show = yearStat.show + stat.show
            else:
                yearStat.show = stat.show
            if yearStat.notShow:
                yearStat.notShow = yearStat.notShow + stat.notShow
            else:
                yearStat.notShow = stat.notShow
            if yearStat.deal:
                yearStat.deal = yearStat.deal + stat.deal
            else:
                yearStat.deal = stat.deal
            if yearStat.refund:
                yearStat.refund = yearStat.refund + stat.refund
            else:
                yearStat.refund = stat.refund

            res.append(stat)

        yearStat = fillStat(yearStat,u'合计')
        res.append(yearStat)

    else:
        stat = getBranchRatio(login_teacher.cityHeadquarter,None,searchBegin,searchEnd,net,excludeContract)
        stat.title = str(month)+u'月'
        res.append(stat)

    return render(request, 'branchRatio.html', {"login_teacher":login_teacher,
                                                "city":cityId,
                                                "year":year,
                                                "month":month,
                                                "res":res
                                                 })
#校区老师各项成绩统计
def statTeacher(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    net = request.GET.get("net")
    branch = request.GET.get("branch")
    if not branch:
        branch = login_teacher.branch
    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    searchBegin = None
    searchEnd = None
    searchEnd2 = None
    if not beginDate or not endDate:
        return render(request, 'statTeacher.html', {"login_teacher":login_teacher,
                                                     "err":""})
    try:
        searchBegin = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        searchEnd2 = datetime.datetime.strptime(endDate,"%Y-%m-%d")
        #searchEnd = searchEnd2 + timedelta(days=1)
        searchEnd = datetime.datetime.strptime(searchEnd2.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    except:
        return render(request, 'statTeacher.html', {"login_teacher":login_teacher,
                                                    "err":"date err"
                                        })
    if not searchBegin or not searchEnd:
        return render(request, 'statTeacher.html', {"login_teacher":login_teacher,
                                                    "err":"date err"})
    cityId = login_teacher.cityId
    try:
        city = City.objects.get(id=cityId)  # @UndefinedVariable
    except:
        city = None
    #excludeContract = None
    ctQuery = None
    try:
        #excludeContract = getNoneDealContractTypes(city)
        #redealCT = zhenpustat.getRedealCT(city)
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
    except:
        #excludeContract = None
        ctQuery = None
    #reg,show,newdeal,refund = getBranchStat(login_teacher.branch,searchBegin,searchEnd,excludeContract)
    res = []

    reg = getBranchRegB(branch,searchBegin,searchEnd)
    show,showNet,showB = getBranchShowNet(login_teacher.cityHeadquarter,login_teacher.branch,searchBegin,searchEnd)
    #newdeal,redeal,newdealNet,redealNet = getBranchDealNet(login_teacher.cityHeadquarter,login_teacher.branch,searchBegin,searchEnd,excludeContract,None,redealCT)
    newdeal,newdealNet = dbsearch.getBranchDealNewNet(login_teacher.cityHeadquarter, login_teacher.branch, searchBegin, searchEnd2, ctQuery,'all')
    refund = getBranchRefund(login_teacher.branch,searchBegin,searchEnd,None)

    teachers = getTeachers(login_teacher.branch)
    for teacher in teachers:
        stat = zhenpustat.teacherStat2(teacher,searchBegin,searchEnd,newdeal)
        stat.title = teacher.name
        res.append(stat)
    sumStat = UserStat(title=u'合计')
    sumStat.reg = len(reg)
    sumStat.show = len(showB)
    sumStat.demo = len(show)
    sumStat.demoDeal = len(newdeal)
    if sumStat.demo > 0:
        sumStat.dealRatio = int(round((float)(sumStat.demoDeal)/(float)(sumStat.demo)*100,0))
    sumStat.demoNet = len(showNet)
    sumStat.demoDealNet = len(newdealNet)
    if sumStat.demoNet > 0:
        sumStat.dealNetRatio = int(round((float)(sumStat.demoDealNet)/(float)(sumStat.demoNet)*100,0))

    res.append(sumStat)

    return render(request, 'statTeacher.html', {"login_teacher":login_teacher,
                                                "beginDate":beginDate,
                                                "endDate":endDate,
                                                "res":res
                                                 })
#网络部分渠道统计
def netSourceStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityID = request.GET.get("cityID")
    if not cityID:
        cityID = constant.BEIJING
    city = City.objects.get(id=cityID)  # @UndefinedVariable

    begin = request.GET.get("beginDate")
    end = request.GET.get("endDate")
    beginDate = None
    endDate =  None
    try:
        beginDate = datetime.datetime.strptime(begin+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        endDate = datetime.datetime.strptime(end+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        endDate = endDate + timedelta(days=1)
    except:
        return render(request, 'netSourceStat.html', {"login_teacher":login_teacher,"city":city,
                                                     "err":"date err"})

    sum,all = getNetSourceStat(login_teacher.branch,city,beginDate,endDate,None)
    return render(request, 'netSourceStat.html', {"login_teacher":login_teacher,
                                                  "city":city,
                                                "beginDate":begin,
                                                "endDate":end,
                                                "all":all,
                                                "sum":sum

                                                 })
# 校区分渠道统计
def branchSourceStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branchId = request.GET.get("branchId")
    begin = request.GET.get("beginDate")
    end = request.GET.get("endDate")
    beginDate = None
    endDate =  None
    try:
        beginDate = datetime.datetime.strptime(begin+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        endDate = datetime.datetime.strptime(end+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        endDate = endDate + timedelta(days=1)
    except:
        return render(request, 'branchSourceStat.html', {"login_teacher":login_teacher,
                                                     "err":"date err"})
    if not branchId:
        branchId = login_teacher.branch
    branch = Branch.objects.get(id=branchId)  # @UndefinedVariable
    all = zhenpustat.branchSourceStat(branch,beginDate,endDate)
    net = None
    isAll = ''
    if login_teacher.cityHeadquarter and login_teacher.cityHeadquarter != None:
        isAll = 'all'
    if True:
        #net,net2 = zhenpustat.getNetSourceStat(None, login_teacher.cityId, beginDate,endDate, None, branch,isAll)
        net = zhenpustat.getNetBranSourceStat(branch, beginDate, endDate)
    isNet = 0
    if login_teacher.branch == constant.NET_BRANCH:
        isNet = 1
    return render(request, 'branchSourceStat.html', {"login_teacher":login_teacher,"isNet":isNet,
                                                  "branch":branch,
                                                "beginDate":begin,
                                                "endDate":end,
                                                "all":all,"net":net


                                                 })

#老师拜访大排行统计
def statTReg(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityID = request.GET.get("city")
    if not cityID:
        cityID = login_teacher.cityId
    city = City.objects.get(id=cityID)  # @UndefinedVariable
    begin = request.GET.get("beginDate")

    type = request.GET.get("dateType")
    beginDate = None
    endDate =  None
    try:
        beginDate = datetime.datetime.strptime(begin+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        if type == 'week':
            beginDate = utils.getWeekBegin(beginDate, False)
            endDate = beginDate + timedelta(days=7)
        if type == 'month':
            beginDate = utils.getThisMonthBegin(beginDate)
            endDate = utils.monthLastDay(beginDate)

            endDate = endDate + timedelta(days=1)
            endDate = utils.getThisMonthBegin(endDate)
    except:
        beginDate = None
        #return render(request, 'statTReg.html', {"login_teacher":login_teacher,"city":city,
         #                                            "err":"date err"})

    #firstDay,lastDay,lastWeekFirstDay,nextWeekFirstDay = utils.getWeekFirstDay(beginDate)


    all,beginDate,endDate = util3.getWeekReg(city.id,beginDate,endDate)
    msg = None
    if not all:
        msg = u'数据未生成，请联系管理员重新生成本次搜索日期区间的统计数据'

    #===========================================================================
    # branches = utils.getCityBranch(city.id)
    # query = None
    # i = 0
    # for b in branches:
    #     if i == 0:
    #         query = Q(branch=b)
    #     else:
    #         query=query|Q(branch=b)
    #     i = i + 1
    # query = (query)&Q(status__ne=-1)&Q(role__lt=9)
    # teachers = Teacher.objects.filter(query)  # @UndefinedVariable
    # all = []
    # deals = []
    # for teacher in teachers:
    #     stat = zhenpustat.teacherStat2(teacher,beginDate,endDate,deals)
    #     stat.title = teacher.name
    #     stat.teacher = teacher
    #     all.append(stat)
    #===========================================================================

    endDate = endDate - timedelta(days=1)

    return render(request, 'statTReg.html', {"login_teacher":login_teacher,
                                                  "city":cityID,
                                                "beginDate":beginDate.strftime("%Y-%m-%d"),
                                                "endDate":endDate.strftime("%Y-%m-%d"),
                                                "city":city,"dateType":type,
                                                "all":all,"msg":msg
                                                 })

#网络部客户未联系统计
def netBranchRemindStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityId = request.GET.get("cityId")
    cityName = login_teacher.city
    city = login_teacher.cityId
    res = []
    days = []
    daysData = []
    index = []
    netstat = None
    if cityId:
        branches = utils.getCityBranch(constant.BEIJING)
        todayBegin = datetime.datetime.strptime(getDateNow().strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        todayEnd = datetime.datetime.strptime(getDateNow().strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
        weekBegin = getWeekBegin(todayBegin)
        weekEnd = weekBegin + timedelta(days=6)
        res = []
        millis = int(round(time.time() * 1000))
        i = 0
        for branch in branches:
            dayMap = []
            if branch.type != 1 and branch.type != 2:
                dayMap.append(branch.branchName)
                beforeReminds = dbsearch.getRemindNet(branch,None,todayBegin,login_teacher.branch)
                if not 'b' in days:
                    days.append('b')
                dayMap.append(len(beforeReminds))
                todayReminds = dbsearch.getRemindNet(branch,todayBegin,todayEnd,login_teacher.branch)
                if not 't' in days:
                    days.append('t')
                dayMap.append(len(todayReminds))
                day = todayBegin
                while day >= todayBegin and day < weekEnd:
                    day = day + timedelta(days=1)
                    day1 = datetime.datetime.strptime(day.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
                    dayReminds = dbsearch.getRemindNet(branch,day,day1,login_teacher.branch)
                    dayname = str(day.weekday()+1)
                    if not dayname in days:
                        days.append(dayname)
                    dayMap.append(len(dayReminds))

                daysData.append(dayMap)
                i = i + 1

        if True:
            dayMap = []
            if True:
                branch = Branch.objects.get(id=login_teacher.branch)  # @UndefinedVariable
                dayMap.append(branch.branchName)
                beforeReminds = dbsearch.getRemindNetNet(None,None,todayBegin,login_teacher.branch)
                if not 'b' in days:
                    days.append('b')
                dayMap.append(len(beforeReminds))
                todayReminds = dbsearch.getRemindNetNet(None,todayBegin,todayEnd,login_teacher.branch)
                if not 't' in days:
                    days.append('t')
                dayMap.append(len(todayReminds))
                day = todayBegin
                while day >= todayBegin and day < weekEnd:
                    day = day + timedelta(days=1)
                    day1 = datetime.datetime.strptime(day.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
                    dayReminds = dbsearch.getRemindNetNet(None,day,day1,login_teacher.branch)
                    dayname = str(day.weekday()+1)
                    if not dayname in days:
                        days.append(dayname)
                    dayMap.append(len(dayReminds))

                netstat = dayMap





        i = 0
        for d in days:
            i = i + 1
            index.append(i)
        millis = int(round(time.time() * 1000)) - millis

    return render(request, 'netBranchRemindStat.html', {"login_teacher":login_teacher,
                                                "res":daysData,"days":days,"netstat":netstat,
                                                "city":city,"cityName":cityName,"index":index
                                                 })
#各校区客户跟踪情况统计
def allBranchRemindStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityId = request.GET.get("cityId")
    cityName = login_teacher.city
    city = login_teacher.cityId
    res = []
    todayBegin = datetime.datetime.strptime(getDateNow().strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    todayEnd = datetime.datetime.strptime(getDateNow().strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    weekBegin = getWeekBegin(todayBegin)
    weekEnd = weekBegin + timedelta(days=6)
    if cityId:

        branches = utils.getCityBranch(cityId)

        res = []
        millis = int(round(time.time() * 1000))
        for branch in branches:
            if branch.type != 1:
                stat = UserStat(branch=branch)
                todayReminds = dbsearch.getRemind(branch,todayBegin,todayEnd)
                weekReminds = dbsearch.getRemind(branch,weekBegin,weekEnd)
                weekBeforeReminds = dbsearch.getRemind(branch,None,weekBegin)
                stat.show = len(todayReminds)
                stat.showNet = len(weekReminds)
                stat.notShow = len(weekBeforeReminds)
                res.append(stat)
        millis = int(round(time.time() * 1000)) - millis


    return render(request, 'allBranchRemindStat.html', {"login_teacher":login_teacher,
                                                "res":res,"weekBegin":weekBegin,"weekEnd":weekEnd,
                                                "city":city,"cityName":cityName
                                                 })
#本部门老师跟踪客户情况统计
def branchRemindStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branchId = login_teacher.branch
    branch = None
    try:
        branch = Branch.objects.get(id=login_teacher.branch)  # @UndefinedVariable
    except:
        branch = None
    res = []
    days = []
    daysData = []
    index = []
    if branchId and branch:

        teachers = utils.getTeachers(branchId)



        todayBegin = datetime.datetime.strptime(getDateNow().strftime("%Y-%m-%d")+' 00:00:00',"%Y-%m-%d %H:%M:%S")
        todayEnd = datetime.datetime.strptime(getDateNow().strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
        weekBegin = getWeekBegin(todayBegin)
        weekEnd = weekBegin + timedelta(days=6)
        res = []
        millis = int(round(time.time() * 1000))

        if True:
            dayMap = []

            dayMap.append(u'网络部')
            beforeReminds = dbsearch.getRemindNetNet(branch,None,todayBegin,constant.NET_BRANCH)
            if not 'b' in days:
                days.append('b')
            dayMap.append(len(beforeReminds))
            todayReminds = dbsearch.getRemindNetNet(branch,todayBegin,todayEnd,constant.NET_BRANCH)
            if not 't' in days:
                days.append('t')
            dayMap.append(len(todayReminds))
            day = todayBegin
            while day >= todayBegin and day < weekEnd:
                day = day + timedelta(days=1)
                day1 = datetime.datetime.strptime(day.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
                dayReminds = dbsearch.getRemindNetNet(branch,day,day1,constant.NET_BRANCH)

                dayname = str(day.weekday()+1)

                if not dayname in days:
                    days.append(dayname)
                dayMap.append(len(dayReminds))


            daysData.append(dayMap)



        i = 0

        for teacher in teachers:
            dayMap = []

            dayMap.append(teacher.name)
            beforeReminds = dbsearch.getRemind(branch,None,todayBegin,teacher.id)
            if not 'b' in days:
                days.append('b')
            dayMap.append(len(beforeReminds))
            todayReminds = dbsearch.getRemind(branch,todayBegin,todayEnd,teacher.id)
            if not 't' in days:
                days.append('t')
            dayMap.append(len(todayReminds))
            day = todayBegin
            while day >= todayBegin and day < weekEnd:
                day = day + timedelta(days=1)
                day1 = datetime.datetime.strptime(day.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
                dayReminds = dbsearch.getRemind(branch,day,day1,teacher.id)

                dayname = str(day.weekday()+1)

                if not dayname in days:
                    days.append(dayname)
                dayMap.append(len(dayReminds))


            daysData.append(dayMap)
            i = i + 1
        i = 0
        for d in days:
            i = i + 1
            index.append(i)
        millis = int(round(time.time() * 1000)) - millis




    return render(request, 'branchRemindStat.html', {"login_teacher":login_teacher,
                                                     "res":daysData,"days":days,
                                                "index":index})

#老师每周招生大排行
def statTeacherSales(request):

    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')

    doSearch = request.GET.get("doSearch")
    if doSearch != '1':
        return render(request, 'statTeacherSales.html', {"login_teacher":login_teacher})
    beginDateStr = request.GET.get("beginDate")
    endDateStr = request.GET.get("endDate")

    begin = datetime.datetime.strptime(beginDateStr+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    end = datetime.datetime.strptime(endDateStr+' 00:00:00',"%Y-%m-%d %H:%M:%S") + timedelta(days=1)

    persons = newstat.weekSaleEveryPerson(login_teacher.cityId,begin,end)

    return render(request, 'statTeacherSales.html', {"login_teacher":login_teacher,
                                                     "beginDate":beginDateStr,"endDate":endDateStr,
                                                "res":persons })

def cityQuests(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityId = login_teacher.cityId
    beginStr = request.GET.get('beginDate')
    endStr = request.GET.get('endDate')
    begin = None
    end = None
    try:
        begin = datetime.datetime.strptime(beginStr+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    except:
        begin = None
    try:
        end = datetime.datetime.strptime(endStr+' 00:00:00',"%Y-%m-%d %H:%M:%S") + timedelta(days=1)
    except:
        end = None
    res = []
    if begin or end:
        branches = utils.getCityBranch(cityId)
        for branch in branches:
            branchData = {}
            query = Q(branch=branch)
            if begin:
                query = query&Q(appDate__gte=begin)
            if end:
                query = query&Q(appDate__lt=end)
            branchData['branchCode'] = branch.branchCode
            branchData['branchName'] = branch.branchName
            quests = Question.objects.filter(query)  # @UndefinedVariable
            questNo = len(quests)
            branchData['quests'] = questNo
            a2 = 0
            b1 = 0
            b2 = 0
            for q in quests:
                if 'A' in q.a2:
                    a2 = a2 + 1
                if 'A' in q.b1:
                    b1 = b1 + 1
                if 'A' in q.b2:
                    b2 = b2 + 1
            a2rate = None
            if questNo > 0:
                a2rate = int(float(a2)/float(questNo)*100)
            branchData['a2'] = a2rate
            b1rate = None
            if questNo > 0:
                b1rate = int(float(b1)/float(questNo)*100)
            branchData['b1'] = b1rate
            b2rate = None
            if questNo > 0:
                b2rate = int(float(b2)/float(questNo)*100)
            branchData['b2'] = b2rate
            res.append(branchData)
    if not beginStr:
        beginStr = ''
    if not endStr:
        endStr = ''
    return render(request, 'cityQuests.html', {"login_teacher":login_teacher,
                                                     "beginDate":beginStr,"endDate":endStr,
                                                "res":res })

def branchQuests(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if login_teacher.role < 7:
        res = {"error": 1, "msg": u'您无权查看此页面'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))

    beginStr = request.GET.get('beginDate')
    endStr = request.GET.get('endDate')
    begin = None
    end = None
    try:
        begin = datetime.datetime.strptime(beginStr+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    except:
        begin = None
    try:
        end = datetime.datetime.strptime(endStr+' 00:00:00',"%Y-%m-%d %H:%M:%S") + timedelta(days=1)
    except:
        end = None
    res = []
    branchData = {}
    if begin or end:

        query = Q(branch=login_teacher.branch)
        if begin:
                query = query&Q(appDate__gte=begin)
        if end:
                query = query&Q(appDate__lt=end)
        quests = Question.objects.filter(query)  # @UndefinedVariable
        questNo = len(quests)

        b1 = 0
        b2 = 0

        for q in quests:

            if 'A' in q.b1:
                    b1 = b1 + 1
            if 'A' in q.b2:
                    b2 = b2 + 1

        b1rate = None
        if questNo > 0:
            b1rate = int(float(b1)/float(questNo)*100)
        branchData['b1'] = b1rate
        b2rate = None
        if questNo > 0:
                b2rate = int(float(b2)/float(questNo)*100)
        branchData['b2'] = b2rate

        teachers = utils.getTeachers(login_teacher.branch, None, False)

        for teacher in teachers:
            teacherData = {}
            query = Q(teacher=teacher)
            if begin:
                query = query&Q(appDate__gte=begin)
            if end:
                query = query&Q(appDate__lt=end)

            teacherData['teacherName'] = teacher.name
            quests = Question.objects.filter(query)  # @UndefinedVariable
            questNo = len(quests)
            teacherData['quests'] = questNo
            a1 = [0,0,0]
            a2 = [0,0,0]
            a3 = [0,0,0,0,0]
            a4 = [0,0,0,0]
            a5 = [0,0,0]
            a6 = [0,0,0]


            for q in quests:
                if 'A' in q.a1:
                    a1[0] = a1[0] + 1
                if 'B' in q.a1:
                    a1[1] = a1[1] + 1
                if 'C' in q.a1:
                    a1[2] = a1[2] + 1
                if 'A' in q.a2:
                    a2[0] = a2[0] + 1
                if 'B' in q.a2:
                    a2[1] = a2[1] + 1
                if 'C' in q.a2:
                    a2[2] = a2[2] + 1
                if 'A' in q.a3:
                    a3[0] = a3[0] + 1
                if 'B' in q.a3:
                    a3[1] = a3[1] + 1
                if 'C' in q.a3:
                    a3[2] = a3[2] + 1
                if 'D' in q.a3:
                    a3[3] = a3[3] + 1
                if 'E' in q.a3:
                    a3[4] = a3[4] + 1



                if 'A' in q.a4:
                    a4[0] = a4[0] + 1
                if 'B' in q.a4:
                    a4[1] = a4[1] + 1
                if 'C' in q.a4:
                    a4[2] = a4[2] + 1
                if 'D' in q.a4:
                    a4[3] = a4[3] + 1

                if 'A' in q.a5:
                    a5[0] = a5[0] + 1
                if 'B' in q.a5:
                    a5[1] = a5[1] + 1
                if 'C' in q.a5:
                    a5[2] = a5[2] + 1

                if 'A' in q.a6:
                    a6[0] = a6[0] + 1
                if 'B' in q.a6:
                    a6[1] = a6[1] + 1
                if 'C' in q.a6:
                    a6[2] = a6[2] + 1



            if questNo > 0:
                a1rate = 'A-'+str(int(float(a1[0])/float(questNo)*100))+'% | B-'+str(int(float(a1[1])/float(questNo)*100))+'% | C-'+str(int(float(a1[2])/float(questNo)*100))+'%'
                a2rate = 'A-'+str(int(float(a2[0])/float(questNo)*100))+'% | B-'+str(int(float(a2[1])/float(questNo)*100))+'% | C-'+str(int(float(a2[2])/float(questNo)*100))+'%'
                a3rate = 'A-'+str(int(float(a3[0])/float(questNo)*100))+'% | B-'+str(int(float(a3[1])/float(questNo)*100))+'% | C-'+str(int(float(a3[2])/float(questNo)*100))+'% | D-'+str(int(float(a3[3])/float(questNo)*100))+'% | E-'+str(int(float(a3[4])/float(questNo)*100))+'%'
                a4rate = 'A-'+str(int(float(a4[0])/float(questNo)*100))+'% | B-'+str(int(float(a4[1])/float(questNo)*100))+'% | C-'+str(int(float(a4[2])/float(questNo)*100))+'%'
                a5rate = 'A-'+str(int(float(a5[0])/float(questNo)*100))+'% | B-'+str(int(float(a5[1])/float(questNo)*100))+'% | C-'+str(int(float(a5[2])/float(questNo)*100))+'%'
                a6rate = 'A-'+str(int(float(a6[0])/float(questNo)*100))+'% | B-'+str(int(float(a6[1])/float(questNo)*100))+'% | C-'+str(int(float(a6[2])/float(questNo)*100))+'%'

                teacherData['a1'] = a1rate
                teacherData['a2'] = a2rate
                teacherData['a3'] = a3rate
                teacherData['a4'] = a4rate
                teacherData['a5'] = a5rate
                teacherData['a6'] = a6rate

            res.append(teacherData)
    if not beginStr:
        beginStr = ''
    if not endStr:
        endStr = ''
    return render(request, 'branchQuests.html', {"login_teacher":login_teacher,
                                                     "beginDate":beginStr,"endDate":endStr,
                                                "res":res,"branchData":branchData })
#某城市全部校区新生续费统计
def cityNewRedeal(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityId = login_teacher.cityId
    beginStr = request.GET.get('beginDate')
    endStr = request.GET.get('endDate')
    begin = None
    end = None
    try:
        begin = datetime.datetime.strptime(beginStr+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    except:
        begin = None
    try:
        end = datetime.datetime.strptime(endStr+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    except:
        end = None
    ctQuery = None
    try:
        city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
        #excludeContract = getNoneDealContractTypes(city)
        #redealCT = zhenpustat.getRedealCT(city)
    except:
        #excludeContract = None
        ctQuery = None

    res = []
    if begin or end:
        branches = utils.getCityBranch(cityId)
        for branch in branches:
            branchData = {}
            all,done = dbsearch.getBranchDealNew_redeal(branch,begin,end,ctQuery)
            branchData['branchCode'] = branch.branchCode
            branchData['branchName'] = branch.branchName
            branchData['allNew'] = len(all)
            branchData['newDone'] = len(done)
            if len(all) > 0:
                try:
                    branchData['newDoneRate'] = int(float(len(done))/float(len(all))*100)
                except:
                    err = 1
            res.append(branchData)
    if not beginStr:
        beginStr = ''
    if not endStr:
        endStr = ''
    return render(request, 'cityNewRedeal.html', {"login_teacher":login_teacher,
                                                     "beginDate":beginStr,"endDate":endStr,
                                                "res":res })


#某城市全部校区老生续费统计
def cityOldRedeal(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    cityId = login_teacher.cityId
    beginStr = request.GET.get('beginDate')
    endStr = request.GET.get('endDate')
    begin = None
    end = None
    try:
        begin = datetime.datetime.strptime(beginStr+' 00:00:00',"%Y-%m-%d %H:%M:%S")
    except:
        begin = None
    try:
        end = datetime.datetime.strptime(endStr+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    except:
        end = None
    ctQuery = None
    try:
        city = City.objects.get(id=login_teacher.cityId)  # @UndefinedVariable
        cts,ctQuery = dbsearch.getNormalContractTypes(city)
        #excludeContract = getNoneDealContractTypes(city)
        #redealCT = zhenpustat.getRedealCT(city)
    except:
        #excludeContract = None
        ctQuery = None

    res = []
    if begin or end:
        branches = utils.getCityBranch(cityId)
        for branch in branches:
            teachers = utils.getTeachers(branch.id, None, False)
            branchData = []
            for t in teachers:
                teacherData = {}
                teacherData['id'] = str(t.id)
                teacherData['username'] = t.username
                teacherData['name'] = t.name
                teacherData['branchName'] = t.branch.branchName
                teacherData['redeal'] = 0
                query = Q(teacher=t.id)&Q(status=constant.StudentStatus.sign)
                alls = Student.objects.filter(query)  # @UndefinedVariable
                teacherData['alls'] = len(alls)
                branchData.append(teacherData)
            redeals = dbsearch.getBranchDealOld_redeal(branch,begin,end,ctQuery)
            for c in redeals:
                try:
                    student = Student.objects.get(id=c.student_oid)  # @UndefinedVariable
                    for td in branchData:
                        if student.teacher and td['id'] == str(student.teacher.id):
                            td['redeal'] = td['redeal'] + 1
                except Exception,e:
                    print e

            for td in branchData:
                res.append(td)
    if not beginStr:
        beginStr = ''
    if not endStr:
        endStr = ''
    return render(request, 'cityOldRedeal.html', {"login_teacher":login_teacher,
                                                     "beginDate":beginStr,"endDate":endStr,
                                                "res":res })


#本部门老师联系客户数统计
def branchContactStat(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    branchId = login_teacher.branch
    branch = None
    try:
        branch = Branch.objects.get(id=login_teacher.branch)  # @UndefinedVariable
    except:
        branch = None
    res = []
    millis = int(round(time.time() * 1000))

    beginDate = request.GET.get("beginDate")
    endDate = request.GET.get("endDate")
    searchBegin = None
    searchEnd = None
    searchEnd2 = None
    if not beginDate or not endDate:
        return render(request, 'branchContactStat.html', {"login_teacher":login_teacher,
                                                     "err":""})
    try:
        searchBegin = datetime.datetime.strptime(beginDate,"%Y-%m-%d")
        searchEnd2 = datetime.datetime.strptime(endDate,"%Y-%m-%d")
        #searchEnd = searchEnd2 + timedelta(days=1)
        searchEnd = datetime.datetime.strptime(searchEnd2.strftime("%Y-%m-%d")+' 23:59:59',"%Y-%m-%d %H:%M:%S")
    except:
        return render(request, 'branchContactStat.html', {"login_teacher":login_teacher,
                                                    "err":"date err"
                                        })
    if not searchBegin or not searchEnd:
        return render(request, 'branchContactStat.html', {"login_teacher":login_teacher,
                                                    "err":"date err"})


    if branchId and branch:
        teachers = utils.getTeachers(branchId)
        for teacher in teachers:
            dataMap = {}
            query = Q(teacher=teacher)&Q(trackTime__gte=searchBegin)&Q(trackTime__lte=searchEnd)
            contact = StudentTrack.objects.filter(query)  # @UndefinedVariable
            cn = 0
            if contact and len(contact) > 0:
                cn = len(contact)
            dataMap['cn'] = cn
            dataMap['teacher'] = teacher.name
            dataMap['branch'] = teacher.branch.branchName
            res.append(dataMap)

    return render(request, 'branchContactStat.html', {"login_teacher":login_teacher,
                                                     "res":res,"beginDate":beginDate,
                                                      "endDate":endDate})

def lucky20181111(request):
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    if int(login_teacher.branchType) != constant.BranchType.management:
        res = {"error": 1, "msg": u'您无权查看此页面'}
        return http.JSONResponse(json.dumps(res, ensure_ascii=False))
    query = Q(type='20181111luck')
    lucks = Reg.objects.filter(query).order_by("branch")  # @UndefinedVariable
    last = None
    l2 = None
    i = 0
    i1 = 0
    i2 = 0
    i3 = 0
    i4 = 0
    idone = 0
    iin = 0
    res = []
    map = {}
    if lucks and len(lucks) > 0:
      for l in lucks:
        l2 = l
        if last and last.branch != l.branch:
            map = {}
            map['branchId'] = last.branch
            if last.branch == constant.NET_BRANCH:
                map['branchName'] = '网络部'
            else:
                map['branchName'] = last.branchName
            map['all'] = i
            map['1'] = i1
            map['2'] = i2
            map['3'] = i3
            map['4'] = i4
            map['done'] = idone
            map['in'] = iin
            res.append(map)
            i = 0
            i1 = 0
            i2 = 0
            i3 = 0
            i4 = 0
            idone = 0
            iin = 0

            last = l
        if not last:
            last = l
        i = i + 1
        if l.memo == '1111':
            i1 = i1 + 1
        if l.memo == '511':
            i2 = i2 + 1
        if l.memo == '211':
            i3 = i3 + 1
        if l.memo == '11':
            i4 = i4 + 1
        if l.done:
            idone = idone + 1
        if l.isStudent == u'是' :
            iin = iin + 1
      map = {}
      map['branch'] = l2.branch
      if l2.branch == constant.NET_BRANCH:
          map['branchName'] = '网络部'
      else:
          map['branchName'] = l2.branchName
      map['all'] = i
      map['1'] = i1
      map['2'] = i2
      map['3'] = i3
      map['4'] = i4
      map['done'] = idone
      map['in'] = iin
      res.append(map)
    return render(request, 'lucky20181111.html', {"login_teacher":login_teacher,
                                                     "res":res})

def channelBranchStat(request):
    channel = None
    res = []
    login_teacher = checkCookie(request)
    if not (login_teacher):
        return HttpResponseRedirect('/login')
    channelId = request.GET.get("channel")
    searchBegin = ''
    searchEnd = ''
    channel = None
    try:
        query = Q(id=channelId)

        channel = SourceCategory.objects.get(query)  # @UndefinedVariable
        print channel.categoryName
        #channel = channels[0]
    except:
        return(request, 'channelBranchStat.html', {"login_teacher":login_teacher,"beginDate":searchBegin,
                                                      "endDate":searchEnd,
                                                      "channel":channel,
                                                     "res":res})
    searchBegin = request.GET.get("beginDate")
    searchEnd = request.GET.get("endDate")
    branches = utils.getCityBranch(login_teacher.cityId)

    for branch in branches:
        stat = zhenpustat.getChannelBranchStat(channel,branch,searchBegin,searchEnd)
        res.append(stat)
    return render(request, 'channelBranchStat.html', {"login_teacher":login_teacher,
                                                      "beginDate":searchBegin,
                                                      "endDate":searchEnd,
                                                      "channel":channel,
                                                     "res":res})
