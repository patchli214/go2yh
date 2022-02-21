# -*- coding:utf-8 -*-
from django.db import models
from mongoengine import *
from branch.models import Branch
from regUser.models import Student,StudentFile
from teacher.models import Teacher

class Webpage(Document):
    sn = IntField() #顺序号，不重复
    publishDate = StringField()
    title = StringField()
    text = StringField()
    background = StringField()
    branch = ReferenceField(Branch)
    createDate = DateTimeField()
    teacher = StringField()
    student = StringField()
    sourceType = StringField()
    source = StringField()
    pics = ListField(ReferenceField(StudentFile))
    sortedPics = ListField()
    
    fileType = IntField()

    meta = {
        'collection': 'webpage'
    }

class Reg(Document):
    regTime = DateTimeField()
    name = StringField()
    mobile = StringField()
    gender = StringField()
    year = StringField()
    month = StringField()
    source = StringField()
    done = BooleanField()
    memo = StringField() #记录活动事项，比如抽奖结果
    branch = StringField()
    city = StringField()
    type = StringField()#注册类型，没有的是网络部宣传页面注册，其他类型，如双十一抽奖-‘20181111’
    teacher = StringField() #转介老师
    teacherName = StringField()
    branchName = StringField()
    selectBranch = StringField()
    isStudent = StringField()
    studentId = StringField() #兑奖学生
    meta = {
        'collection': 'reg'
    } 
    
class Short(Document):
    key = StringField()
    value = StringField()
    value2 = StringField()
    meta = {'collection':'short'}
    
class WXToken(Document):
    token = StringField()
    tokenTime = DateTimeField()
    meta = {'collection':'WXToken'} 