#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from mongoengine import *
from regUser.models import Student
from datetime import date
from teacher.models import Teacher, Target
from branch.models import Branch

    
    
class User(Document):
    goid = StringField() #zhenpuweiqi.com user id
    student = ReferenceField(Student)
    password = StringField()
    name = StringField()
    nickname = StringField()
    rank = FloatField() #zhenpuweiqi.com user rank, eg. 30K
    diamonds = IntField()
    coins = IntField()
    level = StringField() #级段位
    star = IntField() #星级考
    created_at = DateTimeField()
    one_star_unlocked = BooleanField()
    two_star_unlocked = BooleanField()
    three_star_unlocked = BooleanField()
    
    points_race_points = IntField()    
    
    yesterday_total_question_count = IntField()
    yesterday_total_match_count = IntField()
    yesterday_correct_question_count = IntField()
    yesterday_correct_match_count = IntField()
    today_total_question_count = IntField()
    today_correct_question_count = IntField()
    today_total_match_count = IntField()
    today_correct_match_count = IntField()
    last_one_week_total_question_count = IntField()
    last_one_week_correct_question_count = IntField()
    last_one_week_total_match_count = IntField()
    last_one_week_correct_match_count = IntField()
    last_two_week_total_question_count = IntField()
    last_two_week_correct_question_count = IntField()
    last_two_week_total_match_count = IntField()
    last_two_week_correct_match_count = IntField()
    week_total_question_count = IntField()
    week_correct_question_count = IntField()
    week_total_match_count = IntField()
    week_correct_match_count = IntField()
    month_total_question_count = IntField()
    month_correct_question_count = IntField()
    month_total_match_count = IntField()
    month_correct_match_count = IntField()
    
    history_total_question_count = IntField()
    history_correct_question_count = IntField()
    history_total_match_count = IntField()
    history_correct_match_count = IntField()
    display_nickname = StringField()
    update_date = DateTimeField()
    targets = ListField(ReferenceField(Target))
    level = StringField()
    meta = {
        'collection': 'User'
    }

class History(Document):
    user = ReferenceField(User)
    type = IntField()# 0-teacher fill, 1-rank change, 2-level upgrade, 3-match, 4-zhenpuweiqi.com match,5-zhenpuweiqi.com questions
    memo = StringField()  
    date = DateTimeField()
    image = StringField()
    level = StringField()
    meta = {
        'collection': 'History'
    } 
    
    #x学生月度销课
class MonthIncome(Document): 
    student = StringField()
    month = DateTimeField()
    
    #每周课情况
    lessons1 = IntField()
    lessonPrice1 = FloatField()
    income1 = FloatField()
    lessons2 = IntField()
    lessonPrice2 = FloatField()
    income2 = FloatField()
    lessons3 = IntField()
    lessonPrice3 = FloatField()
    income3 = FloatField()
    lessons4 = IntField()
    lessonPrice4 = FloatField()
    income4 = FloatField()
    lessons5 = IntField()
    lessonPrice5 = FloatField()
    income5 = FloatField()
    
    lessons = IntField() #合计课销
    income = FloatField() #合计实际收入
    lessonsFirst4 = IntField() #本月前四次课次数
    first4Price = FloatField() #本月前四次课单价
    incomeFirst4 = FloatField() #本月前四次课收入
    lessonsFirst4All = IntField() #前四次课总次数
    incomeFirst4All = FloatField() #前四次课总收入
    classNow = StringField() #当前班级


#休学    
class Suspension(Document):
    branch = StringField()
    student = StringField()
    beginDate = DateTimeField()
    endDate = DateTimeField()
    appDate = DateTimeField()
    meta = {
        'collection': 'Suspension'
    } 
    
class Receipt(Document):
    student = ReferenceField(Student)
    appDate = DateTimeField() #申请日期
    printDate = DateTimeField() #开票日期
    sum = FloatField() #开票金额
    title = StringField()#发票抬头
    rType = IntField()#1-普票 2-专票
    taxNo = StringField()#税号
    address = StringField()#公司地址电话
    bank = StringField()#开户行及帐号
    status = IntField()#1-已开，0或None-未开，－1:驳回
    memo = StringField()
    contractSum = IntField()#申请时的合同总金额
    isMemberFee = BooleanField()#是否会员费
    meta = {'collection':'Receipt'}

class Question(Document):
    branch = ReferenceField(Branch)
    student = ReferenceField(Student)
    studentName = StringField()
    teacher = ReferenceField(Teacher)
    appDate = DateTimeField()
    length = StringField()
    a1 = StringField()
    a2 = StringField()
    a3 = StringField()
    a4 = StringField()
    a5 = StringField()
    a6 = StringField()
    a7 = StringField()
    b1 = StringField()
    b2 = StringField()
    b3 = StringField()
    b4 = StringField()
    