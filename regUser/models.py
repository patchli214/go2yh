#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from mongoengine import *
from teacher.models import Teacher
from branch.models import *
#from bs4.tests.test_tree import SiblingTest
from mongoengine.fields import StringField


class Classroom(Document):
    branch = ReferenceField(Branch)
    name = StringField()
    sn = IntField()

    meta = {
        'collection': 'classroom'
    }  

class ClassType(Document):
    name = StringField()
    sn = IntField()

    meta = {
        'collection': 'classType'
    }

class SourceType(Document):#渠道类型，网络、拜访、用户转介、社会walk in、其他渠道、
    typeCode = StringField()
    typeName = StringField()
    content = IntField()#1-source,2-Category+Sorce,3-source+category+contact
    meta = {
        'collection': 'sourceType'
    }

class SourceCategory(Document):
    categoryCode = StringField()
    categoryName = StringField()
    branch = ReferenceField(Branch)
    typeCode = StringField()
    deleted = IntField()
    meta = {
        'collection': 'sourceCategory'
    }

class Source(Document):
    branch = ReferenceField(Branch)
    typeCode = StringField()
    categoryCode = StringField() 
    sourceName = StringField()
    contact = StringField()
    mobile = StringField()
    weixin = StringField()
    sourceCode = StringField()
    deleted = IntField()
    
    meta = {
        'collection': 'source'
    }

class ContractType(Document):
    city = ReferenceField(City)
    duration = IntField()
    fee = IntField()
    tuition = IntField()#季度学费
    discountPrice = IntField()
    memo = StringField()
    deleted = IntField()
    code = StringField()
    type = IntField() #0-常规 ，1-假期， 2-赠课
    meta = {
        'collection': 'contractType'
    }
    
class Contract(Document):
    branch = ReferenceField(Branch)
    
    student_oid = StringField()
    student_name = StringField()
    singDate = DateTimeField()   #缴费日期
    beginDate = DateTimeField()  #开课日期
    endDate = DateTimeField()
    refundDate = DateTimeField()
    classType = ReferenceField(ClassType)
    memo = StringField()
    contractType = ReferenceField(ContractType)
    paid = IntField() #实付金额
    paymethod = StringField() #付款方式，见congstant.PAY_METHOD
    weeks = IntField()#实际周数
    status = IntField() #0：正常 ，1：结束，2：退费，3-休学,4-作废,-1:退费申请
    memo2 = StringField()#退费理由
    multi = IntField() # 0:newDeal,1-newRedeal,2-oldReDeal
    refund = IntField() #退费金额
    checkinWeeks = IntField() #实际上课周数
    refundAppDate = DateTimeField()
    refundApprove = IntField() #0-未审批，1-通过，2-驳回
    refundMemo = StringField() #驳回退费理由
    cid = StringField() #学籍单上的唯一编号
    f4date = DateTimeField() #四次课上完的日期
    lessons = FloatField() #总共上过的有效次数
    
    #####################
    # 网课
    teacher = ReferenceField("Teacher")  #  来源老师/签约老师
    assistant = ReferenceField("Teacher") #助教
    
    #########################
    #   元十九app信息
    #########################
    mobile = StringField()
    regName = StringField()
    
    ###########################
    #  季度学费合同新加项
    ###########################
    contractId = StringField() #所属主合同（会员费合同）
    dueDate = DateTimeField()  #应收款日期
    shouldPay = IntField() #会员费合同如有此值按照这个值生成每期季度学费
    meta = {
        'collection': 'contract'
    }
     
