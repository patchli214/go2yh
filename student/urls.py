#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'patch'
from django.conf.urls import include, url
from student.views import *
urlpatterns = [
    url(r'^achievement$', achievement,name='achievement'),  # @UndefinedVariable
    url(r'^students$', students,name='students'),  # @UndefinedVariable
    url(r'^studentMemo$', studentMemo,name='studentMemo'),  # @UndefinedVariable
    url(r'^api_studentMemo$', api_studentMemo,name='api_studentMemo'),  # @UndefinedVariable
    url(r'^api_memoDelete$', api_memoDelete,name='api_memoDelete'),  # @UndefinedVariable
    url(r'^api_end$', api_end,name='api_end'),  # @UndefinedVariable
    url(r'^habit$', habit,name='habit'),  # @UndefinedVariable
    url(r'^title$', title,name='title'),  # @UndefinedVariable
    url(r'^titleLogin$', titleLogin,name='titleLogin'),  # @UndefinedVariable
    url(r'^api_suspend$', api_suspend,name='api_suspend'),  # @UndefinedVariable
    url(r'^api_delSuspension$', api_delSuspension,name='api_delSuspension'),  # @UndefinedVariable
    url(r'^question$', question,name='question'),  # @UndefinedVariable
    url(r'^quests$',quests,name="quests"),
    url(r'^studentDo$',studentDo,name="studentDo"),
    url(r'^api_editTarget$', api_editTarget,name='api_editTarget'),  # @UndefinedVariable
    url(r'^api_saveRecord$', api_saveRecord,name='api_saveRecord'),  # @UndefinedVariable
    url(r'^tweet$',tweet,name="tweet"),
    url(r'^api_tweet$',api_tweet,name="api_tweet"),
]
