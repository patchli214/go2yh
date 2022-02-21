#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from mongoengine import *
from branch.models import Branch
from teacher.models import Teacher
from regUser.models import Student

class UserStat(Document):
    title = StringField()
    branch = ReferenceField(Branch)
    teacher = ReferenceField(Teacher)
    reg = FloatField() #拜访（咨询）
    regNet = IntField() #拜访（咨询）
    regAll = IntField()
    regValid = IntField() #有效咨询
    reservation = IntField() #预约
    reservationNet = IntField() #预约
    show = IntField() #到场
    showB = IntField() #拜访到场
    showNet = IntField()
    notShow = IntField()#未到场
    demo = IntField() #老师上试听课数量
    demoDeal = IntField() #老师试听课成交数量
    deal = IntField() #老师招生数
    refund = IntField()#退费
    refundNet = IntField()#退费
    newdeal = IntField()#新成交
    newdealAll = IntField()#新成交
    newdealNet = IntField()#新成交
    redeal = IntField()
    redealNew = IntField()#新生续费
    redealOld = IntField()#老生续费
    oid = StringField()

class WeekReg(Document):
    cityId = StringField()
    beginDate = DateTimeField()
    endDate = DateTimeField()
    regs = ListField()
    updateDate = DateTimeField()
    meta = {
        'collection': 'WeekReg'
    } 
    
class Stats(Document):
    statBranch = UserStat()
    statNet = UserStat()
    studentSum = IntField()
    title = StringField()
    
class PageVisit(Document):
    branch = StringField()
    page = StringField()
    teacher = StringField()
    student = StringField()
    visitTime = DateTimeField()
    visit = IntField()
class VisitIp(Document):
    visitIp = StringField()
    visitDate = DateTimeField()
    visitPage = StringField()#pageName-student
    meta = {
        'collection': 'visitIp'
    } 
class StatStudent(Document):
    branch = ReferenceField(Branch)
    teacher = ReferenceField(Teacher)
    visit = IntField()
    refer = IntField()
    online = IntField()
    album = IntField()
    pageShare = IntField()
    pageReg = IntField()
    pageNum = IntField()
    memo = StringField()
    rate1 = FloatField()
    branchShare = IntField()
    branchPages = IntField()

class BranchIncome(Document):
    teacher_oid = StringField()
    teacherName = StringField()
    month = StringField()
    lessons = IntField()
    sum = IntField()
    eve = IntField()
    duePay = FloatField()
    payRatio = IntField()
    first4 = IntField()
    student = ReferenceField(Student)
    sumFirst4 = IntField()
    
#每天统计的当月课时，记录进数据库，便于第二天快速统计之前的课时消费-即将废止，被Checkin取代
class LessonCheck(Document):
    branchId = StringField()
    branchName = StringField()
    year = StringField()
    month = StringField()
    teacherCheckin = ListField()
    branchIncome = DictField()
    updateTime = DateTimeField() #最新统计时间
    updateCheckinTime = DateTimeField()#最新签到时间
    meta = {'collection':'LessonCheck'}

#每个学生每月课程签到，用于计算课时费
class Checkin(Document):
    branchId = StringField()
    branchName = StringField()
    teacherId = StringField() #上课老师
    teacherName = StringField()
    studentId = StringField()
    studentName = StringField()
    classId = StringField()
    className = StringField()
    
    year = StringField()
    month = StringField()
    studentLMLeft = FloatField() #学生上月底剩余课时
    studentShouldCheckin = FloatField() #学生应消课时数
    
    checkinF4 = FloatField() #本月本学生上过的前4次课数，0-4
    
    checkinPay = FloatField() #有收入的课时数
    payF4 = FloatField() #前四次课课时费，上完四次课计入校区利润，不计入老师工资
    payTeacher = FloatField() #老师课时费（包括转介课时费）
    paySchool = FloatField() #校区利润
    
    updateTime = DateTimeField() #最新统计时间
    updateCheckinTime = DateTimeField()#最新签到时间
    meta = {'collection':'Checkin'}
    
class StatHistory(Document):
    type = StringField()
    beginDate = StringField()
    data = {}
    meta = {'collection':'StatHistory'}
    