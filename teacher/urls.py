#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bee'
from django.conf.urls import include, url
from teacher.views import *
urlpatterns = [

    # reg
    url(r'^reg$', reg, name='reg'),
    url(r'^apiReg$', api_reg, name='api_reg'),

    # 老师列表
    url(r'^teacherList$', teacher_list, name='teacher_list'),
    url(r'^trainings/(?P<teacher_oid>[\w]{24})/$', trainings, name='trainings'),
    url(r'^trainingEditForm$', trainingEditForm, name='trainingEditForm'),
    url(r'^trainingEdit$', trainingEdit, name='trainingEdit'),
    url(r'^changePw$', changePw, name='changePw'),
    url(r'^pwForm$', pwForm, name='pwForm'),
    url(r'^checkOpenId$',checkOpenId,name="checkOpenId"),
    url(r'^api_getMessage$',api_getMessage,name="api_getMessage"),
    url(r'^api_readMessage$',api_readMessage,name="api_readMessage"),
    url(r'^message$',message,name="message"),
    url(r'^api_sendMessage$',api_sendMessage,name="api_sendMessage"),
    url(r'^api_push$',api_push,name="api_push"),
    url(r'^teacherQrcode$',teacherQrcode,name="teacherQrcode"),
    url(r'^api_headmasterAssess$',api_headmasterAssess,name="api_headmasterAssess"),
    url(r'^headmasterAssess$',headmasterAssess,name="headmasterAssess"),
    url(r'^headmasterAssesses$',headmasterAssesses,name="headmasterAssesses"),
    url(r'^questionnaire$',questionnaire,name="questionnaire"),
    url(r'^api_questionnaire$',api_questionnaire,name="api_questionnaire"),
    url(r'^questionnaireResult$',questionnaireResult,name="questionnaireResult"),
    url(r'^teacherAvail$',teacherAvail,name="teacherAvail"),
    url(r'^markStep$',markStep,name="markStep"),
    url(r'^api_markStep$',api_markStep,name="api_markStep"),
    url(r'^wxqrcodePic$',wxqrcodePic,name="wxqrcodePic"),
    url(r'^p20181111$',p20181111,name="p20181111"),
    url(r'^cityTeacherSteps$',cityTeacherSteps,name="cityTeacherSteps"),
    url(r'^api_editTarget$', api_editTarget,name='api_editTarget'),  # @UndefinedVariable
    url(r'^teacherSteps$',teacherSteps,name="teacherSteps"),
    url(r'^api_resetTestPassword$',api_resetTestPassword,name="api_resetTestPassword"),
    url(r'^testUser$',testUser,name="testUser"),
    url(r'^q2019$',q2019,name="q2019"),
    url(r'^api_q2019$',api_q2019,name="api_q2019"),
    url(r'^q2019Result$',q2019Result,name="q2019Result"),
    
]
