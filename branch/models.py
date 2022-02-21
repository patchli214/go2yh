#!/usr/bin/env python
# -*- coding:utf-8 -*-

from django.db import models
from mongoengine import *

class City(Document):
    sn = IntField() #顺序号
    cityName= StringField()
    dealDuration = IntField()
    financialAdmin = StringField()  #财务审批老师ID（teacher.model.Teacher）
    financialRefund = StringField()  #财务退费操作老师ID（teacher.model.Teacher）
    financialReceipt = StringField()  #财务开发票老师ID（teacher.model.Teacher）
    financialReimburse = StringField() #报销人
    financialReimburse2 = StringField() #报销人2（无发票）
    meta = {
        'collection': 'city'
    }

class Branch(Document): #校区
    sn = IntField() #顺序号
    city = ReferenceField(City)
    branchName = StringField()
    branchAddr = StringField()
    branchRooms = IntField()
    branchTel = StringField()
    branchCode = StringField()
    excel = BooleanField()
    type = IntField() #None,0-school; 1-headquarter(网络部)
    payBranch = ListField(StringField()) #可以为本部门付账单的外地非业务部门，比如北京财务可以为上海总部等报销
    deleted = BooleanField()
    isY19 = BooleanField()
    meta = {
        'collection': 'branch'
    }
    
class Stat(Document):
    branch = ReferenceField(Branch)
    visit = IntField()
    refer = IntField()
    online = IntField()
    album = IntField()
    pageShare = IntField()
    pageReg = IntField()
    pageNum = IntField()

class Vocation(Document):
    beginDate = DateTimeField()
    endDate = DateTimeField()
    city = ReferenceField(City)
    meta = {
        'collection': 'Vocation'
    }

class ReimburseItem(Document):
    rid = StringField() #Reimburse oid
    branch = ReferenceField(Branch)
    applicant = StringField() #申请人ID
    appDate = DateTimeField()
    paidDate = DateTimeField()
    status = IntField() #参见tools.constant.ReimburseStatus
    
    type = StringField() #报销种类，办公用品、电费、玩具、课间食品等
    typeName = StringField()
    amount = FloatField() #金额
    itemName = StringField() #商品或服务名
    count = IntField() #数量
    meta = {
        'collection': 'ReimburseItem'
    }

#报销或请款单
class Reimburse(Document): 
    city = ReferenceField(City)
    branch = ReferenceField(Branch)
    payBranch = ReferenceField(Branch) 
    applicant = StringField() #申请人ID
    applicantName = StringField() #申请人姓名
    branchLeader = StringField() #部门审批人ID
    branchLeaderName = StringField() #部门审批人
    cashier = StringField() #出纳
    appDate = DateTimeField() #申请日期
    paidDate = DateTimeField()#报销单：报销日期；请款单：借款日期
    status = IntField() #参见tools.constant.ReimburseStatus
    items = ListField(ReferenceField(ReimburseItem))
    hasReceipt = BooleanField() #是否有发票
    sum = FloatField()
    proof = StringField() #票据照片
    appmemo = StringField() #申请人备注
    finmemo = StringField() # 财务备注
    budget = BooleanField() #是否预算内
    #added 20180514
    isBorrow = BooleanField() #是否请款单
    borrowId = StringField() #如果有对应的请款单，对应的请款申请单id号
    isClear = BooleanField() #本请款是否已清
    statusName = StringField()
    typeName = StringField()
    color = StringField()
    op = StringField()
    opName = StringField()
    
    meta = {
        'collection': 'Reimburse'
    }
    