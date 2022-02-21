#!/usr/bin/env python
# -*- coding:utf-8 -*-
__author__ = 'bee'
from django.conf.urls import include, url
from gradeClass.views import *
urlpatterns = [

    url(r'^saveGradeClass/(?P<gradeClass_type>[\d]+)$', api_save_gradeClass, name='api_save_gradeClass'),
    url(r'^removeGradeClass$', api_remove_gradeClass, name='api_remove_gradeClass'),
    url(r'^api_cancel_demo$',api_cancel_demo,name='api_cancel_demo'),
    url(r'^editGradeClass/(?P<gradeClass_type>[\d]+)/(?P<gradeClass_oid>[\w]*)$', edit_gradeClass, name='edit_gradeClass'),
    
    url(r'^gradeClassList$', gradeClass_list, name='gradeClass_list'),
    url(r'^gradeClassInfo/(?P<gradeClass_oid>[\w]{24})/$', gradeClass_info, name='gradeClass_info'),

    url(r'^scheduleList$', schedule_list, name='schedule_list'),
    url(r'^schedule$', schedule, name='schedule'),
    url(r'^lessons$', lessons, name='lessons'),
    url(r'^extraLesson$', extraLesson, name='extraLesson'),
    url(r'^api_extraLesson$', api_extraLesson, name='api_extraLesson'),
    url(r'^studentLessons$', studentLessons, name='studentLessons'),
    url(r'^signLesson$', signLesson, name='signLesson'),
    url(r'^checkin$', checkin, name='checkin'),
    url(r'^saveLessonContent$', saveLessonContent, name='saveLessonContent'),
    url(r'^studentDemo/(?P<student_oid>[\w]{24})/$', studentDemo, name='studentDemo'),
    url(r'^makePassLessons$', makePassLessons, name='makePassLessons'),
    url(r'^changeLesson$', changeLesson, name='changeLesson'),
    url(r'^api_changeLesson$', api_changeLesson, name='api_changeLesson'),
    url(r'^api_save_demo$', api_save_demo, name='api_save_demo'),
    url(r'^api_removeLesson$', api_removeLesson, name='api_removeLesson'),
    url(r'^editSchedule/(?P<gradeClass_oid>[\w]*)$', edit_schedule, name='edit_schedule'),
    url(r'^delLessons$', delLessons, name='delLessons'),
    url(r'^deletedClassList$', deletedClass_list, name='deletedClass_list'),
    url(r'^api_restore_gradeClass$', api_restore_gradeClass, name='api_restore_gradeClass'),
    

]
