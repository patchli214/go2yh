#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'patch'
from django.conf.urls import include, url
from regUser.views import *

urlpatterns = [

    # reg
    url(r'^reg$', reg,name='reg'),
    url(r'^netReg$',netReg,name='netReg'),
    url(r'^apiReg$', api_reg, name='api_reg'),
    url(r'^addSourceCategory$', addSourceCategory,name='addSourceCategory'),
    url(r'^addSource$', addSource,name='addSource'),
    # 学生列表
    url(r'^studentList$', student_list, name='student_list'),
    url(r'^studentInfo/(?P<student_oid>[\w]{24})/$', student_info, name='student_info'),
    url(r'^apiSaveDemo/(?P<demo_oid>[\w]{24})/$', api_save_demo, name='api_save_demo'),
    url(r'^saveUserRemind$', save_user_remind, name='save_user_remind'),
    url(r'^studentSaveDeposit$', student_save_deposit, name='student_save_deposit'),
    url(r'^studentDeposit$', student_deposit, name='student_deposit'),
    url(r'^getByOids$', getByOids,name='getByOids'),
    url(r'^sms$', sms,name='sms'),
    url(r'^SMSTemplateEdit$', smsTemplateEdit,name='smsTemplateEdit'),
    url(r'^saveSMSTemplate$', api_saveSMSTemplate,name='api_saveSMSTemplate'),
    url(r'^showSMSTemplates$', showSMSTemplates,name='showSMSTemplates'),
    url(r'^uploadPic$', uploadPic,name='uploadPic'),
    url(r'^removePic$', removePic,name='removePic'),
    url(r'^removeTrack$', removeTrack,name='removeTrack'),
    url(r'^removeDup$', removeDup,name='removeDup'),
    url(r'^resolve_api$', resolve_api,name='resolve_api'),
    url(r'^resolve0$', resolve0,name='resolve0'),
    url(r'^resolve0_api$', resolve0_api,name='resolve0_api'),
    url(r'^resolveToDo_api$', resolveToDo_api,name='resolveToDo_api'),
    url(r'^done$', done,name='done'),
    url(r'^rr$', rr,name='rr'),
    url(r'^rer$', rer,name='rer'),
    url(r'^excelUser$', excelUser,name='excelUser'),
    url(r'^userShare$', userShare,name='userShare'),
    url(r'^picMemo$', picMemo,name='picMemo'),
    url(r'^dboard1$', dboard1,name='dboard1'),
    url(r'^dboard2$', dboard2,name='dboard2'),
    url(r'^dboard3$', dboard3,name='dboard3'),
    url(r'^dboard4$', dboard4,name='dboard4'),
    url(r'^dboard5$', dboard5,name='dboard5'),
    url(r'^dboard6$', dboard6,name='dboard6'),
    url(r'^dboard9$', dboard9,name='dboard9'),
    url(r'^dboard10$', dboard10,name='dboard10'),
    url(r'^dboard11$', dboard11,name='dboard11'),
    url(r'^dboard12$', dboard12,name='dboard12'),
    url(r'^dboard13$', dboard13,name='dboard13'),
    url(r'^searchKid$', searchKid,name='searchKid'),
    url(r'^searchReferTeacher$', searchReferTeacher,name='searchReferTeacher'),
    url(r'^regFromWxProg$', regFromWxProg,name='regFromWxProg'),
    url(r'^fan$', fan,name='fan'),
    url(r'^referPages$', referPages,name='referPages'),
]