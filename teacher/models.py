# -*- coding:utf-8 -*-
from django.db import models
from mongoengine import *
from branch.models import Branch
import code
from tools import constant

class Target(Document):
    
    userId = StringField()
    beginDate = DateTimeField()
    endDate = DateTimeField()
    beginLevel = StringField()
    endLevel = StringField()
    quarterTarget = StringField()
    halfyearTarget = StringField()
    yearTarget = StringField()
    meta = {
        'collection': 'Target'
    }
class Teacher(Document):
    username = StringField()
    name = StringField()
    name2 = StringField()
    password = StringField()
    role = IntField()
    weixin = StringField()
    mobile = StringField()
    branch = ReferenceField(Branch)
    checkinDate = DateTimeField()
    quitDate = DateTimeField()
    status = IntField()#0：正常，-1：离职
    page = IntField()
    openId = StringField()
    value = FloatField()
    go_login = StringField()
    go_password = StringField()
    payRatio = IntField()
    pushId = StringField()
    email = StringField()
    inReview = BooleanField() #是否参与教室考评
    isY19 = BooleanField()
    targets = ListField(ReferenceField(Target))
    level = StringField()
    beginLevel = StringField()
    targetLevel1 = StringField()
    targetLevel2 = StringField()
    targetLevel3 = StringField()
    targetBeginDate = DateTimeField()
    
    meta = {
        'collection': 'teacher'
    }
    
class Role(Document):
    roleName = StringField()
    code = IntField()
    memo = StringField()

    meta = {
        'collection': 'role'
    }

class Login_teacher(Document):
    id = StringField()
    teacherName = StringField()
    name2 = StringField()
    username = StringField()
    role = IntField()
    roleName = StringField()
    branch = StringField()
    branchName = StringField()
    branchType = IntField() #1-市场、网络，0-校区,2-职能部门，3-管理
    cityHeadquarter = StringField() #所在城市主要收单部门branchId
    cityHeadquarterName = StringField() #所在城市主要收单部门branchName
    branchTel = StringField()
    cityId = StringField()#city oid
    city = StringField()#city name
    page = IntField()
    branchSN = StringField()
    cityFA = StringField() #地区财务审批人
    cityFR = StringField() #地区退款操作人
    cityRT = StringField() #地区开发票人
    cityRB = StringField() #报销人
    cityRB2 = StringField() #报销人（无发票）
    RoleFin = constant.Role.financial
    RoleAdm = constant.Role.admin
    RoleTea = constant.Role.teacher
    RoleMas = constant.Role.master
    RoleOpe = constant.Role.operator
    showIncome = IntField() #是否可查看收入列表-财务、人事部门可以查看
    isSuper = StringField()

class Training(Document):
    teacher_oid = StringField()
    teacher_name = StringField()
    training_date = DateTimeField()
    review_date = DateTimeField()
    type = IntField()#1-试听课，2-上课，3-电话，4-斯汀可演练，5-上课演练，6-电话演练
    memo = StringField()
    meta = {'collection':'training'}
    
class Message(Document):
    sendTime = DateTimeField()
    readTime = DateTimeField()
    doneTime = DateTimeField()
    fromBranch = StringField()
    fromBranchName = StringField()
    toBranch = StringField()
    toBranchName = StringField()
    fromTeacher_oid = StringField()
    toTeacher_oid = StringField()
    fromTeacherName = StringField()
    toTeacherName = StringField()
    message = StringField()
    isRead = IntField() #0-未读，1-已读
    isDone = IntField() #-1不需要处理，0-未处理，1-已处理
    todoUrl = StringField() 
    phone = StringField()
    meta = {'collection':'message'}

class Assess(Document):
    city = StringField()
    branch = StringField() #被评价人所在校区
    assessObject = StringField() #被评价人的teacher id
    assessDate = DateTimeField()
    assessCode = StringField() #哪次考评，比如201808
    assessor = StringField() #评价人的teacher id
    score = IntField()
    memo = StringField()
    assessObjectName = StringField()
    branchName = StringField()
    branchSn = StringField()
    averageScore = FloatField()
    
    meta = {'collection':'assess'}
    
#调查问卷
class Questionnaire(Document):
    city = StringField()
    branchId = StringField() #被评价人所在校区
    branchName = StringField()
    #branchSn = StringField()
    assessObject = StringField() #被评价人的teacher id
    assessObjectName = StringField()
    assessDate = DateTimeField() #问卷提交时间
    assessCode = StringField() #考评代码，比如201808
    assessor = StringField() #评价人，如果记名，记录评价人id
    assessorName = StringField()
    answers = DictField()
    
    meta = {'collection':'questionnaire'}
    
class TeacherStep(Document):
    cityId = StringField()
    branchId = StringField()
    branchName = StringField()
    teacherId = StringField()
    teacherName = StringField()
    beginDate = DateTimeField()
    endDate = DateTimeField()
    item = StringField() #评分项目名
    value = StringField() #项目值
    valid = BooleanField() #是否合格
    score = IntField() #项目得分，累计总分用
    masterId = StringField() #打分主任id
    masterName = StringField() #打分主任姓名
    dateType = StringField() #week,month,month3,year
    
    meta = {'collection':'TeacherStep'}