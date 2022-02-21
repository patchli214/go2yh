#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bee'
from django.conf.urls import include, url
from statistic.views import *
urlpatterns = [
    url(r'^statStudent$', statStudent,name='statStudent'),
    url(r'^statDemoBranch$', statDemoBranch,name='statDemoBranch'),
    url(r'^statDayDemoBranch$', statDayDemoBranch,name='statDayDemoBranch'),
    url(r'^statDayBranch$', statDayBranch,name='statDayBranch'),
    url(r'^indexStat$', indexStat,name='indexStat'),
    
    url(r'^branchIncome2$', branchIncome2,name='branchIncome2'),
    url(r'^branchIncomeDue$', branchIncomeDue,name='branchIncomeDue'),
    url(r'^statRemainBranch$', statRemainBranch,name='statRemainBranch'),
    url(r'^statRatioBranch$', statRatioBranch,name='statRatioBranch'),
    url(r'^statTeacher$', statTeacher,name='statTeacher'),
    url(r'^netSourceStat$', netSourceStat,name='netSourceStat'),
    url(r'^allRemainBranch$', allRemainBranch,name='allRemainBranch'),
    url(r'^statTReg$', statTReg,name='statTReg'),  # @UndefinedVariable
    url(r'^netBranchRemindStat$', netBranchRemindStat,name='netBranchRemindStat'),
    url(r'^allBranchRemindStat$', allBranchRemindStat,name='allBranchRemindStat'),
    url(r'^branchRemindStat$', branchRemindStat,name='branchRemindStat'),
    url(r'^branchSourceStat$', branchSourceStat,name='branchSourceStat'),
    url(r'^allBranchRevenue$', allBranchRevenue,name='allBranchRevenue'),
    url(r'^allBranchReport$', allBranchReport,name='allBranchReport'),
    
    url(r'^statTeacherSales$', statTeacherSales,name='statTeacherSales'),
    url(r'^cityQuests$', cityQuests,name='cityQuests'),
    url(r'^branchQuests$', branchQuests,name='branchQuests'),
    url(r'^cityNewRedeal$', cityNewRedeal,name='cityNewRedeal'),
    url(r'^cityOldRedeal$', cityOldRedeal,name='cityOldRedeal'),
    url(r'^branchContactStat$', branchContactStat,name='branchContactStat'),
    url(r'^lucky20181111$', lucky20181111,name='lucky20181111'),
    url(r'^channelBranchStat$', channelBranchStat,name='channelBranchStat'),
    
    url(r'^allBranchRevenue2$', allBranchRevenue2,name='allBranchRevenue2'),
    url(r'^oneBranchRevenue$', oneBranchRevenue,name='oneBranchRevenue'),
    
    
]
