#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from mongoengine import *
from regUser.models import *
from teacher.models import Teacher

class Lesson(Document):
    lessonId = StringField()
    branch = StringField()
    gradeClass = ReferenceField(GradeClass)#班级
    teacher = ReferenceField(Teacher) #实际上课老师，不是班级老师
    student = StringField()
    oriTime = DateTimeField() #正课应上课时间
    lessonTime = DateTimeField() #实际上课时间
    classroom = IntField()
    memo = StringField()
    type = IntField()#0-安排class,1-签到student,2-补课安排，3-补课签到
    checked = BooleanField()
    value = FloatField()
    oriLessons = ListField(StringField())#这个值代表补课学生和对应的那个正课（type＝0） 的id，形如：studentId－lessonId，studentId2-lessonId2
    payTeacher = FloatField() #老师课消费用
    paySchool = FloatField()  #学校利润
    #checkinIndex = FloatField()     #是第几次课，lastIndex+=value
    meta = {
        'collection': 'lesson'
    }