class Student(Document):
    uid = IntField()#可重复，一个人一个uid，但可以存在两条以上数据
    demoTime = DateTimeField() #
    inTeacher = ReferenceField(Teacher)#录入人，登录人，可空
    callInTime = DateTimeField() #来电时间
    regTime = DateTimeField() #登记时间
    regTeacher = ReferenceField(Teacher) #接单（拜访）老师，如果用户自己登记，分配给网络部或url链接对应校区主任
    regTeacherName = StringField()
    regBranch = ReferenceField(Branch) #接单部门，可以是别的部门
    regBranchName = StringField()
    branch = ReferenceField(Branch) #所在校区,可空
    branchName = StringField()
    source = ReferenceField(Source)
    referrer = StringField() #转介人，如果是学员，记录其code
    referrerName = StringField() #转介人，可展示内容
    referTeacher = StringField() #转介老师Id
    referTeacherName = StringField() #转介老师姓名
    co_teacher = ListField(ReferenceField(Teacher)) #共同拜访老师
    code = StringField() #代码 形如：XX2016111801
    name = StringField()
    name2 = StringField()
    gender = StringField()
    birthday = DateTimeField()
    yearMonth = StringField()
    siblingName = StringField()
    siblingName2 = StringField()
    siblingName3 = StringField()
    prt1mobile = StringField() #家长电话
    prt2mobile = StringField()
    prt1 = StringField() #家长1
    prt2 = StringField() #家长2
    wantClass = StringField()#班型
    wantDemoTime = DateTimeField()
    gradeClass = StringField() #班级
    teacher = ReferenceField(Teacher) #任课老师
    teacherName = StringField()
    status = IntField()  # 学生状态：1签约，2退费，3结束,0-未签约,5-集训
    dup = IntField()#-1 冻结,0-正常
    resolved = IntField() #如果冻结，是否已解决冲突:-1冲突，0无冲突
    sourceType = StringField()#A -网络,B-拜访,C-转介,D-walkin
    sourceCategory = ReferenceField(SourceCategory)
    contract = ListField(ReferenceField(Contract))
    demo = ListField(StringField())
    isDemo = IntField()
    memo = StringField()
    probability = StringField()#A,B,C
    deposit = IntField() #定金金额
    depositBranch = IntField() #在哪个校区交的定金
    depositCompany = IntField() #是否进公帐：1-公帐，0-未进公帐   
    depositDate = DateTimeField()
    depositCollecter = ReferenceField(Teacher)
    depositWay = StringField()
    depositStatus = IntField() #1-change to contract,2-returned
    checked = BooleanField()
    lessons = FloatField() #change from int to float --20180623 已上课时
    commonCheckin = IntField()#共用合同的所有学生签到总次数
    lessonLeft = IntField() #剩余课时
    branch2 = StringField()
    branch3 = StringField()
    branch4 = StringField()
    branch2name = StringField()
    branch3name = StringField()
    branch4name = StringField()
    netStatus = IntField()#网络部分类，0（null）-有效，-1-无效，
    school = StringField()
    kindergarten = StringField()
    cdate = DateTimeField()#change to type C date
    siblingId = StringField()#sibling student id
    deleted = BooleanField()
    memo2 = StringField()
    ########  reimind
    remindTime = DateTimeField()
    remind_txt = StringField()
    isDone = IntField() #提醒是否完成
    remindTeacher = ReferenceField(Teacher)
    remindTeacherName = StringField()
    track = StringField()
    contractDeadline = DateTimeField() #合同预计结束日期
    lessonStartDate = DateTimeField() #合同实际开课日期
    canStop = BooleanField()
    resolver = ReferenceField(Teacher)
    Bsub = StringField()#渠道B的细分，比如：早，晚拜访
    meta = {
        'collection': 'student'
    }


class GradeClass(Document):
    name = StringField()
    start_date = DateTimeField()  # 开班时间
    school_day = IntField()  # 上课日
    school_time = StringField()  # 上课时间
    classroom = IntField()  # 教室
    teacher = ReferenceField("Teacher")  # 老师
    students = ListField(ReferenceField(Student))
    created_at = DateTimeField()  # 创建时间
    gradeClass_type = IntField()  # 课程类型：正常，补课，试听，其他
    demoIsFinish = IntField()# 1:finish,-1:cancel
    info = StringField()
    branch = ReferenceField(Branch)
    fromLast = IntField()
    toLast = IntField()
    deleted = IntField()#1-deleted

    meta = {
        'collection': 'gradeClass'
    }

class TeacherRemind(Document):
    student = ReferenceField(Student)  # student
    remindTeachers = ListField(ReferenceField(Teacher))  # list of teacher
    isRemind = IntField()
    remindTime = DateTimeField()
    remind_txt = StringField()  # 填写内容
    branch = StringField()
    regBranch = StringField()
    isDone = IntField() #是否完成
    regTime = DateTimeField()
    meta = {'collection': 'TeacherRemind'}

class StudentTrack(Document):
    student = ReferenceField(Student)  # student
    teacher = ReferenceField(Teacher)  # teacher
    trackTime = DateTimeField()
    recordTime = DateTimeField()
    track_txt = StringField()  # 填写内容
    deleted = IntField()
    branch = StringField()
    important = IntField()
    meta = {'collection': 'StudentTrack'}

class Stat(Document):
    dayTag = StringField()
    visit = IntField()
    demo = IntField()
    sign = IntField()
    signNewwork = IntField()
   
class StudentFile(Document):
    branch = StringField()
    teacher = StringField()
    student = ReferenceField(Student)
    studentName = StringField()
    filepath = StringField()
    filename = StringField()
    fileType = IntField() #1-pic,2-video,3-branch
    fileCreateTime = DateTimeField()
    memo = StringField()
    order = IntField()
    selected = IntField()
    contractId = StringField()
    meta = {'collection': 'studentFile'}

class SMSTemplate(Document):
    branch = StringField()
    title = StringField()
    type = StringField()
    isDefault = IntField() #1-default
    txt = StringField()  # 填写内容
    meta = {'collection': 'SMSTemplate'}

